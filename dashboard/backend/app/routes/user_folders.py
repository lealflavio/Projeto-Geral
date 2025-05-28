"""
Rota para integração com a VM para criação de pastas de usuários.
Este arquivo implementa os endpoints para criação de pastas de usuários.
"""

from flask import Blueprint, request, jsonify
import logging
from ..services.vm_integration import VMIntegration
from ..models import User, Task
from flask_jwt_extended import jwt_required, get_jwt_identity

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar blueprint
user_folders_bp = Blueprint('user_folders', __name__)

@user_folders_bp.route('/api/users/folders/create', methods=['POST'])
@jwt_required()
def create_user_folders():
    """
    Endpoint para criar pastas para um usuário.
    Cria pastas tanto na VM quanto no Google Drive.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validar dados de entrada
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    # Obter usuário atual
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"status": "error", "message": "Usuário não encontrado"}), 404
    
    # Verificar se as pastas já foram criadas
    if user.folders_created:
        return jsonify({
            "status": "success", 
            "message": "Pastas já foram criadas anteriormente",
            "folders": {
                "drive_folder_id": user.drive_folder_id,
                "drive_novos_folder_id": user.drive_novos_folder_id
            }
        }), 200
    
    # Criar tarefa para acompanhamento
    task = Task(
        user_id=current_user_id,
        task_type="create_folders",
        status="pending",
        description="Criação de pastas do usuário"
    )
    task.save()
    
    # Solicitar criação de pastas na VM
    result = VMIntegration.create_user_folders(
        user_id=str(user.id),
        user_email=user.email,
        user_name=f"{user.first_name} {user.last_name}",
        async_processing=True
    )
    
    # Atualizar tarefa com o job_id
    if result.get("status") == "accepted":
        task.job_id = result.get("job_id")
        task.status = "processing"
        task.save()
        
        return jsonify({
            "status": "accepted",
            "message": "Solicitação de criação de pastas aceita",
            "task_id": task.id,
            "job_id": task.job_id
        }), 202
    else:
        task.status = "failed"
        task.result = result
        task.save()
        
        return jsonify({
            "status": "error",
            "message": "Falha ao solicitar criação de pastas",
            "details": result
        }), 500

@user_folders_bp.route('/api/users/folders/status', methods=['GET'])
@jwt_required()
def check_user_folders_status():
    """
    Endpoint para verificar o status das pastas de um usuário.
    """
    current_user_id = get_jwt_identity()
    
    # Obter usuário atual
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"status": "error", "message": "Usuário não encontrado"}), 404
    
    # Verificar se as pastas já foram criadas localmente
    if user.folders_created and user.drive_folder_id and user.drive_novos_folder_id:
        return jsonify({
            "status": "success",
            "folders_created": True,
            "folders": {
                "drive_folder_id": user.drive_folder_id,
                "drive_novos_folder_id": user.drive_novos_folder_id,
                "drive_processados_folder_id": user.drive_processados_folder_id,
                "drive_erros_folder_id": user.drive_erros_folder_id,
                "vm_folder_path": user.vm_folder_path,
                "vm_novos_path": user.vm_novos_path,
                "vm_processados_path": user.vm_processados_path,
                "vm_erros_path": user.vm_erros_path
            }
        }), 200
    
    # Verificar status na VM
    result = VMIntegration.check_folder_status(user_id=str(user.id))
    
    if result.get("status") == "success" and result.get("exists", False):
        # Atualizar informações do usuário se as pastas existirem na VM
        user_data = result.get("user_data", {})
        
        user.drive_folder_id = user_data.get("drive_folder_id")
        user.drive_novos_folder_id = user_data.get("novos_folder_id")
        user.vm_folder_path = user_data.get("vm_folder_path")
        user.folders_created = True
        user.save()
        
        return jsonify({
            "status": "success",
            "folders_created": True,
            "folders": {
                "drive_folder_id": user.drive_folder_id,
                "drive_novos_folder_id": user.drive_novos_folder_id,
                "vm_folder_path": user.vm_folder_path
            }
        }), 200
    else:
        # Verificar se há uma tarefa pendente
        task = Task.query.filter_by(
            user_id=current_user_id,
            task_type="create_folders",
            status="processing"
        ).order_by(Task.created_at.desc()).first()
        
        if task:
            return jsonify({
                "status": "processing",
                "message": "Criação de pastas em andamento",
                "task_id": task.id,
                "job_id": task.job_id
            }), 200
        else:
            return jsonify({
                "status": "not_found",
                "message": "Pastas não criadas",
                "folders_created": False
            }), 200
