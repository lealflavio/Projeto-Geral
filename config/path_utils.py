#!/usr/bin/env python3
"""
Utilitários para gerenciamento de caminhos relativos

Este módulo fornece funções para trabalhar com caminhos relativos,
facilitando a portabilidade do código entre diferentes ambientes.

Integrado com o sistema centralizado de configurações.
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('path_utils')

# Adicionar diretório raiz ao path para importação
try:
    # Determinar o diretório base do projeto
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)
    sys.path.insert(0, base_dir)
except Exception as e:
    logger.error(f"Erro ao configurar path: {str(e)}")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Importar o sistema de configuração
try:
    from config.config import config
    USING_CONFIG = True
except ImportError:
    logger.warning("Sistema centralizado de configurações não encontrado. Usando valores padrão.")
    USING_CONFIG = False

# Configurações padrão (usadas se o sistema de configuração não estiver disponível)
DEFAULT_PATHS = {
    'base_dir': base_dir,
    'config_dir': os.path.join(base_dir, 'config'),
    'tecnicos_dir': os.path.join(base_dir, 'tecnicos'),
    'extracao_dados_dir': os.path.join(base_dir, 'extracao_dados'),
    'logs_dir': os.path.join(base_dir, 'logs'),
    'backup_dir': os.path.join(base_dir, 'backups'),
    'dashboard_dir': os.path.join(base_dir, 'dashboard'),
    'scripts_dir': os.path.join(base_dir, 'scripts')
}

def get_path(path_key, default=None):
    """
    Obtém um caminho do sistema de configuração ou usa o valor padrão.
    
    Args:
        path_key (str): Chave do caminho no formato 'paths.nome_do_caminho'.
        default (str, opcional): Valor padrão a ser usado se o caminho não for encontrado.
    
    Returns:
        str: Caminho absoluto.
    """
    if USING_CONFIG:
        # Se a chave não inclui 'paths.', adiciona automaticamente
        if not path_key.startswith('paths.'):
            path_key = f'paths.{path_key}'
        
        path = config.get(path_key)
        if path:
            return path
    
    # Fallback para valores padrão
    if default:
        return default
    
    # Extrair nome do caminho da chave
    if path_key.startswith('paths.'):
        path_name = path_key[6:]  # Remove 'paths.'
    else:
        path_name = path_key
    
    # Verificar se existe no dicionário de caminhos padrão
    if path_name in DEFAULT_PATHS:
        return DEFAULT_PATHS[path_name]
    
    # Se não encontrou, retorna o diretório base
    logger.warning(f"Caminho '{path_key}' não encontrado. Usando diretório base.")
    return DEFAULT_PATHS['base_dir']

def join_path(path_key, *args, create=False):
    """
    Une um caminho base com componentes adicionais.
    
    Args:
        path_key (str): Chave do caminho base no formato 'paths.nome_do_caminho'.
        *args: Componentes adicionais do caminho.
        create (bool, opcional): Se True, cria o diretório se não existir.
    
    Returns:
        str: Caminho absoluto completo.
    """
    base_path = get_path(path_key)
    full_path = os.path.join(base_path, *args)
    
    if create and not os.path.exists(full_path):
        try:
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"Diretório criado: {full_path}")
        except Exception as e:
            logger.error(f"Erro ao criar diretório {full_path}: {str(e)}")
    
    return full_path

def relative_to_absolute(relative_path):
    """
    Converte um caminho relativo para absoluto, baseado no diretório base do projeto.
    
    Args:
        relative_path (str): Caminho relativo ao diretório base do projeto.
    
    Returns:
        str: Caminho absoluto.
    """
    base_dir = get_path('base_dir')
    return os.path.join(base_dir, relative_path)

def absolute_to_relative(absolute_path):
    """
    Converte um caminho absoluto para relativo ao diretório base do projeto.
    
    Args:
        absolute_path (str): Caminho absoluto.
    
    Returns:
        str: Caminho relativo ao diretório base do projeto.
    """
    base_dir = get_path('base_dir')
    try:
        return os.path.relpath(absolute_path, base_dir)
    except ValueError:
        # Se os caminhos estão em unidades diferentes (Windows)
        return absolute_path

def ensure_dir_exists(path, is_file=False):
    """
    Garante que um diretório existe, criando-o se necessário.
    
    Args:
        path (str): Caminho do diretório ou arquivo.
        is_file (bool, opcional): Se True, path é um caminho de arquivo,
                                 e o diretório pai será verificado.
    
    Returns:
        bool: True se o diretório existe ou foi criado com sucesso.
    """
    try:
        dir_path = os.path.dirname(path) if is_file else path
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Diretório criado: {dir_path}")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar diretório {dir_path}: {str(e)}")
        return False

def update_config_paths():
    """
    Atualiza o sistema de configuração com caminhos padrão.
    
    Esta função é útil para garantir que todos os caminhos necessários
    estejam definidos no sistema de configuração.
    
    Returns:
        bool: True se a atualização foi bem-sucedida.
    """
    if not USING_CONFIG:
        logger.warning("Sistema centralizado de configurações não disponível.")
        return False
    
    try:
        # Verificar se a seção 'paths' existe
        paths = config.get('paths', {})
        
        # Adicionar caminhos padrão que não existem na configuração
        for key, value in DEFAULT_PATHS.items():
            if key not in paths:
                config.set(f'paths.{key}', value)
                logger.info(f"Adicionado caminho padrão: paths.{key} = {value}")
        
        # Salvar configuração
        config.save()
        logger.info("Configuração de caminhos atualizada com sucesso.")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao atualizar configuração de caminhos: {str(e)}")
        return False

# Exemplo de uso
if __name__ == "__main__":
    # Atualizar configuração com caminhos padrão
    update_config_paths()
    
    # Exemplos de uso
    print(f"Diretório base: {get_path('base_dir')}")
    print(f"Diretório de técnicos: {get_path('tecnicos_dir')}")
    print(f"Caminho para arquivo de configuração: {join_path('config_dir', 'tecnicos.json')}")
    
    # Criar diretório se não existir
    logs_dir = join_path('logs_dir', 'daily', create=True)
    print(f"Diretório de logs criado: {logs_dir}")
