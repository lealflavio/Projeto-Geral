#!/usr/bin/env python3
"""
Script de Backup Automático

Este script realiza backups automáticos dos componentes críticos do sistema:
1. Configurações
2. Banco de dados
3. Logs
4. Dados extraídos

Integrado com o sistema centralizado de configurações.

Uso:
    python3 backup.py [--full] [--config-only] [--db-only] [--logs-only] [--data-only]

Opções:
    --full: Realiza backup completo de todos os componentes
    --config-only: Realiza backup apenas das configurações
    --db-only: Realiza backup apenas do banco de dados
    --logs-only: Realiza backup apenas dos logs
    --data-only: Realiza backup apenas dos dados extraídos
"""

import os
import sys
import json
import logging
import argparse
import shutil
import subprocess
from datetime import datetime
import zipfile
import tarfile

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
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'backup.log'))
    ]
)
logger = logging.getLogger('backup')

# Configurações padrão (usadas se o sistema de configuração não estiver disponível)
DEFAULT_CONFIG = {
    'paths': {
        'base_dir': '/home/flavioleal_souza/Sistema',
        'config_dir': '/home/flavioleal_souza/Sistema/config',
        'extracao_dados_dir': '/home/flavioleal_souza/Sistema/extracao_dados',
        'logs_dir': '/home/flavioleal_souza/Sistema/logs',
    },
    'backup': {
        'dir': '/home/flavioleal_souza/Sistema/backups',
        'db_name': 'sistema',
        'db_user': 'postgres',
        'db_host': 'localhost',
        'db_port': '5432',
        'retention_days': 30,
        'compression': 'zip'  # 'zip' ou 'tar.gz'
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

def criar_diretorio_backup():
    """Cria o diretório de backup se não existir"""
    backup_dir = get_config('backup.dir', DEFAULT_CONFIG['backup']['dir'])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
    
    os.makedirs(backup_path, exist_ok=True)
    logger.info(f"Diretório de backup criado: {backup_path}")
    
    return backup_path

def backup_configuracoes(backup_path):
    """Realiza backup das configurações"""
    logger.info("Iniciando backup das configurações...")
    
    config_dir = get_config('paths.config_dir', DEFAULT_CONFIG['paths']['config_dir'])
    config_backup_dir = os.path.join(backup_path, "config")
    
    if not os.path.exists(config_dir):
        logger.warning(f"Diretório de configurações não encontrado: {config_dir}")
        return False
    
    try:
        # Criar diretório de backup para configurações
        os.makedirs(config_backup_dir, exist_ok=True)
        
        # Copiar arquivos de configuração
        for item in os.listdir(config_dir):
            item_path = os.path.join(config_dir, item)
            if os.path.isfile(item_path):
                shutil.copy2(item_path, config_backup_dir)
            elif os.path.isdir(item_path):
                shutil.copytree(item_path, os.path.join(config_backup_dir, item))
        
        logger.info(f"Backup de configurações concluído: {config_backup_dir}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao realizar backup das configurações: {str(e)}")
        return False

def backup_banco_dados(backup_path):
    """Realiza backup do banco de dados"""
    logger.info("Iniciando backup do banco de dados...")
    
    db_name = get_config('backup.db_name', DEFAULT_CONFIG['backup']['db_name'])
    db_user = get_config('backup.db_user', DEFAULT_CONFIG['backup']['db_user'])
    db_host = get_config('backup.db_host', DEFAULT_CONFIG['backup']['db_host'])
    db_port = get_config('backup.db_port', DEFAULT_CONFIG['backup']['db_port'])
    
    db_backup_file = os.path.join(backup_path, f"{db_name}.sql")
    
    try:
        # Verificar se pg_dump está disponível
        try:
            subprocess.run(['pg_dump', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("pg_dump não encontrado. Pulando backup do banco de dados.")
            return False
        
        # Executar pg_dump
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-p', db_port,
            '-U', db_user,
            '-F', 'p',  # Formato plain text
            '-f', db_backup_file,
            db_name
        ]
        
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if os.path.exists(db_backup_file) and os.path.getsize(db_backup_file) > 0:
            logger.info(f"Backup do banco de dados concluído: {db_backup_file}")
            return True
        else:
            logger.error("Backup do banco de dados falhou: arquivo vazio ou inexistente")
            return False
    
    except Exception as e:
        logger.error(f"Erro ao realizar backup do banco de dados: {str(e)}")
        return False

def backup_logs(backup_path):
    """Realiza backup dos logs"""
    logger.info("Iniciando backup dos logs...")
    
    logs_dir = get_config('paths.logs_dir', DEFAULT_CONFIG['paths']['logs_dir'])
    logs_backup_dir = os.path.join(backup_path, "logs")
    
    if not os.path.exists(logs_dir):
        logger.warning(f"Diretório de logs não encontrado: {logs_dir}")
        return False
    
    try:
        # Criar diretório de backup para logs
        os.makedirs(logs_backup_dir, exist_ok=True)
        
        # Copiar arquivos de log
        for item in os.listdir(logs_dir):
            if item.endswith('.log'):
                item_path = os.path.join(logs_dir, item)
                if os.path.isfile(item_path):
                    shutil.copy2(item_path, logs_backup_dir)
        
        logger.info(f"Backup de logs concluído: {logs_backup_dir}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao realizar backup dos logs: {str(e)}")
        return False

def backup_dados_extraidos(backup_path):
    """Realiza backup dos dados extraídos"""
    logger.info("Iniciando backup dos dados extraídos...")
    
    dados_dir = get_config('paths.extracao_dados_dir', DEFAULT_CONFIG['paths']['extracao_dados_dir'])
    dados_backup_dir = os.path.join(backup_path, "extracao_dados")
    
    if not os.path.exists(dados_dir):
        logger.warning(f"Diretório de dados extraídos não encontrado: {dados_dir}")
        return False
    
    try:
        # Criar diretório de backup para dados
        os.makedirs(dados_backup_dir, exist_ok=True)
        
        # Copiar arquivos de dados
        for item in os.listdir(dados_dir):
            item_path = os.path.join(dados_dir, item)
            if os.path.isfile(item_path):
                shutil.copy2(item_path, dados_backup_dir)
        
        logger.info(f"Backup de dados extraídos concluído: {dados_backup_dir}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao realizar backup dos dados extraídos: {str(e)}")
        return False

def comprimir_backup(backup_path):
    """Comprime o diretório de backup"""
    logger.info("Comprimindo backup...")
    
    compression = get_config('backup.compression', DEFAULT_CONFIG['backup']['compression'])
    backup_dir = os.path.dirname(backup_path)
    backup_name = os.path.basename(backup_path)
    
    try:
        if compression == 'zip':
            # Comprimir usando ZIP
            zip_file = os.path.join(backup_dir, f"{backup_name}.zip")
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)
            
            logger.info(f"Backup comprimido em ZIP: {zip_file}")
            return zip_file
        
        elif compression == 'tar.gz':
            # Comprimir usando TAR.GZ
            tar_file = os.path.join(backup_dir, f"{backup_name}.tar.gz")
            with tarfile.open(tar_file, "w:gz") as tar:
                tar.add(backup_path, arcname=backup_name)
            
            logger.info(f"Backup comprimido em TAR.GZ: {tar_file}")
            return tar_file
        
        else:
            logger.warning(f"Formato de compressão não suportado: {compression}")
            return None
    
    except Exception as e:
        logger.error(f"Erro ao comprimir backup: {str(e)}")
        return None

def limpar_backups_antigos():
    """Remove backups mais antigos que o período de retenção configurado"""
    logger.info("Verificando backups antigos...")
    
    backup_dir = get_config('backup.dir', DEFAULT_CONFIG['backup']['dir'])
    retention_days = get_config('backup.retention_days', DEFAULT_CONFIG['backup']['retention_days'])
    
    if not os.path.exists(backup_dir):
        logger.warning(f"Diretório de backups não encontrado: {backup_dir}")
        return
    
    try:
        # Calcular data limite
        now = datetime.now()
        limit_date = now.timestamp() - (retention_days * 24 * 60 * 60)
        
        # Listar arquivos de backup
        backup_files = []
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            if os.path.isfile(item_path) and (item.endswith('.zip') or item.endswith('.tar.gz')):
                mtime = os.path.getmtime(item_path)
                if mtime < limit_date:
                    backup_files.append(item_path)
        
        # Remover backups antigos
        for file_path in backup_files:
            os.remove(file_path)
            logger.info(f"Backup antigo removido: {file_path}")
        
        logger.info(f"{len(backup_files)} backups antigos removidos")
    
    except Exception as e:
        logger.error(f"Erro ao limpar backups antigos: {str(e)}")

def main():
    """Função principal"""
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='Backup Automático do Sistema')
    parser.add_argument('--full', action='store_true', help='Realiza backup completo')
    parser.add_argument('--config-only', action='store_true', help='Realiza backup apenas das configurações')
    parser.add_argument('--db-only', action='store_true', help='Realiza backup apenas do banco de dados')
    parser.add_argument('--logs-only', action='store_true', help='Realiza backup apenas dos logs')
    parser.add_argument('--data-only', action='store_true', help='Realiza backup apenas dos dados extraídos')
    args = parser.parse_args()
    
    # Se nenhuma opção for especificada, assume backup completo
    if not (args.full or args.config_only or args.db_only or args.logs_only or args.data_only):
        args.full = True
    
    logger.info("Iniciando processo de backup...")
    
    # Criar diretório de backup
    backup_path = criar_diretorio_backup()
    
    # Realizar backups conforme solicitado
    results = {}
    
    if args.full or args.config_only:
        results['config'] = backup_configuracoes(backup_path)
    
    if args.full or args.db_only:
        results['db'] = backup_banco_dados(backup_path)
    
    if args.full or args.logs_only:
        results['logs'] = backup_logs(backup_path)
    
    if args.full or args.data_only:
        results['data'] = backup_dados_extraidos(backup_path)
    
    # Comprimir backup
    compressed_file = comprimir_backup(backup_path)
    
    # Limpar diretório temporário
    if compressed_file:
        shutil.rmtree(backup_path)
        logger.info(f"Diretório temporário removido: {backup_path}")
    
    # Limpar backups antigos
    limpar_backups_antigos()
    
    # Resumo
    logger.info("Resumo do backup:")
    for component, success in results.items():
        logger.info(f"- {component}: {'Sucesso' if success else 'Falha'}")
    
    if compressed_file:
        logger.info(f"Backup concluído: {compressed_file}")
        return 0
    else:
        logger.error("Falha ao comprimir backup")
        return 1

if __name__ == "__main__":
    sys.exit(main())
