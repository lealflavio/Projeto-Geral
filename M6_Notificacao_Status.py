#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
M6_Notificacao_Status.py
Sistema de notificação e monitoramento de status para processamento de PDFs.

Este módulo implementa um sistema robusto de notificações via WhatsApp com
mecanismos de retry, fallback e monitoramento de status em tempo real.

Autor: Agente 3 - Especialista em Automação Selenium #2
Data: 24/05/2025
"""

import os
import json
import logging
import time
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
import structlog

# Configuração de logging estruturado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configuração do logger padrão
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.FileHandler("notificacao_status.log"),
        logging.StreamHandler()
    ]
)

logger = structlog.get_logger()

# --- Configurações do Twilio ---
try:
    # Tentar obter credenciais de variáveis de ambiente
    TWILIO_SID = os.environ.get("TWILIO_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
    
    # Verificar se as credenciais estão presentes
    if not all([TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
        # Tentar carregar de arquivo de configuração
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "twilio_config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                TWILIO_SID = config.get("sid")
                TWILIO_AUTH_TOKEN = config.get("auth_token")
                TWILIO_WHATSAPP_NUMBER = config.get("whatsapp_number")
except Exception as e:
    logger.error("Erro ao carregar configurações do Twilio", error=str(e))
    # Valores padrão para desenvolvimento (não funcionais)
    TWILIO_SID = "AC00000000000000000000000000000000"
    TWILIO_AUTH_TOKEN = "0000000000000000000000000000000000"
    TWILIO_WHATSAPP_NUMBER = "+14155238886"

# --- Configurações de fallback ---
FALLBACK_SMS_ENABLED = True
FALLBACK_EMAIL_ENABLED = True
FALLBACK_WEBHOOK_URL = os.environ.get("FALLBACK_WEBHOOK_URL", "")

# --- Inicialização do cliente Twilio ---
try:
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    logger.info("Cliente Twilio inicializado com sucesso")
except Exception as e:
    logger.error("Erro ao inicializar cliente Twilio", error=str(e))
    client = None

# --- Classe de monitoramento de status ---
class StatusMonitor:
    """Sistema de monitoramento de status para notificações."""
    
    def __init__(self, storage_path=None):
        """
        Inicializa o monitor de status.
        
        Args:
            storage_path (str, optional): Caminho para armazenamento de status.
                Se None, usa o diretório padrão.
        """
        self.log = logger.bind(component="StatusMonitor")
        
        if storage_path is None:
            self.storage_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "status_monitor"
            )
        else:
            self.storage_path = storage_path
            
        os.makedirs(self.storage_path, exist_ok=True)
        self.log.info("Monitor de status inicializado", storage_path=self.storage_path)
    
    def registrar_evento(self, numero_wo, tipo_evento, detalhes=None, tecnico=None):
        """
        Registra um evento de status.
        
        Args:
            numero_wo (str): Número da WO
            tipo_evento (str): Tipo do evento (inicio, sucesso, erro, etc.)
            detalhes (dict, optional): Detalhes adicionais do evento
            tecnico (str, optional): Nome do técnico
            
        Returns:
            bool: True se o registro foi bem-sucedido, False caso contrário
        """
        try:
            evento = {
                "numero_wo": numero_wo,
                "tipo_evento": tipo_evento,
                "timestamp": datetime.now().isoformat(),
                "tecnico": tecnico,
                "detalhes": detalhes or {}
            }
            
            # Cria diretório para a WO se não existir
            wo_dir = os.path.join(self.storage_path, numero_wo)
            os.makedirs(wo_dir, exist_ok=True)
            
            # Gera nome de arquivo baseado no timestamp
            filename = f"{int(time.time())}_{tipo_evento}.json"
            filepath = os.path.join(wo_dir, filename)
            
            # Salva o evento
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(evento, f, ensure_ascii=False, indent=2)
                
            self.log.info("Evento registrado com sucesso", 
                         numero_wo=numero_wo, 
                         tipo_evento=tipo_evento)
            return True
            
        except Exception as e:
            self.log.error("Erro ao registrar evento", 
                          numero_wo=numero_wo, 
                          tipo_evento=tipo_evento, 
                          error=str(e))
            return False
    
    def obter_historico_wo(self, numero_wo):
        """
        Obtém o histórico de eventos de uma WO.
        
        Args:
            numero_wo (str): Número da WO
            
        Returns:
            list: Lista de eventos ordenados por timestamp
        """
        try:
            wo_dir = os.path.join(self.storage_path, numero_wo)
            if not os.path.exists(wo_dir):
                return []
                
            eventos = []
            for filename in os.listdir(wo_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(wo_dir, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        evento = json.load(f)
                        eventos.append(evento)
                        
            # Ordena por timestamp
            eventos.sort(key=lambda x: x["timestamp"])
            
            self.log.info("Histórico de eventos obtido com sucesso", 
                         numero_wo=numero_wo, 
                         total_eventos=len(eventos))
            return eventos
            
        except Exception as e:
            self.log.error("Erro ao obter histórico de eventos", 
                          numero_wo=numero_wo, 
                          error=str(e))
            return []
    
    def obter_status_atual(self, numero_wo):
        """
        Obtém o status atual de uma WO.
        
        Args:
            numero_wo (str): Número da WO
            
        Returns:
            dict: Status atual da WO ou None se não encontrado
        """
        eventos = self.obter_historico_wo(numero_wo)
        if not eventos:
            return None
            
        # O último evento representa o status atual
        return eventos[-1]
    
    def gerar_relatorio_status(self, data_inicio=None, data_fim=None, tecnico=None):
        """
        Gera um relatório de status para todas as WOs no período.
        
        Args:
            data_inicio (str, optional): Data de início no formato ISO
            data_fim (str, optional): Data de fim no formato ISO
            tecnico (str, optional): Filtrar por técnico
            
        Returns:
            dict: Relatório de status
        """
        try:
            relatorio = {
                "total_wos": 0,
                "wos_sucesso": 0,
                "wos_erro": 0,
                "wos_pendentes": 0,
                "detalhes_por_wo": {}
            }
            
            # Converte datas para objetos datetime se fornecidas
            inicio_dt = None
            fim_dt = None
            
            if data_inicio:
                inicio_dt = datetime.fromisoformat(data_inicio)
            if data_fim:
                fim_dt = datetime.fromisoformat(data_fim)
                
            # Percorre todos os diretórios de WO
            for wo_dir in os.listdir(self.storage_path):
                wo_path = os.path.join(self.storage_path, wo_dir)
                if os.path.isdir(wo_path):
                    eventos = self.obter_historico_wo(wo_dir)
                    
                    if not eventos:
                        continue
                        
                    # Filtra por data se necessário
                    if inicio_dt or fim_dt:
                        eventos_filtrados = []
                        for evento in eventos:
                            evento_dt = datetime.fromisoformat(evento["timestamp"])
                            if inicio_dt and evento_dt < inicio_dt:
                                continue
                            if fim_dt and evento_dt > fim_dt:
                                continue
                            eventos_filtrados.append(evento)
                        
                        if not eventos_filtrados:
                            continue
                        eventos = eventos_filtrados
                    
                    # Filtra por técnico se necessário
                    if tecnico and all(e.get("tecnico") != tecnico for e in eventos):
                        continue
                    
                    # Incrementa contadores
                    relatorio["total_wos"] += 1
                    
                    # Determina status final
                    ultimo_evento = eventos[-1]
                    if ultimo_evento["tipo_evento"] == "sucesso":
                        relatorio["wos_sucesso"] += 1
                    elif ultimo_evento["tipo_evento"] == "erro":
                        relatorio["wos_erro"] += 1
                    else:
                        relatorio["wos_pendentes"] += 1
                    
                    # Adiciona detalhes
                    relatorio["detalhes_por_wo"][wo_dir] = {
                        "status_atual": ultimo_evento["tipo_evento"],
                        "timestamp_ultimo_evento": ultimo_evento["timestamp"],
                        "tecnico": ultimo_evento.get("tecnico"),
                        "total_eventos": len(eventos)
                    }
            
            self.log.info("Relatório de status gerado com sucesso", 
                         total_wos=relatorio["total_wos"])
            return relatorio
            
        except Exception as e:
            self.log.error("Erro ao gerar relatório de status", error=str(e))
            return {"erro": str(e)}

# --- Envio de mensagens com retry e fallback ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(TwilioRestException),
    reraise=True
)
def enviar_mensagem_whatsapp(numero_destino, mensagem, tipo_log=None, numero_wo=None):
    """
    Envia mensagem via WhatsApp com retry automático.
    
    Args:
        numero_destino (str): Número de telefone de destino
        mensagem (str): Conteúdo da mensagem
        tipo_log (str, optional): Tipo de log para registro
        numero_wo (str, optional): Número da WO para registro
        
    Returns:
        dict: Resultado do envio
        
    Raises:
        Exception: Se o envio falhar após todas as tentativas
    """
    log = logger.bind(
        numero_destino=numero_destino,
        tipo_log=tipo_log,
        numero_wo=numero_wo
    )
    
    if not client:
        log.error("Cliente Twilio não inicializado")
        return _enviar_fallback(numero_destino, mensagem, tipo_log, numero_wo)
    
    try:
        # Formata o número de destino
        if not numero_destino.startswith("whatsapp:"):
            numero_destino = f"whatsapp:{numero_destino}"
        
        # Envia a mensagem
        message = client.messages.create(
            body=mensagem,
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            to=numero_destino
        )
        
        # Registra o sucesso
        if tipo_log and numero_wo:
            log.info(f"Notificação enviada com sucesso", 
                    message_sid=message.sid)
        else:
            log.info(f"Mensagem enviada com sucesso", 
                    message_sid=message.sid)
        
        # Registra no monitor de status se WO fornecida
        if numero_wo:
            monitor = StatusMonitor()
            monitor.registrar_evento(
                numero_wo=numero_wo,
                tipo_evento=f"notificacao_{tipo_log}" if tipo_log else "notificacao",
                detalhes={
                    "numero_destino": numero_destino,
                    "message_sid": message.sid,
                    "status": "enviado"
                }
            )
        
        return {
            "success": True,
            "message_sid": message.sid,
            "status": "enviado"
        }
        
    except TwilioRestException as e:
        log.warning(f"Erro Twilio ao enviar mensagem, tentando novamente", 
                   error_code=e.code,
                   error_message=e.msg)
        raise
        
    except Exception as e:
        log.error(f"Erro inesperado ao enviar mensagem", 
                 error=str(e))
        return _enviar_fallback(numero_destino, mensagem, tipo_log, numero_wo)

def _enviar_fallback(numero_destino, mensagem, tipo_log=None, numero_wo=None):
    """
    Envia mensagem por canais alternativos quando WhatsApp falha.
    
    Args:
        numero_destino (str): Número de telefone de destino
        mensagem (str): Conteúdo da mensagem
        tipo_log (str, optional): Tipo de log para registro
        numero_wo (str, optional): Número da WO para registro
        
    Returns:
        dict: Resultado do envio fallback
    """
    log = logger.bind(
        numero_destino=numero_destino,
        tipo_log=tipo_log,
        numero_wo=numero_wo
    )
    
    fallback_methods = []
    fallback_results = {}
    
    # Tenta SMS se habilitado
    if FALLBACK_SMS_ENABLED and client:
        try:
            message = client.messages.create(
                body=mensagem,
                from_=TWILIO_WHATSAPP_NUMBER.replace("whatsapp:", ""),
                to=numero_destino.replace("whatsapp:", "")
            )
            
            fallback_methods.append("sms")
            fallback_results["sms"] = {
                "success": True,
                "message_sid": message.sid
            }
            
            log.info("Fallback: Mensagem enviada por SMS", 
                    message_sid=message.sid)
                    
        except Exception as e:
            log.error("Fallback: Erro ao enviar SMS", 
                     error=str(e))
            fallback_results["sms"] = {
                "success": False,
                "error": str(e)
            }
    
    # Tenta webhook se URL configurada
    if FALLBACK_WEBHOOK_URL:
        try:
            response = requests.post(
                FALLBACK_WEBHOOK_URL,
                json={
                    "numero_destino": numero_destino,
                    "mensagem": mensagem,
                    "tipo_log": tipo_log,
                    "numero_wo": numero_wo,
                    "timestamp": datetime.now().isoformat()
                },
                timeout=10
            )
            
            response.raise_for_status()
            fallback_methods.append("webhook")
            fallback_results["webhook"] = {
                "success": True,
                "status_code": response.status_code
            }
            
            log.info("Fallback: Mensagem enviada por webhook", 
                    status_code=response.status_code)
                    
        except Exception as e:
            log.error("Fallback: Erro ao enviar webhook", 
                     error=str(e))
            fallback_results["webhook"] = {
                "success": False,
                "error": str(e)
            }
    
    # Registra no monitor de status se WO fornecida
    if numero_wo:
        monitor = StatusMonitor()
        monitor.registrar_evento(
            numero_wo=numero_wo,
            tipo_evento=f"notificacao_fallback_{tipo_log}" if tipo_log else "notificacao_fallback",
            detalhes={
                "numero_destino": numero_destino,
                "fallback_methods": fallback_methods,
                "fallback_results": fallback_results
            }
        )
    
    if fallback_methods:
        return {
            "success": True,
            "fallback": True,
            "methods": fallback_methods,
            "results": fallback_results
        }
    else:
        return {
            "success": False,
            "error": "Todos os métodos de fallback falharam"
        }

# --- Mensagens formatadas ---
def mensagem_boas_vindas(nome_completo):
    """
    Gera mensagem de boas-vindas para o técnico.
    
    Args:
        nome_completo (str): Nome completo do técnico
        
    Returns:
        str: Mensagem formatada
    """
    return f"""
