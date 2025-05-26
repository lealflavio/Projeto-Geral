"""
Adaptador para o módulo orquestrador de PDFs.
Este arquivo conecta a API REST aos scripts existentes de orquestração,
utilizando o cliente Selenium existente para alocação de WO.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path para importar os scripts existentes
sys.path.append(str(Path(__file__).parent.parent.parent))

# Importar os scripts existentes
try:
    import M2_Orquestrador_PDFs as orquestrador
    logger.info("Módulo M2_Orquestrador_PDFs importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar M2_Orquestrador_PDFs: {e}")
    raise

# Importar a integração com o WondercomClient
try:
    from .wondercom_integration import WondercomIntegration
    logger.info("Módulo WondercomIntegration importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar WondercomIntegration: {e}")
    raise

class OrquestradorAdapter:
    @staticmethod
    def processar_pdf(caminho_pdf, tecnico_id, credenciais=None):
        """
        Adaptador para a função de processamento de PDF.
        
        Args:
            caminho_pdf (str): Caminho para o arquivo PDF
            tecnico_id (int): ID do técnico
            credenciais (dict, opcional): Credenciais do técnico
            
        Returns:
            dict: Resultado do processamento
        """
        logger.info(f"Iniciando processamento do PDF: {caminho_pdf} para técnico: {tecnico_id}")
        
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(caminho_pdf):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho_pdf}")
            
            # Chamar a função do script existente
            resultado = orquestrador.processar_pdf(caminho_pdf, tecnico_id)
            logger.info(f"Processamento concluído com sucesso para: {caminho_pdf}")
            
            # Formatar o resultado conforme esperado pela API
            return {
                "status": "success",
                "data": resultado
            }
        except Exception as e:
            logger.error(f"Erro no processamento do PDF {caminho_pdf}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    @staticmethod
    def alocar_wo(work_order_id, credenciais):
        """
        Adaptador para a função de alocação de WO.
        Utiliza o WondercomClient existente para realizar a alocação.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            credenciais (dict): Credenciais do técnico (username, password)
            
        Returns:
            dict: Resultado da alocação
        """
        logger.info(f"Iniciando alocação da WO: {work_order_id}")
        
        # Utilizar a integração com o WondercomClient
        return WondercomIntegration.alocar_wo(work_order_id, credenciais)
