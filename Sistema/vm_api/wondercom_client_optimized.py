"""
Módulo cliente para automação do Portal Wondercom.
Versão otimizada com esperas adaptativas e melhor performance.
"""
import time
import logging
import re
from functools import wraps
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes para configuração
DEFAULT_TIMEOUT = 30  # Timeout padrão em segundos
MIN_TIMEOUT = 10      # Timeout mínimo para esperas adaptativas
MAX_TIMEOUT = 60      # Timeout máximo para esperas adaptativas
MAX_RETRIES = 3       # Número máximo de tentativas para operações críticas
BACKOFF_FACTOR = 1.5  # Fator de aumento para esperas exponenciais

class AdaptiveWait:
    """Classe para gerenciar esperas adaptativas baseadas na resposta do portal."""
    
    def __init__(self, initial_timeout=DEFAULT_TIMEOUT):
        self.current_timeout = initial_timeout
        self.success_count = 0
        self.failure_count = 0
    
    def adjust_timeout(self, success):
        """Ajusta o timeout com base no sucesso ou falha da operação anterior."""
        if success:
            self.success_count += 1
            self.failure_count = 0
            # Reduz o timeout após 3 sucessos consecutivos, mas não abaixo do mínimo
            if self.success_count >= 3:
                self.current_timeout = max(MIN_TIMEOUT, self.current_timeout * 0.8)
                self.success_count = 0
        else:
            self.failure_count += 1
            self.success_count = 0
            # Aumenta o timeout após cada falha, mas não acima do máximo
            self.current_timeout = min(MAX_TIMEOUT, self.current_timeout * BACKOFF_FACTOR)
    
    def get_timeout(self):
        """Retorna o timeout atual."""
        return self.current_timeout

