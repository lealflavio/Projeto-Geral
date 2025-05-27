"""
Cliente para comunicação com a VM API.
Versão refatorada para ser compatível com FastAPI.
Timeouts ajustados para operações longas do Selenium.
"""
import os
import logging
import requests

# Configurar logging
logger = logging.getLogger(__name__)

class VMApiClient:
    """Cliente para comunicação com a VM API."""
    
    def __init__(self, base_callback_url=None):
        """
        Inicializa o cliente da VM API.
        
        Args:
            base_callback_url (str, opcional): URL base para callbacks
                Se não fornecido, será obtido da variável de ambiente BACKEND_URL
        """
        self.base_url = os.getenv('VM_API_URL', 'http://34.88.3.237:5000')
        self.api_key = os.getenv('VM_API_KEY', 'api-key-temporaria')
        
        # URL base para callbacks - não depende mais do Flask request
        self.base_callback_url = base_callback_url or os.getenv('BACKEND_URL')
        
        # Timeouts configuráveis via variáveis de ambiente
        self.timeout_allocate = int(os.getenv('VM_API_TIMEOUT_ALLOCATE', '120'))  # 2 minutos para alocação
        self.timeout_process = int(os.getenv('VM_API_TIMEOUT_PROCESS', '30'))     # 30 segundos para processamento
        self.timeout_status = int(os.getenv('VM_API_TIMEOUT_STATUS', '20'))       # 20 segundos para status
        self.timeout_health = int(os.getenv('VM_API_TIMEOUT_HEALTH', '10'))       # 10 segundos para health check
        
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
    
    def _get_callback_url(self, endpoint):
        """
        Gera URL de callback para o endpoint especificado.
        
        Args:
            endpoint (str): Endpoint para callback (ex: 'allocation-result')
            
        Returns:
            str: URL completa para callback
        """
        if not self.base_callback_url:
            logger.warning("URL base para callbacks não configurada")
            return None
        
        # Garantir que a URL base não termine com barra
        base = self.base_callback_url.rstrip('/')
        
        # Garantir que o endpoint não comece com barra
        endpoint = endpoint.lstrip('/')
        
        return f"{base}/api/callbacks/{endpoint}"
    
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
            callback_url = self._get_callback_url('allocation-result')
            if callback_url:
                data['callback_url'] = callback_url
        
        try:
            # Timeout aumentado para 120 segundos (2 minutos) para acomodar operações longas do Selenium
            # Usa timeout menor para processamento assíncrono
            timeout = self.timeout_process if async_processing else self.timeout_allocate
            
            logger.info(f"Alocando WO {work_order_id} com timeout de {timeout} segundos")
            
            response = requests.post(
                url,
                json=data,
                headers=self._get_headers(),
                timeout=timeout
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
        callback_url = self._get_callback_url('processing-result')
        if callback_url:
            data['callback_url'] = callback_url
        
        try:
            response = requests.post(
                url,
                json=data,
                headers=self._get_headers(),
                timeout=self.timeout_process
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
                timeout=self.timeout_status
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
                timeout=self.timeout_health
            )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao verificar saúde da VM API: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
