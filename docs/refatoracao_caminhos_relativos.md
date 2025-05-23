# Refatoração de Caminhos Absolutos para Relativos

## Visão Geral

Este documento descreve o processo de refatoração dos caminhos absolutos para caminhos relativos no projeto, utilizando o sistema centralizado de configurações implementado anteriormente.

## Objetivo

Substituir todos os caminhos absolutos hardcoded (como `/home/flavioleal_souza/Sistema/...`) por referências ao sistema centralizado de configurações, tornando o código mais portátil e fácil de manter.

## Benefícios

1. **Portabilidade**: O código funcionará em qualquer ambiente sem necessidade de alterações manuais
2. **Manutenção simplificada**: Alterações de caminhos serão feitas em um único local
3. **Redução de erros**: Elimina inconsistências entre diferentes partes do código
4. **Facilidade para novos desenvolvedores**: Configuração mais simples e intuitiva

## Arquivos Afetados

Os seguintes arquivos contêm caminhos absolutos que precisam ser refatorados:

1. Scripts principais:
   - `M1_Extrator_PDF.py`
   - `M2_Orquestrador_PDFs.py`
   - `M3_Leitura_Drive.py`
   - `M4_Manipulacao_Arquivos.py`
   - `M5_Config_Tecnicos.py`

2. Dashboard:
   - `dashboard/backend/app/create_tables.py`
   - `dashboard/backend/app/routes/wondercom.py`
   - `dashboard/backend/app/services/tecnico_setup.py`

3. Scripts de monitoramento:
   - `scripts/monitoramento/backup.py`
   - `scripts/monitoramento/log_monitor.py`
   - `scripts/monitoramento/system_health.py`

## Estratégia de Refatoração

### 1. Configuração Centralizada

Todos os caminhos serão definidos no sistema centralizado de configurações:

```python
# Em config/config.py
DEFAULT_CONFIG = {
    "paths": {
        "base_dir": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tecnicos_dir": os.path.join("{base_dir}", "tecnicos"),
        "extracao_dados_dir": os.path.join("{base_dir}", "extracao_dados"),
        "config_dir": os.path.join("{base_dir}", "config"),
        "logs_dir": os.path.join("{base_dir}", "logs"),
        "backup_dir": os.path.join("{base_dir}", "backups"),
        "dashboard_dir": os.path.join("{base_dir}", "dashboard"),
        "scripts_dir": os.path.join("{base_dir}", "scripts")
    }
}
```

### 2. Substituição nos Scripts

Em cada script, os caminhos absolutos serão substituídos por referências ao sistema de configuração:

**Antes:**
```python
TECNICOS_DIR = "/home/flavioleal_souza/Sistema/tecnicos"
CONFIG_TECNICOS_JSON_PATH = "/home/flavioleal_souza/Sistema/config/tecnicos.json"
```

**Depois:**
```python
from config.config import config

TECNICOS_DIR = config.get('paths.tecnicos_dir')
CONFIG_TECNICOS_JSON_PATH = os.path.join(config.get('paths.config_dir'), "tecnicos.json")
```

### 3. Compatibilidade

Para garantir compatibilidade com código existente, será implementado um mecanismo de fallback:

```python
try:
    from config.config import config
    USING_CONFIG = True
except ImportError:
    print("AVISO: Sistema centralizado de configurações não encontrado. Usando valores padrão.")
    USING_CONFIG = False
    # Definir caminhos padrão
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TECNICOS_DIR = os.path.join(BASE_DIR, "tecnicos")
    # ...
```

## Processo de Migração

A migração será realizada em etapas:

1. **Atualização do sistema de configuração**: Adicionar todos os caminhos necessários
2. **Refatoração dos scripts principais**: Substituir caminhos absolutos por referências à configuração
3. **Refatoração do dashboard**: Atualizar componentes do backend e frontend
4. **Testes**: Verificar se todas as funcionalidades continuam operando corretamente
5. **Documentação**: Atualizar a documentação para refletir as mudanças

## Testes

Cada script refatorado será testado para garantir que:

1. Funciona corretamente com o sistema centralizado de configurações
2. Mantém compatibilidade com o código existente
3. Opera em diferentes ambientes sem modificações

## Próximos Passos

Após a refatoração, será possível:

1. Configurar facilmente o sistema para diferentes ambientes
2. Mover o projeto para diferentes servidores sem alterações no código
3. Simplificar o processo de onboarding para novos desenvolvedores
