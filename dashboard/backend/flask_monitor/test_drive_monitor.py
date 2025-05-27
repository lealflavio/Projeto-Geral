"""
Script para testar o monitoramento do Google Drive.
Este script simula uma notificação do Google Drive e verifica se o processamento
dos arquivos está funcionando corretamente.
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("drive_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("drive_test")

# Adiciona o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importa o serviço do Google Drive
from dashboard.backend.app.services.drive_service import DriveService

def test_drive_service():
    """Testa as funcionalidades básicas do serviço do Google Drive."""
    logger.info("Iniciando teste do serviço do Google Drive...")
    
    # Verifica se as variáveis de ambiente estão configuradas
    credentials_path = os.environ.get('GOOGLE_DRIVE_CREDENTIALS_PATH')
    base_folder_id = os.environ.get('GOOGLE_DRIVE_BASE_FOLDER_ID')
    
    if not credentials_path or not os.path.exists(credentials_path):
        logger.error(f"Arquivo de credenciais não encontrado: {credentials_path}")
        logger.info("Configure a variável de ambiente GOOGLE_DRIVE_CREDENTIALS_PATH com o caminho para o arquivo de credenciais JSON.")
        return False
    
    if not base_folder_id:
        logger.error("ID da pasta base não configurado.")
        logger.info("Configure a variável de ambiente GOOGLE_DRIVE_BASE_FOLDER_ID com o ID da pasta a ser monitorada.")
        return False
    
    try:
        # Inicializa o serviço do Drive
        drive_service = DriveService(credentials_path=credentials_path)
        logger.info("Serviço do Google Drive inicializado com sucesso.")
        
        # Testa a listagem de arquivos
        files = drive_service.list_files(base_folder_id)
        logger.info(f"Listagem de arquivos: {len(files)} arquivos encontrados.")
        
        # Testa a criação da estrutura de pastas
        folders = drive_service.ensure_folder_structure(base_folder_id)
        logger.info(f"Estrutura de pastas criada: {folders}")
        
        # Testa o processamento de notificações
        download_path = '/tmp/drive_test'
        os.makedirs(download_path, exist_ok=True)
        
        results = drive_service.process_notification(
            notification_data={},
            base_folder_id=base_folder_id,
            download_path=download_path
        )
        
        logger.info(f"Processamento de notificação: {len(results['processed'])} arquivos processados, {len(results['errors'])} erros.")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar o serviço do Google Drive: {str(e)}")
        return False

def test_webhook_endpoint():
    """Testa o endpoint webhook da aplicação Flask."""
    logger.info("Iniciando teste do endpoint webhook...")
    
    try:
        # Verifica se o servidor está rodando
        response = requests.get('http://localhost:5001/status')
        if response.status_code != 200:
            logger.error(f"Erro ao verificar status do servidor: {response.status_code}")
            logger.info("Certifique-se de que a aplicação Flask está rodando na porta 5001.")
            return False
        
        logger.info(f"Status do servidor: {response.json()}")
        
        # Testa o endpoint de verificação manual
        response = requests.get('http://localhost:5001/check')
        if response.status_code != 200:
            logger.error(f"Erro ao verificar arquivos: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        logger.info(f"Verificação manual: {result['processed']} arquivos processados, {result['errors']} erros.")
        
        # Simula uma notificação do Google Drive
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Channel-ID': f'test-channel-{datetime.now().timestamp()}',
            'X-Goog-Resource-ID': 'test-resource',
            'X-Goog-Resource-State': 'change',
            'X-Goog-Message-Number': '1'
        }
        
        payload = {
            'kind': 'drive#change',
            'fileId': 'test-file-id',
            'removed': False,
            'time': datetime.now().isoformat()
        }
        
        response = requests.post('http://localhost:5001/webhook', headers=headers, json=payload)
        if response.status_code != 200:
            logger.error(f"Erro ao enviar notificação: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        logger.info(f"Notificação processada: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar o endpoint webhook: {str(e)}")
        return False

if __name__ == '__main__':
    print("=== Teste do Monitoramento do Google Drive ===")
    
    # Testa o serviço do Drive
    service_ok = test_drive_service()
    print(f"Teste do serviço do Drive: {'OK' if service_ok else 'FALHA'}")
    
    # Testa o endpoint webhook
    webhook_ok = test_webhook_endpoint()
    print(f"Teste do endpoint webhook: {'OK' if webhook_ok else 'FALHA'}")
    
    if service_ok and webhook_ok:
        print("\n✅ Todos os testes passaram! O monitoramento do Google Drive está funcionando corretamente.")
    else:
        print("\n❌ Alguns testes falharam. Verifique os logs para mais detalhes.")
