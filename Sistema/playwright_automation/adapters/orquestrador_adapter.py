"""
Adaptador para o orquestrador usando Playwright.
"""
import logging
import asyncio
from ..wondercom_client import WondercomClient
from .wondercom_integration import WondercomIntegration

logger = logging.getLogger(__name__)

class OrquestradorAdapter:
    """Adaptador para o orquestrador usando Playwright."""
    
    @staticmethod
    async def alocar_wo(work_order_id, credenciais):
        """
        Adaptador para a função de alocação de WO.
        Utiliza o WondercomIntegration para realizar a alocação.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            credenciais (dict): Credenciais do técnico (username, password)
            
        Returns:
            dict: Resultado da alocação
        """
        logger.info(f"Iniciando alocação da WO: {work_order_id}")
        
        try:
            # Usar o adaptador de integração
            result = await WondercomIntegration.alocar_wo(work_order_id, credenciais)
            return result
            
        except Exception as e:
            logger.error(f"Erro na alocação da WO {work_order_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
