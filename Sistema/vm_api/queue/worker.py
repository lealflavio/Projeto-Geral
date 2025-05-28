"""
Worker para processamento de tarefas da fila.
Este arquivo implementa o consumidor de tarefas do sistema de filas Redis.
"""

import json
import time
import redis
import logging
import requests
import traceback
from .. import config
from ..adapters.orquestrador_adapter import OrquestradorAdapter

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

def process_task(task):
    """
    Processa uma tarefa da fila.
    
    Args:
        task (dict): Tarefa a ser processada
        
    Returns:
        dict: Resultado do processamento
    """
    task_type = task.get("type")
    params = task.get("params", {})
    job_id = task.get("job_id")
    
    logger.info(f"Processando tarefa {job_id} do tipo {task_type}")
    
    try:
        if task_type == "allocate_wo":
            # Processar alocação de WO
            work_order_id = params.get("work_order_id")
            credentials = params.get("credentials", {})
            
            result = OrquestradorAdapter.alocar_wo(work_order_id, credentials)
            
        elif task_type == "process_pdf":
            # Processar PDF
            pdf_path = params.get("pdf_path")
            tecnico_id = params.get("tecnico_id")
            credentials = params.get("credentials", {})
            
            result = OrquestradorAdapter.processar_pdf(pdf_path, tecnico_id, credentials)
            
        else:
            logger.error(f"Tipo de tarefa desconhecido: {task_type}")
            result = {
                "status": "error",
                "error": f"Tipo de tarefa desconhecido: {task_type}"
            }
        
        # Adicionar job_id ao resultado
        result["job_id"] = job_id
        
        return result
    except Exception as e:
        logger.error(f"Erro ao processar tarefa {job_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "job_id": job_id
        }

def send_callback(task, result):
    """
    Envia o resultado para a URL de callback.
    
    Args:
        task (dict): Tarefa processada
        result (dict): Resultado do processamento
    """
    callback_url = task.get("callback_url")
    
    if not callback_url:
        logger.warning(f"Nenhuma URL de callback definida para tarefa {task.get('job_id')}")
        return
    
    try:
        response = requests.post(
            callback_url,
            json=result,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Callback enviado com sucesso para {callback_url}")
        else:
            logger.error(f"Erro ao enviar callback: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Erro ao enviar callback: {str(e)}")

def handle_failed_task(task):
    """
    Trata uma tarefa que falhou.
    
    Args:
        task (dict): Tarefa que falhou
    """
    attempts = task.get("attempts", 0) + 1
    task["attempts"] = attempts
    
    if attempts >= task.get("max_attempts", config.MAX_RETRIES):
        # Mover para fila de dead letter
        logger.warning(f"Tarefa {task.get('job_id')} falhou após {attempts} tentativas, movendo para dead letter")
        redis_client.rpush(config.DEAD_LETTER_QUEUE, json.dumps(task))
    else:
        # Recolocar na fila original
        queue_name = config.HIGH_PRIORITY_QUEUE if task.get("priority") == "high" else config.NORMAL_PRIORITY_QUEUE
        logger.info(f"Recolocando tarefa {task.get('job_id')} na fila após falha (tentativa {attempts})")
        redis_client.rpush(queue_name, json.dumps(task))

def worker_loop():
    """
    Loop principal do worker.
    """
    logger.info("Iniciando worker loop")
    
    while True:
        # Verificar primeiro a fila de alta prioridade
        queues = [config.HIGH_PRIORITY_QUEUE, config.NORMAL_PRIORITY_QUEUE]
        
        # Bloquear até que haja uma tarefa disponível
        queue_data = redis_client.blpop(queues, timeout=1)
        
        if not queue_data:
            # Nenhuma tarefa disponível, aguardar um pouco
            time.sleep(0.1)
            continue
        
        queue_name, task_json = queue_data
        queue_name = queue_name.decode('utf-8')
        
        try:
            task = json.loads(task_json)
            logger.info(f"Tarefa obtida da fila {queue_name}: {task.get('job_id')}")
            
            # Processar a tarefa
            result = process_task(task)
            
            # Enviar callback com o resultado
            send_callback(task, result)
            
            # Se houve erro no processamento, tratar a falha
            if result.get("status") == "error":
                handle_failed_task(task)
                
        except Exception as e:
            logger.error(f"Erro ao processar tarefa da fila {queue_name}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Tentar recolocar a tarefa na fila
            try:
                task = json.loads(task_json)
                handle_failed_task(task)
            except:
                # Se não conseguir parsear a tarefa, logar e continuar
                logger.error(f"Não foi possível parsear a tarefa: {task_json}")

if __name__ == "__main__":
    worker_loop()
