"""
Wrapper síncrono para funções assíncronas do Playwright.
Permite compatibilidade com a API Flask existente.
"""
import asyncio
import logging
from .wondercom_integration import WondercomIntegration
from .orquestrador_adapter import OrquestradorAdapter

logger = logging.getLogger(__name__)

class SyncWrapper:
    """Wrapper síncrono para funções assíncronas do Playwright."""
    
    @staticmethod
    def alocar_wo(work_order_id, credenciais):
        """
        Versão síncrona da função de alocação de WO.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            credenciais (dict): Credenciais do técnico (username, password)
            
        Returns:
            dict: Resultado da alocação
        """
        try:
            # Criar novo loop de eventos se necessário
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Executar função assíncrona de forma síncrona
            return loop.run_until_complete(
                OrquestradorAdapter.alocar_wo(work_order_id, credenciais)
            )
        except Exception as e:
            logger.error(f"Erro no wrapper síncrono: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
