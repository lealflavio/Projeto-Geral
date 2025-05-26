"""
Endpoints de callback para receber resultados da VM API.
Este módulo implementa as rotas para receber callbacks da VM.
"""

from flask import Blueprint, request, jsonify
import logging
from ..models import db, WorkOrder, User
from ..services.notification_service import NotificationService

# Configurar logging
logger = logging.getLogger(__name__)

# Criar blueprint
callbacks_bp = Blueprint('callbacks', __name__)

@callbacks_bp.route('/api/callbacks/allocation-result', methods=['POST'])
def allocation_result():
    """
    Endpoint para receber resultados de alocação de WO.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    job_id = data.get('job_id')
    status = data.get('status')
    
    logger.info(f"Recebido callback de alocação para job {job_id} com status {status}")
    
    # Processar o resultado
    if status == "success":
        # Extrair dados da WO
        wo_data = data.get('data', {})
        
        # Aqui você pode armazenar os dados no banco de dados
        # e enviar notificações para o usuário
        
        # Exemplo de notificação via Twilio
        # notification_service = NotificationService()
        # notification_service.send_whatsapp_notification(user.whatsapp, message)
        
        return jsonify({"status": "success", "message": "Resultado processado com sucesso"}), 200
    else:
        # Processar erro
        error = data.get('error', 'Erro desconhecido')
        logger.error(f"Erro na alocação da WO: {error}")
        
        return jsonify({"status": "error", "message": "Erro processado"}), 200

@callbacks_bp.route('/api/callbacks/processing-result', methods=['POST'])
def processing_result():
    """
    Endpoint para receber resultados de processamento de PDF.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    job_id = data.get('job_id')
    status = data.get('status')
    
    logger.info(f"Recebido callback de processamento para job {job_id} com status {status}")
    
    # Processar o resultado
    if status == "success":
        # Extrair dados do processamento
        processing_data = data.get('data', {})
        
        # Aqui você pode atualizar o status da WO no banco de dados,
        # decrementar créditos do usuário e enviar notificações
        
        # Exemplo de atualização de WO e créditos
        # work_order = WorkOrder.query.filter_by(job_id=job_id).first()
        # if work_order:
        #     work_order.status = 'processado'
        #     work_order.resultado = json.dumps(processing_data)
        #     
        #     # Decrementar créditos
        #     user = User.query.get(work_order.tecnico_id)
        #     if user:
        #         user.creditos -= 1
        #         db.session.commit()
        
        return jsonify({"status": "success", "message": "Resultado processado com sucesso"}), 200
    else:
        # Processar erro
        error = data.get('error', 'Erro desconhecido')
        logger.error(f"Erro no processamento do PDF: {error}")
        
        # Atualizar status da WO para erro
        # work_order = WorkOrder.query.filter_by(job_id=job_id).first()
        # if work_order:
        #     work_order.status = 'erro'
        #     work_order.erro = error
        #     db.session.commit()
        
        return jsonify({"status": "error", "message": "Erro processado"}), 200
