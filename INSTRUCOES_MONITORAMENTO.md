# Instruções para o Monitoramento de Pastas no Google Drive

## Visão Geral

O sistema de monitoramento de pastas no Google Drive foi implementado com sucesso. Esta solução permite:

1. Receber notificações quando arquivos são adicionados ou modificados em pastas específicas do Google Drive
2. Processar automaticamente os arquivos novos ou modificados
3. Baixar os arquivos para processamento local
4. Mover os arquivos processados para pastas de "concluídos" ou "erros"
5. Registrar todo o processo em logs para auditoria

## Arquitetura da Solução

A solução é composta por dois componentes principais:

1. **Serviço de Integração com Google Drive (DriveService)**
   - Localizado em: `dashboard/backend/app/services/drive_service.py`
   - Responsável pela autenticação, listagem, download e movimentação de arquivos no Google Drive

2. **Aplicação Flask para Webhook**
   - Localizado em: `dashboard/backend/flask_monitor/app.py`
   - Recebe notificações do Google Drive e aciona o processamento dos arquivos

## Configuração Necessária

Para que o monitoramento funcione corretamente, é necessário configurar:

1. **Credenciais do Google Drive**
   - Crie um projeto no Google Cloud Console
   - Habilite a API do Google Drive
   - Crie credenciais de conta de serviço
   - Baixe o arquivo JSON de credenciais

2. **Variáveis de Ambiente**
   - `GOOGLE_DRIVE_CREDENTIALS_PATH`: Caminho para o arquivo de credenciais JSON
   - `GOOGLE_DRIVE_BASE_FOLDER_ID`: ID da pasta base a ser monitorada no Google Drive
   - `DOWNLOAD_PATH`: Caminho local onde os arquivos serão baixados (padrão: /tmp/drive_files)

3. **Configuração de Notificações Push**
   - No Google Cloud Console, configure notificações push para a pasta monitorada
   - Aponte o webhook para o endpoint: `http://seu-servidor:5001/webhook`

## Como Executar

1. **Iniciar o Serviço de Monitoramento**
   ```bash
   cd dashboard/backend/flask_monitor
   python app.py
   ```

2. **Verificar o Status do Serviço**
   - Acesse: `http://localhost:5001/status`

3. **Testar Manualmente o Monitoramento**
   - Acesse: `http://localhost:5001/check`
   - Ou execute o script de teste: `python test_drive_monitor.py`

## Fluxo de Funcionamento

1. Um arquivo é adicionado ou modificado na pasta monitorada do Google Drive
2. O Google Drive envia uma notificação para o endpoint webhook
3. O webhook aciona o processamento da notificação
4. O sistema lista os arquivos na pasta monitorada
5. Para cada arquivo:
   - Baixa o arquivo para o diretório local
   - Move o arquivo para a pasta "concluídos" se o download for bem-sucedido
   - Move o arquivo para a pasta "erros" se ocorrer algum problema

## Logs e Monitoramento

Os logs são gerados em:
- `drive_monitor.log`: Logs do serviço de integração com o Google Drive
- `drive_webhook.log`: Logs do webhook Flask

## Próximos Passos Recomendados

1. **Integração com Sistema de Processamento**
   - Implemente a lógica específica para processar os arquivos baixados
   - Adicione callbacks para notificar outros sistemas após o processamento

2. **Monitoramento e Alertas**
   - Configure alertas para erros frequentes
   - Implemente um dashboard para visualizar o status do monitoramento

3. **Segurança**
   - Adicione autenticação ao endpoint webhook
   - Implemente validação de origem das notificações

4. **Escalabilidade**
   - Configure o serviço para execução como um serviço do sistema
   - Considere usar um servidor WSGI como Gunicorn para produção
