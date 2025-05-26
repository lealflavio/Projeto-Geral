"""
Produtor de tarefas para o sistema de filas.
Este arquivo implementa a funcionalidade de adicionar tarefas à fila Redis.
"""

import json
import uuid
import redis
import logging
import datetime
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

def enqueue_task(task_type, params, priority="normal", callback_url=None):
    """
    Adiciona uma tarefa à fila.
    
    Args:
        task_type (str): Tipo da tarefa ('allocate_wo' ou 'process_pdf')
        params (dict): Parâmetros da tarefa
        priority (str): Prioridade da tarefa ('high' ou 'normal')
        callback_url (str, opcional): URL para callback após conclusão
        
    Returns:
        str: ID da tarefa
    """
    # Gerar ID único para a tarefa
    job_id = str(uuid.uuid4())
    
    # Determinar a fila com base na prioridade
    queue_name = config.HIGH_PRIORITY_QUEUE if priority == "high" else config.NORMAL_PRIORITY_QUEUE
    
    # Criar mensagem da tarefa
    task = {
        "job_id": job_id,
        "type": task_type,
        "params": params,
        "priority": priority,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "attempts": 0,
        "max_attempts": config.MAX_RETRIES,
        "callback_url": callback_url or config.DEFAULT_CALLBACK_URL
    }
    
    # Adicionar à fila
    try:
        redis_client.rpush(queue_name, json.dumps(task))
        logger.info(f"Tarefa {job_id} adicionada à fila {queue_name}")
        return {
            "job_id": job_id,
            "status": "enqueued",
            "queue": queue_name
        }
    except Exception as e:
        logger.error(f"Erro ao adicionar tarefa à fila: {str(e)}")
        raise
