#!/usr/bin/env python3
"""
Script de Monitoramento de Saúde do Sistema

Este script verifica o status dos três componentes principais do sistema:
1. Scripts de Automação (VM)
2. Backend (Render)
3. Frontend (Netlify)

Integrado com o sistema centralizado de configurações.

Uso:
    python3 system_health.py [--email] [--json]

Opções:
    --email: Envia relatório por email para os destinatários configurados
    --json: Salva o relatório em formato JSON
"""

import os
import sys
import json
import logging
import argparse
import requests
import subprocess
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'system_health.log'))
    ]
)
logger = logging.getLogger('system_health')

# Configurações padrão (usadas se o sistema de configuração não estiver disponível)
DEFAULT_CONFIG = {
    'backend_url': 'http://localhost:5000',
    'frontend_url': 'http://localhost:3000',
    'vm_scripts_dir': '/home/flavioleal_souza/Sistema',
    'log_dir': os.path.dirname(__file__),
    'email': {
        'enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'seu-email@gmail.com',
        'password': 'sua-senha',
        'recipients': ['admin@example.com']
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

def verificar_backend():
    """Verifica se o backend está respondendo corretamente"""
    logger.info("Verificando Backend (Render)...")
    
    backend_url = get_config('monitoring.backend_url', DEFAULT_CONFIG['backend_url'])
    health_endpoint = f"{backend_url}/health"
    
    try:
        # Tenta acessar o endpoint de saúde do backend
        response = requests.get(health_endpoint, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("Backend está online")
            logger.info(f"Versão: {data.get('version', 'N/A')}")
            logger.info(f"Banco de dados: {data.get('database_status', 'N/A')}")
            return True, data
        else:
            logger.error(f"Backend retornou status code: {response.status_code}")
            return False, {"error": f"Status code: {response.status_code}"}
    
    except requests.RequestException as e:
        logger.error(f"Erro ao conectar ao backend: {str(e)}")
        return False, {"error": str(e)}

def verificar_frontend():
    """Verifica se o frontend está acessível"""
    logger.info("Verificando Frontend (Netlify)...")
    
    frontend_url = get_config('monitoring.frontend_url', DEFAULT_CONFIG['frontend_url'])
    
    try:
        # Tenta acessar a página principal do frontend
        response = requests.get(frontend_url, timeout=10)
        
        if response.status_code == 200:
            logger.info("Frontend está online")
            logger.info(f"Tamanho da resposta: {len(response.text)} bytes")
            return True, {"status": "online"}
        else:
            logger.error(f"Frontend retornou status code: {response.status_code}")
            return False, {"error": f"Status code: {response.status_code}"}
    
    except requests.RequestException as e:
        logger.error(f"Erro ao conectar ao frontend: {str(e)}")
        return False, {"error": str(e)}

def verificar_scripts_vm():
    """Verifica o status dos scripts de automação na VM"""
    logger.info("Verificando Scripts de Automação (VM)...")
    
    vm_scripts_dir = get_config('paths.base_dir', DEFAULT_CONFIG['vm_scripts_dir'])
    
    # Verificar se os diretórios principais existem
    diretorios = [
        os.path.join(vm_scripts_dir, "config"),
        os.path.join(vm_scripts_dir, "extracao_dados"),
        os.path.join(vm_scripts_dir, "tecnicos")
    ]
    
    diretorios_existem = all(os.path.exists(d) for d in diretorios)
    
    # Verificar se os scripts principais existem
    scripts = [
        os.path.join(vm_scripts_dir, "M1_Extrator_PDF.py"),
        os.path.join(vm_scripts_dir, "M2_Orquestrador_PDFs.py"),
        os.path.join(vm_scripts_dir, "M3_Leitura_Drive.py"),
        os.path.join(vm_scripts_dir, "M4_Manipulacao_Arquivos.py"),
        os.path.join(vm_scripts_dir, "M5_Config_Tecnicos.py"),
        os.path.join(vm_scripts_dir, "M6_Notificacao_Status.py")
    ]
    
    scripts_existem = all(os.path.exists(s) for s in scripts)
    
    # Verificar logs recentes
    log_dir = get_config('paths.log_dir', os.path.join(vm_scripts_dir, "logs"))
    logs_recentes = []
    
    if os.path.exists(log_dir):
        try:
            # Listar arquivos de log ordenados por data de modificação
            logs = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith('.log')]
            logs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Verificar os logs mais recentes
            for log_file in logs[:5]:  # Verificar os 5 logs mais recentes
                mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                logs_recentes.append({
                    "arquivo": os.path.basename(log_file),
                    "ultima_modificacao": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                    "tamanho": os.path.getsize(log_file)
                })
        except Exception as e:
            logger.error(f"Erro ao verificar logs: {str(e)}")
    
    # Verificar PDFs processados recentemente
    pdfs_processados = []
    pdfs_erro = []
    
    tecnicos_dir = os.path.join(vm_scripts_dir, "tecnicos")
    if os.path.exists(tecnicos_dir):
        try:
            for tecnico in os.listdir(tecnicos_dir):
                tecnico_path = os.path.join(tecnicos_dir, tecnico)
                if os.path.isdir(tecnico_path):
                    # Verificar PDFs processados
                    processados_dir = os.path.join(tecnico_path, "pdfs", "processados")
                    if os.path.exists(processados_dir):
                        pdfs = [f for f in os.listdir(processados_dir) if f.endswith('.pdf')]
                        pdfs_processados.extend(pdfs)
                    
                    # Verificar PDFs com erro
                    erro_dir = os.path.join(tecnico_path, "pdfs", "erro")
                    if os.path.exists(erro_dir):
                        pdfs = [f for f in os.listdir(erro_dir) if f.endswith('.pdf')]
                        pdfs_erro.extend(pdfs)
        except Exception as e:
            logger.error(f"Erro ao verificar PDFs: {str(e)}")
    
    status = "operational" if diretorios_existem and scripts_existem else "warning"
    
    if diretorios_existem and scripts_existem:
        logger.info("Scripts de automação estão presentes")
        logger.info("Todos os diretórios necessários existem")
        logger.info("Todos os scripts principais estão presentes")
    else:
        if not diretorios_existem:
            logger.warning("Alguns diretórios necessários não existem")
        if not scripts_existem:
            logger.warning("Alguns scripts principais não existem")
    
    logger.info(f"PDFs processados: {len(pdfs_processados)}")
    logger.info(f"PDFs com erro: {len(pdfs_erro)}")
    
    return diretorios_existem and scripts_existem, {
        "status": status,
        "diretorios": diretorios_existem,
        "scripts": scripts_existem,
        "logs_recentes": logs_recentes,
        "pdfs_processados": len(pdfs_processados),
        "pdfs_erro": len(pdfs_erro)
    }

def gerar_relatorio(resultados):
    """Gera um relatório completo do status do sistema"""
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    status_geral = "OK" if all(r[0] for r in resultados.values()) else "ALERTA"
    
    relatorio = {
        "timestamp": agora,
        "status_geral": status_geral,
        "componentes": {
            "backend": resultados["backend"][1],
            "frontend": resultados["frontend"][1],
            "vm_scripts": resultados["vm_scripts"][1]
        }
    }
    
    # Gerar relatório em texto
    texto_relatorio = []
    texto_relatorio.append("=" * 50)
    texto_relatorio.append(f"RELATÓRIO DE SAÚDE DO SISTEMA - {agora}")
    texto_relatorio.append("=" * 50)
    texto_relatorio.append(f"Status Geral: {status_geral}")
    texto_relatorio.append("")
    
    # Backend
    texto_relatorio.append("-" * 20)
    texto_relatorio.append("BACKEND (Render)")
    texto_relatorio.append("-" * 20)
    if resultados["backend"][0]:
        texto_relatorio.append("Status: ONLINE")
        for key, value in resultados["backend"][1].items():
            texto_relatorio.append(f"{key}: {value}")
    else:
        texto_relatorio.append("Status: OFFLINE")
        texto_relatorio.append(f"Erro: {resultados['backend'][1].get('error', 'Desconhecido')}")
    texto_relatorio.append("")
    
    # Frontend
    texto_relatorio.append("-" * 20)
    texto_relatorio.append("FRONTEND (Netlify)")
    texto_relatorio.append("-" * 20)
    if resultados["frontend"][0]:
        texto_relatorio.append("Status: ONLINE")
    else:
        texto_relatorio.append("Status: OFFLINE")
        texto_relatorio.append(f"Erro: {resultados['frontend'][1].get('error', 'Desconhecido')}")
    texto_relatorio.append("")
    
    # VM Scripts
    texto_relatorio.append("-" * 20)
    texto_relatorio.append("SCRIPTS DE AUTOMAÇÃO (VM)")
    texto_relatorio.append("-" * 20)
    vm_data = resultados["vm_scripts"][1]
    texto_relatorio.append(f"Status: {vm_data['status'].upper()}")
    texto_relatorio.append(f"Diretórios: {'OK' if vm_data['diretorios'] else 'FALTANDO'}")
    texto_relatorio.append(f"Scripts: {'OK' if vm_data['scripts'] else 'FALTANDO'}")
    texto_relatorio.append(f"PDFs Processados: {vm_data['pdfs_processados']}")
    texto_relatorio.append(f"PDFs com Erro: {vm_data['pdfs_erro']}")
    
    if vm_data.get('logs_recentes'):
        texto_relatorio.append("\nLogs Recentes:")
        for log in vm_data['logs_recentes']:
            texto_relatorio.append(f"- {log['arquivo']} ({log['ultima_modificacao']})")
    
    return relatorio, "\n".join(texto_relatorio)

def salvar_relatorio_json(relatorio, caminho=None):
    """Salva o relatório em formato JSON"""
    if caminho is None:
        log_dir = get_config('monitoring.log_dir', DEFAULT_CONFIG['log_dir'])
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho = os.path.join(log_dir, f"relatorio_saude_{timestamp}.json")
    
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Relatório JSON salvo em: {caminho}")
    return caminho

def enviar_email(texto_relatorio):
    """Envia o relatório por email"""
    if not get_config('email.enabled', DEFAULT_CONFIG['email']['enabled']):
        logger.info("Envio de email desativado nas configurações")
        return False
    
    smtp_server = get_config('email.smtp_server', DEFAULT_CONFIG['email']['smtp_server'])
    smtp_port = get_config('email.smtp_port', DEFAULT_CONFIG['email']['smtp_port'])
    username = get_config('email.username', DEFAULT_CONFIG['email']['username'])
    password = get_config('email.password', DEFAULT_CONFIG['email']['password'])
    recipients = get_config('email.recipients', DEFAULT_CONFIG['email']['recipients'])
    
    if not recipients:
        logger.error("Nenhum destinatário configurado para envio de email")
        return False
    
    try:
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = f"Relatório de Saúde do Sistema - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Adicionar corpo da mensagem
        msg.attach(MIMEText(texto_relatorio, 'plain'))
        
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

def main():
    """Função principal"""
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='Verificador de Saúde do Sistema')
    parser.add_argument('--email', action='store_true', help='Envia relatório por email')
    parser.add_argument('--json', action='store_true', help='Salva relatório em formato JSON')
    args = parser.parse_args()
    
    logger.info("Iniciando verificação de saúde do sistema...")
    
    # Verificar componentes
    resultados = {
        "backend": verificar_backend(),
        "frontend": verificar_frontend(),
        "vm_scripts": verificar_scripts_vm()
    }
    
    # Gerar relatório
    relatorio, texto_relatorio = gerar_relatorio(resultados)
    
    # Exibir relatório
    print(texto_relatorio)
    
    # Salvar relatório em JSON se solicitado
    if args.json:
        salvar_relatorio_json(relatorio)
    
    # Enviar relatório por email se solicitado
    if args.email:
        enviar_email(texto_relatorio)
    
    # Retornar código de saída baseado no status geral
    return 0 if relatorio["status_geral"] == "OK" else 1

if __name__ == "__main__":
    sys.exit(main())
