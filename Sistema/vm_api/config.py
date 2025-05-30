"""
Configurações para o sistema VM API.
Adaptado para suportar Playwright em vez de Selenium.
"""

# Configurações do Portal Wondercom
WONDERCOM_PORTAL_URL = "https://portal.wondercom.pt/group/guest/intervencoes"

# Configurações de timeout (em milissegundos)
DEFAULT_TIMEOUT = 30000  # 30 segundos
NAVIGATION_TIMEOUT = 60000  # 60 segundos
MAX_RETRIES = 3

# Configurações de viewport
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080

# Configurações de diretórios
TEMP_DIR = "/tmp"
LOG_DIR = "/var/log/vm_api"

# Configurações de API
API_PORT = 5000
API_HOST = "0.0.0.0"
API_DEBUG = True

# Configurações de autenticação
AUTH_ENABLED = False
AUTH_TOKEN_EXPIRY = 86400  # 24 horas em segundos

# Configurações de logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
