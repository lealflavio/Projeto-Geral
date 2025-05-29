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
                tds = linha.find_elements(By.XPATH, ".//td[contains(@class, 'v-table-cell-content')]")
                estado_wo = None
                for td in tds:
                    txt = td.text.strip().upper()
                    if txt and (txt in ["IN PROGRESS", "ALLOCATED", "JOB START", "JOB CLOSED"] or "JOB" in txt or "ALLOCATED" in txt or "PROGRESS" in txt or "CLOSED" in txt):
                        estado_wo = txt
                        break
                if not estado_wo:
                    for td in tds:
                        txt = td.text.strip().upper()
                        if txt:
                            estado_wo = txt
                            break
                if not estado_wo:
                    estado_wo = "DESCONHECIDO"
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

    def cor_para_hex(self, cor_texto):
        """Converte nome de cor para código hexadecimal."""
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

    def extract_work_order_details(self, work_order_id, estado_wo):
        """
        Extrai detalhes da ordem de trabalho da página de detalhes:
        - Descrição (textarea)
        - PLC - Cor da Fibra (input)
        - SLID/Username (input)
        - Morada (input ou textarea)
        - Coordenadas (extraídas da descrição)
        - Dona de Rede (input)
        - Porto Primário do PDO(in) (input)
        - Data Início Agendamento (input)
        - Estado da Intervenção (input)
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
                "dona_rede": "",         # Novo campo: PDO (Dona de Rede)
                "porto_primario": "",    # Novo campo: Porto Primário do PDO(in)
                "data_agendamento": "",  # Novo campo: Data Início Agendamento
                "estado_intervencao": "" # Novo campo: Estado da Intervenção
            }

            # DESCRIÇÃO
            try:
                descricao_element = self.driver.find_element(By.XPATH, "//span[text()='Descrição:']/ancestor::tr//textarea")
                descricao_valor = descricao_element.get_attribute("value") or descricao_element.text
                dados_wo["descricao"] = descricao_valor.strip()
            except Exception as e:
                logger.warning(f"Não foi possível extrair Descrição: {e}")

            # FIBRA
            try:
                fibra_element = self.driver.find_element(By.XPATH, "//span[text()='PLC - Cor da Fibra:']/ancestor::tr//input")
                fibra_valor = fibra_element.get_attribute("value")
                dados_wo["fibra"] = fibra_valor.strip()
            except Exception as e:
                logger.warning(f"Não foi possível extrair Fibra: {e}")

            # SLID/Username
            try:
                slid_element = self.driver.find_element(By.XPATH, "//span[text()='SLID/Username:']/ancestor::tr//input")
                slid_valor = slid_element.get_attribute("value")
                dados_wo["slid"] = slid_valor.strip()
            except Exception as e:
                logger.warning(f"Não foi possível extrair SLID/Username: {e}")

            # MORADA
            try:
                morada_element = self.driver.find_element(By.XPATH, "//span[text()='Morada:']/ancestor::tr//input|//span[text()='Morada:']/ancestor::tr//textarea")
                morada_valor = morada_element.get_attribute("value") or morada_element.text
                dados_wo["morada"] = morada_valor.strip()
            except Exception as e:
                logger.warning(f"Não foi possível extrair Morada: {e}")

            # DONA DE REDE (PDO)
            try:
                dona_rede_element = self.driver.find_element(By.XPATH, "//span[text()='Dona de Rede:']/ancestor::tr//input")
                dona_rede_valor = dona_rede_element.get_attribute("value")
                dados_wo["dona_rede"] = dona_rede_valor.strip()
            except Exception as e:
                logger.warning(f"Não foi possível extrair Dona de Rede: {e}")

            # PORTO PRIMÁRIO
            try:
                porto_element = self.driver.find_element(By.XPATH, "//span[text()='Porto Primário do PDO(in):']/ancestor::tr//input")
                porto_valor = porto_element.get_attribute("value")
                dados_wo["porto_primario"] = porto_valor.strip()
            except Exception as e:
                logger.warning(f"Não foi possível extrair Porto Primário: {e}")

            # DATA INÍCIO AGENDAMENTO
            try:
                data_element = self.driver.find_element(By.XPATH, "//span[text()='Data Início Agendamento:']/ancestor::tr//input")
                data_valor = data_element.get_attribute("value")
                dados_wo["data_agendamento"] = data_valor.strip()
            except Exception as e:
                logger.warning(f"Não foi possível extrair Data Início Agendamento: {e}")
                
            # ESTADO DA INTERVENÇÃO
            try:
                estado_intervencao_element = self.driver.find_element(By.XPATH, "//span[text()='Estado da Intervenção:']/ancestor::tr//input")
                estado_intervencao_valor = estado_intervencao_element.get_attribute("value")
                dados_wo["estado_intervencao"] = estado_intervencao_valor.strip()
            except Exception as e:
                logger.warning(f"Não foi possível extrair Estado da Intervenção: {e}")

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

    def allocate_work_order(self, work_order_id):
        try:
            dados_wo = self.search_work_order(work_order_id)
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