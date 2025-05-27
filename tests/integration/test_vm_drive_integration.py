"""
Script para testar a integração entre backend, VM e Google Drive.
Este script testa o fluxo completo de criação de pastas e processamento de arquivos.
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
        logging.FileHandler("integration_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("integration_test")

# Adicionar o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar o serviço do Google Drive
from dashboard.backend.app.services.drive_service import DriveService

# Configurações
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5000')
VM_API_URL = os.environ.get('VM_API_URL', 'http://localhost:5000')
VM_API_KEY = os.environ.get('VM_API_KEY', 'api-key-temporaria')
TEST_USER_ID = "test_user_123"
TEST_USER_EMAIL = "test@example.com"

def test_drive_service():
    """Testa as funcionalidades básicas do serviço do Google Drive."""
    logger.info("Iniciando teste do serviço do Google Drive...")
    
    # Verifica se as variáveis de ambiente estão configuradas
    credentials_path = os.environ.get('GOOGLE_DRIVE_CREDENTIALS_PATH')
    
    if not credentials_path or not os.path.exists(credentials_path):
        logger.error(f"Arquivo de credenciais não encontrado: {credentials_path}")
        logger.info("Configure a variável de ambiente GOOGLE_DRIVE_CREDENTIALS_PATH com o caminho para o arquivo de credenciais JSON.")
        return False
    
    try:
        # Inicializa o serviço do Drive
        drive_service = DriveService(credentials_path=credentials_path)
        logger.info("Serviço do Google Drive inicializado com sucesso.")
        
        # Testa a criação de pastas para o usuário de teste
        folders = drive_service.create_user_folders(TEST_USER_ID, TEST_USER_EMAIL)
        logger.info(f"Pastas criadas: {folders}")
        
        if not folders or not folders.get('user_folder_id'):
            logger.error("Falha ao criar pastas no Google Drive.")
            return False
        
        logger.info("Teste do serviço do Google Drive concluído com sucesso.")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar o serviço do Google Drive: {str(e)}")
        return False

def test_vm_folder_manager():
    """Testa o endpoint de gerenciamento de pastas na VM."""
    logger.info("Iniciando teste do gerenciamento de pastas na VM...")
    
    try:
        # Preparar dados para a requisição
        url = f"{VM_API_URL}/api/folders/create"
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': VM_API_KEY
        }
        payload = {
            'user_id': TEST_USER_ID,
            'user_email': TEST_USER_EMAIL,
            'async': False  # Processamento síncrono para teste
        }
        
        # Enviar requisição para a VM
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Resultado da criação de pastas na VM: {result}")
        
        if result.get('status') != 'success':
            logger.error("Falha ao criar pastas na VM.")
            return False
        
        logger.info("Teste do gerenciamento de pastas na VM concluído com sucesso.")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar o gerenciamento de pastas na VM: {str(e)}")
        return False

def test_backend_integration():
    """Testa a integração do backend com a VM e o Google Drive."""
    logger.info("Iniciando teste da integração do backend...")
    
    try:
        # Simular a criação de pastas a partir do backend
        # Normalmente isso seria feito através de uma rota do backend
        # Aqui vamos testar diretamente o serviço do Drive
        
        # Inicializa o serviço do Drive
        credentials_path = os.environ.get('GOOGLE_DRIVE_CREDENTIALS_PATH')
        drive_service = DriveService(credentials_path=credentials_path)
        
        # Testa a delegação de criação de pastas à VM
        folders = drive_service.create_user_folders(TEST_USER_ID, TEST_USER_EMAIL)
        logger.info(f"Pastas criadas e delegadas à VM: {folders}")
        
        if not folders or not folders.get('user_folder_id'):
            logger.error("Falha na integração do backend com a VM e o Google Drive.")
            return False
        
        # Simular o processamento de arquivos
        # Normalmente isso seria acionado por uma notificação do Google Drive
        result = drive_service.process_notification({}, folders.get('novos_folder_id'), TEST_USER_ID)
        logger.info(f"Resultado do processamento de arquivos: {result}")
        
        logger.info("Teste da integração do backend concluído com sucesso.")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar a integração do backend: {str(e)}")
        return False

def test_end_to_end_flow():
    """Testa o fluxo completo de ponta a ponta."""
    logger.info("Iniciando teste do fluxo completo de ponta a ponta...")
    
    try:
        # 1. Criar pastas no Google Drive
        drive_service = DriveService()
        folders = drive_service.create_user_folders(TEST_USER_ID, TEST_USER_EMAIL)
        
        if not folders or not folders.get('user_folder_id'):
            logger.error("Falha ao criar pastas no Google Drive.")
            return False
        
        logger.info(f"Pastas criadas no Google Drive: {folders}")
        
        # 2. Verificar se as pastas foram criadas na VM
        # Isso normalmente seria verificado através do callback
        # Aqui vamos simular verificando diretamente
        
        # Preparar dados para a requisição
        url = f"{VM_API_URL}/api/folders/status"
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': VM_API_KEY
        }
        payload = {
            'user_id': TEST_USER_ID
        }
        
        # Enviar requisição para a VM
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Status das pastas na VM: {result}")
            
            if result.get('status') != 'success':
                logger.warning("Pastas podem não ter sido criadas na VM.")
        except Exception as e:
            logger.warning(f"Não foi possível verificar o status das pastas na VM: {str(e)}")
        
        # 3. Simular o processamento de arquivos
        result = drive_service.process_notification({}, folders.get('novos_folder_id'), TEST_USER_ID)
        logger.info(f"Resultado do processamento de arquivos: {result}")
        
        logger.info("Teste do fluxo completo de ponta a ponta concluído com sucesso.")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar o fluxo completo de ponta a ponta: {str(e)}")
        return False

if __name__ == '__main__':
    print("=== Teste de Integração Backend-VM-Drive ===")
    
    # Testa o serviço do Drive
    drive_ok = test_drive_service()
    print(f"Teste do serviço do Drive: {'OK' if drive_ok else 'FALHA'}")
    
    # Testa o gerenciamento de pastas na VM
    vm_ok = test_vm_folder_manager()
    print(f"Teste do gerenciamento de pastas na VM: {'OK' if vm_ok else 'FALHA'}")
    
    # Testa a integração do backend
    backend_ok = test_backend_integration()
    print(f"Teste da integração do backend: {'OK' if backend_ok else 'FALHA'}")
    
    # Testa o fluxo completo de ponta a ponta
    e2e_ok = test_end_to_end_flow()
    print(f"Teste do fluxo completo de ponta a ponta: {'OK' if e2e_ok else 'FALHA'}")
    
    if drive_ok and vm_ok and backend_ok and e2e_ok:
        print("\n✅ Todos os testes passaram! A integração está funcionando corretamente.")
    else:
        print("\n❌ Alguns testes falharam. Verifique os logs para mais detalhes.")
