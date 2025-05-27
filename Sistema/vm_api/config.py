"""
Arquivo de configuração para a API REST da VM.
Este arquivo centraliza todas as configurações da API.
"""

import os
from pathlib import Path

# Diretório base do projeto (ajustar conforme a estrutura na VM)
BASE_DIR = Path(__file__).parent.parent

# Configurações da API
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 5000))
API_DEBUG = os.getenv('API_DEBUG', 'False').lower() == 'true'

# Configurações de segurança
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'chave-secreta-temporaria')
API_KEY = os.getenv('API_KEY', '99722340')

# Configurações do Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Configurações de filas
HIGH_PRIORITY_QUEUE = 'high_priority'
NORMAL_PRIORITY_QUEUE = 'normal_priority'
DEAD_LETTER_QUEUE = 'dead_letter'
MAX_RETRIES = 3

# Configurações de callback
DEFAULT_CALLBACK_URL = os.getenv('DEFAULT_CALLBACK_URL', 'https://api.projeto-geral.render.com/api/callbacks/job-result' )

# Configurações de logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', str(BASE_DIR / 'logs' / 'vm_api.log'))

# Caminhos para scripts existentes
SCRIPTS_DIR = BASE_DIR
