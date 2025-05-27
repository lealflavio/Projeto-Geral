"""
Endpoint de callback para receber resultados da VM.
Este arquivo implementa os endpoints para receber callbacks da VM.
"""
from flask import Blueprint, request, jsonify
import logging
from ..models import User, Task
from ..services.drive_service import DriveService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar blueprint
callbacks_bp = Blueprint('callbacks', __name__)

@callbacks_bp.route('/api/callbacks/folders', methods=['POST'])
def folder_creation_callback():
    """
    Endpoint para receber callback de criação de pastas na VM.
    """
    data = request.get_json()
    
    # Validar dados de entrada
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    user_id = data.get('user_id')
    job_id = data.get('job_id')
    status = data.get('status')
    result = data.get('result', {})
    
    logger.info(f"Callback recebido para criação de pastas: user_id={user_id}, job_id={job_id}, status={status}")
    
    try:
        # Atualizar status da tarefa no banco de dados
        task = Task.query.filter_by(job_id=job_id).first()
        if task:
            task.status = status
            task.result = result
            task.save()
        
        # Atualizar informações do usuário se a criação foi bem-sucedida
        if status == "success" and user_id:
            user = User.query.get(user_id)
            if user:
                # Atualizar IDs das pastas do Drive
                drive_folders = result.get('drive_folders', {})
                if drive_folders:
                    user.drive_folder_id = drive_folders.get('user_folder_id')
                    user.drive_novos_folder_id = drive_folders.get('novos_folder_id')
                    user.drive_processados_folder_id = drive_folders.get('processados_folder_id')
                    user.drive_erros_folder_id = drive_folders.get('erros_folder_id')
                
                # Atualizar caminhos das pastas na VM
                vm_folders = result.get('vm_folders', {})
                if vm_folders:
                    user.vm_folder_path = vm_folders.get('user_folder')
                    user.vm_novos_path = vm_folders.get('novos_folder')
                    user.vm_processados_path = vm_folders.get('processados_folder')
                    user.vm_erros_path = vm_folders.get('erros_folder')
                
                user.folders_created = True
                user.save()
                
                logger.info(f"Informações de pastas atualizadas para o usuário {user_id}")
        
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        logger.error(f"Erro ao processar callback de criação de pastas: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@callbacks_bp.route('/api/callbacks/process', methods=['POST'])
def file_processing_callback():
    """
    Endpoint para receber callback de processamento de arquivos na VM.
    """
    data = request.get_json()
    
    # Validar dados de entrada
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    user_id = data.get('user_id')
    job_id = data.get('job_id')
    status = data.get('status')
    result = data.get('result', {})
    
    logger.info(f"Callback recebido para processamento de arquivos: user_id={user_id}, job_id={job_id}, status={status}")
    
    try:
        # Atualizar status da tarefa no banco de dados
        task = Task.query.filter_by(job_id=job_id).first()
        if task:
            task.status = status
            task.result = result
            task.save()
        
        # Registrar estatísticas de processamento se bem-sucedido
        if status == "success" and user_id:
            # Aqui você pode adicionar lógica para registrar estatísticas
            # ou acionar outros processos baseados no resultado
            pass
        
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        logger.error(f"Erro ao processar callback de processamento de arquivos: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
