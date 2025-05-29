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

# Importar o WondercomClient diretamente
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

# Importar configurações
from .. import config

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
        Utiliza o WondercomClient diretamente para realizar a alocação.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            credenciais (dict): Credenciais do técnico (username, password)
            
        Returns:
            dict: Resultado da alocação
        """
        logger.info(f"Iniciando alocação da WO: {work_order_id}")
        
        # Obter configurações do arquivo config.py ou usar valores padrão
        chrome_driver_path = getattr(config, 'CHROME_DRIVER_PATH', '/usr/local/bin/chromedriver')
        portal_url = getattr(config, 'WONDERCOM_PORTAL_URL', 'https://portal.wondercom.pt/group/guest/intervencoes')
        
        # Extrair credenciais
        username = credenciais.get('username')
        password = credenciais.get('password')
        
        if not username or not password:
            return {
                "status": "error",
                "error": "Credenciais incompletas",
                "error_type": "ValueError"
            }
        
        client = None
        try:
            # Inicializar o cliente Selenium diretamente
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
        finally:
            # Garantir que o navegador seja fechado em caso de erro
            try:
                if client:
                    client.close_driver()
            except Exception as e:
                logger.warning(f"Erro ao fechar o navegador: {e}")
