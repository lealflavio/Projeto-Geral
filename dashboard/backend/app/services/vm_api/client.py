"""
Cliente para comunicação com a API da VM.
Este módulo implementa as funções para interagir com a API REST da VM.
"""

import requests
import logging
import os
import json
from flask import current_app, request

# Configurar logging
logger = logging.getLogger(__name__)

class VMApiClient:
    def __init__(self):
        self.base_url = os.getenv('VM_API_URL', 'http://34.88.3.237:5000')
        self.api_key = os.getenv('VM_API_KEY', 'api-key-temporaria')
        
        if not self.base_url:
            logger.error("VM_API_URL não configurada")
            raise ValueError("VM_API_URL não configurada")
        
        if not self.api_key:
            logger.error("VM_API_KEY não configurada")
            raise ValueError("VM_API_KEY não configurada")
    
    def _get_headers(self):
        """Retorna os headers padrão para requisições."""
        return {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
    
    def allocate_work_order(self, work_order_id, credentials, async_processing=False):
        """
        Aloca uma ordem de trabalho.
        
        Args:
            work_order_id (str): ID da ordem de trabalho
            credentials (dict): Credenciais do técnico
            async_processing (bool): Se True, processa de forma assíncrona
            
        Returns:
            dict: Resultado da alocação
        """
        url = f"{self.base_url}/api/allocate"
        
        data = {
            'work_order_id': work_order_id,
            'credentials': credentials,
            'async': async_processing
        }
        
        if async_processing:
            # Se for assíncrono, adicionar URL de callback
            callback_url = f"{request.url_root.rstrip('/')}/api/callbacks/allocation-result"
            data['callback_url'] = callback_url
        
        try:
            response = requests.post(
                url,
                json=data,
                headers=self._get_headers(),
                timeout=30 if not async_processing else 10
            )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao alocar WO {work_order_id}: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Resposta de erro: {e.response.text}")
            raise
    
    def process_pdf(self, pdf_path, tecnico_id, credentials=None):
        """
        Envia um PDF para processamento.
        
        Args:
            pdf_path (str): Caminho do PDF na VM
            tecnico_id (int): ID do técnico
            credentials (dict, opcional): Credenciais do técnico
            
        Returns:
            dict: Resultado do enfileiramento
        """
        url = f"{self.base_url}/api/process"
        
        data = {
            'pdf_path': pdf_path,
            'tecnico_id': tecnico_id
        }
        
        if credentials:
            data['credentials'] = credentials
        
        # Adicionar URL de callback
        callback_url = f"{request.url_root.rstrip('/')}/api/callbacks/processing-result"
        data['callback_url'] = callback_url
        
        try:
            response = requests.post(
                url,
                json=data,
                headers=self._get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao processar PDF {pdf_path}: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Resposta de erro: {e.response.text}")
            raise
    
    def get_job_status(self, job_id):
        """
        Verifica o status de uma tarefa.
        
        Args:
            job_id (str): ID da tarefa
            
        Returns:
            dict: Status da tarefa
        """
        url = f"{self.base_url}/api/status/{job_id}"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao verificar status da tarefa {job_id}: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Resposta de erro: {e.response.text}")
            raise
    
    def check_health(self):
        """
        Verifica a saúde da VM API.
        
        Returns:
            dict: Status de saúde
        """
        url = f"{self.base_url}/api/health"
        
        try:
            response = requests.get(
                url,
                timeout=5
            )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao verificar saúde da VM API: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
