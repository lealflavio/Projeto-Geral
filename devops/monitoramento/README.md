# Guia de Monitoramento

Este documento descreve como implementar e utilizar o sistema de monitoramento configurado para o Projeto Wondercom Automation.

## Estrutura de Arquivos

Os arquivos de configuração do monitoramento estão localizados no diretório `/home/ubuntu/Projeto-Geral/devops/monitoramento/`:

- `prometheus.yml`: Configuração principal do Prometheus
- `alert_rules.yml`: Regras de alerta
- `alertmanager.yml`: Configuração do Alertmanager
- `docker-compose.yml`: Configuração para execução do stack de monitoramento

## Componentes do Sistema

O sistema de monitoramento é composto por:

1. **Prometheus**: Coleta e armazena métricas
2. **Alertmanager**: Gerencia e envia alertas
3. **Grafana**: Visualização de dashboards
4. **Node Exporter**: Coleta métricas do sistema
5. **Postgres Exporter**: Coleta métricas do PostgreSQL

## Implementação

Para implementar o sistema de monitoramento:

1. Copie os arquivos de configuração para o ambiente:
   ```bash
   mkdir -p /opt/monitoring
   cp /home/ubuntu/Projeto-Geral/devops/monitoramento/* /opt/monitoring/
   ```

2. Inicie o stack de monitoramento:
   ```bash
   cd /opt/monitoring
   docker-compose up -d
   ```

3. Acesse o Grafana:
   - URL: http://localhost:3001
   - Usuário: admin
   - Senha: wondercom_admin

## Alertas Configurados

Os seguintes alertas estão configurados:

1. **HighCPULoad**: CPU acima de 80% por 5 minutos
2. **HighMemoryUsage**: Uso de memória acima de 85% por 5 minutos
3. **HighDiskUsage**: Uso de disco acima de 85% por 5 minutos
4. **APIHighResponseTime**: Tempo de resposta da API acima de 1s (95º percentil)
5. **APIHighErrorRate**: Taxa de erro da API acima de 5%
6. **PDFProcessingQueueGrowing**: Fila de processamento com mais de 50 itens por 15 minutos

## Notificações

As notificações são enviadas para:

1. **Slack**: Canal #alertas-wondercom para todos os alertas
2. **PagerDuty**: Apenas para alertas críticos

## Dashboards Recomendados

Recomendamos configurar os seguintes dashboards no Grafana:

1. **Visão Geral do Sistema**: CPU, memória, disco e rede
2. **Performance da API**: Tempo de resposta, taxa de erro, requisições por segundo
3. **Processamento de PDFs**: Tamanho da fila, tempo de processamento, taxa de sucesso
4. **Banco de Dados**: Conexões, queries, tempo de resposta

## Métricas Personalizadas

Para adicionar métricas personalizadas ao backend:

1. Instale a biblioteca prometheus-client:
   ```bash
   pip install prometheus-client
   ```

2. Adicione instrumentação ao código:
   ```python
   from prometheus_client import Counter, Histogram, Gauge
   
   # Contador de PDFs processados
   pdf_processed = Counter('wondercom_pdf_processed_total', 'Total de PDFs processados', ['status'])
   
   # Histograma de tempo de processamento
   pdf_processing_time = Histogram('wondercom_pdf_processing_seconds', 'Tempo de processamento de PDFs')
   
   # Gauge para tamanho da fila
   pdf_queue_size = Gauge('wondercom_pdf_queue_size', 'Tamanho da fila de processamento de PDFs')
   ```

## Troubleshooting

### Prometheus não está coletando métricas

1. Verifique se os targets estão acessíveis:
   ```bash
   curl http://backend:8000/metrics
   ```

2. Verifique os logs do Prometheus:
   ```bash
   docker-compose logs prometheus
   ```

### Alertas não estão sendo enviados

1. Verifique a configuração do Alertmanager:
   ```bash
   docker-compose logs alertmanager
   ```

2. Teste a integração com Slack/PagerDuty manualmente
