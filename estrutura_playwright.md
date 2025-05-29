# Planejamento da Estrutura Playwright

## Visão Geral da Nova Arquitetura

A nova implementação com Playwright será organizada em uma pasta exclusiva chamada `playwright_automation` para permitir testes isolados. A estrutura manterá compatibilidade com a API Flask e o sistema de filas Redis existentes, enquanto substitui completamente a camada de automação Selenium.

## Estrutura de Diretórios

```
Sistema/
└── playwright_automation/
    ├── __init__.py
    ├── wondercom_client.py         # Cliente Playwright principal
    ├── adapters/
    │   ├── __init__.py
    │   ├── wondercom_integration.py # Adaptador para API
    │   └── orquestrador_adapter.py  # Adaptador para orquestrador
    ├── utils/
    │   ├── __init__.py
    │   ├── selectors.py            # Seletores centralizados
    │   └── wait_strategies.py      # Estratégias de espera
    ├── config.py                   # Configurações específicas do Playwright
    ├── requirements.txt            # Dependências do Playwright
    └── tests/                      # Testes isolados
        ├── __init__.py
        ├── test_login.py
        ├── test_search.py
        └── test_allocate.py
```

## Componentes Principais

### 1. Cliente Playwright (`wondercom_client.py`)

```python
"""
Cliente Playwright para automação do Portal Wondercom.
Substitui a implementação Selenium existente.
"""
import asyncio
import logging
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from .utils.selectors import Selectors
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class WondercomClient:
    """Cliente para automação do Portal Wondercom usando Playwright."""
    
    def __init__(self, portal_url, username, password, headless=True):
        self.portal_url = portal_url
        self.username = username
        self.password = password
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    async def __aenter__(self):
        await self.start_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_browser()
    
    async def start_browser(self):
        """Inicia o navegador Playwright."""
        logger.info("Iniciando o navegador Playwright...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        
        # Criar contexto com viewport específico
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        
        # Habilitar logs de console
        self.context.on("console", lambda msg: logger.debug(f"Console {msg.type}: {msg.text}"))
        
        # Criar página
        self.page = await self.context.new_page()
        
        return self.page
    
    async def close_browser(self):
        """Fecha o navegador Playwright."""
        if self.page:
            await self.page.close()
            self.page = None
        
        if self.context:
            await self.context.close()
            self.context = None
        
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
    
    async def login(self):
        """Realiza login no portal Wondercom."""
        logger.info(f"Acessando o portal: {self.portal_url}")
        
        try:
            # Navegar para o portal
            await self.page.goto(self.portal_url)
            
            # Preencher credenciais - Playwright espera automaticamente pelos elementos
            await self.page.fill(Selectors.LOGIN_USERNAME, self.username)
            await self.page.fill(Selectors.LOGIN_PASSWORD, self.password)
            
            # Clicar no botão de login
            await self.page.click(Selectors.LOGIN_BUTTON)
            
            # Esperar pela página de pesquisa
            await self.page.wait_for_selector(Selectors.SEARCH_PAGE_INDICATOR)
            
            logger.info("Login realizado com sucesso.")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao realizar login: {e}")
            return False
    
    async def search_work_order(self, work_order_id):
        """Busca uma ordem de trabalho pelo ID."""
        try:
            # Esperar pelo campo de busca
            await self.page.wait_for_selector(Selectors.SEARCH_FIELD)
            
            # Limpar campo e preencher
            await self.page.fill(Selectors.SEARCH_FIELD, work_order_id)
            
            # Clicar no botão de pesquisa
            await self.page.click(Selectors.SEARCH_BUTTON)
            
            # Esperar pelos resultados - usando networkidle para garantir que todas as requisições foram completadas
            await self.page.wait_for_load_state("networkidle")
            
            # Buscar a linha da WO
            row_selector = Selectors.get_wo_row_selector(work_order_id)
            
            try:
                # Esperar pela linha com timeout adaptativo
                await self.page.wait_for_selector(row_selector, timeout=30000)
                
                # Extrair estado da WO
                estado_wo = await self.extract_wo_state(row_selector)
                
                # Extrair detalhes completos
                return await self.extract_work_order_details(work_order_id, estado_wo)
                
            except Exception as e:
                logger.warning(f"WO {work_order_id} não encontrada: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar WO {work_order_id}: {e}")
            return None
    
    async def extract_wo_state(self, row_selector):
        """Extrai o estado da WO da linha de resultado."""
        # Implementação para extrair o estado da linha
        cells = await self.page.query_selector_all(f"{row_selector} td")
        
        for cell in cells:
            text = await cell.text_content()
            text = text.strip().upper()
            if text and (text in ["IN PROGRESS", "ALLOCATED", "JOB START", "JOB CLOSED"] or 
                        "JOB" in text or "ALLOCATED" in text or "PROGRESS" in text or "CLOSED" in text):
                return text
        
        return None
    
    async def extract_work_order_details(self, work_order_id, estado_wo):
        """Extrai detalhes completos da ordem de trabalho."""
        try:
            dados_wo = {
                "id": work_order_id,
                "estado": estado_wo
            }
            
            # Extrair HTML para processamento com BeautifulSoup
            html_content = await self.page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extrair morada (exemplo)
            morada_elements = soup.select("div.v-label:contains('Morada')")
            if morada_elements:
                parent = morada_elements[0].parent
                morada = parent.get_text().replace("Morada:", "").strip()
                dados_wo["morada"] = morada
            
            # Extrair coordenadas da descrição
            descricao = dados_wo.get("descricao", "")
            coord = None
            
            if descricao:
                coord_pattern = re.compile(r'([+-]?\d{1,3}\.\d+)[,\s]+([+-]?\d{1,3}\.\d+)')
                
                for linha in descricao.splitlines():
                    linha = linha.strip()
                    if linha.startswith("PDO Coordenadas:"):
                        partes = linha.split("PDO Coordenadas:")
                        if len(partes) > 1:
                            possiveis_coords = partes[1].strip()
                            match = coord_pattern.match(possiveis_coords)
                            if match:
                                coord = f"{match.group(1)},{match.group(2)}"
                                break
                
                if not coord:
                    match = coord_pattern.search(descricao)
                    if match:
                        coord = f"{match.group(1)},{match.group(2)}"
            
            dados_wo["coordenadas"] = coord
            return dados_wo
            
        except Exception as e:
            logger.error(f"Erro ao extrair detalhes da WO: {e}")
            return {
                "id": work_order_id,
                "estado": estado_wo,
                "erro": str(e)
            }
    
    async def allocate_work_order(self, work_order_id):
        """Aloca uma ordem de trabalho."""
        try:
            dados_wo = await self.search_work_order(work_order_id)
            if not dados_wo:
                return {"success": False, "message": f"WO {work_order_id} não encontrada."}
            
            estado_wo = dados_wo["estado"]
            
            # Verificar se já está no estado desejado
            if estado_wo in ["ALLOCATED", "JOB START"]:
                return {
                    "success": True,
                    "message": f"WO {work_order_id} já está no estado {estado_wo}.",
                    "dados": dados_wo
                }
            
            # Lógica para IN PROGRESS -> ALLOCATED
            if estado_wo == "IN PROGRESS":
                logger.info("Executando etapa de IN PROGRESS -> ALLOCATED")
                
                if await self.clicar_por_texto("Avançar Auto-Alocacao"):
                    if await self.clicar_por_texto("Evoluir WorkOrder"):
                        if await self.clicar_por_texto("Sim"):
                            # Espera curta para processamento
                            await asyncio.sleep(1)
                            
                            if await self.clicar_por_texto("Ok"):
                                logger.info("Botão 'Ok' da janela de informação clicado com sucesso.")
                            else:
                                logger.warning("ATENÇÃO: Não foi possível clicar no botão 'Ok' da janela de informação.")
                            
                            # Espera adaptativa
                            await self.page.wait_for_load_state("networkidle")
                            
                            # Busca dados atualizados
                            dados_atualizados = await self.search_work_order(work_order_id)
                            return {
                                "success": True,
                                "message": f"WO {work_order_id} alocada com sucesso (IN PROGRESS -> ALLOCATED).",
                                "dados": dados_atualizados
                            }
                
                return {
                    "success": False,
                    "message": f"Falha ao alocar WO {work_order_id} (IN PROGRESS -> ALLOCATED).",
                    "dados": dados_wo
                }
            
            # Lógica para outros estados
            logger.info(f"Tentando alocar WO {work_order_id} do estado {estado_wo}")
            
            if await self.clicar_por_texto("Avançar"):
                # Espera adaptativa
                await asyncio.sleep(1)
                
                # Verificar se precisa confirmar
                page_content = await self.page.content()
                if "Confirmar" in page_content:
                    await self.clicar_por_texto("Sim")
                    await asyncio.sleep(1)
                
                # Busca dados atualizados
                dados_atualizados = await self.search_work_order(work_order_id)
                return {
                    "success": True,
                    "message": f"WO {work_order_id} alocada com sucesso.",
                    "dados": dados_atualizados
                }
            
            return {
                "success": False,
                "message": f"Falha ao alocar WO {work_order_id}.",
                "dados": dados_wo
            }
            
        except Exception as e:
            logger.error(f"Erro geral ao alocar WO: {e}")
            return {"success": False, "message": str(e)}
    
    async def clicar_por_texto(self, texto, timeout=15000):
        """Clica em um elemento com o texto especificado."""
        try:
            # Usar seletor XPath similar ao original, mas com sintaxe do Playwright
            selector = Selectors.get_button_by_text_selector(texto)
            
            # Esperar pelo elemento e clicar
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.click(selector)
            
            logger.info(f"Clicado no botão com texto: '{texto}'")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao tentar clicar no botão com texto '{texto}': {e}")
            return False
    
    async def clicar_com_botao_direito(self, selector):
        """Clica com o botão direito em um elemento."""
        try:
            await self.page.click(selector, button="right")
            logger.info(f"Clique com botão direito realizado em: {selector}")
            return True
        except Exception as e:
            logger.error(f"Erro ao clicar com botão direito em {selector}: {e}")
            return False
    
    def cor_para_hex(self, nome_cor):
        """Converte nome de cor para código hexadecimal."""
        # Implementação igual à original
        cores = {
            "AZUL": "#0000FF",
            "VERDE": "#008000",
            "VERMELHO": "#FF0000",
            "AMARELO": "#FFFF00",
            "BRANCO": "#FFFFFF",
            "CINZA": "#808080",
            "MARROM": "#A52A2A",
            "LARANJA": "#FFA500",
            "ROSA": "#FFC0CB",
            "VIOLETA": "#EE82EE",
            "PRETO": "#000000"
        }
        return cores.get(nome_cor.upper(), "#000000")
```