👋 Olá, {nome_completo}!

Você foi registrado no sistema automático da Wondercom.  
A partir de agora, receberá atualizações sobre suas WOs por aqui.

Em caso de dúvidas, fale com o suporte.
"""

def mensagem_inicio_processamento(nome_completo, numero_wo, dados):
    """
    Gera mensagem de início de processamento de WO.
    
    Args:
        nome_completo (str): Nome completo do técnico
        numero_wo (str): Número da WO
        dados (dict): Dados da intervenção
        
    Returns:
        str: Mensagem formatada
    """
    tipo = dados.get("tipo_intervencao", "-")
    data = dados.get("data_inicio", "-")
    hora = dados.get("hora_inicio", "-")

    equipamentos = dados.get("equipamentos_entregues", [])
    materiais = dados.get("materiais_usados", [])

    equipamentos_formatado = "\n".join([f"• {linha.strip()}" for linha in equipamentos]) or "Nenhum"
    materiais_formatado = "\n".join([f"• {linha.strip()}" for linha in materiais]) or "Nenhum"

    return f"""
⚙️ Início do processamento da WO {numero_wo}

Técnico: {nome_completo}  
Tipo: {tipo}  
Data: {data} às {hora}

📦 Equipamentos entregues:  
{equipamentos_formatado}

