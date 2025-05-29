"""
Configurações para o cliente Playwright.
"""

# Configurações do navegador
HEADLESS = True
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080

# Timeouts (em milissegundos)
DEFAULT_TIMEOUT = 30000
NAVIGATION_TIMEOUT = 60000
NETWORK_IDLE_TIMEOUT = 5000

# URLs
PORTAL_URL = "https://portal.wondercom.pt/group/guest/intervencoes"

# Configurações de retry
MAX_RETRIES = 3
RETRY_DELAY = 1000  # ms

# Configurações de paralelismo
MAX_CONTEXTS = 5  # Número máximo de contextos paralelos
