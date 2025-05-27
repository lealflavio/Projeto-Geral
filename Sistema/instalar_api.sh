#!/bin/bash
# Script de instalação e configuração da API REST na VM

# Criar diretório de logs
mkdir -p /home/flavioleal/Sistema/logs

# Copiar arquivos para a estrutura correta
echo "Copiando arquivos para a estrutura correta..."

# Arquivo de configuração
cp /home/ubuntu/vm_api_config.py /home/flavioleal/Sistema/vm_api/config.py

# Arquivo de autenticação
cp /home/ubuntu/vm_api_auth.py /home/flavioleal/Sistema/vm_api/auth.py

# Adaptadores
cp /home/ubuntu/vm_api_extrator_adapter.py /home/flavioleal/Sistema/vm_api/adapters/extrator_adapter.py
cp /home/ubuntu/vm_api_orquestrador_adapter.py /home/flavioleal/Sistema/vm_api/adapters/orquestrador_adapter.py

# Sistema de filas
cp /home/ubuntu/vm_api_producer.py /home/flavioleal/Sistema/vm_api/queue/producer.py
cp /home/ubuntu/vm_api_worker.py /home/flavioleal/Sistema/vm_api/queue/worker.py

# Rotas
cp /home/ubuntu/vm_api_allocate.py /home/flavioleal/Sistema/vm_api/routes/allocate.py
cp /home/ubuntu/vm_api_process.py /home/flavioleal/Sistema/vm_api/routes/process.py
cp /home/ubuntu/vm_api_status.py /home/flavioleal/Sistema/vm_api/routes/status.py

# Aplicação principal
cp /home/ubuntu/vm_api_app.py /home/flavioleal/Sistema/vm_api/app.py

# Criar arquivos __init__.py vazios
touch /home/flavioleal/Sistema/vm_api/__init__.py
touch /home/flavioleal/Sistema/vm_api/routes/__init__.py
touch /home/flavioleal/Sistema/vm_api/adapters/__init__.py
touch /home/flavioleal/Sistema/vm_api/queue/__init__.py

echo "Instalação concluída!"