🧰 Materiais usados:  
{materiais_formatado}
"""

def mensagem_sucesso(numero_wo):
    """
    Gera mensagem de sucesso no processamento de WO.
    
    Args:
        numero_wo (str): Número da WO
        
    Returns:
        str: Mensagem formatada
    """
    return f"""
✅ Sucesso na WO {numero_wo}!

Todos os dados foram extraídos corretamente e estão prontos para envio.
"""

def mensagem_erro(numero_wo):
    """
    Gera mensagem de erro no processamento de WO.
    
    Args:
        numero_wo (str): Número da WO
        
    Returns:
        str: Mensagem formatada
    """
    return f"""
⚠️ Erro ao processar a WO {numero_wo}.

Não foi possível extrair os dados corretamente.  
Revise o PDF e tente novamente.

Se precisar de ajuda, fale com o suporte.
"""

def mensagem_status_atual(numero_wo, status):
    """
    Gera mensagem com status atual da WO.
    
    Args:
        numero_wo (str): Número da WO
        status (dict): Status atual da WO
        
    Returns:
        str: Mensagem formatada
    """
    if not status:
        return f"Não há informações de status para a WO {numero_wo}."
    
    tipo_evento = status.get("tipo_evento", "desconhecido")
    timestamp = status.get("timestamp", "")
    
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp)
            timestamp_formatado = dt.strftime("%d/%m/%Y às %H:%M:%S")
        except:
            timestamp_formatado = timestamp
    else:
        timestamp_formatado = "data desconhecida"
    
    status_texto = {
        "inicio": "Em processamento",
        "sucesso": "Concluída com sucesso",
        "erro": "Falha no processamento",
        "notificacao_inicio": "Notificação de início enviada",
        "notificacao_sucesso": "Notificação de sucesso enviada",
        "notificacao_erro": "Notificação de erro enviada"
    }.get(tipo_evento, tipo_evento)
    
    return f"""
