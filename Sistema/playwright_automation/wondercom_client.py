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
import json
import requests

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
    "OK_BUTTON": "xpath=//span[contains(text(), 'Ok')]/parent::div[contains(@class, 'v-button')]",
    
    # Menu de contexto
    "CONSULTAR_DETALHE": "xpath=//div[contains(@class, 'ctxmenu-name') and contains(text(), 'Consultar Detalhe')]"
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
            
            # Esperar pelos resultados - aumentar timeout para rede
            await wait_for_network_idle(self.page, timeout=15000)  # 15 segundos
            
            # Aguardar um pouco para garantir que a tabela foi carregada
            await asyncio.sleep(2)
            
            # Buscar a célula com o estado da WO - usando o seletor baseado no HTML fornecido
            cell_selector = "//td[contains(@class, 'v-table-cell-content')]//div[contains(@class, 'v-table-cell-wrapper')]"
            
            try:
                # Esperar pela célula com timeout adaptativo
                cell_elements = await self.page.query_selector_all(cell_selector)
                
                if not cell_elements or len(cell_elements) == 0:
                    logger.warning(f"Células da tabela não encontradas para WO {work_order_id}")
                    await self.page.screenshot(path="table_not_found.png")
                    return None
                
                # Encontrar a célula que contém o estado da WO
                estado_wo = None
                for cell in cell_elements:
                    text = await cell.text_content()
                    text = text.strip().upper()
                    if text and (text in ["IN PROGRESS", "ALLOCATED", "JOB START", "JOB CLOSED", "PENDENTE FATURACAO"] or 
                                "JOB" in text or "ALLOCATED" in text or "PROGRESS" in text or 
                                "CLOSED" in text or "PENDENTE" in text):
                        estado_wo = text
                        # Salvar a célula para cliques
                        self.estado_cell = cell
                        break
                
                if not estado_wo:
                    logger.warning(f"Estado da WO {work_order_id} não encontrado")
                    return None
                
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
    
    async def extract_work_order_details(self, work_order_id, estado_wo):
        """Extrai detalhes completos da ordem de trabalho."""
        try:
            dados_wo = {
                "id": work_order_id,
                "estado": estado_wo
            }
            
            # Clicar na célula do estado para selecionar a linha
            if hasattr(self, 'estado_cell') and self.estado_cell:
                # Primeiro clique normal (esquerdo)
                await self.estado_cell.click()
                logger.info(f"Clique normal na célula de estado da WO {work_order_id}")
                
                # Aguardar um pouco para garantir que a linha foi selecionada
                await asyncio.sleep(1)
                
                # Clique com botão direito
                await self.estado_cell.click(button="right")
                logger.info(f"Clique com botão direito na célula de estado da WO {work_order_id}")
                
                # Aguardar um pouco para o menu de contexto aparecer
                await asyncio.sleep(1)
                
                # Clicar em "Consultar Detalhe" no menu de contexto
                consultar_detalhe_selector = "//div[contains(@class, 'ctxmenu-name') and contains(text(), 'Consultar Detalhe')]"
                try:
                    await self.page.click(consultar_detalhe_selector)
                    logger.info("Clicado em 'Consultar Detalhe' no menu de contexto")
                    
                    # Aguardar carregamento dos detalhes
                    await wait_for_network_idle(self.page, timeout=15000)
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Erro ao clicar em 'Consultar Detalhe': {e}")
                    await self.page.screenshot(path="menu_contexto_error.png")
            
            # Extrair morada
            try:
                morada_element = await self.page.query_selector("//div[contains(@class, 'v-label') and contains(text(), 'Morada:')]")
                if morada_element:
                    parent = await morada_element.evaluate("el => el.parentElement")
                    morada_text = await self.page.evaluate("el => el.textContent", parent)
                    morada = morada_text.replace("Morada:", "").strip()
                    dados_wo["morada"] = morada
            except Exception as e:
                logger.warning(f"Erro ao extrair morada: {e}")
            
            # Extrair SLID (PDO)
            try:
                slid_element = await self.page.query_selector("//div[contains(@class, 'v-label') and contains(text(), 'SLID:')]")
                if slid_element:
                    parent = await slid_element.evaluate("el => el.parentElement")
                    slid_text = await self.page.evaluate("el => el.textContent", parent)
                    slid = slid_text.replace("SLID:", "").strip()
                    dados_wo["slid"] = slid
            except Exception as e:
                logger.warning(f"Erro ao extrair SLID: {e}")
            
            # Extrair fibra
            try:
                fibra_element = await self.page.query_selector("//div[contains(@class, 'v-label') and contains(text(), 'Fibra:')]")
                if fibra_element:
                    parent = await fibra_element.evaluate("el => el.parentElement")
                    fibra_text = await self.page.evaluate("el => el.textContent", parent)
                    fibra = fibra_text.replace("Fibra:", "").strip()
                    dados_wo["fibra"] = fibra
            except Exception as e:
                logger.warning(f"Erro ao extrair fibra: {e}")
            
            # Extrair coordenadas da descrição
            try:
                descricao_element = await self.page.query_selector("//div[contains(@class, 'v-label') and contains(text(), 'Descrição:')]")
                if descricao_element:
                    parent = await descricao_element.evaluate("el => el.parentElement")
                    descricao_text = await self.page.evaluate("el => el.textContent", parent)
                    descricao = descricao_text.replace("Descrição:", "").strip()
                    dados_wo["descricao"] = descricao
                    
                    # Extrair coordenadas
                    coord_pattern = r'Coordenadas:\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)'
                    coord_match = re.search(coord_pattern, descricao)
                    if coord_match:
                        dados_wo["latitude"] = coord_match.group(1)
                        dados_wo["longitude"] = coord_match.group(2)
            except Exception as e:
                logger.warning(f"Erro ao extrair descrição: {e}")
            
            # Extrair cliente
            try:
                cliente_element = await self.page.query_selector("//div[contains(@class, 'v-label') and contains(text(), 'Cliente:')]")
                if cliente_element:
                    parent = await cliente_element.evaluate("el => el.parentElement")
                    cliente_text = await self.page.evaluate("el => el.textContent", parent)
                    cliente = cliente_text.replace("Cliente:", "").strip()
                    dados_wo["cliente"] = cliente
            except Exception as e:
                logger.warning(f"Erro ao extrair cliente: {e}")
            
            # Extrair contacto
            try:
                contacto_element = await self.page.query_selector("//div[contains(@class, 'v-label') and contains(text(), 'Contacto:')]")
                if contacto_element:
                    parent = await contacto_element.evaluate("el => el.parentElement")
                    contacto_text = await self.page.evaluate("el => el.textContent", parent)
                    contacto = contacto_text.replace("Contacto:", "").strip()
                    dados_wo["contacto"] = contacto
            except Exception as e:
                logger.warning(f"Erro ao extrair contacto: {e}")
            
            # Extrair tipo de serviço
            try:
                tipo_servico_element = await self.page.query_selector("//div[contains(@class, 'v-label') and contains(text(), 'Tipo de Serviço:')]")
                if tipo_servico_element:
                    parent = await tipo_servico_element.evaluate("el => el.parentElement")
                    tipo_servico_text = await self.page.evaluate("el => el.textContent", parent)
                    tipo_servico = tipo_servico_text.replace("Tipo de Serviço:", "").strip()
                    dados_wo["tipo_servico"] = tipo_servico
            except Exception as e:
                logger.warning(f"Erro ao extrair tipo de serviço: {e}")
            
            # Enviar dados para o backend
            try:
                # URL do backend (ajustar conforme necessário)
                backend_url = "http://localhost:5000/api/work_order_details"
                
                # Enviar dados via POST
                logger.info(f"Enviando dados da WO {work_order_id} para o backend...")
                
                # Simulação do envio para o backend (comentar esta linha e descomentar a próxima em produção)
                logger.info(f"Dados que seriam enviados ao backend: {json.dumps(dados_wo, indent=2)}")
                
                # Em produção, descomentar esta linha:
                # response = requests.post(backend_url, json=dados_wo)
                # logger.info(f"Resposta do backend: {response.status_code} - {response.text}")
                
                return dados_wo
                
            except Exception as e:
                logger.error(f"Erro ao enviar dados para o backend: {e}")
                return dados_wo
                
        except Exception as e:
            logger.error(f"Erro ao extrair detalhes da WO: {e}")
            return {"id": work_order_id, "estado": estado_wo, "erro": str(e)}
    
    async def allocate_work_order(self, work_order_id):
        """
        Método mantido para compatibilidade, mas agora apenas retorna os dados extraídos
        sem realizar a alocação da WO.
        """
        try:
            # Buscar dados da WO
            dados_wo = await self.search_work_order(work_order_id)
            
            if not dados_wo:
                return {
                    "success": False,
                    "message": f"WO {work_order_id} não encontrada.",
                    "dados": None
                }
            
            # Retornar os dados extraídos sem realizar alocação
            return {
                "success": True,
                "message": f"Dados da WO {work_order_id} extraídos com sucesso.",
                "dados": dados_wo
            }
            
        except Exception as e:
            logger.error(f"Erro geral ao processar WO: {e}")
            return {"success": False, "message": str(e)}
    
    async def clicar_por_texto(self, texto, timeout=None):
        """Clica em um elemento com o texto especificado."""
        if timeout is None:
            timeout = self.adaptive_wait.get_timeout()
            
        try:
            # Usar seletor do Selenium
            xpath = f"//span[contains(@class, 'v-button-caption') and contains(text(), '{texto}')]/parent::div[contains(@class, 'v-button')]"
            
            # Esperar pelo elemento e clicar
            await self.page.wait_for_selector(xpath, timeout=timeout)
            await self.page.click(xpath)
            
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
