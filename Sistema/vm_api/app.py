"""
Aplicação principal da API da VM.
Este arquivo implementa a aplicação Flask principal.
"""
from flask import Flask, jsonify
import logging
from .routes.allocate import allocate_bp
from .routes.process import process_bp
from .routes.status import status_bp
from .routes.folder_manager import folder_manager_bp  # Importando o novo blueprint

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='/home/flavioleal/Sistema/logs/vm_api.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__)

# Registrar blueprints
app.register_blueprint(allocate_bp)
app.register_blueprint(process_bp)
app.register_blueprint(status_bp)
app.register_blueprint(folder_manager_bp)  # Registrando o novo blueprint

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint para verificação de saúde da API."""
    return jsonify({"status": "ok", "message": "API da VM está funcionando"}), 200

@app.errorhandler(404)
def not_found(error):
    """Handler para erros 404."""
    return jsonify({"status": "error", "message": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def server_error(error):
    """Handler para erros 500."""
    logger.error(f"Erro interno do servidor: {str(error)}")
    return jsonify({"status": "error", "message": "Erro interno do servidor"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
