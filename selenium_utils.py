#!/usr/bin/env python3
"""
Utilitários para interação robusta com o portal Wondercom via Selenium.

Este módulo fornece classes e funções para interação robusta com o portal Wondercom,
incluindo estratégias avançadas de espera, detecção de elementos, e mecanismos
para lidar com carregamentos dinâmicos.
"""

import os
import time
import logging
import json
from datetime import datetime
from typing import Optional, Union, List, Dict, Any, Callable
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    WebDriverException
)

# Configurar logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'selenium_portal.log'))
    ]
)
logger = logging.getLogger('selenium_portal')

# Tentar importar utilitários de caminho
try:
    from config.path_utils import get_path, join_path, ensure_dir_exists
    USING_PATH_UTILS = True
except ImportError:
    logger.warning("Utilitários de caminho não encontrados. Usando caminhos padrão.")
    USING_PATH_UTILS = False
    # Definir caminho padrão para compatibilidade
    DEFAULT_SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
    DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")

# Constantes
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 10
LONG_TIMEOUT = 30
SHORT_TIMEOUT = 5

class ElementNotFoundError(Exception):
    """Exceção personalizada para elemento não encontrado após múltiplas tentativas."""
    pass

class ElementInteractionError(Exception):
    """Exceção personalizada para falha na interação com elemento após múltiplas tentativas."""
    pass

class PortalNavigationError(Exception):
    """Exceção personalizada para falha na navegação no portal."""
    pass

