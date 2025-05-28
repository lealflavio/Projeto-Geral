# Documentação da Integração VM-Drive para Monitoramento de Pastas

## Visão Geral

A integração VM-Drive foi implementada com sucesso, permitindo:

1. Criação automatizada de pastas tanto na VM quanto no Google Drive
2. Compartilhamento da pasta "Novos" com o email do usuário
3. Delegação do download e movimentação de arquivos exclusivamente para a VM
4. Integração com o fluxo de perfil do usuário no Dashboard

## Arquitetura da Solução

A solução implementa um fluxo distribuído onde:

1. **Backend (Dashboard)**: Orquestra o processo e mantém os registros
2. **VM**: Realiza o trabalho pesado (download, processamento e movimentação de arquivos)
3. **Google Drive**: Armazena os arquivos e notifica sobre alterações

## Componentes Implementados

### 1. Endpoint de Gerenciamento de Pastas na VM

- **Arquivo**: `vm_api/routes/folder_manager.py`
- **Funcionalidades**:
  - Criação de pastas na VM
  - Criação de pastas no Google Drive
  - Compartilhamento da pasta "Novos" com o usuário
  - Processamento de arquivos do Drive

### 2. Serviço de Drive Modificado

- **Arquivo**: `dashboard/backend/app/services/drive_service.py`
- **Modificações**:
  - Delegação do download e movimentação para a VM
  - Adição de funcionalidade de compartilhamento
  - Integração com a API da VM

### 3. Endpoints de Callback

- **Arquivo**: `dashboard/backend/app/routes/callbacks.py`
- **Funcionalidades**:
  - Recebimento de resultados da VM
  - Atualização de informações do usuário
  - Registro de estatísticas de processamento

### 4. Testes de Integração

- **Arquivo**: `tests/integration/test_vm_drive_integration.py`
- **Funcionalidades**:
  - Teste do serviço do Drive
  - Teste do gerenciamento de pastas na VM
  - Teste da integração do backend
  - Teste do fluxo completo de ponta a ponta

## Fluxo de Funcionamento

1. **Criação de Pastas**:
   - Quando um usuário é integrado pelo perfil, o backend solicita a criação de pastas
   - O serviço do Drive cria as pastas no Google Drive
   - O serviço do Drive delega a criação de pastas na VM
   - A VM cria as pastas localmente e retorna o resultado via callback
   - O backend atualiza as informações do usuário

2. **Processamento de Arquivos**:
   - Quando um arquivo é adicionado à pasta "Novos" no Google Drive
   - O Google Drive envia uma notificação para o webhook
   - O backend delega o processamento à VM
   - A VM baixa o arquivo, processa e move para a pasta apropriada
   - A VM retorna o resultado via callback
   - O backend registra as estatísticas de processamento

## Configuração Necessária

Para que a integração funcione corretamente, é necessário configurar:

1. **Variáveis de Ambiente**:
   - `VM_API_URL`: URL da API da VM
   - `VM_API_KEY`: Chave de API para autenticação com a VM
   - `BACKEND_URL`: URL do backend para callbacks
   - `VM_BASE_FOLDER`: Diretório base para pastas de usuários na VM
   - `GOOGLE_DRIVE_CREDENTIALS_PATH`: Caminho para o arquivo de credenciais JSON

2. **Permissões**:
   - A conta de serviço do Google Drive deve ter permissões para criar e compartilhar pastas
   - O usuário da VM deve ter permissões para criar diretórios no caminho base

## Próximos Passos Recomendados

1. **Configuração em Produção**:
   - Definir as variáveis de ambiente em produção
   - Configurar as credenciais do Google Drive
   - Garantir que os serviços da VM estejam em execução

2. **Monitoramento**:
   - Implementar monitoramento dos logs para detectar falhas
   - Configurar alertas para erros frequentes

3. **Melhorias Futuras**:
   - Implementar retry em caso de falhas temporárias
   - Adicionar mais testes de integração
   - Implementar dashboard para visualização do status do monitoramento
