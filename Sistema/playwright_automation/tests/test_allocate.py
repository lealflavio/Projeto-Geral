"""
Teste de busca e alocação de ordem de trabalho usando Playwright.
"""
import asyncio
import logging
import sys
import os

# Adicionar diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wondercom_client import WondercomClient
from utils.wait_strategies import retry_async

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_search_and_allocate():
    """Testa a busca e alocação de uma ordem de trabalho."""
    # Credenciais de teste
    portal_url = "https://portal.wondercom.pt/group/guest/intervencoes"
    username = "flavio.leal"
    password = "MFH8fQgAa4"
    work_order_id = "16722483"
    
    logger.info(f"Iniciando teste de busca e alocação da WO {work_order_id}...")
    
    # Inicializar cliente com modo headless=False para visualizar o navegador
    client = None
    try:
        client = WondercomClient(
            portal_url=portal_url,
            username=username,
            password=password,
            headless=False  # Definir como False para visualizar o navegador
        )
        
        # Iniciar navegador
        await client.start_browser()
        
        # Realizar login
        login_success = await client.login()
        
        if not login_success:
            logger.error("❌ Falha no login, não é possível continuar o teste!")
            return
            
        logger.info("✅ Login realizado com sucesso!")
        
        # Buscar ordem de trabalho
        logger.info(f"Buscando WO {work_order_id}...")
        dados_wo = await client.search_work_order(work_order_id)
        
        if not dados_wo:
            logger.error(f"❌ WO {work_order_id} não encontrada!")
            return
            
        logger.info(f"✅ WO {work_order_id} encontrada com estado: {dados_wo.get('estado', 'N/A')}")
        
        # Tentar alocar a ordem de trabalho
        logger.info(f"Tentando alocar WO {work_order_id}...")
        result = await client.allocate_work_order(work_order_id)
        
        if result.get("success"):
            logger.info(f"✅ Alocação bem-sucedida: {result.get('message')}")
        else:
            logger.error(f"❌ Falha na alocação: {result.get('message')}")
            
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}")
    finally:
        # Fechar navegador
        if client:
            await client.close_browser()

if __name__ == "__main__":
    # Executar teste
    asyncio.run(test_search_and_allocate())
