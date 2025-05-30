"""
Teste básico de login no portal Wondercom usando Playwright.
Usando exatamente os mesmos seletores do Selenium para garantir compatibilidade.
"""
import asyncio
import logging
import sys
import os

# Configurar path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wondercom_client import WondercomClient

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_login():
    """Testa o login no portal Wondercom."""
    # Credenciais de teste
    portal_url = "https://portal.wondercom.pt/group/guest/intervencoes"
    username = "flavio.leal"
    password = "MFH8fQgAa4"
    
    logger.info("Iniciando teste de login...")
    
    # Inicializar cliente com modo headless=True para ambiente sem interface gráfica
    client = None
    try:
        client = WondercomClient(
            portal_url=portal_url,
            username=username,
            password=password,
            headless=True  # Definir como True para ambiente sem interface gráfica
        )
        
        # Iniciar navegador
        await client.start_browser()
        
        # Realizar login
        login_success = await client.login()
        
        if login_success:
            logger.info("✅ Teste de login bem-sucedido!")
        else:
            logger.error("❌ Teste de login falhou!")
            
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}")
    finally:
        # Fechar navegador
        if client:
            await client.close_browser()

if __name__ == "__main__":
    # Executar teste
    asyncio.run(test_login())
