#!/usr/bin/env python3
"""
Script de exemplo para demonstrar o uso do sistema centralizado de configurações.

Este script cria um arquivo de configuração principal e mostra como acessar
e modificar configurações usando o novo sistema.
"""

import os
import json
import logging
from pathlib import Path
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('config_setup')

# Adicionar diretório raiz ao path para importação
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar o sistema de configuração
from config.config import Config

def criar_configuracao_inicial():
    """Cria um arquivo de configuração inicial com valores padrão."""
    # Determinar diretório base do projeto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(base_dir, 'config')
    
    # Garantir que o diretório de configuração existe
    os.makedirs(config_dir, exist_ok=True)
    
    # Criar configuração principal
    main_config = {
        'app': {
            'name': 'Sistema de Automação',
            'environment': 'development',
            'debug': True,
            'version': '1.0.0'
        },
        'paths': {
            'base_dir': base_dir,
            'tecnicos_dir': os.path.join(base_dir, 'tecnicos'),
            'extracao_dados_dir': os.path.join(base_dir, 'extracao_dados')
        },
        'database': {
            'url': 'postgresql://user:password@localhost:5432/mydb',
            'pool_size': 5,
            'timeout': 30
        },
        'api': {
            'url': 'https://api.example.com',
            'timeout': 10,
            'retry_attempts': 3
        },
        'notificacao': {
            'enabled': True,
            'service': 'email',
            'recipients': ['admin@example.com']
        }
    }
    
    # Salvar configuração principal
    main_config_file = os.path.join(config_dir, 'main_config.json')
    with open(main_config_file, 'w', encoding='utf-8') as f:
        json.dump(main_config, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Configuração principal criada em {main_config_file}")
    
    # Migrar configuração de técnicos existente, se disponível
    tecnicos_json_path = os.path.join(base_dir, 'config', 'tecnicos.json')
    if os.path.exists(tecnicos_json_path):
        # Se já existe, apenas informar
        logger.info(f"Arquivo de configuração de técnicos já existe em {tecnicos_json_path}")
    else:
        # Verificar se existe no caminho antigo
        old_tecnicos_path = os.path.join(base_dir, 'tecnicos', 'tecnicos.json')
        if os.path.exists(old_tecnicos_path):
            # Copiar do caminho antigo
            with open(old_tecnicos_path, 'r', encoding='utf-8') as f:
                tecnicos_config = json.load(f)
            
            # Salvar no novo local
            with open(tecnicos_json_path, 'w', encoding='utf-8') as f:
                json.dump(tecnicos_config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Configuração de técnicos migrada para {tecnicos_json_path}")
        else:
            # Criar exemplo de configuração de técnicos
            tecnicos_config = {
                "flavio": {
                    "nome": "Flavio Leal",
                    "email": "flavio@example.com",
                    "telefone": "123456789",
                    "ativo": True
                },
                "teste": {
                    "nome": "Usuário Teste",
                    "email": "teste@example.com",
                    "telefone": "987654321",
                    "ativo": True
                }
            }
            
            # Salvar configuração de técnicos
            with open(tecnicos_json_path, 'w', encoding='utf-8') as f:
                json.dump(tecnicos_config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Configuração de exemplo de técnicos criada em {tecnicos_json_path}")
    
    # Criar arquivo .env de exemplo
    env_file = os.path.join(config_dir, '.env')
    if not os.path.exists(env_file):
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# Variáveis de ambiente para o sistema\n")
            f.write("APP_ENVIRONMENT=development\n")
            f.write("APP_DEBUG=true\n")
            f.write("APP_DATABASE_URL=postgresql://user:password@localhost:5432/mydb\n")
            f.write("APP_API_KEY=your_api_key_here\n")
        
        logger.info(f"Arquivo .env de exemplo criado em {env_file}")
    
    return main_config_file, tecnicos_json_path, env_file

def demonstrar_uso_configuracao():
    """Demonstra como usar o sistema de configuração."""
    # Inicializar sistema de configuração
    config = Config()
    
    # Mostrar valores de configuração
    logger.info("=== Valores de Configuração ===")
    logger.info(f"Nome da aplicação: {config.get('app.name')}")
    logger.info(f"Ambiente: {config.get('app.environment')}")
    logger.info(f"Modo debug: {config.get('app.debug')}")
    logger.info(f"Diretório base: {config.get('paths.base_dir')}")
    logger.info(f"Diretório de técnicos: {config.get('paths.tecnicos_dir')}")
    logger.info(f"URL do banco de dados: {config.get('database.url')}")
    logger.info(f"Serviço de notificação: {config.get('notificacao.service')}")
    
    # Mostrar como acessar configuração de técnicos
    tecnicos = config.get('tecnicos', {})
    logger.info("\n=== Técnicos Configurados ===")
    for tecnico_id, tecnico_info in tecnicos.items():
        logger.info(f"ID: {tecnico_id}")
        logger.info(f"  Nome: {tecnico_info.get('nome', 'N/A')}")
        logger.info(f"  Email: {tecnico_info.get('email', 'N/A')}")
        logger.info(f"  Ativo: {tecnico_info.get('ativo', False)}")
    
    # Demonstrar como modificar configurações
    logger.info("\n=== Modificando Configurações ===")
    
    # Modificar um valor existente
    old_debug = config.get('app.debug')
    config.set('app.debug', not old_debug)
    logger.info(f"Modo debug alterado de {old_debug} para {config.get('app.debug')}")
    
    # Adicionar um novo valor
    config.set('app.last_update', '2025-05-23')
    logger.info(f"Adicionado novo valor: app.last_update = {config.get('app.last_update')}")
    
    # Adicionar um novo técnico
    if 'novo_tecnico' not in tecnicos:
        config.set('tecnicos.novo_tecnico', {
            'nome': 'Novo Técnico',
            'email': 'novo@example.com',
            'telefone': '555-123456',
            'ativo': True
        })
        logger.info("Adicionado novo técnico: novo_tecnico")
    
    # Salvar as alterações
    config.save()
    config.save_section('tecnicos')
    logger.info("Alterações salvas com sucesso")

def main():
    """Função principal."""
    logger.info("Iniciando configuração do sistema...")
    
    # Criar configuração inicial
    main_config_file, tecnicos_json_path, env_file = criar_configuracao_inicial()
    
    logger.info("\nArquivos de configuração criados:")
    logger.info(f"1. Configuração principal: {main_config_file}")
    logger.info(f"2. Configuração de técnicos: {tecnicos_json_path}")
    logger.info(f"3. Variáveis de ambiente: {env_file}")
    
    # Demonstrar uso do sistema de configuração
    logger.info("\nDemonstrando uso do sistema de configuração...")
    demonstrar_uso_configuracao()
    
    logger.info("\nConfigurações inicializadas com sucesso!")
    logger.info("Você pode agora usar o sistema centralizado de configurações em seus scripts.")
    logger.info("Para mais informações, consulte a documentação em docs/migracao_configuracoes.md")

if __name__ == "__main__":
    main()