📊 Status da WO {numero_wo}

Status atual: {status_texto}
Última atualização: {timestamp_formatado}
"""

# --- Interfaces públicas ---
def enviar_notificacao_boas_vindas(numero_whatsapp, nome_tecnico):
    """
    Envia notificação de boas-vindas para o técnico.
    
    Args:
        numero_whatsapp (str): Número do WhatsApp do técnico
        nome_tecnico (str): Nome completo do técnico
        
    Returns:
        dict: Resultado do envio
    """
    mensagem = mensagem_boas_vindas(nome_tecnico)
    return enviar_mensagem_whatsapp(numero_whatsapp, mensagem, tipo_log="boas-vindas")

def enviar_notificacao_wo_iniciada(numero_whatsapp, nome_tecnico, numero_wo, dados_intervencao):
    """
    Envia notificação de início de processamento de WO.
    
    Args:
        numero_whatsapp (str): Número do WhatsApp do técnico
        nome_tecnico (str): Nome completo do técnico
        numero_wo (str): Número da WO
        dados_intervencao (dict): Dados da intervenção
        
    Returns:
        dict: Resultado do envio
    """
    mensagem = mensagem_inicio_processamento(nome_tecnico, numero_wo, dados_intervencao)
    
    # Registra evento no monitor de status
    monitor = StatusMonitor()
    monitor.registrar_evento(
        numero_wo=numero_wo,
        tipo_evento="inicio",
        detalhes=dados_intervencao,
        tecnico=nome_tecnico
    )
    
    return enviar_mensagem_whatsapp(numero_whatsapp, mensagem, tipo_log="início", numero_wo=numero_wo)

def enviar_notificacao_wo_sucesso(numero_whatsapp, numero_wo):
    """
    Envia notificação de sucesso no processamento de WO.
    
    Args:
        numero_whatsapp (str): Número do WhatsApp do técnico
        numero_wo (str): Número da WO
        
    Returns:
        dict: Resultado do envio
    """
    mensagem = mensagem_sucesso(numero_wo)
    
    # Registra evento no monitor de status
    monitor = StatusMonitor()
    monitor.registrar_evento(
        numero_wo=numero_wo,
        tipo_evento="sucesso"
    )
    
    return enviar_mensagem_whatsapp(numero_whatsapp, mensagem, tipo_log="sucesso", numero_wo=numero_wo)

def enviar_notificacao_wo_erro(numero_whatsapp, numero_wo):
    """
    Envia notificação de erro no processamento de WO.
    
    Args:
        numero_whatsapp (str): Número do WhatsApp do técnico
        numero_wo (str): Número da WO
        
    Returns:
        dict: Resultado do envio
    """
    mensagem = mensagem_erro(numero_wo)
    
    # Registra evento no monitor de status
    monitor = StatusMonitor()
    monitor.registrar_evento(
        numero_wo=numero_wo,
        tipo_evento="erro"
    )
    
    return enviar_mensagem_whatsapp(numero_whatsapp, mensagem, tipo_log="erro", numero_wo=numero_wo)

def obter_status_wo(numero_wo):
    """
    Obtém o status atual de uma WO.
    
    Args:
        numero_wo (str): Número da WO
        
    Returns:
        dict: Status atual da WO ou None se não encontrado
    """
    monitor = StatusMonitor()
    return monitor.obter_status_atual(numero_wo)

def enviar_notificacao_status_atual(numero_whatsapp, numero_wo):
    """
    Envia notificação com status atual da WO.
    
    Args:
        numero_whatsapp (str): Número do WhatsApp do técnico
        numero_wo (str): Número da WO
        
    Returns:
        dict: Resultado do envio
    """
    status = obter_status_wo(numero_wo)
    mensagem = mensagem_status_atual(numero_wo, status)
    return enviar_mensagem_whatsapp(numero_whatsapp, mensagem, tipo_log="status", numero_wo=numero_wo)

def gerar_relatorio_status(data_inicio=None, data_fim=None, tecnico=None):
    """
    Gera um relatório de status para todas as WOs no período.
    
    Args:
        data_inicio (str, optional): Data de início no formato ISO
        data_fim (str, optional): Data de fim no formato ISO
        tecnico (str, optional): Filtrar por técnico
        
    Returns:
        dict: Relatório de status
    """
    monitor = StatusMonitor()
    return monitor.gerar_relatorio_status(data_inicio, data_fim, tecnico)

# --- Função principal para testes ---
if __name__ == "__main__":
    # Exemplo de uso
    print("Sistema de Notificação e Monitoramento de Status")
    print("Módulo para importação - não possui função principal")
