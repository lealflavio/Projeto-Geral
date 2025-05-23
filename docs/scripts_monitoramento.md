# Documentação dos Scripts de Monitoramento e Manutenção

Este documento descreve os scripts de monitoramento e manutenção implementados para facilitar a operação e manutenção do sistema. Todos os scripts estão integrados com o sistema centralizado de configurações.

## Visão Geral

Os scripts de monitoramento e manutenção foram desenvolvidos para:

1. Monitorar a saúde dos três componentes principais do sistema (VM/Selenium, Backend, Frontend)
2. Realizar backups automáticos de configurações, banco de dados, logs e dados extraídos
3. Monitorar logs em busca de erros e gerar alertas quando necessário

## Scripts Disponíveis

### 1. Verificador de Saúde do Sistema (`system_health.py`)

Este script verifica o status dos três componentes principais do sistema e gera um relatório detalhado.

**Uso:**
```bash
python3 scripts/monitoramento/system_health.py [--email] [--json]
```

**Opções:**
- `--email`: Envia o relatório por email para os destinatários configurados
- `--json`: Salva o relatório em formato JSON

**Exemplo de saída:**
```
RELATÓRIO DE SAÚDE DO SISTEMA - 2025-05-23 21:42:31
==================================================
Status Geral: OK

--------------------
BACKEND (Render)
--------------------
Status: ONLINE
version: 1.0.0
database_status: connected

--------------------
FRONTEND (Netlify)
--------------------
Status: ONLINE

--------------------
SCRIPTS DE AUTOMAÇÃO (VM)
--------------------
Status: OPERATIONAL
Diretórios: OK
Scripts: OK
PDFs Processados: 15
PDFs com Erro: 2

Logs Recentes:
- system.log (2025-05-23 20:30:45)
- extraction.log (2025-05-23 19:15:22)
```

### 2. Backup Automático (`backup.py`)

Este script realiza backups automáticos dos componentes críticos do sistema.

**Uso:**
```bash
python3 scripts/monitoramento/backup.py [--full] [--config-only] [--db-only] [--logs-only] [--data-only]
```

**Opções:**
- `--full`: Realiza backup completo de todos os componentes (padrão)
- `--config-only`: Realiza backup apenas das configurações
- `--db-only`: Realiza backup apenas do banco de dados
- `--logs-only`: Realiza backup apenas dos logs
- `--data-only`: Realiza backup apenas dos dados extraídos

**Funcionalidades:**
- Backup de configurações
- Backup do banco de dados (PostgreSQL)
- Backup de logs
- Backup de dados extraídos
- Compressão automática (ZIP ou TAR.GZ)
- Limpeza de backups antigos conforme período de retenção configurado

### 3. Monitoramento de Logs (`log_monitor.py`)

Este script monitora os logs do sistema, detecta padrões de erro e gera alertas quando necessário.

**Uso:**
```bash
python3 scripts/monitoramento/log_monitor.py [--watch] [--analyze] [--report {day,week,month,all}]
```

**Opções:**
- `--watch`: Monitora logs em tempo real
- `--analyze`: Analisa logs existentes
- `--report {day,week,month,all}`: Gera relatório de erros para o período especificado

**Funcionalidades:**
- Monitoramento em tempo real de novos erros
- Análise de logs existentes
- Geração de relatórios de erros
- Alertas por email quando o número de erros ultrapassa o limite configurado

## Integração com o Sistema Centralizado de Configurações

Todos os scripts estão integrados com o sistema centralizado de configurações, permitindo fácil personalização sem modificar o código. As configurações relevantes incluem:

### Para o Verificador de Saúde (`system_health.py`):
```json
{
  "monitoring": {
    "backend_url": "http://localhost:5000",
    "frontend_url": "http://localhost:3000"
  },
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "seu-email@gmail.com",
    "password": "sua-senha",
    "recipients": ["admin@example.com"]
  }
}
```

### Para o Backup Automático (`backup.py`):
```json
{
  "backup": {
    "dir": "/path/to/backups",
    "db_name": "sistema",
    "db_user": "postgres",
    "db_host": "localhost",
    "db_port": "5432",
    "retention_days": 30,
    "compression": "zip"
  }
}
```

### Para o Monitoramento de Logs (`log_monitor.py`):
```json
{
  "log_monitor": {
    "patterns": {
      "error": ["ERROR", "Exception", "Traceback", "Failed", "Falha"],
      "warning": ["WARNING", "WARN", "Aviso"],
      "critical": ["CRITICAL", "FATAL", "EMERGENCY"]
    },
    "watch_interval": 5,
    "alert_threshold": 5,
    "report_dir": "/path/to/reports"
  }
}
```

## Configuração de Cron Jobs

Para automatizar a execução dos scripts, você pode configurar cron jobs. Exemplos:

```bash
# Verificar saúde do sistema a cada hora
0 * * * * cd /path/to/project && python3 scripts/monitoramento/system_health.py --json

# Realizar backup completo diariamente às 2h da manhã
0 2 * * * cd /path/to/project && python3 scripts/monitoramento/backup.py --full

# Monitorar logs em busca de erros a cada 5 minutos
*/5 * * * * cd /path/to/project && python3 scripts/monitoramento/log_monitor.py --analyze

# Gerar relatório semanal de logs aos domingos
0 0 * * 0 cd /path/to/project && python3 scripts/monitoramento/log_monitor.py --report week
```

## Próximos Passos

1. Personalizar as configurações conforme necessidades específicas do projeto
2. Configurar cron jobs para automação
3. Testar os scripts em ambiente de produção
4. Expandir funcionalidades conforme necessário

## Suporte

Em caso de dúvidas ou problemas, consulte a documentação detalhada nos próprios scripts ou entre em contato com a equipe de desenvolvimento.
