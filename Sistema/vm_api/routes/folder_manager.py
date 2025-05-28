"""
Endpoint para gerenciamento de pastas na VM e no Google Drive.
Este arquivo implementa as rotas para criação, listagem e gerenciamento de pastas.
"""
from flask import Blueprint, request, jsonify
import logging
import os
import json
import sys
from pathlib import Path
import importlib.util
from ..auth import api_key_required
from ..queue.producer import enqueue_task

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar blueprint
folder_manager_bp = Blueprint('folder_manager', __name__)

# Caminho para o script M1_Criar_Tecnico.py
SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../M1_Criar_Tecnico.py'))

# Importar o módulo M1_Criar_Tecnico.py dinamicamente
def import_criar_tecnico_module():
    try:
        spec = importlib.util.spec_from_file_location("criar_tecnico_module", SCRIPT_PATH)
        criar_tecnico_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(criar_tecnico_module)
        return criar_tecnico_module
    except Exception as e:
        logger.error(f"Erro ao importar o módulo M1_Criar_Tecnico.py: {str(e)}")
        return None

@folder_manager_bp.route('/api/folders/create', methods=['POST'])
@api_key_required
def create_folders():
    """
    Endpoint para criar estrutura de pastas para um usuário.
    Cria pastas tanto na VM quanto no Google Drive usando o script M1_Criar_Tecnico.py.
    """
    data = request.get_json()
    
    # Validar dados de entrada
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    user_id = data.get('user_id')
    user_email = data.get('user_email')
    user_name = data.get('user_name', f"Usuario_{user_id}")
    
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
                "user_name": user_name
            },
            priority="high",
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
            # Importar o módulo M1_Criar_Tecnico.py
            criar_tecnico_module = import_criar_tecnico_module()
            if not criar_tecnico_module:
                return jsonify({
                    "status": "error",
                    "message": "Erro ao importar o módulo de criação de pastas"
                }), 500
            
            # Chamar a função criar_tecnico do módulo
            # Nota: Estamos usando uma senha temporária que será alterada pelo usuário depois
            result = criar_tecnico_module.criar_tecnico(
                nome_completo=user_name,
                email=user_email,
                usuario_portal=user_id,
                senha_portal="temp_password_123"
            )
            
            if result:
                # Obter os IDs das pastas criadas
                tecnicos_json_path = Path("/home/flavioleal/Sistema/tecnicos/tecnicos.json")
                if tecnicos_json_path.exists():
                    with open(tecnicos_json_path, "r", encoding="utf-8") as f_in:
                        tecnicos_data = json.load(f_in)
                        
                    # Encontrar o usuário recém-criado
                    user_data = next((t for t in tecnicos_data if t["email"] == user_email), None)
                    
                    if user_data:
                        return jsonify({
                            "status": "success",
                            "message": "Pastas criadas com sucesso",
                            "result": {
                                "user_folder_id": user_data.get("pasta_drive_id"),
                                "novos_folder_id": user_data.get("pasta_novos_id"),
                                "vm_folder_path": user_data.get("pasta_vm")
                            }
                        }), 200
                
                # Fallback se não conseguir obter os IDs específicos
                return jsonify({
                    "status": "success",
                    "message": "Pastas criadas com sucesso, mas não foi possível obter os IDs"
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": "Falha ao criar pastas"
                }), 500
                
        except Exception as e:
            logger.error(f"Erro ao criar pastas para usuário {user_id}: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Erro ao criar pastas: {str(e)}"
            }), 500

@folder_manager_bp.route('/api/folders/status', methods=['POST'])
@api_key_required
def check_folder_status():
    """
    Endpoint para verificar o status das pastas de um usuário.
    """
    data = request.get_json()
    
    # Validar dados de entrada
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    user_id = data.get('user_id')
    user_email = data.get('user_email')
    
    if not (user_id or user_email):
        return jsonify({"status": "error", "message": "ID do usuário ou email ausente"}), 400
    
    try:
        # Verificar se o usuário existe no arquivo tecnicos.json
        tecnicos_json_path = Path("/home/flavioleal/Sistema/tecnicos/tecnicos.json")
        if tecnicos_json_path.exists():
            with open(tecnicos_json_path, "r", encoding="utf-8") as f_in:
                tecnicos_data = json.load(f_in)
            
            # Encontrar o usuário pelo ID ou email
            if user_id:
                user_data = next((t for t in tecnicos_data if t["usuario_portal"] == user_id), None)
            else:
                user_data = next((t for t in tecnicos_data if t["email"] == user_email), None)
            
            if user_data:
                # Verificar se as pastas existem na VM
                pasta_vm = Path(user_data.get("pasta_vm", ""))
                pastas_existem = pasta_vm.exists() and \
                                (pasta_vm / "pdfs" / "novos").exists() and \
                                (pasta_vm / "pdfs" / "processados").exists() and \
                                (pasta_vm / "pdfs" / "erro").exists()
                
                return jsonify({
                    "status": "success",
                    "exists": True,
                    "folders_exist": pastas_existem,
                    "user_data": {
                        "name": user_data.get("nome"),
                        "email": user_data.get("email"),
                        "drive_folder_id": user_data.get("pasta_drive_id"),
                        "novos_folder_id": user_data.get("pasta_novos_id"),
                        "vm_folder_path": user_data.get("pasta_vm")
                    }
                }), 200
            else:
                return jsonify({
                    "status": "success",
                    "exists": False,
                    "message": "Usuário não encontrado"
                }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Arquivo de técnicos não encontrado"
            }), 404
            
    except Exception as e:
        logger.error(f"Erro ao verificar status das pastas: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Erro ao verificar status das pastas: {str(e)}"
        }), 500

@folder_manager_bp.route('/api/folders/process', methods=['POST'])
@api_key_required
def process_folder_files():
    """
    Endpoint para processar arquivos em uma pasta específica.
    """
    data = request.get_json()
    
    # Validar dados de entrada
    if not data:
        return jsonify({"status": "error", "message": "Dados ausentes"}), 400
    
    user_id = data.get('user_id')
    drive_folder_id = data.get('drive_folder_id')
    
    if not user_id:
        return jsonify({"status": "error", "message": "ID do usuário ausente"}), 400
    
    # Opção para processamento síncrono ou assíncrono
    async_processing = data.get('async', True)
    callback_url = data.get('callback_url')
    
    if async_processing:
        # Processamento assíncrono via fila
        logger.info(f"Enfileirando processamento de arquivos para usuário {user_id} para processamento assíncrono")
        
        result = enqueue_task(
            task_type="process_files",
            params={
                "user_id": user_id,
                "drive_folder_id": drive_folder_id
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
        # Processamento síncrono direto (não implementado neste exemplo)
        return jsonify({
            "status": "error",
            "message": "Processamento síncrono não suportado para esta operação"
        }), 400
