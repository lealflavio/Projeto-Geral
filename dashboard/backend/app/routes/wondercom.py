"""
Endpoints para integração com o Wondercom.
Este módulo implementa as rotas para alocação de WO e outras funcionalidades.
"""

from flask import Blueprint, request, jsonify
import logging
import re
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, User, WorkOrder
from ..services.vm_api import VMApiClient
from ..services.notification_service import NotificationService

# Configurar logging
logger = logging.getLogger(__name__)

# Criar blueprint
wondercom_bp = Blueprint('wondercom', __name__)

@wondercom_bp.route('/api/wondercom/allocate', methods=['POST'])
@jwt_required()
def allocate_work_order():
    """
    Endpoint para alocação de ordem de trabalho.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"status": "error", "message": "Usuário não encontrado"}), 404
    
    # Verificar se o usuário tem integração configurada
    if not user.usuario_portal or not user.senha_portal:
        return jsonify({"status": "error", "message": "Integração com portal não configurada"}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    work_order_id = data.get('work_order_id')
    
    if not work_order_id:
        return jsonify({"status": "error", "message": "ID da ordem de trabalho ausente"}), 400
    
    # Validar formato do work_order_id (8 dígitos numéricos)
    if not re.match(r'^\d{8}$', work_order_id):
        return jsonify({"status": "error", "message": "ID da ordem de trabalho deve ter 8 dígitos numéricos"}), 400
    
    # Preparar credenciais
    credentials = {
        "username": user.usuario_portal,
        "password": user.senha_portal
    }
    
    try:
        # Chamar a VM API
        vm_api_client = VMApiClient()
        result = vm_api_client.allocate_work_order(work_order_id, credentials)
        
        # Se processamento síncrono, enviar notificação
        if result.get('status') == 'success' and user.whatsapp:
            notification_service = NotificationService()
            
            # Preparar mensagem com dados da WO
            wo_data = result.get('data', {})
            message = f"Detalhes da WO {work_order_id}:\n"
            message += f"Endereço: {wo_data.get('endereco', 'N/A')}\n"
            message += f"PDO: {wo_data.get('pdo', 'N/A')}\n"
            message += f"Cor da Fibra: {wo_data.get('cor_fibra', 'N/A')}\n"
            message += f"Coordenadas: {wo_data.get('latitude', 'N/A')}, {wo_data.get('longitude', 'N/A')}"
            
            # Enviar notificação
            notification_service.send_whatsapp_notification(user.whatsapp, message)
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Erro ao alocar WO {work_order_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@wondercom_bp.route('/api/wondercom/calcular-kms', methods=['POST'])
@jwt_required()
def calcular_kms():
    """
    Endpoint para cálculo de KMs percorridos.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"status": "error", "message": "Usuário não encontrado"}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    data_inicio = data.get('data_inicio')
    data_fim = data.get('data_fim')
    endereco_residencial = data.get('endereco_residencial')
    
    if not data_inicio or not data_fim:
        return jsonify({"status": "error", "message": "Datas de início e fim são obrigatórias"}), 400
    
    try:
        # Buscar WOs do período
        work_orders = WorkOrder.query.filter(
            WorkOrder.tecnico_id == current_user_id,
            WorkOrder.data >= data_inicio,
            WorkOrder.data <= data_fim,
            WorkOrder.status == 'processado'
        ).all()
        
        if not work_orders:
            return jsonify({
                "status": "success",
                "total_km": 0,
                "detalhes": []
            }), 200
        
        # Extrair coordenadas
        coordenadas = []
        
        # Adicionar endereço residencial se fornecido
        if endereco_residencial:
            # Aqui você precisaria implementar a geocodificação do endereço
            # usando Google Maps API ou similar
            # coords_casa = geocode_address(endereco_residencial)
            # if coords_casa:
            #     coordenadas.append(coords_casa)
            pass
        
        # Adicionar coordenadas das WOs
        for wo in work_orders:
            # Extrair coordenadas do resultado da WO
            # resultado = json.loads(wo.resultado)
            # lat = resultado.get('latitude')
            # lng = resultado.get('longitude')
            # if lat and lng:
            #     coordenadas.append({"lat": lat, "lng": lng})
            pass
        
        # Adicionar endereço residencial no final se fornecido
        if endereco_residencial and len(coordenadas) > 0:
            coordenadas.append(coordenadas[0])
        
        # Calcular distâncias
        # Aqui você precisaria implementar o cálculo de distâncias
        # usando Google Maps API ou similar
        # distancias = calculate_distances(coordenadas)
        
        # Para fins de exemplo, vamos simular um resultado
        distancias = [10.5, 15.2, 8.7, 12.3]
        total_km = sum(distancias)
        
        detalhes = [
            {"origem": i, "destino": i+1, "distancia": dist}
            for i, dist in enumerate(distancias)
        ]
        
        return jsonify({
            "status": "success",
            "total_km": total_km,
            "detalhes": detalhes
        }), 200
    except Exception as e:
        logger.error(f"Erro ao calcular KMs: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
