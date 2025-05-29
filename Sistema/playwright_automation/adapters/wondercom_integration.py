"""
Adaptador para integração do cliente Playwright com a API.
"""
import logging
import asyncio
from ..wondercom_client import WondercomClient

logger = logging.getLogger(__name__)

class WondercomIntegration:
    """
    Adaptador para integração do cliente Playwright.
    Fornece métodos para utilizar o cliente Playwright a partir da VM API.
    """
    
    # Configurações padrão
    DEFAULT_PORTAL_URL = "https://portal.wondercom.pt/group/guest/intervencoes"
    
    @staticmethod
    async def alocar_wo(work_order_id, credentials, portal_url=None):
        """
        Aloca uma ordem de trabalho utilizando o cliente Playwright.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            credentials (dict): Credenciais do usuário (username, password)
            portal_url (str, opcional): URL do portal Wondercom
            
        Returns:
            dict: Resultado da alocação
        """
        logger.info(f"Iniciando alocação da WO {work_order_id} via WondercomClient (Playwright)")
        
        try:
            # Extrair credenciais
            username = credentials.get('username')
            password = credentials.get('password')
            
            if not username or not password:
                raise ValueError("Credenciais incompletas")
            
            # Definir URL padrão se não fornecida
            portal_url = portal_url or WondercomIntegration.DEFAULT_PORTAL_URL
            
            # Inicializar o cliente Playwright
            async with WondercomClient(
                portal_url=portal_url,
                username=username,
                password=password,
                headless=True
            ) as client:
                # Realizar login
                login_success = await client.login()
                if not login_success:
                    raise Exception("Falha no login")
                
                # Alocar a ordem de trabalho
                result = await client.allocate_work_order(work_order_id)
                
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
                            "cor_fibra_hex": client.cor_para_hex(dados_wo.get('fibra', '')),
                            "latitude": None,
                            "longitude": None,
                            "estado": dados_wo.get('estado', 'N/A'),
                            "descricao": dados_wo.get('descricao', 'N/A'),
                            "dona_rede": dados_wo.get('dona_rede', 'N/A'),
                            "porto_primario": dados_wo.get('porto_primario', 'N/A'),
                            "data_agendamento": dados_wo.get('data_agendamento', 'N/A'),
                            "estado_intervencao": dados_wo.get('estado_intervencao', 'N/A')
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
