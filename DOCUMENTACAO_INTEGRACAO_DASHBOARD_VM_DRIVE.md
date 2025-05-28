# Documentação da Integração Dashboard-VM-Drive

## Visão Geral

Esta documentação descreve a integração entre o Dashboard, a VM e o Google Drive para criação e monitoramento automático de pastas de usuários.

## Arquitetura da Solução

A solução implementa um fluxo distribuído onde:

1. **Dashboard (Frontend)**: Interface para o usuário solicitar a criação de pastas
2. **Backend**: Orquestra o processo e mantém os registros
3. **VM**: Executa o script M1_Criar_Tecnico.py que cria as pastas tanto na VM quanto no Google Drive
4. **Google Drive**: Armazena os arquivos e notifica sobre alterações

## Componentes Implementados

### 1. Endpoint de Gerenciamento de Pastas na VM

- **Arquivo**: `Sistema/vm_api/routes/folder_manager.py`
- **Funcionalidades**:
  - Criação de pastas na VM e no Google Drive usando o script M1_Criar_Tecnico.py
  - Verificação de status das pastas
  - Processamento de arquivos

### 2. Integração do Dashboard com a VM

- **Arquivo**: `dashboard/backend/app/services/vm_integration.py`
- **Funcionalidades**:
  - Comunicação com a API da VM
  - Solicitação de criação de pastas
  - Verificação de status das pastas

### 3. Endpoints do Backend para Pastas de Usuários

- **Arquivo**: `dashboard/backend/app/routes/user_folders.py`
- **Funcionalidades**:
  - Endpoint para solicitar criação de pastas
  - Endpoint para verificar status das pastas
  - Integração com o modelo de usuário

### 4. Worker para Processamento Assíncrono

- **Arquivo**: `Sistema/vm_api/queue/worker.py`
- **Funcionalidades**:
  - Processamento assíncrono de tarefas
  - Execução do script M1_Criar_Tecnico.py
  - Envio de callbacks para o backend

## Fluxo de Funcionamento

1. **Criação de Pastas**:
   - O usuário solicita a criação de pastas pelo frontend
   - O backend envia uma requisição para a API da VM
   - A VM executa o script M1_Criar_Tecnico.py que:
     - Cria a estrutura de pastas na VM
     - Cria a estrutura de pastas no Google Drive
     - Configura webhooks para monitoramento automático
     - Compartilha a pasta "novos" com o usuário
   - A VM envia um callback para o backend com o resultado
   - O backend atualiza as informações do usuário

2. **Monitoramento de Arquivos**:
   - Quando um arquivo é adicionado à pasta "novos" no Google Drive
   - O webhook configurado notifica o sistema
   - A VM processa o arquivo e o move para a pasta apropriada

## Configuração Necessária

Para que a integração funcione corretamente, é necessário configurar:

1. **Variáveis de Ambiente**:
   - `VM_API_URL`: URL da API da VM
   - `VM_API_KEY`: Chave de API para autenticação com a VM
   - `BACKEND_URL`: URL do backend para callbacks
   - `GOOGLE_APPLICATION_CREDENTIALS`: Caminho para o arquivo de credenciais JSON

2. **Arquivos de Configuração**:
   - Certifique-se de que o arquivo de credenciais do Google Drive está no caminho correto
   - Verifique se o arquivo de chave para criptografia está presente

## Solução de Problemas

Se as pastas não estiverem sendo criadas corretamente:

1. Verifique se o script M1_Criar_Tecnico.py está acessível e tem as permissões corretas
2. Confirme que as variáveis de ambiente estão configuradas corretamente
3. Verifique os logs da VM em `/home/flavioleal/Sistema/logs/vm_api.log`
4. Teste a API da VM diretamente usando o script de teste em `tests/integration/test_folder_creation_integration.py`

## Próximos Passos

1. Implementar interface no frontend para visualização do status das pastas
2. Adicionar funcionalidade para recriar pastas caso necessário
3. Implementar monitoramento e alertas para falhas no processo
