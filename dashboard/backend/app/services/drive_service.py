"""
Serviço de integração com Google Drive para monitoramento de pastas.
Este módulo implementa as funcionalidades necessárias para:
1. Autenticar com a API do Google Drive
2. Listar arquivos em pastas específicas
3. Baixar arquivos
4. Mover arquivos entre pastas
5. Processar notificações de alterações
"""

import os
import json
import logging
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
    
    def ensure_folder_structure(self, base_folder_id):
        """
        Garante que a estrutura de pastas necessária existe.
        Cria pastas 'concluidos' e 'erros' se não existirem.
        
        Args:
            base_folder_id (str): ID da pasta base.
            
        Returns:
            dict: Dicionário com IDs das pastas criadas.
        """
        folders = {
            'base': base_folder_id,
            'concluidos': None,
            'erros': None
        }
        
        # Cria pasta de concluídos se não existir
        folders['concluidos'] = self.create_folder('concluidos', base_folder_id)
        
        # Cria pasta de erros se não existir
        folders['erros'] = self.create_folder('erros', base_folder_id)
        
        return folders
    
    def process_notification(self, notification_data, base_folder_id, download_path):
        """
        Processa uma notificação de alteração no Google Drive.
        
        Args:
            notification_data (dict): Dados da notificação.
            base_folder_id (str): ID da pasta base a ser monitorada.
            download_path (str): Caminho base para download de arquivos.
            
        Returns:
            dict: Resultado do processamento.
        """
        try:
            # Garante que a estrutura de pastas existe
            folders = self.ensure_folder_structure(base_folder_id)
            
            # Lista arquivos novos na pasta base
            files = self.list_files(base_folder_id, file_types=['application/pdf'])
            
            # Processa cada arquivo
            results = {
                'processed': [],
                'errors': []
            }
            
            for file in files:
                file_id = file['id']
                file_name = file['name']
                
                # Define o caminho de destino para o download
                destination_path = os.path.join(download_path, file_name)
                
                # Baixa o arquivo
                downloaded_path = self.download_file(file_id, destination_path)
                
                if downloaded_path:
                    # Move o arquivo para a pasta de concluídos
                    if self.move_file(file_id, folders['concluidos']):
                        results['processed'].append({
                            'file_id': file_id,
                            'file_name': file_name,
                            'local_path': downloaded_path,
                            'status': 'success'
                        })
                    else:
                        results['errors'].append({
                            'file_id': file_id,
                            'file_name': file_name,
                            'error': 'Falha ao mover arquivo para pasta de concluídos'
                        })
                else:
                    # Move o arquivo para a pasta de erros
                    if self.move_file(file_id, folders['erros']):
                        results['errors'].append({
                            'file_id': file_id,
                            'file_name': file_name,
                            'error': 'Falha ao baixar arquivo'
                        })
            
            logger.info(f"Processamento concluído: {len(results['processed'])} arquivos processados, {len(results['errors'])} erros.")
            return results
            
        except Exception as e:
            logger.error(f"Erro ao processar notificação: {str(e)}")
            self.log_drive_error(e, "process_notification", base_folder_id=base_folder_id)
            return {'processed': [], 'errors': [{'error': str(e)}]}
    
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
        
        # Aqui você pode implementar lógica adicional como:
        # - Enviar notificação por email
        # - Registrar em banco de dados
        # - Acionar sistema de alertas
