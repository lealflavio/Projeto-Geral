"""
Ponto de entrada principal para a API VM.
Adaptado para usar o cliente Playwright em vez do Selenium.
"""

import os
import sys
import logging
from flask import Flask, request, jsonify
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path para importações
sys.path.append(str(Path(__file__).parent.parent))

# Importar adapters
from adapters.orquestrador_adapter_playwright import OrquestradorAdapter
from adapters.wondercom_integration_playwright import WondercomIntegration

# Importar configurações
import config

# Criar aplicação Flask
app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint para verificar a saúde da API."""
    return jsonify({
        "status": "ok",
        "message": "API VM está funcionando corretamente"
    })

@app.route('/api/processar_pdf', methods=['POST'])
def processar_pdf():
    """Endpoint para processar um PDF."""
    try:
        # Validar dados da requisição
        data = request.json
        if not data:
            return jsonify({
                "status": "error",
                "error": "Dados da requisição inválidos",
                "error_type": "ValueError"
            }), 400
        
        # Extrair parâmetros
        caminho_pdf = data.get('caminho_pdf')
        tecnico_id = data.get('tecnico_id')
        credenciais = data.get('credenciais')
        
        if not caminho_pdf or not tecnico_id:
            return jsonify({
                "status": "error",
                "error": "Parâmetros obrigatórios não fornecidos",
                "error_type": "ValueError"
            }), 400
        
        # Processar PDF
        resultado = OrquestradorAdapter.processar_pdf(caminho_pdf, tecnico_id, credenciais)
        
        # Retornar resultado
        return jsonify(resultado)
    
    except Exception as e:
        logger.error(f"Erro ao processar PDF: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }), 500

@app.route('/api/alocar_wo', methods=['POST'])
def alocar_wo():
    """Endpoint para alocar uma ordem de trabalho."""
    try:
        # Validar dados da requisição
        data = request.json
        if not data:
            return jsonify({
                "status": "error",
                "error": "Dados da requisição inválidos",
                "error_type": "ValueError"
            }), 400
        
        # Extrair parâmetros
        work_order_id = data.get('work_order_id')
        credenciais = data.get('credenciais')
        
        if not work_order_id or not credenciais:
            return jsonify({
                "status": "error",
                "error": "Parâmetros obrigatórios não fornecidos",
                "error_type": "ValueError"
            }), 400
        
        # Alocar WO usando o adapter Playwright
        resultado = WondercomIntegration.alocar_wo(work_order_id, credenciais)
        
        # Retornar resultado
        return jsonify(resultado)
    
    except Exception as e:
        logger.error(f"Erro ao alocar WO: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }), 500

@app.route('/api/extrair_dados_wo', methods=['POST'])
def extrair_dados_wo():
    """
    Endpoint para extrair dados de uma ordem de trabalho sem alocação.
    Novo endpoint que utiliza o cliente Playwright para apenas extrair dados.
    """
    try:
        # Validar dados da requisição
        data = request.json
        if not data:
            return jsonify({
                "status": "error",
                "error": "Dados da requisição inválidos",
                "error_type": "ValueError"
            }), 400
        
        # Extrair parâmetros
        work_order_id = data.get('work_order_id')
        credenciais = data.get('credenciais')
        
        if not work_order_id or not credenciais:
            return jsonify({
                "status": "error",
                "error": "Parâmetros obrigatórios não fornecidos",
                "error_type": "ValueError"
            }), 400
        
        # Extrair dados da WO usando o adapter Playwright
        # Aqui usamos o mesmo método de alocação, mas o cliente Playwright
        # foi modificado para apenas extrair dados sem alocar
        resultado = WondercomIntegration.alocar_wo(work_order_id, credenciais)
        
        # Retornar resultado
        return jsonify(resultado)
    
    except Exception as e:
        logger.error(f"Erro ao extrair dados da WO: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }), 500

if __name__ == '__main__':
    # Obter configurações da API
    host = getattr(config, 'API_HOST', '0.0.0.0')
    port = getattr(config, 'API_PORT', 5000)
    debug = getattr(config, 'API_DEBUG', True)
    
    # Iniciar a aplicação
    logger.info(f"Iniciando API VM em {host}:{port}")
    app.run(host=host, port=port, debug=debug)
