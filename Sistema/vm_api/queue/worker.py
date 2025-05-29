"""
Módulo de worker para processamento de tarefas em fila.
Este arquivo implementa o worker que processa tarefas da fila.
"""
import logging
import os
import sys
import json
import importlib.util
import requests
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Caminho para o script M1_Criar_Tecnico.py
SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../M1_Criar_Tecnico.py'))

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

    try:
        # Importar o módulo M1_Criar_Tecnico.py
        criar_tecnico_module = import_criar_tecnico_module()
        if not criar_tecnico_module:
            result = {
                "status": "error",
                "message": "Erro ao importar o módulo de criação de pastas"
            }
            send_callback(callback_url, user_id, task_data.get('job_id'), "error", result)
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
                    result = {
                        "status": "success",
                        "message": "Pastas criadas com sucesso",
                        "result": {
                            "drive_folders": {
                                "user_folder_id": user_data.get("pasta_drive_id"),
                                "novos_folder_id": user_data.get("pasta_novos_id")
                            },
                            "vm_folders": {
                                "user_folder": user_data.get("pasta_vm"),
                                "novos_folder": os.path.join(user_data.get("pasta_vm", ""), "pdfs", "novos"),
                                "processados_folder": os.path.join(user_data.get("pasta_vm", ""), "pdfs", "processados"),
                                "erros_folder": os.path.join(user_data.get("pasta_vm", ""), "pdfs", "erro")
                            }
                        }
                    }
                    send_callback(callback_url, user_id, task_data.get('job_id'), "success", result)
                    return result

            # Fallback se não conseguir obter os IDs específicos
            result = {
                "status": "success",
                "message": "Pastas criadas com sucesso, mas não foi possível obter os IDs"
            }
            send_callback(callback_url, user_id, task_data.get('job_id'), "success", result)
            return result
        else:
            result = {
                "status": "error",
                "message": "Falha ao criar pastas"
            }
            send_callback(callback_url, user_id, task_data.get('job_id'), "error", result)
            return result

    except Exception as e:
        logger.error(f"Erro ao criar pastas para usuário {user_id}: {str(e)}")
        result = {
            "status": "error",
            "message": f"Erro ao criar pastas: {str(e)}"
        }
        send_callback(callback_url, user_id, task_data.get('job_id'), "error", result)
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

    try:
        # Aqui você implementaria a lógica para processar os arquivos
        # Por exemplo, chamar um script existente que faz o download e processamento

        # Simulação de processamento bem-sucedido
        result = {
            "status": "success",
            "message": "Arquivos processados com sucesso",
            "files_processed": 0
        }

        send_callback(callback_url, user_id, task_data.get('job_id'), "success", result)
        return result

    except Exception as e:
        logger.error(f"Erro ao processar arquivos para usuário {user_id}: {str(e)}")
        result = {
            "status": "error",
            "message": f"Erro ao processar arquivos: {str(e)}"
        }
        send_callback(callback_url, user_id, task_data.get('job_id'), "error", result)
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

    if task_type == 'create_folders':
        return process_create_folders_task(task_data)
    elif task_type == 'process_files':
        return process_files_task(task_data)
    else:
        logger.error(f"Tipo de tarefa desconhecido: {task_type}")
        return {
            "status": "error",
            "message": f"Tipo de tarefa desconhecido: {task_type}"
        }