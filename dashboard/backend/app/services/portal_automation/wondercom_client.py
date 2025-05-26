import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

# (Opcional) logging para debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WondercomClient:
    def __init__(self, chrome_driver_path, portal_url, username, password):
        self.chrome_driver_path = chrome_driver_path
        self.portal_url = portal_url
        self.username = username
        self.password = password
        self.driver = None
        self.wait = None
        self.actions = None

    def __enter__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        service = Service(self.chrome_driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        self.actions = ActionChains(self.driver)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None
            self.actions = None

    def login(self):
        self.driver.get(self.portal_url)
        time.sleep(2)
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, "_58_login"))).send_keys(self.username)
            self.wait.until(EC.visibility_of_element_located((By.ID, "_58_password"))).send_keys(self.password)
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))).click()
            logger.info("Login realizado com sucesso.")
            time.sleep(4)
            self.wait.until(EC.title_contains("Pesquisa de Intervenções"))
            return True
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return False

    def alocar_wo(self, wo_id):
        try:
            # Aguarda até o campo de busca da WO estar visível
            campo_wo = self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//input[@class='v-textfield' and @aria-hidden='false']")
            ))
            campo_wo.clear()
            campo_wo.send_keys(wo_id)
            time.sleep(1)
            # Botão pesquisar
            btn_search = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[normalize-space()='Pesquisar']/ancestor::div[contains(@class,'v-button') and not(contains(@class,'v-disabled'))]")
            ))
            btn_search.click()
            logger.info("Clicado no botão 'Pesquisar'")
            time.sleep(5)
            # (Opcional) Buscar o status da WO
            try:
                linha = self.wait.until(EC.visibility_of_element_located((
                    By.XPATH, f"//tr[@class='v-table-row'][.//div[contains(text(), '{wo_id}')]]"
                )))
                estado_element = linha.find_element(By.XPATH, ".//td[contains(@class, 'v-table-cell-content')][div[contains(text(),'IN PROGRESS') or contains(text(),'ALLOCATED') or contains(text(),'JOB START')]]")
                wo_status = estado_element.text.strip().upper()
            except TimeoutException:
                logger.error(f"WO {wo_id} não encontrada.")
                return {"status": "error", "error": f"WO {wo_id} não encontrada."}
            return {
                "status": "success",
                "wo_id": wo_id,
                "wo_status": wo_status
            }
        except Exception as e:
            logger.error(f"Erro ao alocar WO: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


class WondercomIntegration:
    @staticmethod
    def alocar_wo(wo_id, credentials):
        with WondercomClient(
            chrome_driver_path="/usr/local/bin/chromedriver",
            portal_url="https://portal.wondercom.pt/group/guest/intervencoes",
            username=credentials["username"],
            password=credentials["password"]
        ) as client:
            logged_in = client.login()
            if not logged_in:
                return {"status": "error", "error": "Falha no login"}
            
            resultado = client.alocar_wo(wo_id)
            return resultado
