"""
Serviço de integração com Google Drive para monitoramento de pastas.
Este módulo implementa as funcionalidades necessárias para:
1. Autenticar com a API do Google Drive
2. Listar arquivos em pastas específicas
3. Criar e compartilhar pastas
4. Delegar download e movimentação para a VM
"""

import os
import json
import logging
import requests
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("drive_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("drive_service")

# URL da API da VM
VM_API_URL = os.environ.get('VM_API_URL', 'http://localhost:5000')
VM_API_KEY = os.environ.get('VM_API_KEY', 'api-key-temporaria')

class DriveService:
    """Classe para gerenciar operações com o Google Drive."""
    
    def __init__(self, credentials_path=None):
        """
        Inicializa o serviço do Google Drive.
        
        Args:
            credentials_path (str): Caminho para o arquivo de credenciais JSON.
                Se None, tentará usar variáveis de ambiente.
        """
        self.service = None
        self.credentials = None
        self.credentials_path = credentials_path
        self.initialize_service()
    
    def initialize_service(self):
        """Inicializa o serviço do Google Drive com as credenciais apropriadas."""
        try:
            # Tenta usar o arquivo de credenciais se fornecido
            if self.credentials_path and os.path.exists(self.credentials_path):
                self.credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
            # Caso contrário, tenta usar variáveis de ambiente
            else:
                # Verifica se as credenciais estão nas variáveis de ambiente
                creds_json = os.environ.get('GOOGLE_DRIVE_CREDENTIALS')
                if creds_json:
                    creds_info = json.loads(creds_json)
                    self.credentials = service_account.Credentials.from_service_account_info(
                        creds_info,
                        scopes=['https://www.googleapis.com/auth/drive']
                    )
                else:
                    logger.error("Credenciais não encontradas. Forneça um arquivo de credenciais ou configure a variável de ambiente GOOGLE_DRIVE_CREDENTIALS.")
                    return
            
            # Cria o serviço do Drive
            self.service = build('drive', 'v3', credentials=self.credentials)
            logger.info("Serviço do Google Drive inicializado com sucesso.")
        
        except Exception as e:
            logger.error(f"Erro ao inicializar o serviço do Google Drive: {str(e)}")
            raise
    
    def list_files(self, folder_id, file_types=None, max_results=100):
        """
        Lista arquivos em uma pasta específica do Google Drive.
        
        Args:
            folder_id (str): ID da pasta no Google Drive.
            file_types (list): Lista de tipos MIME para filtrar (ex: ['application/pdf']).
            max_results (int): Número máximo de resultados a retornar.
            
        Returns:
            list: Lista de dicionários com informações dos arquivos.
        """
        if not self.service:
            logger.error("Serviço do Google Drive não inicializado.")
            return []
        
        try:
            # Constrói a query para listar arquivos na pasta
            query = f"'{folder_id}' in parents and trashed = false"
            
            # Adiciona filtro por tipo de arquivo se especificado
            if file_types:
                mime_filters = " or ".join([f"mimeType='{mime}'" for mime in file_types])
                query += f" and ({mime_filters})"
            
            # Executa a consulta
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="files(id, name, mimeType, createdTime, modifiedTime, size)"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Encontrados {len(files)} arquivos na pasta {folder_id}.")
            return files
            
        except Exception as e:
            logger.error(f"Erro ao listar arquivos da pasta {folder_id}: {str(e)}")
            self.log_drive_error(e, "list_files", folder_id=folder_id)
            return []
    
    def download_file(self, file_id, destination_path):
        """
        Baixa um arquivo do Google Drive.
        NOTA: Esta função é mantida para compatibilidade, mas o download
        deve ser delegado à VM para novos fluxos.
        
        Args:
            file_id (str): ID do arquivo no Google Drive.
            destination_path (str): Caminho local onde o arquivo será salvo.
            
        Returns:
            str: Caminho do arquivo baixado ou None em caso de erro.
        """
        if not self.service:
            logger.error("Serviço do Google Drive não inicializado.")
            return None
        
        try:
            # Cria o diretório de destino se não existir
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            # Obtém o arquivo
            request = self.service.files().get_media(fileId=file_id)
            
            # Baixa o arquivo
            with open(destination_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    logger.debug(f"Download {int(status.progress() * 100)}%.")
            
            logger.info(f"Arquivo {file_id} baixado com sucesso para {destination_path}.")
            return destination_path
            
        except Exception as e:
            logger.error(f"Erro ao baixar arquivo {file_id}: {str(e)}")
            self.log_drive_error(e, "download_file", file_id=file_id)
            return None
    
    def move_file(self, file_id, destination_folder_id):
        """
        Move um arquivo para outra pasta no Google Drive.
        NOTA: Esta função é mantida para compatibilidade, mas a movimentação
        deve ser delegada à VM para novos fluxos.
        
        Args:
            file_id (str): ID do arquivo a ser movido.
            destination_folder_id (str): ID da pasta de destino.
            
        Returns:
            bool: True se o arquivo foi movido com sucesso, False caso contrário.
        """
        if not self.service:
            logger.error("Serviço do Google Drive não inicializado.")
            return False
        
        try:
            # Obtém as pastas atuais do arquivo
            file = self.service.files().get(
                fileId=file_id,
                fields='parents'
            ).execute()
            
            # Remove das pastas atuais e adiciona à pasta de destino
            previous_parents = ",".join(file.get('parents', []))
            file = self.service.files().update(
                fileId=file_id,
                addParents=destination_folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            
            logger.info(f"Arquivo {file_id} movido com sucesso para a pasta {destination_folder_id}.")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao mover arquivo {file_id}: {str(e)}")
            self.log_drive_error(e, "move_file", file_id=file_id, destination_folder_id=destination_folder_id)
            return False
    
    def create_folder(self, folder_name, parent_folder_id):
        """
        Cria uma nova pasta no Google Drive.
        
        Args:
            folder_name (str): Nome da pasta a ser criada.
            parent_folder_id (str): ID da pasta pai.
            
        Returns:
            str: ID da pasta criada ou None em caso de erro.
        """
        if not self.service:
            logger.error("Serviço do Google Drive não inicializado.")
            return None
        
        try:
            # Verifica se a pasta já existe
            query = f"name='{folder_name}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            
            existing_folders = results.get('files', [])
            if existing_folders:
                logger.info(f"Pasta '{folder_name}' já existe com ID {existing_folders[0]['id']}.")
                return existing_folders[0]['id']
            
            # Cria a pasta
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            logger.info(f"Pasta '{folder_name}' criada com ID {folder['id']}.")
            return folder['id']
            
        except Exception as e:
            logger.error(f"Erro ao criar pasta '{folder_name}': {str(e)}")
            self.log_drive_error(e, "create_folder", folder_name=folder_name, parent_folder_id=parent_folder_id)
            return None
    
    def share_folder(self, folder_id, email, role='reader'):
        """
        Compartilha uma pasta com um usuário específico.
        
        Args:
            folder_id (str): ID da pasta a ser compartilhada.
            email (str): Email do usuário com quem compartilhar.
            role (str): Papel do usuário (reader, writer, commenter, owner).
            
        Returns:
            bool: True se a pasta foi compartilhada com sucesso, False caso contrário.
        """
        if not self.service:
            logger.error("Serviço do Google Drive não inicializado.")
            return False
        
        try:
            # Cria a permissão
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            # Compartilha a pasta
            self.service.permissions().create(
                fileId=folder_id,
                body=permission,
                sendNotificationEmail=True,
                fields='id'
            ).execute()
            
            logger.info(f"Pasta {folder_id} compartilhada com sucesso com {email}.")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao compartilhar pasta {folder_id} com {email}: {str(e)}")
            self.log_drive_error(e, "share_folder", folder_id=folder_id, email=email, role=role)
            return False
    
    def ensure_folder_structure(self, base_folder_id):
        """
        Garante que a estrutura de pastas necessária existe.
        Cria pastas 'Processados' e 'Erros' se não existirem.
        
        Args:
            base_folder_id (str): ID da pasta base.
            
        Returns:
            dict: Dicionário com IDs das pastas criadas.
        """
        folders = {
            'base': base_folder_id,
            'processados': None,
            'erros': None
        }
        
        # Cria pasta de processados se não existir
        folders['processados'] = self.create_folder('Processados', base_folder_id)
        
        # Cria pasta de erros se não existir
        folders['erros'] = self.create_folder('Erros', base_folder_id)
        
        return folders
    
    def create_user_folders(self, user_id, user_email):
        """
        Cria estrutura de pastas para um usuário e delega à VM.
        
        Args:
            user_id (str): ID do usuário.
            user_email (str): Email do usuário para compartilhamento.
            
        Returns:
            dict: Informações sobre as pastas criadas.
        """
        logger.info(f"Criando pastas para usuário {user_id} com email {user_email}")
        
        try:
            # Criar pasta principal do usuário
            user_folder_name = f"Usuario_{user_id}"
            user_folder_id = self.create_folder(user_folder_name, "root")
            
            if not user_folder_id:
                raise Exception(f"Falha ao criar pasta principal para usuário {user_id}")
            
            # Criar subpastas
            novos_folder_id = self.create_folder("Novos", user_folder_id)
            processados_folder_id = self.create_folder("Processados", user_folder_id)
            erros_folder_id = self.create_folder("Erros", user_folder_id)
            
            # Compartilhar pasta "Novos" com o usuário
            if novos_folder_id:
                shared = self.share_folder(novos_folder_id, user_email, role='writer')
                if not shared:
                    logger.warning(f"Falha ao compartilhar pasta 'Novos' com o usuário {user_email}")
            
            # Delegar criação de pastas na VM
            self.delegate_folder_creation_to_vm(user_id, user_email, {
                "user_folder_id": user_folder_id,
                "novos_folder_id": novos_folder_id,
                "processados_folder_id": processados_folder_id,
                "erros_folder_id": erros_folder_id
            })
            
            logger.info(f"Pastas criadas com sucesso para usuário {user_id}")
            
            return {
                "user_folder_id": user_folder_id,
                "novos_folder_id": novos_folder_id,
                "processados_folder_id": processados_folder_id,
                "erros_folder_id": erros_folder_id
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar pastas para usuário {user_id}: {str(e)}")
            self.log_drive_error(e, "create_user_folders", user_id=user_id, user_email=user_email)
            raise
    
    def delegate_folder_creation_to_vm(self, user_id, user_email, drive_folders):
        """
        Delega a criação de pastas na VM.
        
        Args:
            user_id (str): ID do usuário.
            user_email (str): Email do usuário.
            drive_folders (dict): Informações sobre as pastas criadas no Drive.
            
        Returns:
            bool: True se a delegação foi bem-sucedida, False caso contrário.
        """
        logger.info(f"Delegando criação de pastas na VM para usuário {user_id}")
        
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
                'drive_folders': drive_folders,
                'async': True,
                'callback_url': f"{os.environ.get('BACKEND_URL', 'http://localhost:5000')}/api/callbacks/folders"
            }
            
            # Enviar requisição para a VM
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Delegação de criação de pastas na VM concluída: {result}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao delegar criação de pastas na VM: {str(e)}")
            self.log_drive_error(e, "delegate_folder_creation_to_vm", user_id=user_id)
            return False
    
    def delegate_file_processing_to_vm(self, user_id, drive_folder_id):
        """
        Delega o processamento de arquivos à VM.
        
        Args:
            user_id (str): ID do usuário.
            drive_folder_id (str): ID da pasta do Drive a ser monitorada.
            
        Returns:
            dict: Resultado da delegação.
        """
        logger.info(f"Delegando processamento de arquivos à VM para usuário {user_id}")
        
        try:
            # Preparar dados para a requisição
            url = f"{VM_API_URL}/api/folders/process"
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': VM_API_KEY
            }
            payload = {
                'user_id': user_id,
                'drive_folder_id': drive_folder_id,
                'async': True,
                'callback_url': f"{os.environ.get('BACKEND_URL', 'http://localhost:5000')}/api/callbacks/process"
            }
            
            # Enviar requisição para a VM
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Delegação de processamento de arquivos concluída: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao delegar processamento de arquivos à VM: {str(e)}")
            self.log_drive_error(e, "delegate_file_processing_to_vm", user_id=user_id, drive_folder_id=drive_folder_id)
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def process_notification(self, notification_data, base_folder_id, user_id):
        """
        Processa uma notificação de alteração no Google Drive.
        Delega o processamento à VM.
        
        Args:
            notification_data (dict): Dados da notificação.
            base_folder_id (str): ID da pasta base a ser monitorada.
            user_id (str): ID do usuário.
            
        Returns:
            dict: Resultado do processamento.
        """
        logger.info(f"Processando notificação do Drive para usuário {user_id}")
        
        try:
            # Delegar processamento à VM
            result = self.delegate_file_processing_to_vm(user_id, base_folder_id)
            
            if result.get("status") == "accepted":
                return {
                    "status": "accepted",
                    "message": "Processamento delegado à VM",
                    "job_id": result.get("job_id")
                }
            else:
                return {
                    "status": "error",
                    "error": "Falha ao delegar processamento à VM",
                    "details": result
                }
            
        except Exception as e:
            logger.error(f"Erro ao processar notificação: {str(e)}")
            self.log_drive_error(e, "process_notification", base_folder_id=base_folder_id, user_id=user_id)
            return {'status': 'error', 'error': str(e)}
    
    def log_drive_error(self, exception, operation, **context):
        """
        Registra erros de operações do Google Drive.
        
        Args:
            exception (Exception): Exceção capturada.
            operation (str): Nome da operação que falhou.
            **context: Contexto adicional para o log.
        """
        error_log = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'error': str(exception),
            'context': context
        }
        
        logger.error(f"Drive error: {json.dumps(error_log)}")
