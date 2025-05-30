"""
Teste de busca e alocação de ordem de trabalho usando Playwright.
"""
import asyncio
import logging
import sys
import os
import time

# Configurar path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wondercom_client import WondercomClient

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_allocate():
    """Testa a busca e alocação de uma ordem de trabalho."""
    # Credenciais de teste
    portal_url = "https://portal.wondercom.pt/group/guest/intervencoes"
    username = "flavio.leal"
    password = "MFH8fQgAa4"
    work_order_id = "16722483"
    
    logger.info(f"Iniciando teste de busca e alocação da WO {work_order_id}..." )
    
    # Inicializar cliente
    client = None
    try:
        client = WondercomClient(
            portal_url=portal_url,
            username=username,
            password=password,
            headless=False  # Definir como False para ver o navegador
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
        start_time = time.time()
        dados_wo = await client.search_work_order(work_order_id)
        search_time = time.time() - start_time
        
        if not dados_wo:
            logger.error(f"❌ WO {work_order_id} não encontrada!")
            return
            
        logger.info(f"✅ WO {work_order_id} encontrada em {search_time:.2f} segundos!")
        logger.info(f"Estado atual: {dados_wo.get('estado', 'Desconhecido')}")
        
        # Alocar ordem de trabalho
        start_time = time.time()
        resultado = await client.allocate_work_order(work_order_id)
        allocate_time = time.time() - start_time
        
        if resultado["success"]:
            logger.info(f"✅ Alocação realizada com sucesso em {allocate_time:.2f} segundos!")
            logger.info(f"Mensagem: {resultado['message']}")
            logger.info(f"Estado final: {resultado['dados'].get('estado', 'Desconhecido')}")
        else:
            logger.error(f"❌ Falha na alocação: {resultado['message']}")
            
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}")
    finally:
        # Fechar navegador
        if client:
            await client.close_browser()

if __name__ == "__main__":
    # Executar teste
    asyncio.run(test_allocate())