### 2. Seletores Centralizados (`utils/selectors.py`)

```python
"""
Seletores centralizados para o cliente Playwright.
"""

class Selectors:
    """Classe para armazenar todos os seletores usados na automação."""
    
    # Seletores de login
    LOGIN_USERNAME = "#_58_login"
    LOGIN_PASSWORD = "#_58_password"
    LOGIN_BUTTON = "input[type='submit']"
    
    # Seletores de pesquisa
    SEARCH_PAGE_INDICATOR = "text=Pesquisa de Intervenções"
    SEARCH_FIELD = "input.v-textfield[aria-hidden='false']"
    SEARCH_BUTTON = "//span[normalize-space()='Pesquisar']/ancestor::div[contains(@class,'v-button') and not(contains(@class,'v-disabled'))]"
    
    @staticmethod
    def get_wo_row_selector(work_order_id):
        """Retorna o seletor para a linha da WO específica."""
        return f"//tr[@class='v-table-row'][.//div[contains(text(), '{work_order_id}')]]"
    
    @staticmethod
    def get_button_by_text_selector(texto):
        """Retorna o seletor para um botão com o texto específico."""
        return f"//span[@class='v-button-caption' and normalize-space()='{texto}']/ancestor::div[contains(@class, 'v-button') and not(contains(@class,'v-disabled'))]"
```

