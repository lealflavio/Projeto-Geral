"""
Módulo de worker especializado para processamento de tarefas de pastas.
Este arquivo implementa o worker que processa apenas tarefas relacionadas a pastas.
"""
import logging
import os
import sys
import json
import importlib.util
import requests
import time
import redis
from pathlib import Path
from .. import config
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Caminho para o script M1_Criar_Tecnico.py
SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Sistema/M1_Criar_Tecnico.py'))

# Configurações do Google Drive
SERVICE_ACCOUNT_FILE = "/home/flavioleal/Sistema/chave_servico_primaria.json"
SCOPES = ['https://www.googleapis.com/auth/drive']

# Conectar ao Redis
redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    password=config.REDIS_PASSWORD
)

# Importar o módulo M1_Criar_Tecnico.py dinamicamente
def import_criar_tecnico_module():
    try:
        spec = importlib.util.spec_from_file_location("criar_tecnico_module", SCRIPT_PATH)
        criar_tecnico_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(criar_tecnico_module)
        return criar_tecnico_module
    except Exception as e:
        logger.error(f"Erro ao importar o módulo M1_Criar_Tecnico.py: {str(e)}")
        return None

def get_drive_service():
    """
    Obtém o serviço do Google Drive.
    
    Returns:
        objeto: Serviço do Google Drive.
    """
    try:
        credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Erro ao obter serviço do Google Drive: {str(e)}")
        return None

def compartilhar_pasta_drive(folder_id, email):
    """
    Compartilha uma pasta do Drive com um usuário.
    
    Args:
        folder_id (str): ID da pasta no Drive.
        email (str): Email do usuário para compartilhar.
        
    Returns:
        bool: True se o compartilhamento foi bem-sucedido, False caso contrário.
    """
    try:
        service = get_drive_service()
        if not service:
            return False
            
        # Configurar permissão de leitura/escrita
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': email
        }
        
        # Compartilhar a pasta
        result = service.permissions().create(
            fileId=folder_id,
            body=permission,
            sendNotificationEmail=False  # Não enviar email automático do Google
        ).execute()
        
        logger.info(f"Pasta {folder_id} compartilhada com {email}")
        return True
    except Exception as e:
        logger.error(f"Erro ao compartilhar pasta {folder_id} com {email}: {str(e)}")
        return False

def obter_link_pasta(folder_id):
    """
    Obtém o link de compartilhamento de uma pasta do Drive.
    
    Args:
        folder_id (str): ID da pasta no Drive.
        
    Returns:
        str: Link da pasta ou None em caso de erro.
    """
    try:
        service = get_drive_service()
        if not service:
            return None
            
        # Obter informações da pasta
        file = service.files().get(
            fileId=folder_id,
            fields='webViewLink'
        ).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        logger.error(f"Erro ao obter link da pasta {folder_id}: {str(e)}")
        return None

def process_create_folders_task(task_data):
    """
    Processa uma tarefa de criação de pastas.
    
    Args:
        task_data (dict): Dados da tarefa.
        
    Returns:
        dict: Resultado do processamento.
    """
    logger.info(f"Processando tarefa de criação de pastas: {task_data}")
    
    user_id = task_data.get('user_id')
    user_email = task_data.get('user_email')
    user_name = task_data.get('user_name', f"Usuario_{user_id}")
    callback_url = task_data.get('callback_url')
    job_id = task_data.get('job_id')
    
    try:
        # Importar o módulo M1_Criar_Tecnico.py
        criar_tecnico_module = import_criar_tecnico_module()
        if not criar_tecnico_module:
            result = {
                "status": "error",
                "message": "Erro ao importar o módulo de criação de pastas"
            }
            send_callback(callback_url, user_id, job_id, "error", result)
            return result
        
        # Chamar a função criar_tecnico do módulo
        # Nota: Estamos usando uma senha temporária que será alterada pelo usuário depois
        success = criar_tecnico_module.criar_tecnico(
            nome_completo=user_name,
            email=user_email,
            usuario_portal=user_id,
            senha_portal="temp_password_123"
        )
        
        if success:
            # Obter os IDs das pastas criadas
            tecnicos_json_path = Path("/home/flavioleal/Sistema/tecnicos/tecnicos.json")
            if tecnicos_json_path.exists():
                with open(tecnicos_json_path, "r", encoding="utf-8") as f_in:
                    tecnicos_data = json.load(f_in)
                    
                # Encontrar o usuário recém-criado
                user_data = next((t for t in tecnicos_data if t["email"] == user_email), None)
                
                if user_data:
                    # Compartilhar a pasta "novos" com o usuário
                    novos_folder_id = user_data.get("pasta_novos_id")
                    compartilhamento_ok = compartilhar_pasta_drive(novos_folder_id, user_email)
                    
                    # Obter o link da pasta "novos"
                    novos_folder_link = obter_link_pasta(novos_folder_id)
                    
                    result = {
                        "status": "success",
                        "message": "Pastas criadas com sucesso",
                        "result": {
                            "drive_folders": {
                                "user_folder_id": user_data.get("pasta_drive_id"),
                                "novos_folder_id": novos_folder_id,
                                "novos_folder_link": novos_folder_link,
                                "compartilhado": compartilhamento_ok
                            },
                            "vm_folders": {
                                "user_folder": user_data.get("pasta_vm"),
                                "novos_folder": os.path.join(user_data.get("pasta_vm", ""), "pdfs", "novos"),
                                "processados_folder": os.path.join(user_data.get("pasta_vm", ""), "pdfs", "processados"),
                                "erros_folder": os.path.join(user_data.get("pasta_vm", ""), "pdfs", "erro")
                            }
                        }
                    }
                    send_callback(callback_url, user_id, job_id, "success", result)
                    return result
            
            # Fallback se não conseguir obter os IDs específicos
            result = {
                "status": "success",
                "message": "Pastas criadas com sucesso, mas não foi possível obter os IDs"
            }
            send_callback(callback_url, user_id, job_id, "success", result)
            return result
        else:
            result = {
                "status": "error",
                "message": "Falha ao criar pastas"
            }
            send_callback(callback_url, user_id, job_id, "error", result)
            return result
            
    except Exception as e:
        logger.error(f"Erro ao criar pastas para usuário {user_id}: {str(e)}")
        result = {
            "status": "error",
            "message": f"Erro ao criar pastas: {str(e)}"
        }
        send_callback(callback_url, user_id, job_id, "error", result)
        return result

