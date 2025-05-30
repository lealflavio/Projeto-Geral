"""
Módulo cliente para automação do Portal Wondercom usando Playwright.
Substitui a versão baseada em Selenium, mantendo a mesma interface.
"""

import asyncio
import logging
import re
import json
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WondercomClientPlaywright:
    """Cliente para automação do Portal Wondercom usando Playwright."""
    
    def __init__(self, chrome_driver_path=None, portal_url=None, username=None, password=None):
        """
        Inicializa o cliente Playwright.
        Mantém os mesmos parâmetros do cliente Selenium para compatibilidade.
        
        Args:
            chrome_driver_path: Ignorado, mantido para compatibilidade
            portal_url: URL do portal Wondercom
            username: Nome de usuário para login
            password: Senha para login
        """
        self.portal_url = portal_url
        self.username = username
        self.password = password
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._loop = None
        self._running = False
    
    def __enter__(self):
        """Método para uso com context manager (with)."""
        self.start_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Método para uso com context manager (with)."""
        self.close_driver()
    
    def start_driver(self):
        """
        Inicia o navegador Playwright.
        Equivalente ao start_driver do cliente Selenium.
        """
        logger.info("Iniciando o navegador Playwright...")
        
        # Criar um novo event loop se não existir
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        
        # Iniciar o navegador de forma síncrona
        self._running = True
        self._loop.run_until_complete(self._start_browser())
        return self
    
    async def _start_browser(self):
        """Método assíncrono para iniciar o navegador."""
        self.playwright = await async_playwright().start()
        
        # Configurar opções equivalentes às do Selenium
        browser_args = [
            "--headless",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]
        
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=browser_args
        )
        
        # Criar contexto com viewport específico
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        
        # Criar página
        self.page = await self.context.new_page()
        
        # Configurar timeouts
        self.page.set_default_timeout(30000)  # 30 segundos, equivalente ao WebDriverWait
        self.page.set_default_navigation_timeout(60000)  # 60 segundos para navegação
    
    def close_driver(self):
        """
        Fecha o navegador Playwright.
        Equivalente ao close_driver do cliente Selenium.
        """
        if self._running and self._loop:
            logger.info("Fechando o navegador Playwright...")
            self._loop.run_until_complete(self._close_browser())
            self._running = False
    
    async def _close_browser(self):
        """Método assíncrono para fechar o navegador."""
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
    
    def login(self):
        """
        Realiza login no portal Wondercom.
        Equivalente ao login do cliente Selenium.
        
        Returns:
            bool: True se o login foi bem-sucedido, False caso contrário
        """
        if not self._running or not self._loop:
            logger.error("Navegador não iniciado. Chame start_driver primeiro.")
            return False
        
        return self._loop.run_until_complete(self._login())
    
    async def _login(self):
        """Método assíncrono para realizar login."""
        logger.info(f"Acessando o portal: {self.portal_url}")
        
        try:
            # Navegar para o portal
            await self.page.goto(self.portal_url)
            await asyncio.sleep(3)  # Equivalente ao time.sleep(3) do Selenium
            
            # Preencher credenciais
            await self.page.fill("#_58_login", self.username)
            await self.page.fill("#_58_password", self.password)
            
            # Clicar no botão de login
            await self.page.click("input[type='submit']")
            logger.info("Login realizado com sucesso.")
            
            await asyncio.sleep(4)  # Equivalente ao time.sleep(4) do Selenium
            
            # Verificar se o login foi bem-sucedido
            try:
                await self.page.wait_for_function(
                    "document.title.includes('Pesquisa de Intervenções')",
                    timeout=30000
                )
                return True
            except Exception as e:
                logger.error(f"Erro ao verificar título da página após login: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao realizar login: {e}")
            return False
    
    def search_work_order(self, work_order_id):
        """
        Busca uma ordem de trabalho pelo ID.
        Equivalente ao search_work_order do cliente Selenium.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            
        Returns:
            dict: Dados da ordem de trabalho ou None se não encontrada
        """
        if not self._running or not self._loop:
            logger.error("Navegador não iniciado. Chame start_driver primeiro.")
            return None
        
        return self._loop.run_until_complete(self._search_work_order(work_order_id))
    
    async def _search_work_order(self, work_order_id):
        """Método assíncrono para buscar uma ordem de trabalho."""
        try:
            await asyncio.sleep(2)  # Equivalente ao time.sleep(2) do Selenium
            
            # Encontrar e preencher o campo de busca
            campo_wo = await self.page.wait_for_selector(
                "input.v-textfield[aria-hidden='false']",
                timeout=30000
            )
            
            await campo_wo.fill("")  # Limpar campo
            await campo_wo.fill(work_order_id)
            
            await asyncio.sleep(3)  # Equivalente ao time.sleep(3) do Selenium
            
            # Clicar no botão de pesquisa
            await self.page.click("//span[normalize-space()='Pesquisar']/ancestor::div[contains(@class,'v-button') and not(contains(@class,'v-disabled'))]")
            logger.info("Clicado no botão 'Pesquisar'")
            
            await asyncio.sleep(10)  # Equivalente ao time.sleep(10) do Selenium
            
            try:
                # Encontrar a linha da tabela com o ID da WO
                linha_selector = f"//tr[@class='v-table-row'][.//div[contains(text(), '{work_order_id}')]]"
                linha = await self.page.wait_for_selector(linha_selector, timeout=30000)
                
                # Encontrar todas as células da linha
                tds = await linha.query_selector_all("td.v-table-cell-content")
                
                # Buscar o estado da WO
                estado_wo = None
                for td in tds:
                    txt = await td.text_content()
                    txt = txt.strip().upper()
                    if txt and (txt in ["IN PROGRESS", "ALLOCATED", "JOB START", "JOB CLOSED", "PENDENTE FATURACAO"] or 
                               "JOB" in txt or "ALLOCATED" in txt or "PROGRESS" in txt or 
                               "CLOSED" in txt or "PENDENTE" in txt):
                        estado_wo = txt
                        break
                
                if not estado_wo:
                    # Se não encontrou um estado específico, usar o primeiro texto não vazio
                    for td in tds:
                        txt = await td.text_content()
                        txt = txt.strip().upper()
                        if txt:
                            estado_wo = txt
                            break
                
                if not estado_wo:
                    estado_wo = "DESCONHECIDO"
                
                logger.info(f"Estado atual da WO: {estado_wo}")
                
                # Clicar na linha para selecioná-la
                await linha.click()
                await asyncio.sleep(2)  # Equivalente ao time.sleep(2) do Selenium
                
                # Clicar com botão direito
                await linha.click(button="right")
                await asyncio.sleep(2)  # Equivalente ao time.sleep(2) do Selenium
                
                # Clicar em "Consultar Detalhe" no menu de contexto
                await self.page.click("//div[@class='ctxmenu-name' and normalize-space()='Consultar Detalhe']")
                logger.info("Clicado em 'Consultar Detalhe'")
                
                await asyncio.sleep(8)  # Equivalente ao time.sleep(8) do Selenium
                
                # Extrair detalhes da WO
                return await self._extract_work_order_details(work_order_id, estado_wo)
                
            except Exception as e:
                logger.error(f"WO {work_order_id} não encontrada: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao pesquisar WO: {e}")
            return None
    
    def cor_para_hex(self, cor_texto):
        """
        Converte nome de cor para código hexadecimal.
        Mantém a mesma implementação do cliente Selenium.
        
        Args:
            cor_texto (str): Nome da cor
            
        Returns:
            str: Código hexadecimal da cor
        """
        mapeamento_cores = {
            "AZUL": "#0000FF",
            "VERMELHO": "#FF0000",
            "VERDE": "#00FF00",
            "AMARELO": "#FFFF00",
            "BRANCO": "#FFFFFF",
            "PRETO": "#000000",
            "LARANJA": "#FFA500",
            "VIOLETA": "#8A2BE2",
            "MARROM": "#A52A2A",
            "CINZA": "#808080"
        }
        
        # Normaliza o texto da cor (maiúsculas e sem acentos)
        cor_normalizada = cor_texto.upper().strip() if cor_texto else ""
        
        # Retorna o código hex correspondente ou um valor padrão
        return mapeamento_cores.get(cor_normalizada, "#0000FF")
    
    async def _extract_work_order_details(self, work_order_id, estado_wo):
        """
        Extrai detalhes da ordem de trabalho da página de detalhes.
        Implementação assíncrona para o Playwright.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            estado_wo (str): Estado atual da ordem de trabalho
            
        Returns:
            dict: Dados da ordem de trabalho
        """
        try:
            dados_wo = {
                "id": work_order_id,
                "estado": estado_wo,
                "descricao": "",
                "fibra": "",
                "slid": "",
                "morada": "",
                "coordenadas": None,
                "dona_rede": "",
                "porto_primario": "",
                "data_agendamento": "",
                "estado_intervencao": ""
            }
            
            # Extrair os campos usando JavaScript diretamente no DOM
            # Esta abordagem é mais robusta para aplicações Vaadin onde o HTML pode ser complexo
            js_extract_fields = """
            () => {
                const result = {};
                
                // Função auxiliar para encontrar o valor de um campo baseado no label
                function findFieldValue(labelText) {
                    // Encontrar todos os spans que contêm o texto do label
                    const spans = Array.from(document.querySelectorAll('span'));
                    const labelSpans = spans.filter(span => span.textContent && span.textContent.includes(labelText));
                    
                    if (labelSpans.length === 0) return null;
                    
                    // Para cada span encontrado, procurar o input ou textarea associado
                    for (const span of labelSpans) {
                        // Navegar para cima até encontrar o elemento td.v-formlayout-captioncell
                        let current = span;
                        let captionCell = null;
                        
                        while (current && !captionCell) {
                            if (current.classList && current.classList.contains('v-formlayout-captioncell')) {
                                captionCell = current;
                                break;
                            }
                            current = current.parentElement;
                        }
                        
                        if (!captionCell) continue;
                        
                        // Encontrar o tr pai
                        const tr = captionCell.parentElement;
                        if (!tr) continue;
                        
                        // Encontrar a célula de conteúdo (contentcell) no mesmo tr
                        const contentCell = tr.querySelector('.v-formlayout-contentcell');
                        if (!contentCell) continue;
                        
                        // Procurar por input, textarea ou div com classe v-filterselect-input
                        const input = contentCell.querySelector('input');
                        if (input) return input.value;
                        
                        const textarea = contentCell.querySelector('textarea');
                        if (textarea) return textarea.value;
                        
                        const filterSelect = contentCell.querySelector('.v-filterselect-input');
                        if (filterSelect) return filterSelect.textContent;
                        
                        // Se não encontrou nenhum dos acima, retornar o texto da célula
                        return contentCell.textContent.trim();
                    }
                    
                    return null;
                }
                
                // Extrair cada campo necessário
                const descricao = findFieldValue('Descrição');
                if (descricao) {
                    result.descricao = descricao;
                }
                
                const fibra = findFieldValue('PLC - Cor da Fibra');
                if (fibra) {
                    result.fibra = fibra;
                }
                
                const slid = findFieldValue('SLID/Username');
                if (slid) {
                    result.slid = slid;
                }
                
                const morada = findFieldValue('Morada');
                if (morada) {
                    result.morada = morada;
                }
                
                const donaRede = findFieldValue('Dona de Rede');
                if (donaRede) {
                    result.dona_rede = donaRede;
                }
                
                const portoPrimario = findFieldValue('Porto Primário do PDO(in)');
                if (portoPrimario) {
                    result.porto_primario = portoPrimario;
                }
                
                const dataAgendamento = findFieldValue('Data Início Agendamento');
                if (dataAgendamento) {
                    result.data_agendamento = dataAgendamento;
                }
                
                const estadoIntervencao = findFieldValue('Estado da Intervenção');
                if (estadoIntervencao) {
                    result.estado_intervencao = estadoIntervencao;
                }
                
                return result;
            }
            """
            
            # Executar o script JavaScript
            js_result = await self.page.evaluate(js_extract_fields)
            
            # Processar os resultados
            if js_result:
                # Adicionar campos encontrados aos dados da WO
                for field, value in js_result.items():
                    if value:
                        dados_wo[field] = value.strip()
                        logger.info(f"Campo {field} extraído com sucesso: {value[:50] if len(str(value)) > 50 else value}")
            
            # Se poucos campos foram encontrados, tentar método alternativo com BeautifulSoup
            if len([v for k, v in dados_wo.items() if v and k not in ["id", "estado"]]) <= 1:
                logger.warning("Poucos campos extraídos via JavaScript, tentando método alternativo com BeautifulSoup")
                
                # Obter o HTML da página
                html = await self.page.content()
                
                # Usar BeautifulSoup para extrair os dados
                soup = BeautifulSoup(html, 'html.parser')
                
                # Função para encontrar o valor de um campo baseado no texto do label
                def find_field_value(label_text):
                    # Encontrar todos os spans que contêm o texto do label
                    spans = soup.find_all('span', string=lambda s: s and label_text in s)
                    
                    for span in spans:
                        # Navegar para cima até encontrar o elemento td.v-formlayout-captioncell
                        caption_cell = span
                        while caption_cell and not (caption_cell.name == 'td' and 'v-formlayout-captioncell' in caption_cell.get('class', [])):
                            caption_cell = caption_cell.parent
                        
                        if not caption_cell:
                            continue
                        
                        # Encontrar o tr pai
                        tr = caption_cell.parent
                        if not tr:
                            continue
                        
                        # Encontrar a célula de conteúdo (contentcell) no mesmo tr
                        content_cell = tr.find('td', class_='v-formlayout-contentcell')
                        if not content_cell:
                            continue
                        
                        # Procurar por input, textarea ou div com classe v-filterselect-input
                        input_elem = content_cell.find('input')
                        if input_elem and input_elem.get('value'):
                            return input_elem.get('value')
                        
                        textarea_elem = content_cell.find('textarea')
                        if textarea_elem and textarea_elem.string:
                            return textarea_elem.string
                        
                        filter_select = content_cell.find('div', class_='v-filterselect-input')
                        if filter_select and filter_select.string:
                            return filter_select.string
                        
                        # Se não encontrou nenhum dos acima, retornar o texto da célula
                        if content_cell.text.strip():
                            return content_cell.text.strip()
                    
                    return None
                
                # Extrair cada campo necessário
                campos = {
                    'descricao': 'Descrição',
                    'fibra': 'PLC - Cor da Fibra',
                    'slid': 'SLID/Username',
                    'morada': 'Morada',
                    'dona_rede': 'Dona de Rede',
                    'porto_primario': 'Porto Primário do PDO(in)',
                    'data_agendamento': 'Data Início Agendamento',
                    'estado_intervencao': 'Estado da Intervenção'
                }
                
                for field_key, label_text in campos.items():
                    value = find_field_value(label_text)
                    if value:
                        dados_wo[field_key] = value.strip()
                        logger.info(f"Campo {field_key} extraído com BeautifulSoup: {value[:50] if len(str(value)) > 50 else value}")
            
            # COORDENADAS (busca dentro da descrição)
            descricao = dados_wo.get("descricao", "")
            coord = None
            if descricao:
                for linha in descricao.splitlines():
                    linha = linha.strip()
                    if linha.startswith("PDO Coordenadas:"):
                        partes = linha.split("PDO Coordenadas:")
                        if len(partes) > 1:
                            possiveis_coords = partes[1].strip()
                            match = re.match(r'([+-]?\d{1,3}\.\d+)\s*,\s*([+-]?\d{1,3}\.\d+)', possiveis_coords)
                            if match:
                                coord = f"{match.group(1)},{match.group(2)}"
                                break
                if not coord:
                    match = re.search(r'([+-]?\d{1,3}\.\d+)[,\s]+([+-]?\d{1,3}\.\d+)\s*$', descricao)
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
    
    def extract_work_order_details(self, work_order_id, estado_wo):
        """
        Método síncrono para extrair detalhes da ordem de trabalho.
        Wrapper para o método assíncrono _extract_work_order_details.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            estado_wo (str): Estado atual da ordem de trabalho
            
        Returns:
            dict: Dados da ordem de trabalho
        """
        if not self._running or not self._loop:
            logger.error("Navegador não iniciado. Chame start_driver primeiro.")
            return {
                "id": work_order_id,
                "estado": estado_wo,
                "erro": "Navegador não iniciado"
            }
        
        return self._loop.run_until_complete(self._extract_work_order_details(work_order_id, estado_wo))
    
    def allocate_work_order(self, work_order_id):
        """
        Aloca uma ordem de trabalho.
        Equivalente ao allocate_work_order do cliente Selenium.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            
        Returns:
            dict: Resultado da alocação
        """
        if not self._running or not self._loop:
            logger.error("Navegador não iniciado. Chame start_driver primeiro.")
            return {"success": False, "message": "Navegador não iniciado"}
        
        return self._loop.run_until_complete(self._allocate_work_order(work_order_id))
    
    async def _allocate_work_order(self, work_order_id):
        """Método assíncrono para alocar uma ordem de trabalho."""
        try:
            dados_wo = await self._search_work_order(work_order_id)
            if not dados_wo:
                return {"success": False, "message": f"WO {work_order_id} não encontrada."}
            
            estado_wo = dados_wo["estado"]
            
            # Só tenta alocar se o estado for IN PROGRESS
            if estado_wo != "IN PROGRESS":
                logger.info(f"WO {work_order_id} está no estado '{estado_wo}', não será tentada alocação. Apenas consulta.")
                return {
                    "success": True,
                    "message": f"WO {work_order_id} está no estado '{estado_wo}', apenas consulta realizada.",
                    "dados": dados_wo
                }
            
            # Aqui só chega se for IN PROGRESS → tenta alocar
            logger.info("Executando etapa de IN PROGRESS -> ALLOCATED")
            
            if await self._clicar_por_texto("Avançar Auto-Alocacao"):
                if await self._clicar_por_texto("Evoluir WorkOrder"):
                    if await self._clicar_por_texto("Sim"):
                        await asyncio.sleep(2)  # Equivalente ao time.sleep(2) do Selenium
                        if await self._clicar_por_texto("Ok"):
                            logger.info("Botão 'Ok' da janela de informação clicado com sucesso.")
                        else:
                            logger.warning("ATENÇÃO: Não foi possível clicar no botão 'Ok' da janela de informação.")
                        
                        await asyncio.sleep(5)  # Equivalente ao time.sleep(5) do Selenium
                        dados_atualizados = await self._search_work_order(work_order_id)
                        
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
            
        except Exception as e:
            logger.error(f"Erro geral ao alocar WO: {e}")
            return {"success": False, "message": str(e)}
    
    def clicar_por_texto(self, texto, timeout=15):
        """
        Clica em um elemento com o texto especificado.
        Equivalente ao clicar_por_texto do cliente Selenium.
        
        Args:
            texto (str): Texto do elemento a ser clicado
            timeout (int, opcional): Tempo máximo de espera em segundos
            
        Returns:
            bool: True se o clique foi bem-sucedido, False caso contrário
        """
        if not self._running or not self._loop:
            logger.error("Navegador não iniciado. Chame start_driver primeiro.")
            return False
        
        return self._loop.run_until_complete(self._clicar_por_texto(texto, timeout))
    
    async def _clicar_por_texto(self, texto, timeout=15):
        """Método assíncrono para clicar em um elemento com o texto especificado."""
        try:
            xpath_expression = f"//span[@class='v-button-caption' and normalize-space()='{texto}']/ancestor::div[contains(@class, 'v-button') and not(contains(@class,'v-disabled'))]"
            
            # Esperar pelo elemento e clicar
            await self.page.wait_for_selector(xpath_expression, timeout=timeout * 1000)
            await self.page.click(xpath_expression)
            
            logger.info(f"Clicado no botão com texto: '{texto}'")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao tentar clicar no botão com texto '{texto}': {e}")
            return False


# Classe de compatibilidade para manter a mesma interface do cliente Selenium
class WondercomClient(WondercomClientPlaywright):
    """
    Classe de compatibilidade para manter a mesma interface do cliente Selenium.
    Herda de WondercomClientPlaywright e mantém a mesma API.
    """
    pass
