"""
Endpoint para gerenciamento de pastas na VM e no Google Drive.
Este arquivo implementa as rotas para criação, listagem e gerenciamento de pastas.
"""
from flask import Blueprint, request, jsonify
import logging
import os
import json
from pathlib import Path
import shutil
from ..auth import api_key_required
from ..queue.producer import enqueue_task

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar blueprint
folder_manager_bp = Blueprint('folder_manager', __name__)

# Diretório base para pastas de usuários na VM
# Nota: Mantemos VM_BASE_FOLDER como variável específica, mas com fallback para PYTHONPATH
VM_BASE_FOLDER = os.environ.get('VM_BASE_FOLDER', os.environ.get('PYTHONPATH', '/home/flavioleal/Sistema/usuarios'))

@folder_manager_bp.route('/api/folders/create', methods=['POST'])
@api_key_required
def create_folders():
    """
    Endpoint para criar estrutura de pastas para um usuário.
    Cria pastas tanto na VM quanto no Google Drive.
    """
    data = request.get_json()
    
    # Validar dados de entrada
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    user_id = data.get('user_id')
    user_email = data.get('user_email')
    drive_credentials = data.get('drive_credentials', {})
    
    if not user_id:
        return jsonify({"status": "error", "message": "ID do usuário ausente"}), 400
    
    if not user_email:
        return jsonify({"status": "error", "message": "Email do usuário ausente"}), 400
    
    # Opção para processamento síncrono ou assíncrono
    async_processing = data.get('async', True)
    callback_url = data.get('callback_url')
    
    if async_processing:
        # Processamento assíncrono via fila
        logger.info(f"Enfileirando criação de pastas para usuário {user_id} para processamento assíncrono")
        
        result = enqueue_task(
            task_type="create_folders",
            params={
                "user_id": user_id,
                "user_email": user_email,
                "drive_credentials": drive_credentials
            },
            priority="medium",
            callback_url=callback_url
        )
        
        return jsonify({
            "status": "accepted",
            "message": "Criação de pastas enfileirada para processamento",
            "job_id": result["job_id"]
        }), 202
    else:
        # Processamento síncrono direto
        logger.info(f"Iniciando criação síncrona de pastas para usuário {user_id}")
        
        try:
            # Criar pastas na VM
            vm_folders = create_vm_folders(user_id)
            
            # Criar pastas no Google Drive e compartilhar
            drive_folders = create_drive_folders(user_id, user_email, drive_credentials)
            
            return jsonify({
                "status": "success",
                "data": {
                    "vm_folders": vm_folders,
                    "drive_folders": drive_folders
                }
            }), 200
        except Exception as e:
            logger.error(f"Erro ao criar pastas para usuário {user_id}: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }), 500

@folder_manager_bp.route('/api/folders/process', methods=['POST'])
@api_key_required
def process_drive_files():
    """
    Endpoint para processar arquivos do Google Drive.
    Baixa arquivos da pasta 'Novos' e move para pasta 'Processados'.
    """
    data = request.get_json()
    
    # Validar dados de entrada
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    user_id = data.get('user_id')
    drive_folder_id = data.get('drive_folder_id')
    drive_credentials = data.get('drive_credentials', {})
    
    if not user_id:
        return jsonify({"status": "error", "message": "ID do usuário ausente"}), 400
    
    if not drive_folder_id:
        return jsonify({"status": "error", "message": "ID da pasta do Drive ausente"}), 400
    
    # Opção para processamento síncrono ou assíncrono
    async_processing = data.get('async', True)
    callback_url = data.get('callback_url')
    
    if async_processing:
        # Processamento assíncrono via fila
        logger.info(f"Enfileirando processamento de arquivos para usuário {user_id} para processamento assíncrono")
        
        result = enqueue_task(
            task_type="process_drive_files",
            params={
                "user_id": user_id,
                "drive_folder_id": drive_folder_id,
                "drive_credentials": drive_credentials
            },
            priority="medium",
            callback_url=callback_url
        )
        
        return jsonify({
            "status": "accepted",
            "message": "Processamento de arquivos enfileirado",
            "job_id": result["job_id"]
        }), 202
    else:
        # Processamento síncrono direto
        logger.info(f"Iniciando processamento síncrono de arquivos para usuário {user_id}")
        
        try:
            # Processar arquivos do Drive
            result = process_drive_files_sync(user_id, drive_folder_id, drive_credentials)
            
            return jsonify({
                "status": "success",
                "data": result
            }), 200
        except Exception as e:
            logger.error(f"Erro ao processar arquivos para usuário {user_id}: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }), 500

def create_vm_folders(user_id):
    """
    Cria estrutura de pastas para o usuário na VM.
    
    Args:
        user_id (str): ID do usuário
        
    Returns:
        dict: Informações sobre as pastas criadas
    """
    logger.info(f"Criando pastas na VM para usuário {user_id}")
    
    # Definir caminhos das pastas
    user_folder = os.path.join(VM_BASE_FOLDER, user_id)
    novos_folder = os.path.join(user_folder, "Novos")
    processados_folder = os.path.join(user_folder, "Processados")
    erros_folder = os.path.join(user_folder, "Erros")
    
    # Criar pastas se não existirem
    os.makedirs(user_folder, exist_ok=True)
    os.makedirs(novos_folder, exist_ok=True)
    os.makedirs(processados_folder, exist_ok=True)
    os.makedirs(erros_folder, exist_ok=True)
    
    logger.info(f"Pastas criadas com sucesso na VM para usuário {user_id}")
    
    return {
        "user_folder": user_folder,
        "novos_folder": novos_folder,
        "processados_folder": processados_folder,
        "erros_folder": erros_folder
    }

def create_drive_folders(user_id, user_email, drive_credentials):
    """
    Cria estrutura de pastas para o usuário no Google Drive e compartilha.
    
    Args:
        user_id (str): ID do usuário
        user_email (str): Email do usuário para compartilhamento
        drive_credentials (dict): Credenciais do Google Drive
        
    Returns:
        dict: Informações sobre as pastas criadas
    """
    logger.info(f"Criando pastas no Google Drive para usuário {user_id}")
    
    try:
        # Importar DriveService do módulo de serviços
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
        from dashboard.backend.app.services.drive_service import DriveService
        
        # Inicializar serviço do Drive
        drive_service = DriveService()
        
        # Criar pasta principal do usuário
        user_folder_name = f"Usuario_{user_id}"
        user_folder_id = drive_service.create_folder(user_folder_name, "root")
        
        if not user_folder_id:
            raise Exception(f"Falha ao criar pasta principal para usuário {user_id}")
        
        # Criar subpastas
        novos_folder_id = drive_service.create_folder("Novos", user_folder_id)
        processados_folder_id = drive_service.create_folder("Processados", user_folder_id)
        erros_folder_id = drive_service.create_folder("Erros", user_folder_id)
        
        # Compartilhar pasta "Novos" com o usuário
        if novos_folder_id:
            shared = drive_service.share_folder(novos_folder_id, user_email, role='writer')
            if not shared:
                logger.warning(f"Falha ao compartilhar pasta 'Novos' com o usuário {user_email}")
        
        logger.info(f"Pastas criadas com sucesso no Google Drive para usuário {user_id}")
        
        return {
            "user_folder_id": user_folder_id,
            "novos_folder_id": novos_folder_id,
            "processados_folder_id": processados_folder_id,
            "erros_folder_id": erros_folder_id
        }
    except Exception as e:
        logger.error(f"Erro ao criar pastas no Google Drive: {str(e)}")
        raise

def process_drive_files_sync(user_id, drive_folder_id, drive_credentials):
    """
    Processa arquivos do Google Drive de forma síncrona.
    
    Args:
        user_id (str): ID do usuário
        drive_folder_id (str): ID da pasta do Drive a ser monitorada
        drive_credentials (dict): Credenciais do Google Drive
        
    Returns:
        dict: Resultado do processamento
    """
    logger.info(f"Processando arquivos do Drive para usuário {user_id}")
    
    try:
        # Importar DriveService do módulo de serviços
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
        from dashboard.backend.app.services.drive_service import DriveService
        
        # Inicializar serviço do Drive
        drive_service = DriveService()
        
        # Definir caminho para download na VM
        vm_download_path = os.path.join(VM_BASE_FOLDER, user_id, "Novos")
        os.makedirs(vm_download_path, exist_ok=True)
        
        # Listar arquivos na pasta "Novos"
        files = drive_service.list_files(drive_folder_id)
        
        # Processar cada arquivo
        results = {
            "processed": [],
            "errors": []
        }
        
        for file in files:
            file_id = file['id']
            file_name = file['name']
            
            # Definir caminho de destino para o download
            destination_path = os.path.join(vm_download_path, file_name)
            
            # Baixar o arquivo
            downloaded_path = drive_service.download_file(file_id, destination_path)
            
            if downloaded_path:
                # Obter IDs das pastas
                folders = drive_service.ensure_folder_structure(drive_folder_id)
                
                # Move o arquivo para a pasta de processados
                if drive_service.move_file(file_id, folders['processados']):
                    results['processed'].append({
                        'file_id': file_id,
                        'file_name': file_name,
                        'local_path': downloaded_path,
                        'status': 'success'
                    })
                else:
                    results['errors'].append({
                        'file_id': file_id,
                        'file_name': file_name,
                        'error': 'Falha ao mover arquivo para pasta de processados'
                    })
            else:
                # Move o arquivo para a pasta de erros
                if drive_service.move_file(file_id, folders['erros']):
                    results['errors'].append({
                        'file_id': file_id,
                        'file_name': file_name,
                        'error': 'Falha ao baixar arquivo'
                    })
        
        logger.info(f"Processamento concluído: {len(results['processed'])} arquivos processados, {len(results['errors'])} erros.")
        return results
        
    except Exception as e:
        logger.error(f"Erro ao processar arquivos do Drive: {str(e)}")
        raise
