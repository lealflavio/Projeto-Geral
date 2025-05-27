# Documentação de Arquitetura

## Visão Geral da Arquitetura

Este documento descreve a arquitetura técnica do Projeto-Geral, um sistema integrado para automação de processamento de relatórios técnicos em PDF.

## Diagrama de Arquitetura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Google Drive   │────▶│  VM / Selenium  │────▶│  Banco de Dados │
│                 │     │  (Extração)     │     │  (PostgreSQL)   │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └────────▲────────┘
                                 │                       │
                                 │                       │
                                 ▼                       │
                        ┌─────────────────┐     ┌────────┴────────┐
                        │                 │     │                 │
                        │  Backend API    │◀───▶│  Frontend       │
                        │  (Flask)        │     │  (React)        │
                        │                 │     │                 │
                        └─────────────────┘     └─────────────────┘
                                 ▲                       ▲
                                 │                       │
                                 │                       │
                        ┌────────┴────────┐     ┌────────┴────────┐
                        │                 │     │                 │
                        │  Scripts de     │     │  Usuários       │
                        │  Monitoramento  │     │  (Navegador)    │
                        │                 │     │                 │
                        └─────────────────┘     └─────────────────┘
```

## Componentes Principais

### 1. Extração de Dados (VM/Selenium)

**Responsabilidade**: Extrair dados estruturados de relatórios técnicos em PDF.

**Componentes**:
- **M1_Extrator_PDF.py**: Extrai dados de PDFs individuais
- **M2_Orquestrador_PDFs.py**: Coordena o processamento de múltiplos PDFs
- **M3_Leitura_Drive.py**: Obtém novos PDFs do Google Drive
- **M4_Manipulacao_Arquivos.py**: Manipula arquivos PDF
- **M5_Config_Tecnicos.py**: Gerencia configurações de técnicos

**Tecnologias**:
- Python 3.8+
- Selenium WebDriver
- PyPDF2
- Google Drive API

**Fluxo de Dados**:
1. Novos PDFs são obtidos do Google Drive
2. O orquestrador distribui os PDFs para processamento
3. O extrator extrai dados estruturados de cada PDF
4. Os dados extraídos são enviados para o backend via API

### 2. Backend API (Flask)

**Responsabilidade**: Fornecer endpoints RESTful para armazenamento e recuperação de dados.

**Componentes**:
- **app/models/**: Modelos de dados (ORM)
- **app/routes/**: Endpoints da API
- **app/services/**: Lógica de negócio
- **app/auth/**: Autenticação e autorização

**Tecnologias**:
- Flask
- SQLAlchemy
- PostgreSQL
- JWT (JSON Web Tokens)

**Fluxo de Dados**:
1. Recebe dados extraídos dos PDFs
2. Valida e processa os dados
3. Armazena os dados no banco de dados
4. Fornece endpoints para consulta e manipulação de dados

### 3. Frontend (React)

**Responsabilidade**: Fornecer interface de usuário para visualização de dados e interação com o sistema.

**Componentes**:
- **src/components/**: Componentes React reutilizáveis
- **src/pages/**: Páginas da aplicação
- **src/services/**: Serviços de API
- **src/redux/**: Gerenciamento de estado

**Tecnologias**:
- React
- Redux
- Material-UI
- Chart.js
- Axios

**Fluxo de Dados**:
1. Obtém dados do backend via API
2. Renderiza visualizações e dashboards
3. Permite interação do usuário com os dados
4. Envia atualizações para o backend quando necessário

### 4. Scripts de Monitoramento

**Responsabilidade**: Monitorar a saúde do sistema e realizar tarefas de manutenção.

**Componentes**:
- **system_health.py**: Verifica o status dos componentes do sistema
- **backup.py**: Realiza backups automáticos
- **log_monitor.py**: Monitora logs e gera alertas

**Tecnologias**:
- Python
- Bibliotecas de monitoramento
- Serviços de notificação

**Fluxo de Dados**:
1. Coleta métricas e logs dos componentes do sistema
2. Analisa os dados coletados
3. Gera alertas e relatórios
4. Executa ações corretivas quando necessário

## Fluxo de Dados Detalhado

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │     │             │
│  PDF no     │────▶│  Extração   │────▶│  Validação  │────▶│ Armazenamento│
│  Google Drive│     │  de Dados   │     │  de Dados   │     │ no Banco    │
│             │     │             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                   │
                                                                   │
                                                                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │     │             │
│  Exportação │◀────│  Visualização│◀────│  Processamento│◀────│  Consulta   │
│  de Dados   │     │  em Dashboard│     │  de Dados   │     │  de Dados   │
│             │     │             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Modelo de Dados

### Principais Entidades

**Relatório**:
- ID
- Título
- Data
- Técnico (referência)
- Equipamentos (lista)
- Materiais (lista)
- Conteúdo (JSON)
- Status

**Técnico**:
- ID
- Nome
- Email
- Telefone
- Status (ativo/inativo)

**Usuário**:
- ID
- Nome
- Email
- Senha (hash)
- Função (admin/usuário)

**Equipamento**:
- ID
- Nome
- Categoria
- Descrição

**Material**:
- ID
- Nome
- Categoria
- Descrição

## Segurança

### Autenticação e Autorização

- Autenticação baseada em JWT (JSON Web Tokens)
- Tokens de acesso com expiração curta (15 minutos)
- Tokens de refresh com expiração longa (7 dias)
- Controle de acesso baseado em funções (RBAC)

### Proteção de Dados

- Comunicação criptografada via HTTPS
- Senhas armazenadas com hash e salt
- Validação de entrada em todos os endpoints
- Proteção contra ataques comuns (CSRF, XSS, SQL Injection)

## Escalabilidade

### Estratégias de Escalabilidade

- Processamento paralelo de PDFs
- Caching de resultados de consultas frequentes
- Paginação de resultados de API
- Otimização de consultas ao banco de dados

### Pontos de Escalabilidade

- Extração de dados: Escalável horizontalmente com múltiplas instâncias
- Backend API: Pode ser escalado com balanceamento de carga
- Banco de dados: Suporta replicação e sharding

## Monitoramento e Observabilidade

### Métricas Coletadas

- Tempo de processamento de PDFs
- Tempo de resposta da API
- Uso de recursos (CPU, memória, disco)
- Taxa de erros
- Número de usuários ativos

### Alertas

- Falhas na extração de dados
- Tempo de resposta da API acima do limite
- Erros de banco de dados
- Uso de recursos acima do limite

## Considerações de Deployment

### Ambientes

- **Desenvolvimento**: Ambiente local para desenvolvimento
- **Teste**: Ambiente para testes de integração
- **Produção**: Ambiente para usuários finais

### Estratégia de Deployment

- CI/CD automatizado via GitHub Actions
- Testes automatizados antes do deployment
- Deployment blue-green para minimizar downtime
- Rollback automatizado em caso de falha

## Dependências Externas

- **Google Drive API**: Para obtenção de novos PDFs
- **Serviço de Email**: Para notificações e alertas
- **Serviço de Armazenamento**: Para backups

## Limitações e Restrições

- Processamento de PDFs limitado a formatos específicos
- Tempo máximo de processamento por PDF: 5 minutos
- Tamanho máximo de PDF: 50MB
- Número máximo de requisições API por minuto: 100 por IP

## Decisões de Arquitetura

### Escolha de Tecnologias

- **Python para Extração**: Facilidade de integração com bibliotecas de processamento de PDF
- **Flask para Backend**: Leve e flexível, ideal para APIs
- **React para Frontend**: Componentização e reatividade
- **PostgreSQL para Banco de Dados**: Suporte a JSON e consultas complexas

### Trade-offs

- **Processamento Síncrono vs. Assíncrono**: Optamos por processamento assíncrono para melhor experiência do usuário
- **Monolito vs. Microserviços**: Optamos por uma arquitetura monolítica para simplificar o desenvolvimento inicial
- **ORM vs. SQL Puro**: Optamos por ORM para maior produtividade, com SQL puro para consultas complexas

## Evolução Futura

### Melhorias Planejadas

- Migração para arquitetura de microserviços
- Implementação de processamento em tempo real
- Integração com sistemas de BI
- Expansão para processamento de outros tipos de documentos

### Roadmap Técnico

1. **Curto Prazo (3 meses)**:
   - Containerização com Docker
   - Implementação de testes automatizados abrangentes
   - Sistema de logging centralizado

2. **Médio Prazo (6-12 meses)**:
   - Interface de administração
   - Processamento em tempo real
   - Expansão da API para integração com sistemas externos

3. **Longo Prazo (1-2 anos)**:
   - Migração para microserviços
   - Implementação de machine learning para extração de dados
   - Expansão para múltiplos idiomas

---

Documentação atualizada: Maio de 2025