class SessionManager:
    """Gerenciador de sessão para o portal Wondercom."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Inicializa o gerenciador de sessão.
        
        Args:
            cache_dir: Diretório para armazenar cookies e dados de sessão
        """
        if USING_PATH_UTILS:
            self.cache_dir = join_path('cache_dir', create=True)
        else:
            self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
            os.makedirs(self.cache_dir, exist_ok=True)
        
        self.sessions = {}
        self._load_sessions()
    
    def _load_sessions(self) -> None:
        """Carrega sessões salvas do disco."""
        try:
            session_file = os.path.join(self.cache_dir, "sessions.json")
            if os.path.exists(session_file):
                with open(session_file, "r") as f:
                    self.sessions = json.load(f)
                
                # Filtrar sessões expiradas
                now = datetime.now().timestamp()
                self.sessions = {
                    username: session for username, session in self.sessions.items()
                    if session.get("expiry", 0) > now
                }
                
                logger.info(f"Carregadas {len(self.sessions)} sessões válidas")
        except Exception as e:
            logger.error(f"Erro ao carregar sessões: {str(e)}")
            self.sessions = {}
    
    def _save_sessions(self) -> None:
        """Salva sessões no disco."""
        try:
            session_file = os.path.join(self.cache_dir, "sessions.json")
            with open(session_file, "w") as f:
                json.dump(self.sessions, f, indent=2)
            
            logger.info(f"Sessões salvas em {session_file}")
        except Exception as e:
            logger.error(f"Erro ao salvar sessões: {str(e)}")
    
    def get_session(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Obtém dados de sessão para um usuário.
        
        Args:
            username: Nome de usuário
            
        Returns:
            Dados de sessão ou None se não existir ou estiver expirada
        """
        session = self.sessions.get(username)
        if not session:
            return None
        
        # Verificar se a sessão expirou
        if session.get("expiry", 0) < datetime.now().timestamp():
            logger.info(f"Sessão expirada para {username}")
            del self.sessions[username]
            self._save_sessions()
            return None
        
        return session
    
    def save_session(self, username: str, cookies: List[Dict[str, Any]], 
                    expiry_hours: int = 8) -> None:
        """
        Salva dados de sessão para um usuário.
        
        Args:
            username: Nome de usuário
            cookies: Lista de cookies do navegador
            expiry_hours: Horas até a expiração da sessão
        """
        expiry = datetime.now().timestamp() + (expiry_hours * 3600)
        
        self.sessions[username] = {
            "cookies": cookies,
            "expiry": expiry,
            "created_at": datetime.now().isoformat()
        }
        
        self._save_sessions()
        logger.info(f"Sessão salva para {username} (expira em {expiry_hours}h)")
    
    def delete_session(self, username: str) -> None:
        """
        Remove dados de sessão para um usuário.
        
        Args:
            username: Nome de usuário
        """
        if username in self.sessions:
            del self.sessions[username]
            self._save_sessions()
            logger.info(f"Sessão removida para {username}")
    
    def clear_expired_sessions(self) -> int:
        """
        Remove todas as sessões expiradas.
        
        Returns:
            Número de sessões removidas
        """
        count_before = len(self.sessions)
        now = datetime.now().timestamp()
        
        self.sessions = {
            username: session for username, session in self.sessions.items()
            if session.get("expiry", 0) > now
        }
        
        removed = count_before - len(self.sessions)
        if removed > 0:
            self._save_sessions()
            logger.info(f"Removidas {removed} sessões expiradas")
        
        return removed


class PortalInteraction:
    """Classe para interação robusta com o portal Wondercom."""
    
    def __init__(self, headless: bool = True, screenshots_dir: Optional[str] = None):
        """
        Inicializa a classe de interação com o portal.
        
        Args:
            headless: Se True, executa o navegador em modo headless
            screenshots_dir: Diretório para salvar screenshots
        """
        self.driver = None
        self.headless = headless
        self.session_manager = SessionManager()
        
        # Configurar diretório para screenshots
        if USING_PATH_UTILS:
            self.screenshots_dir = join_path('screenshots_dir', create=True)
        else:
            self.screenshots_dir = screenshots_dir or DEFAULT_SCREENSHOTS_DIR
            os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def __enter__(self):
        """Método para uso com context manager."""
        self._setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Fecha recursos ao sair do context manager."""
        self._quit_driver()
    
    def _setup_driver(self) -> None:
        """Configura o driver do Selenium."""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(LONG_TIMEOUT)
            
            logger.info("Driver do Selenium configurado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao configurar driver: {str(e)}")
            raise
    
    def _quit_driver(self) -> None:
        """Fecha o driver do Selenium."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Driver do Selenium fechado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao fechar driver: {str(e)}")
            finally:
                self.driver = None
    
    def take_screenshot(self, nome: str) -> str:
        """
        Captura screenshot da página atual.
        
        Args:
            nome: Nome base para o arquivo de screenshot
            
        Returns:
            Caminho para o arquivo de screenshot
        """
        if not self.driver:
            logger.error("Driver não inicializado para captura de screenshot")
            return None
        
        try:
            # Adicionar timestamp ao nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{nome}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Capturar screenshot
            self.driver.save_screenshot(filepath)
            logger.info(f"Screenshot salvo em: {filepath}")
            
            return filepath
        except Exception as e:
            logger.error(f"Erro ao capturar screenshot: {str(e)}")
            return None
    
    def login(self, url: str, username: str, password: str, 
             username_selector: str, password_selector: str, 
             submit_selector: str) -> bool:
        """
        Realiza login no portal, utilizando cache de sessão quando disponível.
        
        Args:
            url: URL da página de login
            username: Nome de usuário
            password: Senha
            username_selector: Seletor CSS para o campo de usuário
            password_selector: Seletor CSS para o campo de senha
            submit_selector: Seletor CSS para o botão de submit
            
        Returns:
            True se o login foi bem-sucedido, False caso contrário
        """
        if not self.driver:
            self._setup_driver()
        
        # Tentar usar sessão em cache
        session = self.session_manager.get_session(username)
        if session:
            try:
                logger.info(f"Tentando restaurar sessão para {username}")
                self.driver.get(url)
                
                # Adicionar cookies da sessão
                for cookie in session["cookies"]:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.warning(f"Erro ao adicionar cookie: {str(e)}")
                
                # Recarregar a página para aplicar cookies
                self.driver.refresh()
                
                # Verificar se o login foi bem-sucedido
                time.sleep(2)  # Pequena pausa para carregar a página
                
                # Se não encontrar o campo de login, consideramos que já estamos logados
                try:
                    self.driver.find_element(By.CSS_SELECTOR, username_selector)
                    logger.info("Sessão expirada ou inválida, realizando novo login")
                except NoSuchElementException:
                    logger.info(f"Sessão restaurada com sucesso para {username}")
                    return True
            except Exception as e:
                logger.warning(f"Erro ao restaurar sessão: {str(e)}")
        
        # Realizar login normal
        try:
            logger.info(f"Realizando login para {username}")
            self.driver.get(url)
            
            # Capturar screenshot antes do login
            self.take_screenshot(f"pre_login_{username}")
            
            # Preencher formulário de login
            self._wait_and_fill(username_selector, username)
            self._wait_and_fill(password_selector, password)
            
            # Clicar no botão de submit
            self._wait_and_click(submit_selector)
            
            # Aguardar redirecionamento após login
            time.sleep(3)
            
            # Capturar screenshot após o login
            self.take_screenshot(f"pos_login_{username}")
            
            # Verificar se o login foi bem-sucedido
            if username_selector in self.driver.page_source:
                logger.error(f"Falha no login para {username}")
                return False
            
            # Salvar cookies da sessão
            cookies = self.driver.get_cookies()
            self.session_manager.save_session(username, cookies)
            
            logger.info(f"Login realizado com sucesso para {username}")
            return True
        except Exception as e:
            logger.error(f"Erro durante login: {str(e)}")
            self.take_screenshot(f"erro_login_{username}")
            return False
    
    def navegar_para_wo(self, numero_wo: str, url_base: str, 
                       campo_busca_selector: str, botao_busca_selector: str) -> bool:
        """
        Navega para uma Work Order específica.
        
        Args:
            numero_wo: Número da Work Order
            url_base: URL base do portal
            campo_busca_selector: Seletor CSS para o campo de busca
            botao_busca_selector: Seletor CSS para o botão de busca
            
        Returns:
            True se a navegação foi bem-sucedida, False caso contrário
        """
        if not self.driver:
            logger.error("Driver não inicializado para navegação")
            return False
        
        try:
            logger.info(f"Navegando para WO {numero_wo}")
            
            # Navegar para a página de busca
            self.driver.get(url_base)
            
            # Capturar screenshot antes da busca
            self.take_screenshot(f"pre_busca_wo_{numero_wo}")
            
            # Preencher campo de busca
            self._wait_and_fill(campo_busca_selector, numero_wo)
            
            # Clicar no botão de busca
            self._wait_and_click(botao_busca_selector)
            
            # Aguardar resultados
            time.sleep(2)
            
            # Capturar screenshot após a busca
            self.take_screenshot(f"pos_busca_wo_{numero_wo}")
            
            # Verificar se a WO foi encontrada
            if numero_wo not in self.driver.page_source:
                logger.error(f"WO {numero_wo} não encontrada")
                return False
            
            logger.info(f"WO {numero_wo} encontrada com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao navegar para WO {numero_wo}: {str(e)}")
            self.take_screenshot(f"erro_busca_wo_{numero_wo}")
            return False
    
    def preencher_formulario(self, campos: Dict[str, str]) -> bool:
        """
        Preenche um formulário com os dados fornecidos.
        
        Args:
            campos: Dicionário com seletores CSS como chaves e valores a preencher
            
        Returns:
            True se o preenchimento foi bem-sucedido, False caso contrário
        """
        if not self.driver:
            logger.error("Driver não inicializado para preenchimento de formulário")
            return False
        
        try:
            logger.info(f"Preenchendo formulário com {len(campos)} campos")
            
            # Capturar screenshot antes do preenchimento
            self.take_screenshot("pre_preenchimento_formulario")
            
            # Preencher cada campo
            for selector, valor in campos.items():
                self._wait_and_fill(selector, valor)
            
            # Capturar screenshot após o preenchimento
            self.take_screenshot("pos_preenchimento_formulario")
            
            logger.info("Formulário preenchido com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao preencher formulário: {str(e)}")
            self.take_screenshot("erro_preenchimento_formulario")
            return False
    
    def submeter_formulario(self, submit_selector: str) -> bool:
        """
        Submete um formulário.
        
        Args:
            submit_selector: Seletor CSS para o botão de submit
            
        Returns:
            True se a submissão foi bem-sucedida, False caso contrário
        """
        if not self.driver:
            logger.error("Driver não inicializado para submissão de formulário")
            return False
        
        try:
            logger.info("Submetendo formulário")
            
            # Capturar screenshot antes da submissão
            self.take_screenshot("pre_submissao_formulario")
            
            # Clicar no botão de submit
            self._wait_and_click(submit_selector)
            
            # Aguardar processamento
            time.sleep(3)
            
            # Capturar screenshot após a submissão
            self.take_screenshot("pos_submissao_formulario")
            
            logger.info("Formulário submetido com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao submeter formulário: {str(e)}")
            self.take_screenshot("erro_submissao_formulario")
            return False
    
    def _wait_and_find(self, selector: str, by: By = By.CSS_SELECTOR, 
                     timeout: int = DEFAULT_TIMEOUT) -> Any:
        """
        Aguarda e encontra um elemento na página.
        
        Args:
            selector: Seletor do elemento
            by: Método de localização (By.CSS_SELECTOR, By.XPATH, etc.)
            timeout: Tempo máximo de espera em segundos
            
        Returns:
            Elemento encontrado
            
        Raises:
            ElementNotFoundError: Se o elemento não for encontrado após múltiplas tentativas
        """
        for attempt in range(MAX_RETRIES):
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, selector))
                )
                return element
            except (TimeoutException, NoSuchElementException) as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Elemento não encontrado após {MAX_RETRIES} tentativas: {selector}")
                    self.take_screenshot(f"elemento_nao_encontrado_{selector.replace(' ', '_')}")
                    raise ElementNotFoundError(f"Elemento não encontrado: {selector}")
                else:
                    logger.warning(f"Tentativa {attempt+1}/{MAX_RETRIES} falhou para {selector}. Tentando novamente...")
                    time.sleep(1)
    
    def _wait_and_click(self, selector: str, by: By = By.CSS_SELECTOR, 
                      timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Aguarda e clica em um elemento na página.
        
        Args:
            selector: Seletor do elemento
            by: Método de localização (By.CSS_SELECTOR, By.XPATH, etc.)
            timeout: Tempo máximo de espera em segundos
            
        Raises:
            ElementInteractionError: Se não for possível clicar no elemento após múltiplas tentativas
        """
        for attempt in range(MAX_RETRIES):
            try:
                # Primeiro aguarda o elemento estar presente
                element = self._wait_and_find(selector, by, timeout)
                
                # Depois aguarda o elemento estar clicável
                WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, selector))
                )
                
                # Tenta clicar no elemento
                element.click()
                return
            except (StaleElementReferenceException, ElementClickInterceptedException, 
                   ElementNotInteractableException) as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Não foi possível clicar no elemento após {MAX_RETRIES} tentativas: {selector}")
                    self.take_screenshot(f"erro_click_{selector.replace(' ', '_')}")
                    raise ElementInteractionError(f"Não foi possível clicar no elemento: {selector}")
                else:
                    logger.warning(f"Tentativa {attempt+1}/{MAX_RETRIES} falhou para clicar em {selector}. Tentando novamente...")
                    time.sleep(1)
    
    def _wait_and_fill(self, selector: str, valor: str, by: By = By.CSS_SELECTOR, 
                     timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Aguarda e preenche um campo na página.
        
        Args:
            selector: Seletor do elemento
            valor: Valor a ser preenchido
            by: Método de localização (By.CSS_SELECTOR, By.XPATH, etc.)
            timeout: Tempo máximo de espera em segundos
            
        Raises:
            ElementInteractionError: Se não for possível preencher o campo após múltiplas tentativas
        """
        for attempt in range(MAX_RETRIES):
            try:
                # Primeiro aguarda o elemento estar presente
                element = self._wait_and_find(selector, by, timeout)
                
                # Limpar o campo antes de preencher
                element.clear()
                
                # Preencher o campo
                element.send_keys(valor)
                return
            except (StaleElementReferenceException, ElementNotInteractableException) as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Não foi possível preencher o campo após {MAX_RETRIES} tentativas: {selector}")
                    self.take_screenshot(f"erro_preenchimento_{selector.replace(' ', '_')}")
                    raise ElementInteractionError(f"Não foi possível preencher o campo: {selector}")
                else:
                    logger.warning(f"Tentativa {attempt+1}/{MAX_RETRIES} falhou para preencher {selector}. Tentando novamente...")
                    time.sleep(1)
    
    def esperar_carregamento(self, indicador_selector: str, 
                           timeout: int = LONG_TIMEOUT) -> bool:
        """
        Aguarda o carregamento da página monitorando um indicador.
        
        Args:
            indicador_selector: Seletor CSS para o indicador de carregamento
            timeout: Tempo máximo de espera em segundos
            
        Returns:
            True se o carregamento foi concluído, False caso contrário
        """
        try:
            # Aguardar o indicador aparecer
            WebDriverWait(self.driver, SHORT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, indicador_selector))
            )
            
            # Aguardar o indicador desaparecer
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, indicador_selector))
            )
            
            logger.info("Carregamento concluído")
            return True
        except TimeoutException:
            logger.warning(f"Timeout aguardando carregamento (indicador: {indicador_selector})")
            self.take_screenshot("timeout_carregamento")
            return False
        except Exception as e:
            logger.error(f"Erro ao aguardar carregamento: {str(e)}")
            return False
    
    def verificar_elemento_presente(self, selector: str, 
                                  timeout: int = SHORT_TIMEOUT) -> bool:
        """
        Verifica se um elemento está presente na página.
        
        Args:
            selector: Seletor CSS para o elemento
            timeout: Tempo máximo de espera em segundos
            
        Returns:
            True se o elemento está presente, False caso contrário
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return True
        except TimeoutException:
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar elemento: {str(e)}")
            return False


# Exemplo de uso
if __name__ == "__main__":
    import argparse
    
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='Utilitários para interação com o portal Wondercom')
    parser.add_argument('--test', action='store_true', help='Executar teste básico')
    args = parser.parse_args()
    
    if args.test:
        try:
            with PortalInteraction(headless=False) as portal:
                # Teste simples - navegar para uma página
                portal.driver.get("https://www.google.com")
                portal.take_screenshot("teste_google")
                print("Teste concluído com sucesso!")
        except Exception as e:
            print(f"Erro no teste: {str(e)}")
