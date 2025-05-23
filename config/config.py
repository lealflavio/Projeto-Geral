#!/usr/bin/env python3
"""
Sistema Centralizado de Configurações

Este módulo fornece um sistema unificado para gerenciar todas as configurações
do projeto, substituindo os múltiplos arquivos de configuração espalhados.

Uso:
    from config.config import Config
    
    # Carregar configuração
    config = Config()
    
    # Acessar valores
    db_url = config.get('database.url')
    api_key = config.get('api.key')
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

class Config:
    """
    Classe para gerenciamento centralizado de configurações.
    
    Carrega configurações de múltiplas fontes em ordem de prioridade:
    1. Variáveis de ambiente
    2. Arquivos .env
    3. Arquivos JSON de configuração
    4. Valores padrão
    """
    
    def __init__(self, config_dir=None):
        """
        Inicializa o sistema de configuração.
        
        Args:
            config_dir (str, opcional): Diretório de configuração personalizado.
                Se não for fornecido, usa o diretório padrão.
        """
        # Configurar logger
        self.logger = logging.getLogger('config')
        self.logger.setLevel(logging.INFO)
        
        # Determinar diretório base do projeto
        self.base_dir = self._get_base_dir()
        
        # Determinar diretório de configuração
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(self.base_dir) / 'config'
        
        # Garantir que o diretório de configuração existe
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Inicializar dicionário de configuração
        self.config_data = {}
        
        # Carregar configurações
        self._load_default_config()
        self._load_json_configs()
        self._load_env_files()
        self._load_environment_vars()
        
        self.logger.info(f"Configuração carregada com sucesso. Base dir: {self.base_dir}")
    
    def _get_base_dir(self):
        """
        Determina o diretório base do projeto.
        
        Returns:
            str: Caminho absoluto para o diretório base do projeto.
        """
        # Tenta obter do ambiente
        if 'PROJECT_BASE_DIR' in os.environ:
            return os.environ['PROJECT_BASE_DIR']
        
        # Caso contrário, infere a partir do caminho atual
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Se estamos em /config, o diretório pai é a base
        if os.path.basename(current_dir) == 'config':
            return os.path.dirname(current_dir)
        
        # Caso contrário, assume que estamos na raiz do projeto
        return current_dir
    
    def _load_default_config(self):
        """Carrega configurações padrão."""
        self.config_data = {
            'app': {
                'name': 'Sistema de Automação',
                'environment': 'development',
                'debug': True
            },
            'paths': {
                'base_dir': self.base_dir,
                'config_dir': str(self.config_dir),
                'tecnicos_dir': os.path.join(self.base_dir, 'tecnicos'),
                'extracao_dados_dir': os.path.join(self.base_dir, 'extracao_dados')
            },
            'database': {
                'url': '',
                'username': '',
                'password': '',
                'database': ''
            },
            'api': {
                'url': '',
                'key': ''
            },
            'google': {
                'service_account_file': os.path.join(self.base_dir, 'chave_servico_primaria.json')
            },
            'notificacao': {
                'enabled': True,
                'service': 'email'
            },
            'tecnicos': {}
        }
    
    def _load_json_configs(self):
        """Carrega configurações de arquivos JSON."""
        # Carregar arquivo principal de configuração
        main_config_file = self.config_dir / 'main_config.json'
        if main_config_file.exists():
            with open(main_config_file, 'r', encoding='utf-8') as f:
                self._merge_config(json.load(f))
        
        # Carregar configurações de técnicos
        tecnicos_config_file = self.config_dir / 'tecnicos.json'
        if tecnicos_config_file.exists():
            with open(tecnicos_config_file, 'r', encoding='utf-8') as f:
                self.config_data['tecnicos'] = json.load(f)
        
        # Carregar outros arquivos JSON de configuração
        for config_file in self.config_dir.glob('*.json'):
            if config_file.name not in ['main_config.json', 'tecnicos.json']:
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        section_name = config_file.stem  # Nome do arquivo sem extensão
                        self.config_data[section_name] = json.load(f)
                except Exception as e:
                    self.logger.error(f"Erro ao carregar {config_file}: {str(e)}")
    
    def _load_env_files(self):
        """Carrega configurações de arquivos .env."""
        # Carregar arquivo .env principal
        env_file = self.config_dir / '.env'
        if env_file.exists():
            load_dotenv(env_file)
        
        # Carregar .env na raiz do projeto
        root_env_file = Path(self.base_dir) / '.env'
        if root_env_file.exists():
            load_dotenv(root_env_file)
    
    def _load_environment_vars(self):
        """
        Carrega configurações de variáveis de ambiente.
        
        As variáveis de ambiente têm prioridade sobre arquivos de configuração.
        O formato esperado é APP_SECTION_KEY=value, que será mapeado para config['section']['key'].
        """
        prefix = 'APP_'
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remover prefixo e dividir em seções
                parts = key[len(prefix):].lower().split('_')
                
                if len(parts) >= 2:
                    section = parts[0]
                    subkey = '_'.join(parts[1:])
                    
                    # Garantir que a seção existe
                    if section not in self.config_data:
                        self.config_data[section] = {}
                    
                    # Definir valor
                    self.config_data[section][subkey] = value
    
    def _merge_config(self, config_data):
        """
        Mescla dados de configuração com os existentes.
        
        Args:
            config_data (dict): Dados de configuração a serem mesclados.
        """
        for section, values in config_data.items():
            if section not in self.config_data:
                self.config_data[section] = {}
            
            if isinstance(values, dict):
                for key, value in values.items():
                    self.config_data[section][key] = value
            else:
                self.config_data[section] = values
    
    def get(self, key_path, default=None):
        """
        Obtém um valor de configuração pelo caminho da chave.
        
        Args:
            key_path (str): Caminho da chave no formato 'section.key'.
            default: Valor padrão a ser retornado se a chave não existir.
        
        Returns:
            Valor da configuração ou o valor padrão se não encontrado.
        """
        parts = key_path.split('.')
        
        if len(parts) == 1:
            return self.config_data.get(parts[0], default)
        
        section = parts[0]
        key = '.'.join(parts[1:])
        
        if section not in self.config_data:
            return default
        
        # Se a chave contém mais pontos, recursivamente busca na subseção
        if '.' in key:
            subsection = key.split('.')[0]
            subkey = '.'.join(key.split('.')[1:])
            
            if isinstance(self.config_data[section], dict) and subsection in self.config_data[section]:
                if isinstance(self.config_data[section][subsection], dict):
                    return self._get_nested(self.config_data[section][subsection], subkey, default)
        
        # Caso simples: section.key
        if isinstance(self.config_data[section], dict):
            return self.config_data[section].get(key, default)
        
        return default
    
    def _get_nested(self, config_section, key_path, default=None):
        """
        Obtém um valor aninhado de configuração.
        
        Args:
            config_section (dict): Seção de configuração.
            key_path (str): Caminho da chave.
            default: Valor padrão a ser retornado se a chave não existir.
        
        Returns:
            Valor da configuração ou o valor padrão se não encontrado.
        """
        parts = key_path.split('.')
        
        if len(parts) == 1:
            return config_section.get(parts[0], default)
        
        key = parts[0]
        remaining = '.'.join(parts[1:])
        
        if key not in config_section or not isinstance(config_section[key], dict):
            return default
        
        return self._get_nested(config_section[key], remaining, default)
    
    def set(self, key_path, value):
        """
        Define um valor de configuração.
        
        Args:
            key_path (str): Caminho da chave no formato 'section.key'.
            value: Valor a ser definido.
        """
        parts = key_path.split('.')
        
        if len(parts) == 1:
            self.config_data[parts[0]] = value
            return
        
        section = parts[0]
        key = '.'.join(parts[1:])
        
        if section not in self.config_data:
            self.config_data[section] = {}
        
        # Se a chave contém mais pontos, recursivamente cria a estrutura
        if '.' in key:
            subsection = key.split('.')[0]
            subkey = '.'.join(key.split('.')[1:])
            
            if subsection not in self.config_data[section]:
                self.config_data[section][subsection] = {}
            
            if not isinstance(self.config_data[section][subsection], dict):
                self.config_data[section][subsection] = {}
            
            self._set_nested(self.config_data[section][subsection], subkey, value)
            return
        
        # Caso simples: section.key
        self.config_data[section][key] = value
    
    def _set_nested(self, config_section, key_path, value):
        """
        Define um valor aninhado de configuração.
        
        Args:
            config_section (dict): Seção de configuração.
            key_path (str): Caminho da chave.
            value: Valor a ser definido.
        """
        parts = key_path.split('.')
        
        if len(parts) == 1:
            config_section[parts[0]] = value
            return
        
        key = parts[0]
        remaining = '.'.join(parts[1:])
        
        if key not in config_section:
            config_section[key] = {}
        
        if not isinstance(config_section[key], dict):
            config_section[key] = {}
        
        self._set_nested(config_section[key], remaining, value)
    
    def save(self, config_file=None):
        """
        Salva a configuração atual em um arquivo JSON.
        
        Args:
            config_file (str, opcional): Caminho para o arquivo de configuração.
                Se não for fornecido, usa o arquivo padrão.
        """
        if config_file is None:
            config_file = self.config_dir / 'main_config.json'
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f, indent=4, ensure_ascii=False)
        
        self.logger.info(f"Configuração salva em {config_file}")
    
    def save_section(self, section, config_file=None):
        """
        Salva uma seção específica da configuração em um arquivo JSON.
        
        Args:
            section (str): Nome da seção a ser salva.
            config_file (str, opcional): Caminho para o arquivo de configuração.
                Se não for fornecido, usa o nome da seção como nome do arquivo.
        """
        if section not in self.config_data:
            self.logger.error(f"Seção {section} não encontrada na configuração")
            return
        
        if config_file is None:
            config_file = self.config_dir / f"{section}.json"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config_data[section], f, indent=4, ensure_ascii=False)
        
        self.logger.info(f"Seção {section} salva em {config_file}")

# Instância global para uso em todo o projeto
config = Config()

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Exemplo de uso
    print("Configuração carregada:")
    print(f"Nome da aplicação: {config.get('app.name')}")
    print(f"Diretório base: {config.get('paths.base_dir')}")
    
    # Exemplo de definição de valor
    config.set('app.version', '1.0.0')
    print(f"Versão da aplicação: {config.get('app.version')}")
    
    # Salvar configuração
    config.save()
    print("Configuração salva com sucesso.")