def retry_on_exception(max_retries=MAX_RETRIES):
    """Decorador para tentar novamente operações que falham com exceções específicas."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            retries = 0
            last_exception = None
            
            while retries < max_retries:
                try:
                    result = func(self, *args, **kwargs)
                    # Se chegou aqui, a operação foi bem-sucedida
                    if hasattr(self, 'adaptive_wait'):
                        self.adaptive_wait.adjust_timeout(True)
                    return result
                except (TimeoutException, StaleElementReferenceException) as e:
                    retries += 1
                    last_exception = e
                    logger.warning(f"Tentativa {retries}/{max_retries} falhou: {e}")
                    
                    # Ajusta o timeout se aplicável
                    if hasattr(self, 'adaptive_wait'):
                        self.adaptive_wait.adjust_timeout(False)
                    
                    # Espera exponencial antes de tentar novamente
                    if retries < max_retries:
                        wait_time = BACKOFF_FACTOR ** retries
                        logger.info(f"Aguardando {wait_time:.1f}s antes da próxima tentativa...")
                        time.sleep(wait_time)
            
            # Se chegou aqui, todas as tentativas falharam
            logger.error(f"Todas as {max_retries} tentativas falharam. Última exceção: {last_exception}")
            raise last_exception
        
        return wrapper
    return decorator

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
        self.adaptive_wait = AdaptiveWait()
        self.element_cache = {}  # Cache para elementos frequentemente acessados
    
    def __enter__(self):
        self.start_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_driver()
    
    def start_driver(self):
        logger.info("Iniciando o WebDriver do Chrome...")
        service = Service(self.chrome_driver_path)
        options = webdriver.ChromeOptions()
        
        # Otimizações para melhorar performance
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--blink-settings=imagesEnabled=false")  # Desativa carregamento de imagens
        
        # Configurações de performance
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.images": 2,  # Bloqueia imagens
            "disk-cache-size": 4096,
            "javascript.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Usa timeout adaptativo para o WebDriverWait
        self.wait = WebDriverWait(
            self.driver, 
            self.adaptive_wait.get_timeout(),
            poll_frequency=0.5  # Verifica mais frequentemente
        )
        
        self.actions = ActionChains(self.driver)
        return self.driver
    
    def close_driver(self):
        if self.driver:
            logger.info("Fechando o WebDriver...")
            self.driver.quit()
            self.driver = None
            self.wait = None
            self.actions = None
            self.element_cache.clear()  # Limpa o cache ao fechar
    
    def update_wait_timeout(self):
        """Atualiza o timeout do WebDriverWait com o valor atual do adaptive_wait."""
        if self.driver:
            self.wait = WebDriverWait(
                self.driver, 
                self.adaptive_wait.get_timeout(),
                poll_frequency=0.5
            )
    
    def clear_cache(self):
        """Limpa o cache de elementos."""
        self.element_cache.clear()
    
    @retry_on_exception(max_retries=MAX_RETRIES)
    def login(self):
        logger.info(f"Acessando o portal: {self.portal_url}")
        self.driver.get(self.portal_url)
        
        # Espera curta inicial para carregar a página básica
        time.sleep(1)
        
        try:
            # Usa esperas explícitas para cada elemento
            username_field = self.wait.until(EC.visibility_of_element_located((By.ID, "_58_login")))
            username_field.clear()  # Limpa o campo antes de inserir
            username_field.send_keys(self.username)
            
            password_field = self.wait.until(EC.visibility_of_element_located((By.ID, "_58_password")))
            password_field.clear()  # Limpa o campo antes de inserir
            password_field.send_keys(self.password)
            
            # Usa JavaScript para clicar no botão de login (mais rápido e confiável)
            submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']")))
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            logger.info("Login realizado com sucesso.")
            
            # Espera pela página de pesquisa com timeout adaptativo
            self.wait.until(EC.title_contains("Pesquisa de Intervenções"))
            
            # Ajusta o timeout após sucesso
            self.adaptive_wait.adjust_timeout(True)
            self.update_wait_timeout()
            
            return True
        except Exception as e:
            logger.error(f"Erro ao realizar login: {e}")
            # Ajusta o timeout após falha
            self.adaptive_wait.adjust_timeout(False)
            self.update_wait_timeout()
            return False
    
    def get_element_with_cache(self, by, value, timeout=None):
        """Busca um elemento usando cache para melhorar performance."""
        cache_key = f"{by}:{value}"
        
        # Verifica se o elemento está no cache e ainda é válido
        if cache_key in self.element_cache:
            try:
                # Tenta usar o elemento em cache
                element = self.element_cache[cache_key]
                # Verifica se o elemento ainda é válido
                element.is_enabled()  # Isso lançará exceção se o elemento estiver obsoleto
                return element
            except (StaleElementReferenceException, NoSuchElementException):
                # Remove do cache se estiver obsoleto
                del self.element_cache[cache_key]
        
        # Se não estiver no cache ou estiver obsoleto, busca novamente
        if timeout is None:
            timeout = self.adaptive_wait.get_timeout()
        
        wait = WebDriverWait(self.driver, timeout)
        element = wait.until(EC.presence_of_element_located((by, value)))
        
        # Adiciona ao cache
        self.element_cache[cache_key] = element
        return element
    
    @retry_on_exception(max_retries=MAX_RETRIES)
    def search_work_order(self, work_order_id):
        try:
            # Espera curta para garantir que a página está pronta
            time.sleep(0.5)
            
            # Busca o campo de WO com cache
            campo_wo = self.get_element_with_cache(
                By.XPATH, 
                "//input[@class='v-textfield' and @aria-hidden='false']"
            )
            
            # Limpa e preenche o campo
            campo_wo.clear()
            campo_wo.send_keys(work_order_id)
            
            # Espera curta para o campo ser preenchido
            time.sleep(0.5)
            
            # Clica no botão de pesquisa usando JavaScript (mais rápido)
            search_button = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[normalize-space()='Pesquisar']/ancestor::div[contains(@class,'v-button') and not(contains(@class,'v-disabled'))]")
            ))
            self.driver.execute_script("arguments[0].click();", search_button)
            logger.info("Clicado no botão 'Pesquisar'")
            
            # Usa espera adaptativa para resultados
            timeout = self.adaptive_wait.get_timeout()
            logger.info(f"Aguardando resultados com timeout de {timeout:.1f}s")
            
            try:
                # Busca a linha da WO com timeout adaptativo
                linha = WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((
                    By.XPATH, f"//tr[@class='v-table-row'][.//div[contains(text(), '{work_order_id}')]]"
                )))
                
                # Extrai os dados da linha
                tds = linha.find_elements(By.XPATH, ".//td[contains(@class, 'v-table-cell-content')]")
                estado_wo = None
                
                # Processa os dados da linha
                for td in tds:
                    txt = td.text.strip().upper()
                    if txt and (txt in ["IN PROGRESS", "ALLOCATED", "JOB START", "JOB CLOSED"] or 
                               "JOB" in txt or "ALLOCATED" in txt or "PROGRESS" in txt or "CLOSED" in txt):
                        estado_wo = txt
                        break
                
                # Ajusta o timeout após sucesso
                self.adaptive_wait.adjust_timeout(True)
                self.update_wait_timeout()
                
                # Extrai detalhes da WO
                return self.extract_work_order_details(work_order_id, estado_wo)
                
            except TimeoutException:
                logger.warning(f"Timeout ao buscar WO {work_order_id}. Ajustando timeout e tentando novamente.")
                self.adaptive_wait.adjust_timeout(False)
                self.update_wait_timeout()
                raise
                
        except Exception as e:
            logger.error(f"Erro ao buscar WO {work_order_id}: {e}")
            return None
    
    def extract_work_order_details(self, work_order_id, estado_wo):
        """Extrai detalhes da WO com tratamento de erros aprimorado."""
        try:
            # Implementação existente com otimizações
            dados_wo = {
                "id": work_order_id,
                "estado": estado_wo
            }
            
            # Usa BeautifulSoup para extrair dados da página mais rapidamente
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extrai dados com BeautifulSoup (mais rápido que Selenium para extração)
            # Implementação específica depende da estrutura da página
            
            # MORADA
            try:
                morada_elements = soup.select("div.v-label:contains('Morada')")
                if morada_elements:
                    parent = morada_elements[0].parent
                    morada = parent.get_text().replace("Morada:", "").strip()
                    dados_wo["morada"] = morada
            except Exception as e:
                logger.warning(f"Não foi possível extrair Morada: {e}")
            
            # COORDENADAS (busca dentro da descrição)
            descricao = dados_wo.get("descricao", "")
            coord = None
            if descricao:
                # Usa regex compilado para melhor performance
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
    
    @retry_on_exception(max_retries=MAX_RETRIES)
    def allocate_work_order(self, work_order_id):
        try:
            dados_wo = self.search_work_order(work_order_id)
            if not dados_wo:
                return {"success": False, "message": f"WO {work_order_id} não encontrada."}
            
            estado_wo = dados_wo["estado"]
            
            # Verifica se já está no estado desejado
            if estado_wo in ["ALLOCATED", "JOB START"]:
                return {
                    "success": True,
                    "message": f"WO {work_order_id} já está no estado {estado_wo}.",
                    "dados": dados_wo
                }
            
            # Lógica para IN PROGRESS -> ALLOCATED
            if estado_wo == "IN PROGRESS":
                logger.info("Executando etapa de IN PROGRESS -> ALLOCATED")
                
                # Usa método otimizado para clicar
                if self.clicar_por_texto_otimizado("Avançar Auto-Alocacao"):
                    if self.clicar_por_texto_otimizado("Evoluir WorkOrder"):
                        if self.clicar_por_texto_otimizado("Sim"):
                            # Reduz tempo de espera fixo
                            time.sleep(1)
                            
                            if self.clicar_por_texto_otimizado("Ok"):
                                logger.info("Botão 'Ok' da janela de informação clicado com sucesso.")
                            else:
                                logger.warning("ATENÇÃO: Não foi possível clicar no botão 'Ok' da janela de informação.")
                            
                            # Espera adaptativa antes de verificar resultado
                            adaptive_sleep = min(5, self.adaptive_wait.get_timeout() / 4)
                            time.sleep(adaptive_sleep)
                            
                            # Busca dados atualizados
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
            
            # Lógica para outros estados
            logger.info(f"Tentando alocar WO {work_order_id} do estado {estado_wo}")
            
            if self.clicar_por_texto_otimizado("Avançar"):
                # Espera adaptativa
                adaptive_sleep = min(3, self.adaptive_wait.get_timeout() / 6)
                time.sleep(adaptive_sleep)
                
                # Verifica se precisa confirmar
                if "Confirmar" in self.driver.page_source:
                    self.clicar_por_texto_otimizado("Sim")
                    time.sleep(1)
                
                # Busca dados atualizados
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
    
    @retry_on_exception(max_retries=MAX_RETRIES)
    def clicar_por_texto_otimizado(self, texto, timeout=None):
        """Versão otimizada do método clicar_por_texto com cache e retries."""
        if timeout is None:
            timeout = self.adaptive_wait.get_timeout()
        
        try:
            # Usa XPath otimizado e mais específico
            xpath_expression = f"//span[@class='v-button-caption' and normalize-space()='{texto}']/ancestor::div[contains(@class, 'v-button') and not(contains(@class,'v-disabled'))]"
            
            # Usa cache para elementos frequentes
            cache_key = f"button:{texto}"
            
            if cache_key in self.element_cache:
                try:
                    elemento = self.element_cache[cache_key]
                    # Verifica se o elemento ainda é válido
                    elemento.is_enabled()
                except (StaleElementReferenceException, NoSuchElementException):
                    # Remove do cache se estiver obsoleto
                    del self.element_cache[cache_key]
                    elemento = WebDriverWait(self.driver, timeout).until(
                        EC.element_to_be_clickable((By.XPATH, xpath_expression))
                    )
                    self.element_cache[cache_key] = elemento
            else:
                elemento = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, xpath_expression))
                )
                self.element_cache[cache_key] = elemento
            
            # Usa JavaScript para clicar (mais confiável e rápido)
            self.driver.execute_script("arguments[0].click();", elemento)
            logger.info(f"Clicado no botão com texto: '{texto}'")
            
            # Ajusta timeout após sucesso
            self.adaptive_wait.adjust_timeout(True)
            self.update_wait_timeout()
            
            return True
            
        except TimeoutException:
            logger.error(f"Não foi possível encontrar ou clicar no botão com texto '{texto}' dentro de {timeout} segundos.")
            
            # Ajusta timeout após falha
            self.adaptive_wait.adjust_timeout(False)
            self.update_wait_timeout()
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao tentar clicar no botão com texto '{texto}': {e}")
            return False
