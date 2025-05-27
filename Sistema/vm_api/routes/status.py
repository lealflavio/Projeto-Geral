"""
Endpoint para verificação de status de tarefas.
Este arquivo implementa as rotas para verificação de status de tarefas e saúde da API.
"""

from flask import Blueprint, request, jsonify
import logging
import json
import redis
from .. import config
from ..auth import token_required, api_key_required

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

# Criar blueprint
status_bp = Blueprint('status', __name__)

@status_bp.route('/api/status/<job_id>', methods=['GET'])
@api_key_required
def get_job_status(job_id):
    """
    Endpoint para verificar o status de uma tarefa.
    """
    # Verificar nas filas
    queues = [
        config.HIGH_PRIORITY_QUEUE,
        config.NORMAL_PRIORITY_QUEUE,
        config.DEAD_LETTER_QUEUE
    ]
    
    for queue_name in queues:
        # Obter todas as tarefas da fila
        queue_length = redis_client.llen(queue_name)
        
        if queue_length > 0:
            for i in range(queue_length):
                task_json = redis_client.lindex(queue_name, i)
                
                if task_json:
                    try:
                        task = json.loads(task_json)
                        
                        if task.get('job_id') == job_id:
                            # Tarefa encontrada na fila
                            return jsonify({
                                "status": "pending",
                                "queue": queue_name,
                                "attempts": task.get('attempts', 0),
                                "created_at": task.get('created_at')
                            }), 200
                    except:
                        continue
    
    # Verificar se há um resultado armazenado
    result_key = f"result:{job_id}"
    result_json = redis_client.get(result_key)
    
    if result_json:
        try:
            result = json.loads(result_json)
            return jsonify(result), 200
        except:
            pass
    
    # Tarefa não encontrada
    return jsonify({
        "status": "not_found",
        "message": f"Tarefa com ID {job_id} não encontrada"
    }), 404

@status_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificação de saúde da API.
    """
    try:
        # Verificar conexão com Redis
        redis_client.ping()
        
        # Verificar filas
        high_priority_length = redis_client.llen(config.HIGH_PRIORITY_QUEUE)
        normal_priority_length = redis_client.llen(config.NORMAL_PRIORITY_QUEUE)
        dead_letter_length = redis_client.llen(config.DEAD_LETTER_QUEUE)
        
        return jsonify({
            "status": "healthy",
            "redis": "connected",
            "queues": {
                "high_priority": high_priority_length,
                "normal_priority": normal_priority_length,
                "dead_letter": dead_letter_length
            }
        }), 200
    except Exception as e:
        logger.error(f"Erro na verificação de saúde: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
