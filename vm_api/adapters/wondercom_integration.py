"""
Módulo de integração entre o OrquestradorAdapter e o WondercomClient.
Este arquivo implementa a adaptação necessária para utilizar o cliente Selenium existente.
"""

import sys
import os
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path para importar os módulos necessários
sys.path.append(str(Path(__file__).parent.parent.parent))

# Importar o cliente Selenium existente
try:
    from vm_api.wondercom_client import WondercomClient
    logger.info("Módulo WondercomClient importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar WondercomClient: {e}")
    # Fallback para ambiente de teste/desenvolvimento
    try:
        # Tentar importar de um caminho relativo para testes
        sys.path.append('/home/flavioleal/Sistema')
        from wondercom_client import WondercomClient
        logger.info("Módulo WondercomClient importado do caminho alternativo")
    except ImportError as e2:
        logger.error(f"Erro ao importar WondercomClient do caminho alternativo: {e2}")
        raise

class WondercomIntegration:
    """
    Classe de integração entre o OrquestradorAdapter e o WondercomClient.
    Fornece métodos para utilizar o cliente Selenium existente a partir da VM API.
    """
    
    # Configurações padrão
    DEFAULT_CHROME_DRIVER_PATH = "/usr/local/bin/chromedriver"
    DEFAULT_PORTAL_URL = "https://portal.wondercom.pt/group/guest/intervencoes"
    
    @staticmethod
    def alocar_wo(work_order_id, credentials, chrome_driver_path=None, portal_url=None):
        """
        Aloca uma ordem de trabalho utilizando o cliente Selenium existente.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            credentials (dict): Credenciais do usuário (username, password)
            chrome_driver_path (str, opcional): Caminho para o chromedriver
            portal_url (str, opcional): URL do portal Wondercom
            
        Returns:
            dict: Resultado da alocação
        """
        logger.info(f"Iniciando alocação da WO {work_order_id} via WondercomClient")
        
        client = None
        try:
            # Extrair credenciais
            username = credentials.get('username')
            password = credentials.get('password')
            
            if not username or not password:
                raise ValueError("Credenciais incompletas")
            
            # Definir caminhos padrão se não fornecidos
            chrome_driver_path = chrome_driver_path or WondercomIntegration.DEFAULT_CHROME_DRIVER_PATH
            portal_url = portal_url or WondercomIntegration.DEFAULT_PORTAL_URL
            
            # Inicializar o cliente Selenium
            client = WondercomClient(
                chrome_driver_path=chrome_driver_path,
                portal_url=portal_url,
                username=username,
                password=password
            )
            
            # Iniciar o driver
            client.start_driver()
            
            # Realizar login
            login_success = client.login()
            if not login_success:
                raise Exception("Falha no login")
            
            # Alocar a ordem de trabalho
            result = client.allocate_work_order(work_order_id)
            
            if result.get("success"):
                # Extrair dados relevantes
                dados_wo = result.get('dados', {})
                
                # Formatar o resultado conforme esperado pela API
                formatted_result = {
                    "status": "success",
                    "data": {
                        "endereco": dados_wo.get('morada', 'N/A'),
                        "pdo": dados_wo.get('slid', 'N/A'),
                        "cor_fibra": dados_wo.get('fibra', 'N/A'),
                        "cor_fibra_hex": "#0000FF",  # Valor padrão, pode ser extraído se disponível
                        "latitude": None,
                        "longitude": None,
                        "estado": dados_wo.get('estado', 'N/A'),
                        "descricao": dados_wo.get('descricao', 'N/A')
                    }
                }
                
                # Extrair coordenadas se disponíveis
                coordenadas = dados_wo.get('coordenadas')
                if coordenadas:
                    try:
                        lat, lng = coordenadas.split(',')
                        formatted_result["data"]["latitude"] = float(lat.strip())
                        formatted_result["data"]["longitude"] = float(lng.strip())
                    except Exception as e:
                        logger.warning(f"Erro ao extrair coordenadas: {e}")
                
                logger.info(f"Alocação concluída com sucesso para WO: {work_order_id}")
                return formatted_result
            else:
                # Retornar erro
                error_message = result.get('message', 'Erro desconhecido na alocação')
                logger.error(f"Erro na alocação da WO {work_order_id}: {error_message}")
                return {
                    "status": "error",
                    "error": error_message,
                    "error_type": "AllocationError"
                }
        except Exception as e:
            logger.error(f"Erro na alocação da WO {work_order_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
        finally:
            # Garantir que o navegador seja fechado em caso de erro
            try:
                if client:
                    client.close_driver()
            except Exception as e:
                logger.warning(f"Erro ao fechar o navegador: {e}")
