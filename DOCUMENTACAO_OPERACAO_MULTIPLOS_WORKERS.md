# Documentação de Operação com Múltiplos Workers

## Visão Geral

Este documento descreve como operar o sistema com múltiplos workers para processamento paralelo de diferentes tipos de tarefas.

## Arquitetura de Workers

O sistema agora utiliza dois workers distintos:

1. **Worker Original (wondercom-worker)**: 
   - Processa tarefas relacionadas a ordens de trabalho (WOs)
   - Configurado como serviço systemd
   - Tipos de tarefas: `allocate_wo`, `process_pdf`

2. **Worker de Pastas (folders_worker)**:
   - Processa tarefas relacionadas a criação e gerenciamento de pastas
   - Executado como processo Python separado
   - Tipos de tarefas: `create_folders`, `process_files`

## Inicialização dos Workers

### Worker Original (WOs)

O worker original está configurado como serviço systemd e inicia automaticamente com o sistema:

```bash
# Verificar status
sudo systemctl status wondercom-worker.service

# Reiniciar se necessário
sudo systemctl restart wondercom-worker.service

# Ver logs
sudo journalctl -u wondercom-worker -f
```

### Worker de Pastas

O worker de pastas deve ser iniciado manualmente ou configurado como serviço:

```bash
# Iniciar manualmente
cd /home/flavioleal/Sistema
source venv/bin/activate
python start_folders_worker.py

# Ou usando nohup para manter rodando em background
nohup python start_folders_worker.py > /home/flavioleal/Sistema/logs/folders_worker.log 2>&1 &
```

## Monitoramento

### Verificar Processos em Execução

```bash
# Verificar todos os processos Python
ps aux | grep python

# Verificar worker de WOs
ps aux | grep "python.*vm_api.queue.worker"

# Verificar worker de pastas
ps aux | grep "python.*start_folders_worker.py"
```

### Verificar Logs

```bash
# Logs do worker de WOs
sudo journalctl -u wondercom-worker -f

# Logs do worker de pastas
tail -f /home/flavioleal/Sistema/logs/folders_worker.log
```

### Verificar Filas Redis

```bash
# Instalar redis-cli se necessário
sudo apt-get install redis-tools

# Verificar filas
redis-cli -a "senha_do_redis" llen high_priority_queue
redis-cli -a "senha_do_redis" llen normal_priority_queue
```

## Solução de Problemas

### Se o Worker de WOs Falhar

```bash
# Resetar contador de falhas
sudo systemctl reset-failed wondercom-worker.service

# Reiniciar serviço
sudo systemctl restart wondercom-worker.service
```

### Se o Worker de Pastas Falhar

```bash
# Verificar se está rodando
ps aux | grep "python.*start_folders_worker.py"

# Matar processo se necessário
pkill -f "python.*start_folders_worker.py"

# Reiniciar
cd /home/flavioleal/Sistema
source venv/bin/activate
nohup python start_folders_worker.py > /home/flavioleal/Sistema/logs/folders_worker.log 2>&1 &
```

## Após Atualização de Código

Quando o código for atualizado via pull request:

1. Atualize o código:
```bash
cd /home/flavioleal/Sistema
git pull origin master
```

2. Reinicie ambos os workers:
```bash
# Worker de WOs
sudo systemctl restart wondercom-worker.service

# Worker de pastas
pkill -f "python.*start_folders_worker.py"
cd /home/flavioleal/Sistema
source venv/bin/activate
nohup python start_folders_worker.py > /home/flavioleal/Sistema/logs/folders_worker.log 2>&1 &
```

## Verificação de Funcionamento

Para verificar se ambos os workers estão funcionando corretamente:

1. Verifique se a API está respondendo:
```bash
curl http://localhost:5000/api/health
```

2. Teste a criação de pastas:
```bash
curl -X POST http://localhost:5000/api/folders/create \
  -H "Content-Type: application/json" \
  -H "X-API-Key: api-key-temporaria" \
  -d '{"user_id": "test_user", "user_email": "test@example.com", "user_name": "Usuário de Teste"}'
```

3. Verifique os logs de ambos os workers para confirmar que cada um está processando apenas suas tarefas específicas.
