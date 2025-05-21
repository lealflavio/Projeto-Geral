"""
Módulo cliente para automação do Portal Wondercom.
Baseado no script wondercom_portal_automator_v29.py
"""
import time
import logging
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WondercomClient:
    """Cliente para automação do Portal Wondercom."""
    
    def __init__(self, chrome_driver_path, portal_url, username, password):
        """
        Inicializa o cliente Wondercom.
        
        Args:
            chrome_driver_path: Caminho para o chromedriver
            portal_url: URL do Portal Wondercom
            username: Nome de usuário para login
            password: Senha para login
        """
        self.chrome_driver_path = chrome_driver_path
        self.portal_url = portal_url
        self.username = username
        self.password = password
        self.driver = None
        self.wait = None
        self.actions = None

    def __enter__(self):
        self.start_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_driver()

    def start_driver(self):
        logger.info("Iniciando o WebDriver do Chrome...")
        service = Service(self.chrome_driver_path)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 30)
        self.actions = ActionChains(self.driver)
        return self.driver

    def close_driver(self):
        if self.driver:
            logger.info("Fechando o WebDriver...")
            self.driver.quit()
            self.driver = None
            self.wait = None
            self.actions = None

    def login(self):
        logger.info(f"Acessando o portal: {self.portal_url}")
        self.driver.get(self.portal_url)
        time.sleep(3)
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, "_58_login"))).send_keys(self.username)
            self.wait.until(EC.visibility_of_element_located((By.ID, "_58_password"))).send_keys(self.password)
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))).click()
            logger.info("Login realizado com sucesso.")
            time.sleep(4)
            self.wait.until(EC.title_contains("Pesquisa de Intervenções"))
            return True
        except Exception as e:
            logger.error(f"Erro ao realizar login: {e}")
            return False

    def search_work_order(self, work_order_id):
        try:
            time.sleep(2)
            campo_wo = self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//input[@class='v-textfield' and @aria-hidden='false']")
            ))
            campo_wo.clear()
            campo_wo.send_keys(work_order_id)
            time.sleep(3)
            self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[normalize-space()='Pesquisar']/ancestor::div[contains(@class,'v-button') and not(contains(@class,'v-disabled'))]")
            )).click()
            logger.info("Clicado no botão 'Pesquisar'")
            time.sleep(10)
            try:
                linha = self.wait.until(EC.visibility_of_element_located((
                    By.XPATH, f"//tr[@class='v-table-row'][.//div[contains(text(), '{work_order_id}')]]"
                )))
                estado_element = linha.find_element(By.XPATH, ".//td[contains(@class, 'v-table-cell-content')][div[contains(text(),'IN PROGRESS') or contains(text(),'ALLOCATED') or contains(text(),'JOB START')]]")
                estado_wo = estado_element.text.strip().upper()
                logger.info(f"Estado atual da WO: {estado_wo}")
                linha.click()
                time.sleep(2)
                self.actions.context_click(linha).perform()
                time.sleep(2)
                self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[@class='ctxmenu-name' and normalize-space()='Consultar Detalhe']")
                )).click()
                logger.info("Clicado em 'Consultar Detalhe'")
                time.sleep(8)
                return self.extract_work_order_details(work_order_id, estado_wo)
            except TimeoutException:
                logger.error(f"WO {work_order_id} não encontrada.")
                return None
        except Exception as e:
            logger.error(f"Erro ao pesquisar WO: {e}")
            return None

    def extract_work_order_details(self, work_order_id, estado_wo):
        """
        Extrai detalhes da ordem de trabalho da página de detalhes.
        - Descrição
        - PLC - Cor da Fibra (exibida como 'Fibra')
        - SLID/Username
        - Morada (endereço)
        - Coordenadas (extraídas do final da descrição, se houver)
        """
        try:
            dados_wo = {
                "id": work_order_id,
                "estado": estado_wo,
                "descricao": None,
                "fibra": None,          # Exibe PLC - Cor da Fibra
                "slid": None,
                "morada": None,
                "coordenadas": None
            }
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            rotulos_desejados = {
                "descricao": "Descrição:",
                "fibra": "PLC - Cor da Fibra:",
                "slid": "SLID/Username:",
                "morada": "Morada:"
            }

            for tr in soup.find_all('tr', class_='v-formlayout-row'):
                label_td = tr.find('td', class_='v-formlayout-captioncell')
                content_td = tr.find('td', class_='v-formlayout-contentcell')
                if not label_td or not content_td:
                    continue
                label_texto = label_td.get_text(strip=True)
                for campo, rotulo in rotulos_desejados.items():
                    if label_texto == rotulo:
                        input_element = content_td.find(['input', 'textarea'])
                        if input_element:
                            valor = input_element.get('value') or input_element.text.strip()
                            dados_wo[campo] = valor

            # Extração das coordenadas do final da descrição (ex: "-23.561684, -46.625378")
            descricao = dados_wo.get("descricao", "")
            if descricao:
                match = re.search(r'([+-]?\d{1,3}\.\d+)[,\s]+([+-]?\d{1,3}\.\d+)\s*$', descricao)
                if match:
                    lat = match.group(1)
                    lng = match.group(2)
                    dados_wo["coordenadas"] = f"{lat},{lng}"
                else:
                    dados_wo["coordenadas"] = None

            return dados_wo
        except Exception as e:
            logger.error(f"Erro ao extrair detalhes da WO: {e}")
            return {
                "id": work_order_id,
                "estado": estado_wo,
                "erro": str(e)
            }

    def allocate_work_order(self, work_order_id):
        try:
            dados_wo = self.search_work_order(work_order_id)
            if not dados_wo:
                return {"success": False, "message": f"WO {work_order_id} não encontrada."}
            estado_wo = dados_wo["estado"]
            if estado_wo in ["ALLOCATED", "JOB START"]:
                return {
                    "success": True,
                    "message": f"WO {work_order_id} já está no estado {estado_wo}.",
                    "dados": dados_wo
                }
            if estado_wo == "IN PROGRESS":
                logger.info("Executando etapa de IN PROGRESS -> ALLOCATED")
                if self.clicar_por_texto("Avançar Auto-Alocacao"):
                    if self.clicar_por_texto("Evoluir WorkOrder"):
                        if self.clicar_por_texto("Sim"):
                            time.sleep(2)
                            if self.clicar_por_texto("Ok"):
                                logger.info("Botão 'Ok' da janela de informação clicado com sucesso.")
                            else:
                                logger.warning("ATENÇÃO: Não foi possível clicar no botão 'Ok' da janela de informação.")
                            time.sleep(5)
                            dados_atualizados = self.search_work_order(work_order_id)
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
            logger.info(f"Tentando alocar WO {work_order_id} do estado {estado_wo}")
            if self.clicar_por_texto("Avançar"):
                time.sleep(3)
                if "Confirmar" in self.driver.page_source:
                    self.clicar_por_texto("Sim")
                    time.sleep(2)
                dados_atualizados = self.search_work_order(work_order_id)
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

    def clicar_por_texto(self, texto, timeout=15):
        try:
            xpath_expression = f"//span[@class='v-button-caption' and normalize-space()='{texto}']/ancestor::div[contains(@class, 'v-button') and not(contains(@class,'v-disabled'))]"
            elemento = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_expression)))
            self.driver.execute_script("arguments[0].click();", elemento)
            logger.info(f"Clicado no botão com texto: '{texto}'")
            return True
        except TimeoutException:
            logger.error(f"Não foi possível encontrar ou clicar no botão com texto '{texto}' dentro de {timeout} segundos.")
            return False
        except Exception as e:
            logger.error(f"Erro ao tentar clicar no botão com texto '{texto}': {e}")
            return False
