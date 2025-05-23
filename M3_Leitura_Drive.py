#!/usr/bin/env python3
"""
Leitor de arquivos do Google Drive

Este script acessa o Google Drive usando uma conta de serviço,
listando arquivos PDF em pastas específicas.
Refatorado para usar caminhos relativos através do sistema centralizado de configurações.
"""

import os
import logging
import sys
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('leitura_drive')

# Adicionar diretório raiz ao path para importação
try:
    # Determinar o diretório base do projeto
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
except Exception as e:
    logger.error(f"Erro ao configurar path: {str(e)}")

# Importar utilitários de caminho
try:
    from config.path_utils import get_path, join_path
    USING_PATH_UTILS = True
except ImportError:
    logger.warning("Utilitários de caminho não encontrados. Usando caminhos padrão.")
    USING_PATH_UTILS = False
    # Definir caminho padrão para compatibilidade
    SERVICE_ACCOUNT_FILE = '/home/flavioleal_souza/Sistema/chave_servico_primaria.json'

# Escopos necessários
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """
    Cria e retorna um serviço autenticado da API do Google Drive.
    
    Returns:
        Um objeto de serviço da API do Google Drive.
    """
    try:
        # Obter caminho do arquivo de credenciais
        if USING_PATH_UTILS:
            # Usar sistema centralizado de configurações
            service_account_file = get_path('google.service_account_file')
        else:
            # Fallback para caminho absoluto
            service_account_file = SERVICE_ACCOUNT_FILE
        
        # Verificar se o arquivo existe
        if not os.path.exists(service_account_file):
            logger.error(f"Arquivo de credenciais não encontrado: {service_account_file}")
            return None
        
        # Autenticar com a chave de serviço
        credentials = Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
        
        # Criar o serviço da API do Google Drive
        service = build('drive', 'v3', credentials=credentials)
        return service
    
    except Exception as e:
        logger.error(f"Erro ao criar serviço do Google Drive: {str(e)}")
        return None

# Função para listar arquivos PDF de uma pasta específica
def listar_pdfs_na_pasta(service, pasta_id):
    """
    Lista todos os arquivos PDF em uma pasta específica do Google Drive.
    
    Args:
        service: Serviço autenticado da API do Google Drive.
        pasta_id: ID da pasta no Google Drive.
    
    Returns:
        Lista de dicionários com informações dos arquivos (id, name).
    """
    if not service:
        logger.error("Serviço do Google Drive não inicializado.")
        return []
    
    try:
        query = f"'{pasta_id}' in parents and mimeType = 'application/pdf'"
        results = service.files().list(q=query, fields='files(id, name)').execute()
        files = results.get('files', [])

        if not files:
            logger.info(f"Nenhum arquivo PDF encontrado na pasta com ID {pasta_id}.")
        else:
            logger.info(f"Arquivos encontrados na pasta {pasta_id}:")
            for file in files:
                logger.info(f"Arquivo: {file['name']} (ID: {file['id']})")
        
        return files
    
    except Exception as e:
        logger.error(f"Erro ao listar arquivos na pasta {pasta_id}: {str(e)}")
        return []

# Função para listar os arquivos na pasta raiz
def listar_arquivos_na_raiz(service):
    """
    Lista todos os arquivos na pasta raiz do Google Drive.
    
    Args:
        service: Serviço autenticado da API do Google Drive.
    
    Returns:
        Lista de dicionários com informações dos arquivos (id, name).
    """
    if not service:
        logger.error("Serviço do Google Drive não inicializado.")
        return []
    
    try:
        results = service.files().list(pageSize=10, fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            logger.info('Nenhum arquivo encontrado na pasta raiz.')
        else:
            logger.info('Arquivos encontrados na pasta raiz:')
            for item in items:
                logger.info(f"{item['name']} ({item['id']})")
        
        return items
    
    except Exception as e:
        logger.error(f"Erro ao listar arquivos na raiz: {str(e)}")
        return []

# Função principal
def main():
    """Função principal do script."""
    # Inicializar serviço do Google Drive
    service = get_drive_service()
    if not service:
        logger.error("Não foi possível inicializar o serviço do Google Drive. Encerrando.")
        return
    
    # ID da pasta no Google Drive
    pasta_id = '1CMW5SmNRzdWEqq0V56LX7a-CP9HoO59k'  # Alterar para o ID correto da pasta de interesse
    listar_pdfs_na_pasta(service, pasta_id)

if __name__ == "__main__":
    main()
