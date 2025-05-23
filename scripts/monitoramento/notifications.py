#!/usr/bin/env python3
"""
Módulo de notificações para scripts de monitoramento

Este módulo fornece funções para enviar notificações por diferentes canais:
- Email
- WhatsApp (via Twilio)
- Webhook genérico

Integrado com o sistema centralizado de configurações.
"""

import os
import sys
import json
import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Adicionar diretório raiz ao path para importação
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Importar o sistema de configuração
try:
    from config.config import config
    USING_CONFIG = True
except ImportError:
    print("AVISO: Sistema centralizado de configurações não encontrado. Usando valores padrão.")
    USING_CONFIG = False

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('notifications')

# Configurações padrão (usadas se o sistema de configuração não estiver disponível)
DEFAULT_CONFIG = {
    'notifications': {
        'default_channel': 'email',
        'email': {
            'enabled': False,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'seu-email@gmail.com',
            'password': 'sua-senha',
            'recipients': ['admin@example.com']
        },
        'whatsapp': {
            'enabled': False,
            'twilio_account_sid': 'your_account_sid',
            'twilio_auth_token': 'your_auth_token',
            'twilio_from_number': 'whatsapp:+14155238886',  # Número do Twilio
            'to_numbers': ['whatsapp:+5511999999999']  # Números de destino
        },
        'webhook': {
            'enabled': False,
            'url': 'https://hooks.example.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX',
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    }
}

def get_config(key, default=None):
    """Obtém um valor de configuração, com fallback para valores padrão."""
    if USING_CONFIG:
        return config.get(key, default)
    
    # Navegação manual na estrutura DEFAULT_CONFIG
    keys = key.split('.')
    value = DEFAULT_CONFIG
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value

def mask_sensitive_data(text):
    """
    Mascara dados sensíveis no texto.
    
    Substitui senhas, tokens e outras informações sensíveis por asteriscos.
    """
    # Lista de palavras-chave que indicam dados sensíveis
    sensitive_keywords = [
        'password', 'senha', 'token', 'secret', 'key', 'api_key', 
        'auth', 'credential', 'private', 'pwd'
    ]
    
    # Procurar por padrões como "password=123456" ou "senha: 123456"
    import re
    for keyword in sensitive_keywords:
        # Padrão para "keyword=valor" ou "keyword: valor"
        pattern = rf'({keyword}[=:]\s*)([^\s,;]+)'
        # Substituir o valor por asteriscos, mantendo o keyword
        text = re.sub(pattern, r'\1********', text, flags=re.IGNORECASE)
    
    return text

def send_email_notification(subject, message, recipients=None):
    """
    Envia uma notificação por email.
    
    Args:
        subject (str): Assunto do email
        message (str): Corpo da mensagem
        recipients (list, opcional): Lista de destinatários. Se não for fornecido,
                                    usa os destinatários configurados.
    
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário
    """
    if not get_config('notifications.email.enabled', DEFAULT_CONFIG['notifications']['email']['enabled']):
        logger.info("Notificações por email desativadas nas configurações")
        return False
    
    smtp_server = get_config('notifications.email.smtp_server', DEFAULT_CONFIG['notifications']['email']['smtp_server'])
    smtp_port = get_config('notifications.email.smtp_port', DEFAULT_CONFIG['notifications']['email']['smtp_port'])
    username = get_config('notifications.email.username', DEFAULT_CONFIG['notifications']['email']['username'])
    password = get_config('notifications.email.password', DEFAULT_CONFIG['notifications']['email']['password'])
    
    if recipients is None:
        recipients = get_config('notifications.email.recipients', DEFAULT_CONFIG['notifications']['email']['recipients'])
    
    if not recipients:
        logger.error("Nenhum destinatário configurado para envio de email")
        return False
    
    try:
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        
        # Adicionar corpo da mensagem
        msg.attach(MIMEText(message, 'plain'))
        
        # Conectar ao servidor SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        
        # Enviar email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email enviado com sucesso para: {', '.join(recipients)}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao enviar email: {str(e)}")
        return False

def send_whatsapp_notification(message, to_numbers=None):
    """
    Envia uma notificação por WhatsApp usando a API do Twilio.
    
    Args:
        message (str): Mensagem a ser enviada
        to_numbers (list, opcional): Lista de números de destino. Se não for fornecido,
                                    usa os números configurados.
    
    Returns:
        bool: True se a mensagem foi enviada com sucesso, False caso contrário
    """
    if not get_config('notifications.whatsapp.enabled', DEFAULT_CONFIG['notifications']['whatsapp']['enabled']):
        logger.info("Notificações por WhatsApp desativadas nas configurações")
        return False
    
    account_sid = get_config('notifications.whatsapp.twilio_account_sid', DEFAULT_CONFIG['notifications']['whatsapp']['twilio_account_sid'])
    auth_token = get_config('notifications.whatsapp.twilio_auth_token', DEFAULT_CONFIG['notifications']['whatsapp']['twilio_auth_token'])
    from_number = get_config('notifications.whatsapp.twilio_from_number', DEFAULT_CONFIG['notifications']['whatsapp']['twilio_from_number'])
    
    if to_numbers is None:
        to_numbers = get_config('notifications.whatsapp.to_numbers', DEFAULT_CONFIG['notifications']['whatsapp']['to_numbers'])
    
    if not to_numbers:
        logger.error("Nenhum número de destino configurado para envio de WhatsApp")
        return False
    
    try:
        # Verificar se o módulo twilio está instalado
        try:
            from twilio.rest import Client
            twilio_available = True
        except ImportError:
            twilio_available = False
            logger.warning("Módulo twilio não encontrado. Tentando usar requests diretamente.")
        
        success = True
        
        if twilio_available:
            # Usar o SDK do Twilio
            client = Client(account_sid, auth_token)
            
            for to_number in to_numbers:
                message_obj = client.messages.create(
                    body=message,
                    from_=from_number,
                    to=to_number
                )
                logger.info(f"WhatsApp enviado para {to_number}, SID: {message_obj.sid}")
        else:
            # Usar requests diretamente
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            auth = (account_sid, auth_token)
            
            for to_number in to_numbers:
                data = {
                    'From': from_number,
                    'To': to_number,
                    'Body': message
                }
                
                response = requests.post(url, auth=auth, data=data)
                
                if response.status_code == 201:
                    logger.info(f"WhatsApp enviado para {to_number}")
                else:
                    logger.error(f"Erro ao enviar WhatsApp para {to_number}: {response.text}")
                    success = False
        
        return success
    
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp: {str(e)}")
        return False

def send_webhook_notification(title, message, data=None):
    """
    Envia uma notificação para um webhook genérico.
    
    Args:
        title (str): Título da notificação
        message (str): Mensagem da notificação
        data (dict, opcional): Dados adicionais a serem enviados
    
    Returns:
        bool: True se a notificação foi enviada com sucesso, False caso contrário
    """
    if not get_config('notifications.webhook.enabled', DEFAULT_CONFIG['notifications']['webhook']['enabled']):
        logger.info("Notificações por webhook desativadas nas configurações")
        return False
    
    webhook_url = get_config('notifications.webhook.url', DEFAULT_CONFIG['notifications']['webhook']['url'])
    method = get_config('notifications.webhook.method', DEFAULT_CONFIG['notifications']['webhook']['method'])
    headers = get_config('notifications.webhook.headers', DEFAULT_CONFIG['notifications']['webhook']['headers'])
    
    if not webhook_url:
        logger.error("URL do webhook não configurada")
        return False
    
    try:
        # Preparar payload
        payload = {
            'title': title,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Adicionar dados extras se fornecidos
        if data:
            payload['data'] = data
        
        # Enviar requisição
        if method.upper() == 'POST':
            response = requests.post(webhook_url, headers=headers, json=payload)
        elif method.upper() == 'PUT':
            response = requests.put(webhook_url, headers=headers, json=payload)
        else:
            logger.error(f"Método HTTP não suportado: {method}")
            return False
        
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"Webhook enviado com sucesso: {response.status_code}")
            return True
        else:
            logger.error(f"Erro ao enviar webhook: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Erro ao enviar webhook: {str(e)}")
        return False

def send_notification(title, message, channel=None, **kwargs):
    """
    Envia uma notificação pelo canal especificado ou pelo canal padrão.
    
    Args:
        title (str): Título da notificação
        message (str): Mensagem da notificação
        channel (str, opcional): Canal de notificação ('email', 'whatsapp', 'webhook')
                                Se não for fornecido, usa o canal padrão configurado.
        **kwargs: Argumentos adicionais específicos para cada canal
    
    Returns:
        bool: True se a notificação foi enviada com sucesso, False caso contrário
    """
    # Mascarar dados sensíveis na mensagem
    safe_message = mask_sensitive_data(message)
    
    # Determinar canal
    if channel is None:
        channel = get_config('notifications.default_channel', DEFAULT_CONFIG['notifications']['default_channel'])
    
    # Enviar notificação pelo canal apropriado
    if channel == 'email':
        return send_email_notification(title, safe_message, **kwargs)
    elif channel == 'whatsapp':
        return send_whatsapp_notification(f"{title}\n\n{safe_message}", **kwargs)
    elif channel == 'webhook':
        return send_webhook_notification(title, safe_message, **kwargs)
    else:
        logger.error(f"Canal de notificação não suportado: {channel}")
        return False

# Exemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Exemplo de notificação
    send_notification(
        "Teste de Notificação",
        "Esta é uma mensagem de teste do sistema de notificações.",
        channel='email'
    )
