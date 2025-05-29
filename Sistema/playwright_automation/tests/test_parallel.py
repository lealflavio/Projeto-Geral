"""
Teste de execução paralela usando Playwright.
"""
import asyncio
import logging
import sys
import os
import time
from datetime import datetime

# Adicionar diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wondercom_client import WondercomClient
from utils.wait_strategies import retry_async

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def process_work_order(work_order_id, username, password, portal_url, headless=True):
    """Processa uma ordem de trabalho específica."""
    logger.info(f"Iniciando processamento da WO {work_order_id}...")
    start_time = time.time()
    
    # Inicializar cliente
    client = None
    try:
        client = WondercomClient(
            portal_url=portal_url,
            username=username,
            password=password,
            headless=headless
        )
        
        # Iniciar navegador
        await client.start_browser()
        
        # Realizar login
        login_success = await client.login()
        
        if not login_success:
            logger.error(f"❌ Falha no login para WO {work_order_id}!")
            return {
                "work_order_id": work_order_id,
                "success": False,
                "message": "Falha no login",
                "time_taken": time.time() - start_time
            }
            
        # Buscar e alocar ordem de trabalho
        result = await client.allocate_work_order(work_order_id)
        
        time_taken = time.time() - start_time
        logger.info(f"WO {work_order_id} processada em {time_taken:.2f} segundos")
        
        return {
            "work_order_id": work_order_id,
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "time_taken": time_taken
        }
            
    except Exception as e:
        time_taken = time.time() - start_time
        logger.error(f"❌ Erro ao processar WO {work_order_id}: {e}")
        return {
            "work_order_id": work_order_id,
            "success": False,
            "message": str(e),
            "time_taken": time_taken
        }
    finally:
        # Fechar navegador
        if client:
            await client.close_browser()

async def test_parallel_execution():
    """Testa a execução paralela de múltiplas ordens de trabalho."""
    # Credenciais de teste
    portal_url = "https://portal.wondercom.pt/group/guest/intervencoes"
    username = "flavio.leal"
    password = "MFH8fQgAa4"
    
    # Lista de WOs para testar (usando a mesma para simplificar)
    work_orders = ["16722483", "16722483", "16722483"]
    
    logger.info(f"Iniciando teste de execução paralela com {len(work_orders)} WOs...")
    start_time = time.time()
    
    # Criar tarefas para processamento paralelo
    tasks = [
        process_work_order(
            work_order_id=wo,
            username=username,
            password=password,
            portal_url=portal_url,
            headless=True  # Usar headless=True para execução paralela
        )
        for wo in work_orders
    ]
    
    # Executar tarefas em paralelo
    results = await asyncio.gather(*tasks)
    
    # Calcular tempo total
    total_time = time.time() - start_time
    
    # Analisar resultados
    success_count = sum(1 for r in results if r["success"])
    
    logger.info(f"Teste de execução paralela concluído em {total_time:.2f} segundos")
    logger.info(f"Sucesso: {success_count}/{len(work_orders)}")
    
    # Exibir resultados individuais
    for result in results:
        status = "✅" if result["success"] else "❌"
        logger.info(f"{status} WO {result['work_order_id']}: {result['time_taken']:.2f}s - {result['message']}")
    
    # Comparar com execução sequencial estimada
    sequential_time = sum(r["time_taken"] for r in results)
    logger.info(f"Tempo estimado para execução sequencial: {sequential_time:.2f}s")
    logger.info(f"Ganho de performance: {sequential_time/total_time:.2f}x")
    
    return {
        "total_time": total_time,
        "success_count": success_count,
        "total_count": len(work_orders),
        "results": results,
        "estimated_sequential_time": sequential_time,
        "performance_gain": sequential_time/total_time
    }

if __name__ == "__main__":
    # Executar teste
    asyncio.run(test_parallel_execution())
