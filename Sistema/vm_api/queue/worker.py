"""
Módulo de worker para processamento de tarefas em fila.
Este arquivo implementa o worker que processa tarefas da fila, exceto tarefas de pastas.
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

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conectar ao Redis
redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    password=config.REDIS_PASSWORD
)

def process_allocate_wo_task(task_data):
    """
    Processa uma tarefa de alocação de ordem de trabalho.
    
    Args:
        task_data (dict): Dados da tarefa.
        
    Returns:
        dict: Resultado do processamento.
    """
        fix-queue-workers
    logger.info(f"Processando tarefa de alocação de WO: {task_data}")
    
    work_order_id = task_data.get('work_order_id')
        
    logger.info(f"Processando tarefa de criação de pastas: {task_data}")

        master
    user_id = task_data.get('user_id')
    credentials = task_data.get('credentials', {})
    callback_url = task_data.get('callback_url')
        fix-queue-workers
    job_id = task_data.get('job_id')
    
    try:
        # Aqui você implementaria a lógica para alocar a ordem de trabalho
        # Por exemplo, chamar o adaptador de orquestração
        
        # Simulação de alocação bem-sucedida
        result = {
            "status": "success",
            "message": f"Ordem de trabalho {work_order_id} alocada com sucesso"
        }
        
        send_callback(callback_url, user_id, job_id, "success", result)
        return result
        
        

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

        master
    except Exception as e:
        logger.error(f"Erro ao alocar ordem de trabalho {work_order_id}: {str(e)}")
        result = {
            "status": "error",
            "message": f"Erro ao alocar ordem de trabalho: {str(e)}"
        }
        send_callback(callback_url, user_id, job_id, "error", result)
        return result

def process_process_pdf_task(task_data):
    """
    Processa uma tarefa de processamento de PDF.
    
    Args:
        task_data (dict): Dados da tarefa.
        
    Returns:
        dict: Resultado do processamento.
    """
        fix-queue-workers
    logger.info(f"Processando tarefa de processamento de PDF: {task_data}")
    
    pdf_path = task_data.get('pdf_path')
       
    logger.info(f"Processando tarefa de processamento de arquivos: {task_data}")

        master
    user_id = task_data.get('user_id')
    callback_url = task_data.get('callback_url')
        fix-queue-workers
    job_id = task_data.get('job_id')
    
    try:
        # Aqui você implementaria a lógica para processar o PDF
        # Por exemplo, chamar o adaptador de extração
        
       

    try:
        # Aqui você implementaria a lógica para processar os arquivos
        # Por exemplo, chamar um script existente que faz o download e processamento

        master
        # Simulação de processamento bem-sucedido
        result = {
            "status": "success",
            "message": f"PDF {pdf_path} processado com sucesso"
        }
        fix-queue-workers
        
        send_callback(callback_url, user_id, job_id, "success", result)
       

        send_callback(callback_url, user_id, task_data.get('job_id'), "success", result)
        master
        return result

    except Exception as e:
        logger.error(f"Erro ao processar PDF {pdf_path}: {str(e)}")
        result = {
            "status": "error",
            "message": f"Erro ao processar PDF: {str(e)}"
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
        fix-queue-workers
    
    # Adicionar job_id aos dados da tarefa para uso nas funções de processamento
    if 'job_id' in task and 'job_id' not in task_data:
        task_data['job_id'] = task.get('job_id')
    
    # Este worker NÃO processa tarefas de pastas, apenas outros tipos
    if task_type == 'create_folders' or task_type == 'process_files':
        logger.info(f"Ignorando tarefa {task.get('job_id')} do tipo {task_type} - será processada pelo folders_worker")
        return None
    elif task_type == 'allocate_wo':
        return process_allocate_wo_task(task_data)
    elif task_type == 'process_pdf':
        return process_process_pdf_task(task_data)
        

    if task_type == 'create_folders':
        return process_create_folders_task(task_data)
    elif task_type == 'process_files':
        return process_files_task(task_data)
        master
    else:
        logger.error(f"Tipo de tarefa desconhecido: {task_type}")
        return {
            "status": "error",
            "message": f"Tipo de tarefa desconhecido: {task_type}"
        fix-queue-workers
        }

def run_worker():
    """
    Executa o worker para processar tarefas da fila.
    """
    logger.info("Iniciando worker principal...")
    
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
                if task_type not in ['create_folders', 'process_files']:
                    logger.info(f"Processando tarefa {task.get('job_id')} do tipo {task_type}")
                    result = process_task(task)
                    logger.info(f"Tarefa {task.get('job_id')} processada com resultado: {result}")
                else:
                    # Devolver a tarefa para a fila se for do tipo que o folders_worker processa
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
        
        }
         master
