"""
Integração do Dashboard com a VM para criação de pastas no Google Drive.
Este arquivo implementa a integração entre o Dashboard e a VM para criação de pastas.
"""

import os
import json
import logging
import requests
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dashboard_vm_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dashboard_vm_integration")

# Configurações da API da VM
VM_API_URL = os.environ.get('VM_API_URL', 'http://localhost:5000')
VM_API_KEY = os.environ.get('VM_API_KEY', 'api-key-temporaria')
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5000')

class VMIntegration:
    """Classe para integração com a VM."""
    
    @staticmethod
    def create_user_folders(user_id, user_email, user_name=None, async_processing=True):
        """
        Cria pastas para um usuário na VM e no Google Drive.
        
        Args:
            user_id (str): ID do usuário.
            user_email (str): Email do usuário.
            user_name (str, optional): Nome do usuário. Se None, usa "Usuario_{user_id}".
            async_processing (bool, optional): Se True, processa de forma assíncrona.
            
        Returns:
            dict: Resultado da criação de pastas.
        """
        logger.info(f"Solicitando criação de pastas para usuário {user_id} ({user_email})")
        
        if not user_name:
            user_name = f"Usuario_{user_id}"
        
        try:
            # Preparar dados para a requisição
            url = f"{VM_API_URL}/api/folders/create"
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': VM_API_KEY
            }
            payload = {
                'user_id': user_id,
                'user_email': user_email,
                'user_name': user_name,
                'async': async_processing
            }
            
            if async_processing:
                payload['callback_url'] = f"{BACKEND_URL}/api/callbacks/folders"
            
            # Enviar requisição para a VM
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Resultado da criação de pastas: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao criar pastas para usuário {user_id}: {str(e)}")
            return {
                "status": "error",
                "message": f"Erro ao criar pastas: {str(e)}"
            }
    
    @staticmethod
    def check_folder_status(user_id=None, user_email=None):
        """
        Verifica o status das pastas de um usuário.
        
        Args:
            user_id (str, optional): ID do usuário.
            user_email (str, optional): Email do usuário.
            
        Returns:
            dict: Status das pastas.
        """
        logger.info(f"Verificando status das pastas para usuário {user_id or user_email}")
        
        if not (user_id or user_email):
            return {
                "status": "error",
                "message": "ID do usuário ou email ausente"
            }
        
        try:
            # Preparar dados para a requisição
            url = f"{VM_API_URL}/api/folders/status"
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': VM_API_KEY
            }
            payload = {}
            
            if user_id:
                payload['user_id'] = user_id
            if user_email:
                payload['user_email'] = user_email
            
            # Enviar requisição para a VM
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Status das pastas: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao verificar status das pastas: {str(e)}")
            return {
                "status": "error",
                "message": f"Erro ao verificar status das pastas: {str(e)}"
            }
    
    @staticmethod
    def process_folder_files(user_id, drive_folder_id=None, async_processing=True):
        """
        Processa arquivos em uma pasta específica.
        
        Args:
            user_id (str): ID do usuário.
            drive_folder_id (str, optional): ID da pasta do Drive a ser processada.
            async_processing (bool, optional): Se True, processa de forma assíncrona.
            
        Returns:
            dict: Resultado do processamento.
        """
        logger.info(f"Solicitando processamento de arquivos para usuário {user_id}")
        
        try:
            # Preparar dados para a requisição
            url = f"{VM_API_URL}/api/folders/process"
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': VM_API_KEY
            }
            payload = {
                'user_id': user_id,
                'async': async_processing
            }
            
            if drive_folder_id:
                payload['drive_folder_id'] = drive_folder_id
            
            if async_processing:
                payload['callback_url'] = f"{BACKEND_URL}/api/callbacks/process"
            
            # Enviar requisição para a VM
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Resultado do processamento de arquivos: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivos para usuário {user_id}: {str(e)}")
            return {
                "status": "error",
                "message": f"Erro ao processar arquivos: {str(e)}"
            }
