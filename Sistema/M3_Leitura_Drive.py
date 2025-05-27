import os
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Caminho para o arquivo JSON da chave de serviço
SERVICE_ACCOUNT_FILE = '/home/flavioleal_souza/Sistema/chave_servico_primaria.json'

# Escopos necessários
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Autenticando com a chave de serviço
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Criando o serviço da API do Google Drive
service = build('drive', 'v3', credentials=credentials)

# Função para listar arquivos PDF de uma pasta específica
def listar_pdfs_na_pasta(service, pasta_id):
    query = f"'{pasta_id}' in parents and mimeType = 'application/pdf'"
    results = service.files().list(q=query, fields='files(id, name)').execute()
    files = results.get('files', [])

    if not files:
        logging.info(f"Nenhum arquivo PDF encontrado na pasta com ID {pasta_id}.")
    else:
        logging.info(f"Arquivos encontrados na pasta {pasta_id}:")
        for file in files:
            logging.info(f"Arquivo: {file['name']} (ID: {file['id']})")

# Função para listar os arquivos na pasta raiz
def listar_arquivos_na_raiz():
    results = service.files().list(pageSize=10, fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        logging.info('Nenhum arquivo encontrado na pasta raiz.')
    else:
        logging.info('Arquivos encontrados na pasta raiz:')
        for item in items:
            logging.info(f"{item['name']} ({item['id']})")

# Função principal
def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # ID da pasta no Google Drive
    pasta_id = '1CMW5SmNRzdWEqq0V56LX7a-CP9HoO59k'  # Alterar para o ID correto da pasta de interesse
    listar_pdfs_na_pasta(service, pasta_id)

if __name__ == "__main__":
    main()
