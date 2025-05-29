"""
Estratégias de espera para o cliente Playwright.
Implementa métodos auxiliares para esperas adaptativas e retries.
"""
import asyncio
import logging
from functools import wraps
import sys
import os

# Importar config de forma absoluta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

class AdaptiveWait:
    """Classe para gerenciar esperas adaptativas baseadas na resposta do portal."""
    
    def __init__(self, initial_timeout=config.DEFAULT_TIMEOUT):
        self.current_timeout = initial_timeout
        self.success_count = 0
        self.failure_count = 0
    
    def adjust_timeout(self, success):
        """Ajusta o timeout com base no sucesso ou falha da operação anterior."""
        if success:
            self.success_count += 1
            self.failure_count = 0
            # Reduz o timeout após 3 sucessos consecutivos, mas não abaixo do mínimo
            if self.success_count >= 3:
                self.current_timeout = max(config.DEFAULT_TIMEOUT / 3, self.current_timeout * 0.8)
                self.success_count = 0
        else:
            self.failure_count += 1
            self.success_count = 0
            # Aumenta o timeout após cada falha, mas não acima do máximo
            self.current_timeout = min(config.NAVIGATION_TIMEOUT, self.current_timeout * 1.5)
    
    def get_timeout(self):
        """Retorna o timeout atual."""
        return self.current_timeout

def retry_async(max_retries=None):
    """Decorador para tentar novamente operações assíncronas que falham."""
    if max_retries is None:
        max_retries = config.MAX_RETRIES
        
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            last_exception = None
            
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    last_exception = e
                    logger.warning(f"Tentativa {retries}/{max_retries} falhou: {e}")
                    
                    # Espera exponencial antes de tentar novamente
                    if retries < max_retries:
                        wait_time = (config.RETRY_DELAY / 1000) * (1.5 ** retries)
                        logger.info(f"Aguardando {wait_time:.1f}s antes da próxima tentativa...")
                        await asyncio.sleep(wait_time)
            
            # Se chegou aqui, todas as tentativas falharam
            logger.error(f"Todas as {max_retries} tentativas falharam. Última exceção: {last_exception}")
            raise last_exception
        
        return wrapper
    return decorator

async def wait_for_network_idle(page, timeout=None):
    """Espera até que a rede esteja ociosa."""
    if timeout is None:
        timeout = config.NETWORK_IDLE_TIMEOUT
        
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
        return True
    except Exception as e:
        logger.warning(f"Timeout esperando por networkidle: {e}")
        return False
