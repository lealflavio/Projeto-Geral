"""
Módulo de autenticação para a API REST da VM.
Este arquivo implementa os mecanismos de autenticação e autorização.
"""

from functools import wraps
from flask import request, jsonify
import jwt
import datetime
from . import config

def generate_token(user_id):
    """Gera um token JWT para o usuário."""
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(
        payload,
        config.JWT_SECRET_KEY,
        algorithm='HS256'
    )

def token_required(f):
    """Decorator para verificar token JWT."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Verificar se o token está no header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Token inválido'}), 401
        
        if not token:
            return jsonify({'message': 'Token ausente'}), 401
        
        try:
            # Decodificar o token
            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
            user_id = payload['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido'}), 401
        
        return f(user_id, *args, **kwargs)
    
    return decorated

def api_key_required(f):
    """Decorator para verificar API key."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key or api_key != config.API_KEY:
            return jsonify({'message': 'API key inválida ou ausente'}), 401
        
        return f(*args, **kwargs)
    
    return decorated
