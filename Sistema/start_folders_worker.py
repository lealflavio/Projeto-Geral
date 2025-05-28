"""
Script para iniciar o worker de pastas.
Este script inicia o worker especializado para processamento de tarefas relacionadas a pastas.
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/flavioleal/Sistema/logs/folders_worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("folders_worker")

# Adicionar o diretório do Sistema ao PYTHONPATH
sistema_dir = Path("/home/flavioleal/Sistema")
sys.path.insert(0, str(sistema_dir))

# Importar o worker de pastas
try:
    from vm_api.queue.folders_worker import run_worker
    logger.info("Worker de pastas importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar o worker de pastas: {str(e)}")
    sys.exit(1)

if __name__ == "__main__":
    logger.info("Iniciando worker de pastas...")
    try:
        run_worker()
    except Exception as e:
        logger.error(f"Erro ao executar o worker de pastas: {str(e)}")
        sys.exit(1)
