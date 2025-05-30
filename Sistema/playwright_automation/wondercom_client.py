"""
Cliente Playwright para automação do Portal Wondercom.
Usando exatamente os mesmos seletores do Selenium para garantir compatibilidade.
"""
import asyncio
import logging
import re
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup
import sys
import os

# Adicionar diretório pai ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.wait_strategies import AdaptiveWait, retry_async, wait_for_network_idle
import config

logger = logging.getLogger(__name__)

# Seletores do Selenium - Definidos diretamente para garantir compatibilidade
SELENIUM_SELECTORS = {
    # Login
    "LOGIN_USERNAME": "id=_58_login",
    "LOGIN_PASSWORD": "id=_58_password",
    "LOGIN_BUTTON": "css=input[type='submit']",
    
    # Pesquisa
    "SEARCH_FIELD": "xpath=//input[contains(@class, 'v-textfield') and not(contains(@style, 'display: none'))]",
    "SEARCH_BUTTON": "xpath=//div[contains(@class, 'v-button-primary') and contains(@class, 'primary')]//span[contains(@class, 'v-button-caption') and contains(text(), 'Pesquisar')]",
    
    # Botões
    "AVANCAR_BUTTON": "xpath=//span[contains(text(), 'Avançar')]/parent::div[contains(@class, 'v-button')]",
    "EVOLUIR_BUTTON": "xpath=//span[contains(text(), 'Evoluir WorkOrder')]/parent::div[contains(@class, 'v-button')]",
    "CONFIRMAR_BUTTON": "xpath=//span[contains(text(), 'Sim')]/parent::div[contains(@class, 'v-button')]",
    "OK_BUTTON": "xpath=//span[contains(text(), 'Ok')]/parent::div[contains(@class, 'v-button')]"
}

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
    
    async def _parse_selenium_selector(self, selector):
        """
        Converte seletores no formato Selenium para o formato Playwright.
        Exemplo: "id=login" -> "#login"
                "xpath=//div[@id='test']" -> "//div[@id='test']"
                "css=input[type='submit']" -> "input[type='submit']"
        """
        if selector.startswith("id="):
            return f"#{selector[3:]}"
        elif selector.startswith("xpath="):
            return selector[6:]
        elif selector.startswith("css="):
            return selector[4:]
        return selector
    
    async def _find_element(self, selenium_selector, timeout=None):
        """
        Encontra um elemento usando o seletor no formato Selenium.
        Converte o seletor para o formato Playwright e retorna o elemento.
        """
        if timeout is None:
            timeout = self.adaptive_wait.get_timeout()
            
        parsed_selector = await self._parse_selenium_selector(selenium_selector)
        try:
            element = await self.page.wait_for_selector(parsed_selector, timeout=timeout)
            return element
        except Exception as e:
            logger.error(f"Erro ao encontrar elemento com seletor '{selenium_selector}': {e}")
            return None
    
    @retry_async(max_retries=config.MAX_RETRIES)
    async def login(self):
        """Realiza login no portal Wondercom usando seletores do Selenium."""
        logger.info(f"Acessando o portal: {self.portal_url}")
        
        try:
            # Navegar para o portal
            await self.page.goto(self.portal_url)
            
            # Preencher credenciais - usando os seletores do Selenium
            username_element = await self._find_element(SELENIUM_SELECTORS["LOGIN_USERNAME"])
            password_element = await self._find_element(SELENIUM_SELECTORS["LOGIN_PASSWORD"])
            
            if not username_element or not password_element:
                logger.error("Não foi possível encontrar os campos de login")
                return False
                
            await username_element.fill(self.username)
            await password_element.fill(self.password)
            
            # Clicar no botão de login
            login_button = await self._find_element(SELENIUM_SELECTORS["LOGIN_BUTTON"])
            if not login_button:
                logger.error("Não foi possível encontrar o botão de login")
                return False
                
            await login_button.click()
            
            # Esperar pela página de pesquisa
            try:
                # Esperar pelo título da página
                await self.page.wait_for_function(
                    "document.title.includes('Pesquisa de Intervenções')",
                    timeout=self.adaptive_wait.get_timeout()
                )
                logger.info("Página de pesquisa encontrada pelo título")
            except Exception as e:
                logger.error(f"Não foi possível encontrar a página de pesquisa: {e}")
                # Capturar screenshot para diagnóstico
                await self.page.screenshot(path="login_error.png")
                return False
            
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
            # Capturar screenshot para diagnóstico
            try:
                await self.page.screenshot(path="login_error.png")
            except:
                pass
            return False
    
    @retry_async(max_retries=config.MAX_RETRIES)
    async def search_work_order(self, work_order_id):
        """Busca uma ordem de trabalho pelo ID usando seletores do Selenium."""
        try:
            # Esperar pelo campo de busca
            search_field = await self._find_element(SELENIUM_SELECTORS["SEARCH_FIELD"], 
                                                 timeout=self.adaptive_wait.get_timeout())
            
            if not search_field:
                logger.error("Campo de busca não encontrado")
                # Capturar screenshot para diagnóstico
                await self.page.screenshot(path="search_field_error.png")
                return None
                
            # Limpar campo e preencher
            await search_field.fill("")  # Limpar campo
            await search_field.fill(work_order_id)
            
            # Clicar no botão de pesquisa
            search_button_selector = SELENIUM_SELECTORS["SEARCH_BUTTON"]
            parsed_selector = await self._parse_selenium_selector(search_button_selector)
            await self.page.click(parsed_selector)
            
            # Esperar pelos resultados
            await wait_for_network_idle(self.page)
            
            # Buscar a linha da WO
            row_selector = f"xpath=//tr[@class='v-table-row'][.//div[contains(text(), '{work_order_id}')]]"
            
            try:
                # Esperar pela linha com timeout adaptativo
                row_element = await self._find_element(row_selector, 
                                                    timeout=self.adaptive_wait.get_timeout())
                
                if not row_element:
                    logger.warning(f"WO {work_order_id} não encontrada")
                    return None
                    
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
        try:
            # Converter seletor para formato Playwright
            parsed_selector = await self._parse_selenium_selector(row_selector)
            
            # Implementação para extrair o estado da linha
            cells = await self.page.query_selector_all(f"{parsed_selector} td")
            
            for cell in cells:
                text = await cell.text_content()
                text = text.strip().upper()
                if text and (text in ["IN PROGRESS", "ALLOCATED", "JOB START", "JOB CLOSED"] or 
                            "JOB" in text or "ALLOCATED" in text or "PROGRESS" in text or "CLOSED" in text):
                    return text
            
            return None
        except Exception as e:
            logger.error(f"Erro ao extrair estado da WO: {e}")
            return None
    
    async def extract_work_order_details(self, work_order_id, estado_wo):
        """Extrai detalhes completos da ordem de trabalho."""
        try:
            dados_wo = {
                "id": work_order_id,
                "estado": estado_wo
            }
            
            # Extrair morada
            try:
                morada_element = await self._find_element("xpath=//div[contains(@class, 'v-label') and contains(text(), 'Morada:')]")
                if morada_element:
                    parent = await morada_element.evaluate("el => el.parentElement")
                    morada_text = await self.page.evaluate("el => el.textContent", parent)
                    morada = morada_text.replace("Morada:", "").strip()
                    dados_wo["morada"] = morada
            except Exception as e:
                logger.warning(f"Erro ao extrair morada: {e}")
            
            # Extrair SLID (PDO)
            try:
                slid_element = await self._find_element("xpath=//div[contains(@class, 'v-label') and contains(text(), 'SLID:')]")
                if slid_element:
                    parent = await slid_element.evaluate("el => el.parentElement")
                    slid_text = await self.page.evaluate("el => el.textContent", parent)
                    slid = slid_text.replace("SLID:", "").strip()
                    dados_wo["slid"] = slid
            except Exception as e:
                logger.warning(f"Erro ao extrair SLID: {e}")
            
            # Extrair fibra
            try:
                fibra_element = await self._find_element("xpath=//div[contains(@class, 'v-label') and contains(text(), 'Fibra:')]")
                if fibra_element:
                    parent = await fibra_element.evaluate("el => el.parentElement")
                    fibra_text = await self.page.evaluate("el => el.textContent", parent)
                    fibra = fibra_text.replace("Fibra:", "").strip()
                    dados_wo["fibra"] = fibra
            except Exception as e:
                logger.warning(f"Erro ao extrair fibra: {e}")
            
            # Extrair coordenadas da descrição
            try:
                descricao_element = await self._find_element("xpath=//div[contains(@class, 'v-label') and contains(text(), 'Descrição:')]")
                if descricao_element:
                    parent = await descricao_element.evaluate("el => el.parentElement")
                    descricao_text = await self.page.evaluate("el => el.textContent", parent)
                    descricao = descricao_text.replace("Descrição:", "").strip()
                    dados_wo["descricao"] = descricao
                    
                    # Extrair coordenadas
                    coord = None
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
            except Exception as e:
                logger.warning(f"Erro ao extrair descrição: {e}")
            
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
                
                # Clicar na linha da WO
                row_selector = f"xpath=//tr[@class='v-table-row'][.//div[contains(text(), '{work_order_id}')]]"
                row_element = await self._find_element(row_selector)
                if not row_element:
                    return {
                        "success": False,
                        "message": f"Não foi possível encontrar a linha da WO {work_order_id}.",
                        "dados": dados_wo
                    }
                
                await row_element.click()
                
                # Clicar com botão direito para abrir menu de contexto
                await self.clicar_com_botao_direito(row_selector)
                
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
            
            # Clicar na linha da WO
            row_selector = f"xpath=//tr[@class='v-table-row'][.//div[contains(text(), '{work_order_id}')]]"
            row_element = await self._find_element(row_selector)
            if not row_element:
                return {
                    "success": False,
                    "message": f"Não foi possível encontrar a linha da WO {work_order_id}.",
                    "dados": dados_wo
                }
            
            await row_element.click()
            
            # Clicar com botão direito para abrir menu de contexto
            await self.clicar_com_botao_direito(row_selector)
            
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
            # Usar seletor do Selenium
            selector = f"xpath=//span[contains(@class, 'v-button-caption') and contains(text(), '{texto}')]/parent::div[contains(@class, 'v-button')]"
            
            # Esperar pelo elemento e clicar
            element = await self._find_element(selector, timeout=timeout)
            if not element:
                logger.error(f"Botão com texto '{texto}' não encontrado")
                return False
                
            await element.click()
            
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
            parsed_selector = await self._parse_selenium_selector(selector)
            element = await self.page.query_selector(parsed_selector)
            if not element:
                logger.error(f"Elemento não encontrado para clique com botão direito: {selector}")
                return False
                
            await element.click(button="right")
            logger.info(f"Clique com botão direito realizado em: {selector}")
            return True
        except Exception as e:
            logger.error(f"Erro ao clicar com botão direito em {selector}: {e}")
            return False
    
    def cor_para_hex(self, nome_cor):
        """Converte nome de cor para código hexadecimal."""
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
