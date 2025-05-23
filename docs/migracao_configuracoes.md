# Guia de Migração para o Sistema Centralizado de Configurações

## Introdução

Este documento descreve o processo de migração dos múltiplos arquivos de configuração espalhados pelo projeto para o novo sistema centralizado de configurações. O objetivo é simplificar a manutenção, reduzir erros e facilitar a portabilidade do sistema entre diferentes ambientes.

## Visão Geral do Novo Sistema

O novo sistema centralizado de configurações:

1. Unifica todas as configurações em um único local
2. Suporta múltiplas fontes de configuração com ordem de prioridade:
   - Variáveis de ambiente (maior prioridade)
   - Arquivos .env
   - Arquivos JSON de configuração
   - Valores padrão (menor prioridade)
3. Fornece uma API simples para acessar e modificar configurações
4. Mantém compatibilidade com o sistema existente durante a transição

## Como Usar o Novo Sistema

### Importação e Inicialização

```python
# Importar o sistema de configuração
from config.config import config

# Acessar valores de configuração
db_url = config.get('database.url')
tecnicos_dir = config.get('paths.tecnicos_dir')
```

### Acessando Configurações

O sistema usa um formato de caminho de chave com pontos para acessar valores:

```python
# Formato: 'secao.chave'
app_name = config.get('app.name')
debug_mode = config.get('app.debug')

# Valores aninhados
tecnico_email = config.get('tecnicos.flavio.email')

# Valores com padrão caso não exista
timeout = config.get('api.timeout', 30)  # Retorna 30 se não estiver definido
```

### Definindo Configurações

```python
# Definir um valor
config.set('app.version', '1.0.0')

# Definir valores aninhados
config.set('tecnicos.novo_tecnico.email', 'novo@exemplo.com')
```

### Salvando Configurações

```python
# Salvar toda a configuração
config.save()

# Salvar apenas uma seção
config.save_section('tecnicos')
```

## Processo de Migração

### 1. Preparação

Antes de iniciar a migração, certifique-se de que:

- O diretório `/config` existe na raiz do projeto
- O arquivo `config.py` está presente no diretório `/config`
- As dependências necessárias estão instaladas (`python-dotenv`)

### 2. Migração dos Arquivos de Configuração

#### Arquivos JSON

1. Mova os arquivos JSON de configuração para o diretório `/config`
2. Renomeie-os de acordo com a seção que representam (ex: `tecnicos.json`)

#### Arquivos .env

1. Consolide os arquivos .env em um único arquivo no diretório `/config`
2. Use o formato `APP_SECAO_CHAVE=valor` para variáveis de ambiente

#### Chaves e Segredos

1. Mova arquivos de chave para o diretório `/config`
2. Atualize as referências nos scripts

### 3. Atualização dos Scripts

Para cada script que utiliza configurações:

1. Importe o sistema centralizado:
   ```python
   from config.config import config
   ```

2. Substitua referências diretas a arquivos de configuração:

   **Antes:**
   ```python
   CONFIG_TECNICOS_JSON_PATH = "/home/flavioleal_souza/Sistema/config/tecnicos.json"
   with open(CONFIG_TECNICOS_JSON_PATH, "r", encoding="utf-8") as f:
       tecnicos_config = json.load(f)
   ```

   **Depois:**
   ```python
   tecnicos_config = config.get('tecnicos')
   ```

3. Substitua caminhos absolutos por valores do sistema de configuração:

   **Antes:**
   ```python
   TECNICOS_DIR = "/home/flavioleal_souza/Sistema/tecnicos"
   ```

   **Depois:**
   ```python
   TECNICOS_DIR = config.get('paths.tecnicos_dir')
   ```

### 4. Testes

Após a migração de cada script:

1. Execute testes para garantir que o comportamento permanece o mesmo
2. Verifique se todas as configurações estão sendo carregadas corretamente
3. Valide o funcionamento em diferentes ambientes

## Exemplo de Migração: M2_Orquestrador_PDFs.py

### Antes

```python
# --- Configurações ---
TECNICOS_DIR = "/home/flavioleal_souza/Sistema/tecnicos"
CONFIG_TECNICOS_JSON_PATH = "/home/flavioleal_souza/Sistema/config/tecnicos.json"

# Carregar configuração de técnicos
if not os.path.exists(CONFIG_TECNICOS_JSON_PATH):
    print(f"Arquivo de configuração não encontrado: {CONFIG_TECNICOS_JSON_PATH}")
    sys.exit(1)

with open(CONFIG_TECNICOS_JSON_PATH, "r", encoding="utf-8") as f:
    tecnicos_config = json.load(f)
```

### Depois

```python
from config.config import config

# --- Configurações ---
TECNICOS_DIR = config.get('paths.tecnicos_dir')

# Carregar configuração de técnicos
tecnicos_config = config.get('tecnicos')
if not tecnicos_config:
    print("Configuração de técnicos não encontrada")
    sys.exit(1)
```

## Benefícios da Migração

1. **Manutenção simplificada**: Todas as configurações em um único local
2. **Redução de erros**: Elimina inconsistências entre diferentes arquivos
3. **Portabilidade**: Facilita a migração entre ambientes
4. **Flexibilidade**: Suporte a múltiplas fontes de configuração
5. **Segurança**: Melhor controle sobre informações sensíveis

## Próximos Passos

Após a migração completa:

1. Remova os arquivos de configuração antigos
2. Atualize a documentação do projeto
3. Treine a equipe no uso do novo sistema

## Suporte

Em caso de dúvidas ou problemas durante a migração, consulte a documentação detalhada no arquivo `config.py` ou entre em contato com a equipe de desenvolvimento.
