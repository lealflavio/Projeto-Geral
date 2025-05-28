"""
Aplicação principal da API REST da VM.
Este arquivo implementa o servidor Flask e registra todas as rotas.
"""

from flask import Flask, jsonify
import logging
import os
from . import config
from .routes.allocate import allocate_bp
from .routes.process import process_bp
from .routes.status import status_bp

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Criar diretório de logs se não existir
os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)

# Criar aplicação Flask
app = Flask(__name__)

# Registrar blueprints
app.register_blueprint(allocate_bp)
app.register_blueprint(process_bp)
app.register_blueprint(status_bp)

# Rota raiz
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "name": "Wondercom VM API",
        "version": "1.0.0",
        "status": "running"
    })

# Tratamento de erros
@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Erro interno do servidor: {str(error)}")
    return jsonify({"status": "error", "message": "Erro interno do servidor"}), 500

# Iniciar aplicação
if __name__ == '__main__':
    logger.info(f"Iniciando API na porta {config.API_PORT}")
    app.run(
        host=config.API_HOST,
        port=config.API_PORT,
        debug=config.API_DEBUG
    )
