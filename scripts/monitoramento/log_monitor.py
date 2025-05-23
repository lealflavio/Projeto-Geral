#!/usr/bin/env python3
"""
Script de Monitoramento de Logs

Este script monitora os logs do sistema, detecta padrões de erro
e gera alertas quando necessário.

Integrado com o sistema centralizado de configurações.

Uso:
    python3 log_monitor.py [--watch] [--analyze] [--report]

Opções:
    --watch: Monitora logs em tempo real
    --analyze: Analisa logs existentes
    --report: Gera relatório de erros
"""

import os
import sys
import json
import logging
import argparse
import re
import time
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict

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
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'log_monitor.log'))
    ]
)
logger = logging.getLogger('log_monitor')

# Configurações padrão (usadas se o sistema de configuração não estiver disponível)
DEFAULT_CONFIG = {
    'paths': {
        'base_dir': '/home/flavioleal_souza/Sistema',
        'logs_dir': '/home/flavioleal_souza/Sistema/logs',
    },
    'log_monitor': {
        'patterns': {
            'error': ['ERROR', 'Exception', 'Traceback', 'Failed', 'Falha'],
            'warning': ['WARNING', 'WARN', 'Aviso'],
            'critical': ['CRITICAL', 'FATAL', 'EMERGENCY']
        },
        'watch_interval': 5,  # segundos
        'alert_threshold': 5,  # número de erros para gerar alerta
        'report_dir': '/home/flavioleal_souza/Sistema/reports'
    },
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

def encontrar_arquivos_log():
    """Encontra todos os arquivos de log no sistema"""
    logs_dir = get_config('paths.logs_dir', DEFAULT_CONFIG['paths']['logs_dir'])
    
    if not os.path.exists(logs_dir):
        logger.warning(f"Diretório de logs não encontrado: {logs_dir}")
        return []
    
    log_files = []
    
    # Procurar arquivos de log no diretório principal
    for item in os.listdir(logs_dir):
        if item.endswith('.log'):
            log_files.append(os.path.join(logs_dir, item))
    
    # Procurar logs em diretórios de técnicos
    tecnicos_dir = os.path.join(get_config('paths.base_dir', DEFAULT_CONFIG['paths']['base_dir']), 'tecnicos')
    if os.path.exists(tecnicos_dir):
        for tecnico in os.listdir(tecnicos_dir):
            tecnico_logs_dir = os.path.join(tecnicos_dir, tecnico, 'logs')
            if os.path.exists(tecnico_logs_dir):
                for item in os.listdir(tecnico_logs_dir):
                    if item.endswith('.log'):
                        log_files.append(os.path.join(tecnico_logs_dir, item))
    
    logger.info(f"Encontrados {len(log_files)} arquivos de log")
    return log_files

def analisar_log(log_file, start_time=None):
    """Analisa um arquivo de log em busca de padrões de erro"""
    patterns = get_config('log_monitor.patterns', DEFAULT_CONFIG['log_monitor']['patterns'])
    
    # Compilar expressões regulares para os padrões
    regex_patterns = {
        level: [re.compile(pattern, re.IGNORECASE) for pattern in patterns_list]
        for level, patterns_list in patterns.items()
    }
    
    # Inicializar contadores
    counts = {
        'error': 0,
        'warning': 0,
        'critical': 0,
        'total_lines': 0
    }
    
    # Armazenar ocorrências
    occurrences = {
        'error': [],
        'warning': [],
        'critical': []
    }
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                counts['total_lines'] += 1
                
                # Verificar se a linha contém timestamp e está dentro do período
                if start_time:
                    # Tentar extrair timestamp da linha (formato comum: 2025-05-23 21:42:31)
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
                    if timestamp_match:
                        try:
                            line_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                            if line_time < start_time:
                                continue  # Pular linhas anteriores ao tempo de início
                        except ValueError:
                            pass  # Se não conseguir parsear o timestamp, continua processando
                
                # Verificar padrões
                for level, patterns in regex_patterns.items():
                    for pattern in patterns:
                        if pattern.search(line):
                            counts[level] += 1
                            occurrences[level].append({
                                'line': line_num,
                                'text': line.strip()
                            })
                            break  # Se encontrou um padrão, não precisa verificar os outros do mesmo nível
        
        logger.info(f"Análise de {log_file}: {counts['error']} erros, {counts['warning']} avisos, {counts['critical']} críticos")
        return counts, occurrences
    
    except Exception as e:
        logger.error(f"Erro ao analisar log {log_file}: {str(e)}")
        return counts, occurrences

def monitorar_logs_tempo_real():
    """Monitora logs em tempo real"""
    logger.info("Iniciando monitoramento de logs em tempo real...")
    
    log_files = encontrar_arquivos_log()
    if not log_files:
        logger.error("Nenhum arquivo de log encontrado para monitorar")
        return False
    
    # Armazenar posições iniciais dos arquivos
    file_positions = {}
    for log_file in log_files:
        try:
            file_positions[log_file] = os.path.getsize(log_file)
        except os.error:
            file_positions[log_file] = 0
    
    # Configurar intervalo de verificação
    interval = get_config('log_monitor.watch_interval', DEFAULT_CONFIG['log_monitor']['watch_interval'])
    
    # Configurar limite de alertas
    alert_threshold = get_config('log_monitor.alert_threshold', DEFAULT_CONFIG['log_monitor']['alert_threshold'])
    
    # Inicializar contadores de erros
    error_counts = defaultdict(int)
    
    try:
        logger.info(f"Monitorando {len(log_files)} arquivos de log. Pressione Ctrl+C para interromper.")
        
        while True:
            for log_file in log_files:
                try:
                    # Verificar se o arquivo existe
                    if not os.path.exists(log_file):
                        continue
                    
                    # Verificar se o arquivo foi modificado
                    current_size = os.path.getsize(log_file)
                    if current_size <= file_positions[log_file]:
                        continue
                    
                    # Ler novas linhas
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(file_positions[log_file])
                        new_lines = f.readlines()
                    
                    # Atualizar posição
                    file_positions[log_file] = current_size
                    
                    # Verificar padrões nas novas linhas
                    patterns = get_config('log_monitor.patterns', DEFAULT_CONFIG['log_monitor']['patterns'])
                    for line in new_lines:
                        for level, patterns_list in patterns.items():
                            for pattern in patterns_list:
                                if re.search(pattern, line, re.IGNORECASE):
                                    if level in ['error', 'critical']:
                                        error_counts[log_file] += 1
                                        logger.warning(f"Detectado {level} em {log_file}: {line.strip()}")
                                        
                                        # Verificar se atingiu o limite para alerta
                                        if error_counts[log_file] >= alert_threshold:
                                            gerar_alerta(log_file, f"Detectados {error_counts[log_file]} erros")
                                            error_counts[log_file] = 0  # Resetar contador após alerta
                                    break
                
                except Exception as e:
                    logger.error(f"Erro ao monitorar {log_file}: {str(e)}")
            
            # Aguardar próxima verificação
            time.sleep(interval)
    
    except KeyboardInterrupt:
        logger.info("Monitoramento interrompido pelo usuário")
    
    return True

def gerar_alerta(log_file, mensagem):
    """Gera um alerta para erros detectados"""
    logger.warning(f"ALERTA: {mensagem} em {log_file}")
    
    # Verificar se envio de email está habilitado
    if get_config('email.enabled', DEFAULT_CONFIG['email']['enabled']):
        enviar_email_alerta(log_file, mensagem)

def enviar_email_alerta(log_file, mensagem):
    """Envia um email de alerta"""
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
        msg['Subject'] = f"ALERTA: Erros detectados em {os.path.basename(log_file)}"
        
        # Corpo da mensagem
        body = f"""
        ALERTA DE MONITORAMENTO DE LOGS
        
        Arquivo: {log_file}
        Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Mensagem: {mensagem}
        
        Este é um email automático. Por favor, verifique o sistema.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Conectar ao servidor SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        
        # Enviar email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email de alerta enviado para: {', '.join(recipients)}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao enviar email de alerta: {str(e)}")
        return False

def gerar_relatorio(periodo=None):
    """Gera um relatório de análise de logs"""
    logger.info("Gerando relatório de análise de logs...")
    
    # Determinar período de análise
    start_time = None
    if periodo:
        if periodo == 'day':
            start_time = datetime.now() - timedelta(days=1)
        elif periodo == 'week':
            start_time = datetime.now() - timedelta(weeks=1)
        elif periodo == 'month':
            start_time = datetime.now() - timedelta(days=30)
    
    # Encontrar arquivos de log
    log_files = encontrar_arquivos_log()
    if not log_files:
        logger.error("Nenhum arquivo de log encontrado para análise")
        return None
    
    # Analisar cada arquivo
    resultados = {}
    for log_file in log_files:
        counts, occurrences = analisar_log(log_file, start_time)
        resultados[log_file] = {
            'counts': counts,
            'occurrences': occurrences
        }
    
    # Gerar relatório
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = get_config('log_monitor.report_dir', DEFAULT_CONFIG['log_monitor']['report_dir'])
    os.makedirs(report_dir, exist_ok=True)
    
    report_file = os.path.join(report_dir, f"log_analysis_{timestamp}.json")
    
    # Adicionar metadados ao relatório
    relatorio = {
        'timestamp': timestamp,
        'periodo': periodo,
        'total_arquivos': len(log_files),
        'resultados': resultados
    }
    
    # Salvar relatório
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Relatório salvo em: {report_file}")
    
    # Gerar resumo
    total_errors = sum(r['counts']['error'] for r in resultados.values())
    total_warnings = sum(r['counts']['warning'] for r in resultados.values())
    total_critical = sum(r['counts']['critical'] for r in resultados.values())
    
    logger.info("Resumo da análise:")
    logger.info(f"- Total de arquivos: {len(log_files)}")
    logger.info(f"- Total de erros: {total_errors}")
    logger.info(f"- Total de avisos: {total_warnings}")
    logger.info(f"- Total de críticos: {total_critical}")
    
    return report_file

def main():
    """Função principal"""
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='Monitoramento de Logs do Sistema')
    parser.add_argument('--watch', action='store_true', help='Monitora logs em tempo real')
    parser.add_argument('--analyze', action='store_true', help='Analisa logs existentes')
    parser.add_argument('--report', choices=['day', 'week', 'month', 'all'], help='Gera relatório de erros para o período especificado')
    args = parser.parse_args()
    
    # Se nenhuma opção for especificada, mostrar ajuda
    if not (args.watch or args.analyze or args.report):
        parser.print_help()
        return 0
    
    # Executar ações solicitadas
    if args.watch:
        monitorar_logs_tempo_real()
    
    if args.analyze or args.report:
        periodo = args.report if args.report else None
        gerar_relatorio(periodo)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
