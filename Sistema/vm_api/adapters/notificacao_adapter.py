"""
Adaptador para o módulo de notificação.
Este arquivo conecta a API REST aos scripts existentes de notificação,
permitindo o envio de notificações por e-mail, SMS e outros canais.
"""

import sys
import os
import logging
import json
from pathlib import Path
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path para importar os scripts existentes
sys.path.append(str(Path(__file__).parent.parent.parent))

# Importar os scripts existentes
try:
    import M6_Notificacao_Status as notificador
    logger.info("Módulo M6_Notificacao_Status importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar M6_Notificacao_Status: {e}")
    raise

# Importar configurações
from .. import config

class NotificacaoAdapter:
    """
    Adaptador para o módulo de notificação.
    Fornece métodos para enviar notificações através de diferentes canais.
    """
    
    @staticmethod
    def enviar_notificacao_email(destinatario, assunto, mensagem, anexos=None):
        """
        Envia uma notificação por e-mail.
        
        Args:
            destinatario (str): Endereço de e-mail do destinatário
            assunto (str): Assunto do e-mail
            mensagem (str): Corpo do e-mail
            anexos (list, opcional): Lista de caminhos para arquivos a serem anexados
            
        Returns:
            dict: Resultado do envio
        """
        logger.info(f"Enviando notificação por e-mail para: {destinatario}")
        
        try:
            # Verificar parâmetros
            if not destinatario or not assunto or not mensagem:
                raise ValueError("Parâmetros incompletos para envio de e-mail")
            
            # Preparar anexos
            anexos_list = []
            if anexos:
                for anexo in anexos:
                    if os.path.exists(anexo):
                        anexos_list.append(anexo)
                    else:
                        logger.warning(f"Anexo não encontrado: {anexo}")
            
            # Chamar a função do script existente
            resultado = notificador.enviar_email(
                destinatario=destinatario,
                assunto=assunto,
                mensagem=mensagem,
                anexos=anexos_list
            )
            
            logger.info(f"E-mail enviado com sucesso para: {destinatario}")
            
            # Formatar o resultado conforme esperado pela API
            return {
                "status": "success",
                "data": {
                    "destinatario": destinatario,
                    "assunto": assunto,
                    "data_envio": datetime.now().isoformat(),
                    "anexos": anexos_list
                }
            }
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail para {destinatario}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    @staticmethod
    def enviar_notificacao_sms(numero, mensagem):
        """
        Envia uma notificação por SMS.
        
        Args:
            numero (str): Número de telefone do destinatário
            mensagem (str): Conteúdo da mensagem SMS
            
        Returns:
            dict: Resultado do envio
        """
        logger.info(f"Enviando notificação por SMS para: {numero}")
        
        try:
            # Verificar parâmetros
            if not numero or not mensagem:
                raise ValueError("Parâmetros incompletos para envio de SMS")
            
            # Formatar número de telefone (remover caracteres não numéricos)
            numero_formatado = ''.join(filter(str.isdigit, numero))
            
            # Chamar a função do script existente
            resultado = notificador.enviar_sms(
                numero=numero_formatado,
                mensagem=mensagem
            )
            
            logger.info(f"SMS enviado com sucesso para: {numero}")
            
            # Formatar o resultado conforme esperado pela API
            return {
                "status": "success",
                "data": {
                    "numero": numero_formatado,
                    "data_envio": datetime.now().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Erro ao enviar SMS para {numero}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    @staticmethod
    def enviar_notificacao_status(tecnico_id, tipo_notificacao, dados):
        """
        Envia uma notificação de status para um técnico.
        
        Args:
            tecnico_id (int): ID do técnico
            tipo_notificacao (str): Tipo de notificação (alocacao, processamento, erro)
            dados (dict): Dados específicos da notificação
            
        Returns:
            dict: Resultado do envio
        """
        logger.info(f"Enviando notificação de status para técnico: {tecnico_id}, tipo: {tipo_notificacao}")
        
        try:
            # Verificar parâmetros
            if not tecnico_id or not tipo_notificacao or not dados:
                raise ValueError("Parâmetros incompletos para envio de notificação de status")
            
            # Validar tipo de notificação
            tipos_validos = ["alocacao", "processamento", "erro", "alerta"]
            if tipo_notificacao not in tipos_validos:
                raise ValueError(f"Tipo de notificação inválido. Valores permitidos: {', '.join(tipos_validos)}")
            
            # Preparar dados para notificação
            dados_notificacao = {
                "tecnico_id": tecnico_id,
                "tipo": tipo_notificacao,
                "timestamp": datetime.now().isoformat(),
                "dados": dados
            }
            
            # Chamar a função do script existente
            resultado = notificador.notificar_status(
                tecnico_id=tecnico_id,
                tipo=tipo_notificacao,
                dados=dados
            )
            
            logger.info(f"Notificação de status enviada com sucesso para técnico: {tecnico_id}")
            
            # Formatar o resultado conforme esperado pela API
            return {
                "status": "success",
                "data": dados_notificacao
            }
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de status para técnico {tecnico_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    @staticmethod
    def registrar_log_atividade(tecnico_id, acao, detalhes=None):
        """
        Registra um log de atividade para um técnico.
        
        Args:
            tecnico_id (int): ID do técnico
            acao (str): Ação realizada
            detalhes (dict, opcional): Detalhes adicionais da ação
            
        Returns:
            dict: Resultado do registro
        """
        logger.info(f"Registrando log de atividade para técnico: {tecnico_id}, ação: {acao}")
        
        try:
            # Verificar parâmetros
            if not tecnico_id or not acao:
                raise ValueError("Parâmetros incompletos para registro de log")
            
            # Preparar dados para log
            dados_log = {
                "tecnico_id": tecnico_id,
                "acao": acao,
                "timestamp": datetime.now().isoformat(),
                "detalhes": detalhes or {}
            }
            
            # Chamar a função do script existente
            resultado = notificador.registrar_log(
                tecnico_id=tecnico_id,
                acao=acao,
                detalhes=detalhes
            )
            
            logger.info(f"Log de atividade registrado com sucesso para técnico: {tecnico_id}")
            
            # Formatar o resultado conforme esperado pela API
            return {
                "status": "success",
                "data": dados_log
            }
        except Exception as e:
            logger.error(f"Erro ao registrar log de atividade para técnico {tecnico_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
