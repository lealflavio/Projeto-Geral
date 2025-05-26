"""
Endpoint para processamento de PDF.
Este arquivo implementa a rota para processamento de PDFs.
"""

from flask import Blueprint, request, jsonify
import logging
import os
from ..adapters.orquestrador_adapter import OrquestradorAdapter
from ..queue.producer import enqueue_task
from ..auth import token_required, api_key_required

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar blueprint
process_bp = Blueprint('process', __name__)

@process_bp.route('/api/process', methods=['POST'])
@api_key_required
def process_pdf():
    """
    Endpoint para processamento de PDF.
    Sempre executa de forma assíncrona.
    """
    data = request.get_json()
    
    # Validar dados de entrada
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    pdf_path = data.get('pdf_path')
    tecnico_id = data.get('tecnico_id')
    credentials = data.get('credentials', {})
    callback_url = data.get('callback_url')
    
    if not pdf_path:
        return jsonify({"status": "error", "message": "Caminho do PDF ausente"}), 400
    
    if not tecnico_id:
        return jsonify({"status": "error", "message": "ID do técnico ausente"}), 400
    
    # Verificar se o arquivo existe
    if not os.path.exists(pdf_path):
        return jsonify({"status": "error", "message": f"Arquivo não encontrado: {pdf_path}"}), 404
    
    # Enfileirar para processamento assíncrono
    logger.info(f"Enfileirando processamento do PDF {pdf_path} para o técnico {tecnico_id}")
    
    result = enqueue_task(
        task_type="process_pdf",
        params={
            "pdf_path": pdf_path,
            "tecnico_id": tecnico_id,
            "credentials": credentials
        },
        priority="normal",
        callback_url=callback_url
    )
    
    return jsonify({
        "status": "accepted",
        "message": "Processamento de PDF enfileirado",
        "job_id": result["job_id"]
    }), 202
