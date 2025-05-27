"""
Endpoint para alocação de ordem de trabalho.
Este arquivo implementa a rota para alocação de WO.
"""

from flask import Blueprint, request, jsonify
import logging
from ..adapters.orquestrador_adapter import OrquestradorAdapter
from ..queue.producer import enqueue_task
from ..auth import token_required, api_key_required

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar blueprint
allocate_bp = Blueprint('allocate', __name__)

@allocate_bp.route('/api/allocate', methods=['POST'])
@api_key_required
def allocate_work_order():
    """
    Endpoint para alocação de ordem de trabalho.
    Executa com alta prioridade.
    """
    data = request.get_json()
    
    # Validar dados de entrada
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    work_order_id = data.get('work_order_id')
    credentials = data.get('credentials', {})
    
    if not work_order_id:
        return jsonify({"status": "error", "message": "ID da ordem de trabalho ausente"}), 400
    
    if not credentials or not credentials.get('username') or not credentials.get('password'):
        return jsonify({"status": "error", "message": "Credenciais incompletas"}), 400
    
    # Verificar formato do work_order_id (8 dígitos numéricos)
    if not (work_order_id.isdigit() and len(work_order_id) == 8):
        return jsonify({"status": "error", "message": "ID da ordem de trabalho deve ter 8 dígitos numéricos"}), 400
    
    # Opção para processamento síncrono ou assíncrono
    async_processing = data.get('async', False)
    callback_url = data.get('callback_url')
    
    if async_processing:
        # Processamento assíncrono via fila
        logger.info(f"Enfileirando alocação da WO {work_order_id} para processamento assíncrono")
        
        result = enqueue_task(
            task_type="allocate_wo",
            params={
                "work_order_id": work_order_id,
                "credentials": credentials
            },
            priority="high",
            callback_url=callback_url
        )
        
        return jsonify({
            "status": "accepted",
            "message": "Alocação de WO enfileirada para processamento",
            "job_id": result["job_id"]
        }), 202
    else:
        # Processamento síncrono direto
        logger.info(f"Iniciando alocação síncrona da WO {work_order_id}")
        
        result = OrquestradorAdapter.alocar_wo(work_order_id, credentials)
        
        if result["status"] == "success":
            return jsonify(result), 200
        else:
            return jsonify(result), 500
