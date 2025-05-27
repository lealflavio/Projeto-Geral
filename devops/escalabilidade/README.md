# Guia de Escalabilidade

Este documento descreve como implementar e utilizar as configurações de escalabilidade para o Projeto Wondercom Automation.

## Estrutura de Arquivos

Os arquivos de configuração de escalabilidade estão localizados no diretório `/home/ubuntu/Projeto-Geral/devops/escalabilidade/`:

- `nginx-load-balancer.yml`: Configuração do balanceador de carga NGINX
- `docker-compose-swarm.yml`: Configuração para Docker Swarm
- `api_queue_handler.py`: Implementação da API com sistema de filas
- `pdf_worker.py`: Worker para processamento paralelo de PDFs

## Componentes do Sistema

O sistema de escalabilidade é composto por:

1. **Balanceador de Carga**: NGINX configurado para distribuir requisições
2. **Orquestração de Containers**: Docker Swarm para gerenciar múltiplas instâncias
3. **Sistema de Filas**: Redis para enfileiramento de tarefas
4. **Workers Paralelos**: Processamento distribuído de PDFs

## Implementação

### Configuração do Balanceador de Carga

1. Instale o NGINX:
   ```bash
   sudo apt-get update
   sudo apt-get install -y nginx
   ```

2. Configure o NGINX com o arquivo de configuração fornecido:
   ```bash
   sudo cp /home/ubuntu/Projeto-Geral/devops/escalabilidade/nginx-load-balancer.yml /etc/nginx/nginx.conf
   sudo systemctl restart nginx
   ```

### Configuração do Docker Swarm

1. Inicialize o Docker Swarm:
   ```bash
   docker swarm init
   ```

2. Implante o stack com Docker Swarm:
   ```bash
   cd /home/ubuntu/Projeto-Geral/devops/escalabilidade/
   docker stack deploy -c docker-compose-swarm.yml wondercom
   ```

### Configuração do Sistema de Filas

1. Instale o Redis:
   ```bash
   sudo apt-get install -y redis-server
   ```

2. Configure o Redis para alta disponibilidade:
   ```bash
   sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup
   sudo sed -i 's/appendonly no/appendonly yes/' /etc/redis/redis.conf
   sudo systemctl restart redis-server
   ```

### Configuração dos Workers

1. Instale as dependências:
   ```bash
   pip install redis fastapi sqlalchemy
   ```

2. Execute os workers:
   ```bash
   python /home/ubuntu/Projeto-Geral/devops/escalabilidade/pdf_worker.py
   ```

## Estratégias de Escalabilidade

### Escalabilidade Horizontal

O sistema está configurado para escalar horizontalmente através de:

1. **Múltiplas Instâncias de Backend**: Configuradas no Docker Swarm
2. **Balanceamento de Carga**: NGINX distribui requisições entre instâncias
3. **Processamento Paralelo**: Workers processam PDFs simultaneamente

### Controle de Taxa e Enfileiramento

Para lidar com picos de demanda:

1. **Rate Limiting**: Configurado no NGINX para limitar requisições por IP
2. **Sistema de Filas**: Tarefas são enfileiradas no Redis
3. **Priorização**: Tarefas podem ser priorizadas com base em critérios de negócio

### Auto-Scaling

Para ajustar recursos automaticamente:

1. **Monitoramento de Carga**: Prometheus monitora uso de recursos
2. **Regras de Escala**: Docker Swarm ajusta número de réplicas
3. **Alertas**: Notificações são enviadas quando recursos estão próximos do limite

## Capacidade e Limites

O sistema foi dimensionado para:

- **Processamento Diário**: Até 500 WOs por dia
- **Pico de Carga**: Até 50 requisições simultâneas
- **Tempo de Resposta**: Menos de 2 segundos para operações da API
- **Tempo de Processamento**: Média de 30 segundos por PDF

## Monitoramento de Escalabilidade

Para monitorar o desempenho:

1. **Tamanho da Fila**: Endpoint `/api/wondercom/queue-status`
2. **Métricas do Sistema**: Prometheus coleta dados de uso
3. **Dashboards**: Grafana visualiza métricas de escalabilidade

## Troubleshooting

### Sistema Lento Durante Picos

1. Verifique o tamanho da fila:
   ```bash
   redis-cli get wondercom_pdf_queue_size
   ```

2. Verifique a utilização de recursos:
   ```bash
   docker stats
   ```

3. Aumente o número de workers:
   ```bash
   docker service scale wondercom_worker=5
   ```

### Erros de Conexão

1. Verifique o status do balanceador:
   ```bash
   sudo systemctl status nginx
   ```

2. Verifique a conectividade entre serviços:
   ```bash
   docker service ls
   docker service logs wondercom_backend
   ```

### Fila Crescendo Rapidamente

1. Verifique se os workers estão processando:
   ```bash
   docker service logs wondercom_worker
   ```

2. Aumente temporariamente os recursos:
   ```bash
   docker service update --limit-cpu 1 --limit-memory 1G wondercom_worker
   ```