### 3. Adaptador de Integração (`adapters/wondercom_integration.py`)

```python
"""
Adaptador para integração do cliente Playwright com a API.
"""
import logging
import asyncio
from ..wondercom_client import WondercomClient

logger = logging.getLogger(__name__)

class WondercomIntegration:
    """
    Adaptador para integração do cliente Playwright.
    Fornece métodos para utilizar o cliente Playwright a partir da VM API.
    """
    
    # Configurações padrão
    DEFAULT_PORTAL_URL = "https://portal.wondercom.pt/group/guest/intervencoes"
    
    @staticmethod
    async def alocar_wo(work_order_id, credentials, portal_url=None):
        """
        Aloca uma ordem de trabalho utilizando o cliente Playwright.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            credentials (dict): Credenciais do usuário (username, password)
            portal_url (str, opcional): URL do portal Wondercom
            
        Returns:
            dict: Resultado da alocação
        """
        logger.info(f"Iniciando alocação da WO {work_order_id} via WondercomClient (Playwright)")
        
        client = None
        try:
            # Extrair credenciais
            username = credentials.get('username')
            password = credentials.get('password')
            
            if not username or not password:
                raise ValueError("Credenciais incompletas")
            
            # Definir URL padrão se não fornecida
            portal_url = portal_url or WondercomIntegration.DEFAULT_PORTAL_URL
            
            # Inicializar o cliente Playwright
            async with WondercomClient(
                portal_url=portal_url,
                username=username,
                password=password,
                headless=True
            ) as client:
                # Realizar login
                login_success = await client.login()
                if not login_success:
                    raise Exception("Falha no login")
                
                # Alocar a ordem de trabalho
                result = await client.allocate_work_order(work_order_id)
                
                return result
                
        except Exception as e:
            logger.error(f"Erro na alocação da WO {work_order_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
```

