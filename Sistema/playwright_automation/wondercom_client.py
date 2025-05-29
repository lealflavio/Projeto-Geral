"""
Cliente Playwright para automação do Portal Wondercom.
Substitui a implementação Selenium existente.
"""
import asyncio
import logging
import re
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup
from utils.selectors import Selectors
from utils.wait_strategies import AdaptiveWait, retry_async, wait_for_network_idle
import config

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
        self.adaptive_wait = AdaptiveWait(config.DEFAULT_TIMEOUT)
    
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
            viewport={"width": config.VIEWPORT_WIDTH, "height": config.VIEWPORT_HEIGHT}
        )
        
        # Habilitar logs de console
        self.context.on("console", lambda msg: logger.debug(f"Console {msg.type}: {msg.text}"))
        
        # Criar página
        self.page = await self.context.new_page()
        
        # Configurar timeouts
        self.page.set_default_timeout(self.adaptive_wait.get_timeout())
        self.page.set_default_navigation_timeout(config.NAVIGATION_TIMEOUT)
        
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
    
    @retry_async(max_retries=config.MAX_RETRIES)
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
            await self.page.wait_for_selector(Selectors.SEARCH_PAGE_INDICATOR, 
                                             timeout=self.adaptive_wait.get_timeout())
            
            # Ajustar timeout após sucesso
            self.adaptive_wait.adjust_timeout(True)
            self.page.set_default_timeout(self.adaptive_wait.get_timeout())
            
            logger.info("Login realizado com sucesso.")
            return True
            
        except Exception as e:
            # Ajustar timeout após falha
            self.adaptive_wait.adjust_timeout(False)
            self.page.set_default_timeout(self.adaptive_wait.get_timeout())
            
            logger.error(f"Erro ao realizar login: {e}")
            return False
    
    @retry_async(max_retries=config.MAX_RETRIES)
    async def search_work_order(self, work_order_id):
        """Busca uma ordem de trabalho pelo ID."""
        try:
            # Esperar pelo campo de busca
            await self.page.wait_for_selector(Selectors.SEARCH_FIELD, 
                                             timeout=self.adaptive_wait.get_timeout())
            
            # Limpar campo e preencher
            await self.page.fill(Selectors.SEARCH_FIELD, work_order_id)
            
            # Clicar no botão de pesquisa
            await self.page.click(Selectors.SEARCH_BUTTON)
            
            # Esperar pelos resultados - usando networkidle para garantir que todas as requisições foram completadas
            await wait_for_network_idle(self.page)
            
            # Buscar a linha da WO
            row_selector = Selectors.get_wo_row_selector(work_order_id)
            
            try:
                # Esperar pela linha com timeout adaptativo
                await self.page.wait_for_selector(row_selector, 
                                                timeout=self.adaptive_wait.get_timeout())
                
                # Extrair estado da WO
                estado_wo = await self.extract_wo_state(row_selector)
                
                # Ajustar timeout após sucesso
                self.adaptive_wait.adjust_timeout(True)
                self.page.set_default_timeout(self.adaptive_wait.get_timeout())
                
                # Extrair detalhes completos
                return await self.extract_work_order_details(work_order_id, estado_wo)
                
            except Exception as e:
                # Ajustar timeout após falha
                self.adaptive_wait.adjust_timeout(False)
                self.page.set_default_timeout(self.adaptive_wait.get_timeout())
                
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
    
    @retry_async(max_retries=config.MAX_RETRIES)
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
                            await wait_for_network_idle(self.page)
                            
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
    
    async def clicar_por_texto(self, texto, timeout=None):
        """Clica em um elemento com o texto especificado."""
        if timeout is None:
            timeout = self.adaptive_wait.get_timeout()
            
        try:
            # Usar seletor XPath similar ao original, mas com sintaxe do Playwright
            selector = Selectors.get_button_by_text_selector(texto)
            
            # Esperar pelo elemento e clicar
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.click(selector)
            
            # Ajustar timeout após sucesso
            self.adaptive_wait.adjust_timeout(True)
            self.page.set_default_timeout(self.adaptive_wait.get_timeout())
            
            logger.info(f"Clicado no botão com texto: '{texto}'")
            return True
            
        except Exception as e:
            # Ajustar timeout após falha
            self.adaptive_wait.adjust_timeout(False)
            self.page.set_default_timeout(self.adaptive_wait.get_timeout())
            
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
