"""
Script de teste para validar a integração da criação de pastas.
Este script testa o fluxo completo de criação de pastas na VM e no Google Drive.
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

# Configurações
VM_API_URL = os.environ.get('VM_API_URL', 'http://localhost:5000')
VM_API_KEY = os.environ.get('VM_API_KEY', 'api-key-temporaria')
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5000')
TEST_USER_ID = "test_user_" + datetime.now().strftime("%Y%m%d%H%M%S")
TEST_USER_EMAIL = f"{TEST_USER_ID}@example.com"
TEST_USER_NAME = "Usuário de Teste"

def test_create_folders_sync():
    """Testa a criação síncrona de pastas."""
    logger.info("Iniciando teste de criação síncrona de pastas...")
    
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
            'user_name': TEST_USER_NAME,
            'async': False  # Processamento síncrono para teste
        }
        
        # Enviar requisição para a VM
        logger.info(f"Enviando requisição para {url} com payload: {payload}")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code >= 400:
            logger.error(f"Erro na requisição: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        logger.info(f"Resultado da criação de pastas: {result}")
        
        if result.get('status') != 'success':
            logger.error("Falha ao criar pastas.")
            return False
        
        logger.info("Teste de criação síncrona de pastas concluído com sucesso.")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar criação síncrona de pastas: {str(e)}")
        return False

def test_create_folders_async():
    """Testa a criação assíncrona de pastas."""
    logger.info("Iniciando teste de criação assíncrona de pastas...")
    
    try:
        # Preparar dados para a requisição
        url = f"{VM_API_URL}/api/folders/create"
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': VM_API_KEY
        }
        payload = {
            'user_id': TEST_USER_ID + "_async",
            'user_email': f"{TEST_USER_ID}_async@example.com",
            'user_name': TEST_USER_NAME + " (Async)",
            'async': True,
            'callback_url': f"{BACKEND_URL}/api/callbacks/folders"
        }
        
        # Enviar requisição para a VM
        logger.info(f"Enviando requisição para {url} com payload: {payload}")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code >= 400:
            logger.error(f"Erro na requisição: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        logger.info(f"Resultado da criação assíncrona de pastas: {result}")
        
        if result.get('status') != 'accepted':
            logger.error("Falha ao enfileirar criação de pastas.")
            return False
        
        logger.info("Teste de criação assíncrona de pastas concluído com sucesso.")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar criação assíncrona de pastas: {str(e)}")
        return False

def test_check_folder_status():
    """Testa a verificação de status das pastas."""
    logger.info("Iniciando teste de verificação de status das pastas...")
    
    try:
        # Esperar um pouco para garantir que as pastas foram criadas
        import time
        time.sleep(2)
        
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
        logger.info(f"Enviando requisição para {url} com payload: {payload}")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code >= 400:
            logger.error(f"Erro na requisição: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        logger.info(f"Resultado da verificação de status das pastas: {result}")
        
        if not result.get('exists', False):
            logger.error("Usuário não encontrado após criação de pastas.")
            return False
        
        logger.info("Teste de verificação de status das pastas concluído com sucesso.")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar verificação de status das pastas: {str(e)}")
        return False

def test_end_to_end_flow():
    """Testa o fluxo completo de ponta a ponta."""
    logger.info("Iniciando teste do fluxo completo de ponta a ponta...")
    
    # 1. Criar pastas de forma síncrona
    if not test_create_folders_sync():
        logger.error("Falha no teste de criação síncrona de pastas.")
        return False
    
    # 2. Verificar status das pastas
    if not test_check_folder_status():
        logger.error("Falha no teste de verificação de status das pastas.")
        return False
    
    # 3. Criar pastas de forma assíncrona
    if not test_create_folders_async():
        logger.error("Falha no teste de criação assíncrona de pastas.")
        return False
    
    logger.info("Teste do fluxo completo de ponta a ponta concluído com sucesso.")
    return True

if __name__ == '__main__':
    print("=== Teste de Integração da Criação de Pastas ===")
    
    # Testar o fluxo completo de ponta a ponta
    success = test_end_to_end_flow()
    
    if success:
        print("\n✅ Todos os testes passaram! A integração está funcionando corretamente.")
    else:
        print("\n❌ Alguns testes falharam. Verifique os logs para mais detalhes.")
