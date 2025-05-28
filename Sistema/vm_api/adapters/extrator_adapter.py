"""
Adaptador para o módulo de extração de PDFs.
Este arquivo conecta a API REST aos scripts existentes de extração.
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

# Importar o script existente
try:
    import M1_Extrator_PDF as extrator
    logger.info("Módulo M1_Extrator_PDF importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar M1_Extrator_PDF: {e}")
    raise

class ExtratorAdapter:
    @staticmethod
    def extrair_dados_pdf(caminho_pdf):
        """
        Adaptador para a função de extração de dados do PDF.
        
        Args:
            caminho_pdf (str): Caminho para o arquivo PDF
            
        Returns:
            dict: Dados extraídos do PDF
        """
        logger.info(f"Iniciando extração de dados do PDF: {caminho_pdf}")
        
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(caminho_pdf):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho_pdf}")
            
            # Chamar a função do script existente
            dados = extrator.extrair_dados_pdf_relevantes(caminho_pdf)
            logger.info(f"Extração concluída com sucesso para: {caminho_pdf}")
            
            # Formatar o resultado conforme esperado pela API
            resultado = {
                "status": "success",
                "data": dados
            }
            
            return resultado
        except Exception as e:
            logger.error(f"Erro na extração de dados do PDF {caminho_pdf}: {str(e)}")
            # Tratamento de erro padronizado
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