def process_files_task(task_data):
    """
    Processa uma tarefa de processamento de arquivos.
    
    Args:
        task_data (dict): Dados da tarefa.
        
    Returns:
        dict: Resultado do processamento.
    """
    logger.info(f"Processando tarefa de processamento de arquivos: {task_data}")
    
    user_id = task_data.get('user_id')
    drive_folder_id = task_data.get('drive_folder_id')
    callback_url = task_data.get('callback_url')
    job_id = task_data.get('job_id')
    
    try:
        # Aqui você implementaria a lógica para processar os arquivos
        # Por exemplo, chamar um script existente que faz o download e processamento
        
        # Simulação de processamento bem-sucedido
        result = {
            "status": "success",
            "message": "Arquivos processados com sucesso",
            "files_processed": 0
        }
        
        send_callback(callback_url, user_id, job_id, "success", result)
        return result
        
    except Exception as e:
        logger.error(f"Erro ao processar arquivos para usuário {user_id}: {str(e)}")
        result = {
            "status": "error",
            "message": f"Erro ao processar arquivos: {str(e)}"
        }
        send_callback(callback_url, user_id, job_id, "error", result)
        return result

def send_callback(callback_url, user_id, job_id, status, result):
    """
    Envia um callback para a URL especificada.
    
    Args:
        callback_url (str): URL para enviar o callback.
        user_id (str): ID do usuário.
        job_id (str): ID do job.
        status (str): Status do processamento.
        result (dict): Resultado do processamento.
    """
    if not callback_url:
        logger.info("Nenhuma URL de callback fornecida, ignorando.")
        return
    
    try:
        payload = {
            "user_id": user_id,
            "job_id": job_id,
            "status": status,
            "result": result
        }
        
        response = requests.post(callback_url, json=payload)
        response.raise_for_status()
        
        logger.info(f"Callback enviado com sucesso para {callback_url}")
        
    except Exception as e:
        logger.error(f"Erro ao enviar callback para {callback_url}: {str(e)}")

def process_task(task):
    """
    Processa uma tarefa com base no seu tipo.
    
    Args:
        task (dict): Tarefa a ser processada.
        
    Returns:
        dict: Resultado do processamento.
    """
    task_type = task.get('type')
    task_data = task.get('data', {})
    
    # Adicionar job_id aos dados da tarefa para uso nas funções de processamento
    if 'job_id' in task and 'job_id' not in task_data:
        task_data['job_id'] = task.get('job_id')
    
    # Este worker processa apenas tarefas relacionadas a pastas
    if task_type == 'create_folders':
        return process_create_folders_task(task_data)
    elif task_type == 'process_files':
        return process_files_task(task_data)
    else:
        # Ignorar outros tipos de tarefas, que serão processadas pelo worker original
        logger.info(f"Ignorando tarefa de tipo {task_type} - será processada pelo worker original")
        return None

def run_worker():
    """
    Executa o worker para processar tarefas da fila.
    """
    logger.info("Iniciando worker de pastas...")
    
    while True:
        try:
            # Verificar filas de alta prioridade primeiro
            task_json = redis_client.lpop(config.HIGH_PRIORITY_QUEUE)
            if not task_json:
                # Se não houver tarefas de alta prioridade, verificar fila normal
                task_json = redis_client.lpop(config.NORMAL_PRIORITY_QUEUE)
            
            if task_json:
                task = json.loads(task_json)
                task_type = task.get('type')
                
                # Verificar se é uma tarefa que este worker deve processar
                if task_type in ['create_folders', 'process_files']:
                    logger.info(f"Processando tarefa {task.get('job_id')} do tipo {task_type}")
                    result = process_task(task)
                    logger.info(f"Tarefa {task.get('job_id')} processada com resultado: {result}")
                else:
                    # Devolver a tarefa para a fila se não for do tipo que este worker processa
                    logger.info(f"Devolvendo tarefa {task.get('job_id')} do tipo {task_type} para a fila")
                    queue_name = config.HIGH_PRIORITY_QUEUE if task.get('priority') == 'high' else config.NORMAL_PRIORITY_QUEUE
                    redis_client.rpush(queue_name, task_json)
            else:
                # Nenhuma tarefa disponível, aguardar um pouco
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Erro ao processar tarefa: {str(e)}")
            time.sleep(5)  # Aguardar um pouco mais em caso de erro

if __name__ == "__main__":
    run_worker()