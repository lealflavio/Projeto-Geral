"""
Aplicação Flask para monitoramento de pastas no Google Drive.
Este módulo implementa um webhook que recebe notificações do Google Drive
e processa os arquivos novos ou modificados.
"""

import os
import json
import logging
from flask import Flask, request, jsonify
import sys

# Adiciona o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importa o serviço do Google Drive
from dashboard.backend.app.services.drive_service import DriveService

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("drive_webhook.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("drive_webhook")

# Inicializa a aplicação Flask
app = Flask(__name__)

# Configurações
CREDENTIALS_PATH = os.environ.get('GOOGLE_DRIVE_CREDENTIALS_PATH')
BASE_FOLDER_ID = os.environ.get('GOOGLE_DRIVE_BASE_FOLDER_ID')
DOWNLOAD_PATH = os.environ.get('DOWNLOAD_PATH', '/tmp/drive_files')

# Inicializa o serviço do Google Drive
drive_service = None

def initialize_drive_service():
    """Inicializa o serviço do Google Drive."""
    global drive_service
    try:
        drive_service = DriveService(credentials_path=CREDENTIALS_PATH)
        logger.info("Serviço do Google Drive inicializado com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao inicializar o serviço do Google Drive: {str(e)}")

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Endpoint para receber notificações do Google Drive.
    
    Este webhook é chamado pelo Google Drive quando há alterações nas pastas monitoradas.
    Processa os arquivos novos ou modificados, baixando-os e movendo-os para as pastas apropriadas.
    """
    global drive_service
    
    # Loga os cabeçalhos da notificação
    logger.info("Notificação recebida do Google Drive!")
    headers_info = {k: v for k, v in request.headers.items()}
    logger.info(f"Headers: {json.dumps(headers_info)}")
    
    # Verifica se o serviço do Drive está inicializado
    if drive_service is None:
        initialize_drive_service()
        if drive_service is None:
            logger.error("Não foi possível inicializar o serviço do Google Drive.")
            return jsonify({"status": "error", "message": "Serviço do Drive não inicializado"}), 500
    
    try:
        # Obtém os dados da notificação
        notification_data = request.get_json() if request.is_json else {}
        
        # Verifica se o ID da pasta base está configurado
        if not BASE_FOLDER_ID:
            logger.error("ID da pasta base não configurado.")
            return jsonify({"status": "error", "message": "ID da pasta base não configurado"}), 500
        
        # Processa a notificação
        results = drive_service.process_notification(
            notification_data=notification_data,
            base_folder_id=BASE_FOLDER_ID,
            download_path=DOWNLOAD_PATH
        )
        
        # Loga os resultados
        logger.info(f"Processamento concluído: {len(results['processed'])} arquivos processados, {len(results['errors'])} erros.")
        
        # Aqui você pode adicionar lógica para processar os arquivos baixados
        # Por exemplo, enviar para um sistema de processamento de documentos
        
        return jsonify({
            "status": "success",
            "processed": len(results['processed']),
            "errors": len(results['errors'])
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao processar notificação: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Endpoint para verificar o status do serviço."""
    global drive_service
    
    # Verifica se o serviço do Drive está inicializado
    if drive_service is None:
        initialize_drive_service()
    
    # Verifica se o ID da pasta base está configurado
    base_folder_configured = BASE_FOLDER_ID is not None
    
    return jsonify({
        "status": "online",
        "drive_service_initialized": drive_service is not None,
        "base_folder_configured": base_folder_configured
    }), 200

@app.route('/check', methods=['GET'])
def check_files():
    """
    Endpoint para verificar manualmente os arquivos na pasta monitorada.
    Útil para testes ou para forçar uma verificação sem esperar por notificações.
    """
    global drive_service
    
    # Verifica se o serviço do Drive está inicializado
    if drive_service is None:
        initialize_drive_service()
        if drive_service is None:
            logger.error("Não foi possível inicializar o serviço do Google Drive.")
            return jsonify({"status": "error", "message": "Serviço do Drive não inicializado"}), 500
    
    try:
        # Verifica se o ID da pasta base está configurado
        if not BASE_FOLDER_ID:
            logger.error("ID da pasta base não configurado.")
            return jsonify({"status": "error", "message": "ID da pasta base não configurado"}), 500
        
        # Processa manualmente (simula uma notificação)
        results = drive_service.process_notification(
            notification_data={},
            base_folder_id=BASE_FOLDER_ID,
            download_path=DOWNLOAD_PATH
        )
        
        return jsonify({
            "status": "success",
            "processed": len(results['processed']),
            "errors": len(results['errors']),
            "processed_files": results['processed'],
            "error_files": results['errors']
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar arquivos: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Inicializa o serviço do Drive na inicialização da aplicação
@app.before_first_request
def before_first_request():
    """Inicializa recursos antes da primeira requisição."""
    initialize_drive_service()
    
    # Cria o diretório de download se não existir
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

if __name__ == '__main__':
    # Cria o diretório de download se não existir
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    
    # Inicializa o serviço do Drive
    initialize_drive_service()
    
    # Inicia a aplicação Flask
    app.run(port=5001, host="0.0.0.0")