### 4. Adaptador do Orquestrador (`adapters/orquestrador_adapter.py`)

```python
"""
Adaptador para o orquestrador usando Playwright.
"""
import logging
import asyncio
from ..wondercom_client import WondercomClient
from .wondercom_integration import WondercomIntegration

logger = logging.getLogger(__name__)

class OrquestradorAdapter:
    """Adaptador para o orquestrador usando Playwright."""
    
    @staticmethod
    async def alocar_wo(work_order_id, credenciais):
        """
        Adaptador para a função de alocação de WO.
        Utiliza o WondercomIntegration para realizar a alocação.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            credenciais (dict): Credenciais do técnico (username, password)
            
        Returns:
            dict: Resultado da alocação
        """
        logger.info(f"Iniciando alocação da WO: {work_order_id}")
        
        try:
            # Usar o adaptador de integração
            result = await WondercomIntegration.alocar_wo(work_order_id, credenciais)
            return result
            
        except Exception as e:
            logger.error(f"Erro na alocação da WO {work_order_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
```

### 5. Wrapper Síncrono para Compatibilidade com API (`adapters/sync_wrapper.py`)

```python
"""
Wrapper síncrono para funções assíncronas do Playwright.
Permite compatibilidade com a API Flask existente.
"""
import asyncio
import logging
from .wondercom_integration import WondercomIntegration
from .orquestrador_adapter import OrquestradorAdapter

logger = logging.getLogger(__name__)

class SyncWrapper:
    """Wrapper síncrono para funções assíncronas do Playwright."""
    
    @staticmethod
    def alocar_wo(work_order_id, credenciais):
        """
        Versão síncrona da função de alocação de WO.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            credenciais (dict): Credenciais do técnico (username, password)
            
        Returns:
            dict: Resultado da alocação
        """
        try:
            # Criar novo loop de eventos se necessário
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Executar função assíncrona de forma síncrona
            return loop.run_until_complete(
                OrquestradorAdapter.alocar_wo(work_order_id, credenciais)
            )
        except Exception as e:
            logger.error(f"Erro no wrapper síncrono: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
```

### 6. Configuração (`config.py`)

```python
"""
Configurações para o cliente Playwright.
"""

# Configurações do navegador
HEADLESS = True
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080

# Timeouts (em milissegundos)
DEFAULT_TIMEOUT = 30000
NAVIGATION_TIMEOUT = 60000
NETWORK_IDLE_TIMEOUT = 5000

# URLs
PORTAL_URL = "https://portal.wondercom.pt/group/guest/intervencoes"

# Configurações de retry
MAX_RETRIES = 3
RETRY_DELAY = 1000  # ms

# Configurações de paralelismo
MAX_CONTEXTS = 5  # Número máximo de contextos paralelos
```

### 7. Requisitos (`requirements.txt`)

```
playwright==1.40.0
asyncio==3.4.3
beautifulsoup4==4.12.2
flask==2.3.3
redis==4.6.0
```

## Integração com Sistema Existente

Para integrar o novo cliente Playwright com o sistema existente, será necessário:

1. **Modificar o Adaptador Orquestrador**: Atualizar para usar o novo cliente Playwright
2. **Adicionar Wrapper Síncrono**: Para compatibilidade com a API Flask existente
3. **Manter Interface Consistente**: Garantir que os resultados retornados sejam compatíveis

## Estratégia de Execução Paralela

A implementação Playwright suporta execução paralela através de:

1. **Múltiplos Contextos**: Um único navegador com múltiplos contextos isolados
2. **Pool de Contextos**: Sistema de pool para reutilização de contextos
3. **Execução Assíncrona**: Uso de asyncio para operações paralelas

## Próximos Passos

1. Implementar o cliente Playwright base
2. Desenvolver adaptadores e wrappers
3. Criar testes isolados
4. Integrar com sistema existente
5. Otimizar para execução paralela
