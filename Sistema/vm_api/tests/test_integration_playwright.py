"""
Script de teste para validar a integração do cliente Playwright com o backend.
Este script testa a extração de dados de uma WO sem realizar alocação.
"""

import sys
import os
import logging
import json
import time
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Adicionar diretório pai ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar o cliente Playwright
from wondercom_client_playwright import WondercomClient

# Credenciais e configurações
PORTAL_URL = "https://portal.wondercom.pt/group/guest/intervencoes"
USERNAME = "seu_usuario"  # Substituir pelo usuário real
PASSWORD = "sua_senha"    # Substituir pela senha real
WORK_ORDER_ID = "16722483"  # ID da WO para teste

def test_extract_wo_data():
    """Testa a extração de dados de uma WO usando o cliente Playwright."""
    logger.info(f"Iniciando teste de extração de dados da WO {WORK_ORDER_ID}...")
    
    start_time = time.time()
    client = None
    
    try:
        # Inicializar o cliente Playwright
        client = WondercomClient(
            portal_url=PORTAL_URL,
            username=USERNAME,
            password=PASSWORD
        )
        
        # Iniciar o driver
        client.start_driver()
        
        # Realizar login
        login_success = client.login()
        if not login_success:
            logger.error("❌ Falha no login. Abortando teste.")
            return False
        
        logger.info("✅ Login realizado com sucesso!")
        
        # Buscar e extrair dados da WO
        dados_wo = client.search_work_order(WORK_ORDER_ID)
        
        if not dados_wo:
            logger.error(f"❌ WO {WORK_ORDER_ID} não encontrada.")
            return False
        
        # Calcular tempo de execução
        execution_time = time.time() - start_time
        logger.info(f"✅ WO {WORK_ORDER_ID} encontrada em {execution_time:.2f} segundos!")
        logger.info(f"Estado atual: {dados_wo.get('estado', 'N/A')}")
        
        # Exibir dados extraídos
        logger.info("Dados extraídos da WO:")
        logger.info(json.dumps(dados_wo, indent=2, ensure_ascii=False))
        
        # Simular envio para o backend
        logger.info("✅ Dados extraídos com sucesso e prontos para envio ao backend!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}")
        return False
        
    finally:
        # Garantir que o navegador seja fechado
        if client:
            client.close_driver()

if __name__ == "__main__":
    # Verificar se as credenciais foram configuradas
    if USERNAME == "seu_usuario" or PASSWORD == "sua_senha":
        logger.error("❌ Configure as credenciais reais no script antes de executar o teste.")
        sys.exit(1)
    
    # Executar o teste
    success = test_extract_wo_data()
    
    # Exibir resultado final
    if success:
        logger.info("✅ Teste concluído com sucesso!")
        sys.exit(0)
    else:
        logger.error("❌ Teste falhou!")
        sys.exit(1)
