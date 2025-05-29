# Instruções para Reinício e Gestão dos Serviços da VM

Este documento contém comandos e instruções para gerenciar os serviços da VM relacionados à integração Dashboard-VM-Drive.

## Reinício de Serviços

### Reiniciar a API da VM

```bash
cd /home/flavioleal/Sistema
sudo systemctl restart vm_api.service
```

### Reiniciar o Monitor do Drive

```bash
sudo systemctl restart drive_monitor.service
```

### Reiniciar Todos os Serviços Relacionados

```bash
sudo systemctl restart vm_api.service
sudo systemctl restart drive_monitor.service
```

## Verificação de Status

### Verificar Status da API da VM

```bash
sudo systemctl status vm_api.service
```

### Verificar Status do Monitor do Drive

```bash
sudo systemctl status drive_monitor.service
```

## Visualização de Logs

### Ver Logs da API da VM em Tempo Real

```bash
sudo journalctl -u vm_api.service -f
```

### Ver Logs do Monitor do Drive em Tempo Real

```bash
sudo journalctl -u drive_monitor.service -f
```

### Ver Logs de Ambos os Serviços

```bash
sudo journalctl -u vm_api.service -u drive_monitor.service -f
```

## Verificação de Pastas

### Verificar Estrutura de Pastas de um Usuário na VM

```bash
ls -la /home/flavioleal/Sistema/tecnicos/NOME_DO_USUARIO
```

### Verificar Arquivo de Configuração de Técnicos

```bash
cat /home/flavioleal/Sistema/tecnicos/tecnicos.json
```

## Solução de Problemas

### Verificar Conectividade com o Google Drive

```bash
cd /home/flavioleal/Sistema
python3 -c "from google.oauth2.service_account import Credentials; from googleapiclient.discovery import build; creds = Credentials.from_service_account_file('chave_servico_primaria.json', scopes=['https://www.googleapis.com/auth/drive']); service = build('drive', 'v3', credentials=creds); print('Conexão com o Drive OK:', service.files().list(pageSize=1).execute())"
```

### Verificar Permissões de Arquivos

```bash
sudo chown -R flavioleal:flavioleal /home/flavioleal/Sistema
sudo chmod -R 755 /home/flavioleal/Sistema
```

### Reiniciar VM (Apenas em Caso de Emergência)

```bash
sudo reboot
```

## Após Atualização de Código

Quando o código for atualizado via pull request, siga estes passos:

1. Atualize o código:
```bash
cd /home/flavioleal/Sistema
git pull origin master
```

2. Reinicie os serviços:
```bash
sudo systemctl restart vm_api.service
sudo systemctl restart drive_monitor.service
```

3. Verifique os logs para garantir que tudo está funcionando:
```bash
sudo journalctl -u vm_api.service -f
```
