#!/usr/bin/env python3
"""
Configuração de Técnicos

Este script gerencia o cadastro e configuração de técnicos no sistema,
incluindo criptografia de senhas.
Refatorado para usar caminhos relativos através do sistema centralizado de configurações.
"""

import os
import json
import sys
import logging
from cryptography.fernet import Fernet

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('config_tecnicos')

# Adicionar diretório raiz ao path para importação
try:
    # Determinar o diretório base do projeto
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
except Exception as e:
    logger.error(f"Erro ao configurar path: {str(e)}")

# Importar utilitários de caminho
try:
    from config.path_utils import get_path, join_path, ensure_dir_exists
    USING_PATH_UTILS = True
except ImportError:
    logger.warning("Utilitários de caminho não encontrados. Usando caminhos padrão.")
    USING_PATH_UTILS = False
    # Definir caminhos padrão para compatibilidade
    CONFIG_DIR = "/home/flavioleal_souza/Sistema/config"
    CHAVE_PATH = os.path.join(CONFIG_DIR, "chave.key")
    JSON_TECNICOS_PATH = os.path.join(CONFIG_DIR, "tecnicos.json")

# --- Funções de criptografia ---
def gerar_chave():
    """
    Gera uma nova chave de criptografia e a salva em um arquivo.
    
    Returns:
        bool: True se a chave foi gerada com sucesso, False caso contrário.
    """
    try:
        if USING_PATH_UTILS:
            # Usar utilitários de caminho
            config_dir = join_path('config_dir', create=True)
            chave_path = join_path('config_dir', 'chave.key')
        else:
            # Fallback para caminho absoluto
            config_dir = CONFIG_DIR
            chave_path = CHAVE_PATH
            os.makedirs(config_dir, exist_ok=True)
        
        chave = Fernet.generate_key()
        with open(chave_path, "wb") as f:
            f.write(chave)
        logger.info("Chave de criptografia gerada com sucesso.")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao gerar chave de criptografia: {str(e)}")
        return False

def carregar_fernet():
    """
    Carrega a chave de criptografia e retorna um objeto Fernet.
    
    Returns:
        Fernet: Objeto Fernet para criptografia/descriptografia, ou None se a chave não for encontrada.
    """
    try:
        if USING_PATH_UTILS:
            # Usar utilitários de caminho
            chave_path = join_path('config_dir', 'chave.key')
        else:
            # Fallback para caminho absoluto
            chave_path = CHAVE_PATH
        
        if not os.path.exists(chave_path):
            logger.warning("Chave de criptografia não encontrada. Execute gerar_chave() primeiro.")
            return None
        
        with open(chave_path, "rb") as f:
            chave = f.read()
        
        return Fernet(chave)
    
    except Exception as e:
        logger.error(f"Erro ao carregar chave de criptografia: {str(e)}")
        return None

def criptografar_senha(senha, fernet):
    """
    Criptografa uma senha usando o objeto Fernet fornecido.
    
    Args:
        senha (str): Senha a ser criptografada.
        fernet (Fernet): Objeto Fernet para criptografia.
    
    Returns:
        str: Senha criptografada em formato string.
    """
    return fernet.encrypt(senha.encode()).decode()

# --- Cadastro de técnico ---
def cadastrar_tecnico(username, nome_completo, whatsapp, usuario_portal, senha_portal):
    """
    Cadastra um novo técnico no sistema.
    
    Args:
        username (str): Nome de usuário único para o técnico.
        nome_completo (str): Nome completo do técnico.
        whatsapp (str): Número de WhatsApp do técnico.
        usuario_portal (str): Nome de usuário do técnico no portal.
        senha_portal (str): Senha do técnico no portal (será criptografada).
    
    Returns:
        bool: True se o cadastro foi bem-sucedido, False caso contrário.
    """
    try:
        fernet = carregar_fernet()
        if fernet is None:
            return False

        senha_criptografada = criptografar_senha(senha_portal, fernet)

        novo_tecnico = {
            "nome_completo": nome_completo,
            "whatsapp": whatsapp,
            "usuario_portal": usuario_portal,
            "senha_portal_criptografada": senha_criptografada,
            "ativo": True
        }

        if USING_PATH_UTILS:
            # Usar utilitários de caminho
            json_tecnicos_path = join_path('config_dir', 'tecnicos.json')
        else:
            # Fallback para caminho absoluto
            json_tecnicos_path = JSON_TECNICOS_PATH

        if os.path.exists(json_tecnicos_path):
            with open(json_tecnicos_path, "r", encoding="utf-8") as f:
                tecnicos = json.load(f)
        else:
            tecnicos = {}

        tecnicos[username] = novo_tecnico

        with open(json_tecnicos_path, "w", encoding="utf-8") as f:
            json.dump(tecnicos, f, indent=2, ensure_ascii=False)

        logger.info(f"Técnico '{nome_completo}' cadastrado com sucesso!")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao cadastrar técnico '{nome_completo}': {str(e)}")
        return False

# --- Execução direta para testes ---
if __name__ == "__main__":
    import argparse
    
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='Configuração de técnicos')
    parser.add_argument('--gerar-chave', action='store_true', help='Gerar nova chave de criptografia')
    parser.add_argument('--cadastrar', action='store_true', help='Cadastrar novo técnico')
    parser.add_argument('--username', help='Nome de usuário do técnico')
    parser.add_argument('--nome', help='Nome completo do técnico')
    parser.add_argument('--whatsapp', help='Número de WhatsApp do técnico')
    parser.add_argument('--usuario-portal', help='Nome de usuário do técnico no portal')
    parser.add_argument('--senha-portal', help='Senha do técnico no portal')
    
    args = parser.parse_args()
    
    # Gerar chave
    if args.gerar_chave:
        gerar_chave()
    
    # Cadastrar técnico
    if args.cadastrar:
        if not all([args.username, args.nome, args.whatsapp, args.usuario_portal, args.senha_portal]):
            logger.error("Todos os parâmetros são obrigatórios para cadastrar um técnico.")
            parser.print_help()
        else:
            cadastrar_tecnico(
                username=args.username,
                nome_completo=args.nome,
                whatsapp=args.whatsapp,
                usuario_portal=args.usuario_portal,
                senha_portal=args.senha_portal
            )
    
    # Se nenhum argumento for fornecido, usar valores de exemplo
    if not (args.gerar_chave or args.cadastrar):
        # Para uso manual: descomente para gerar a chave inicialmente
        # gerar_chave()

        cadastrar_tecnico(
            username="Teste",
            nome_completo="Flávio Leal",
            whatsapp="+351937059712",
            usuario_portal="flavio.leal",
            senha_portal="SENHA_SEGURA"
        )
