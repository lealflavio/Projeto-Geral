# Mapeamento da Estrutura do Projeto

## Visão Geral

O projeto está dividido em três pilares principais:

1. **Scripts de Automação (VM/Selenium)** - Arquivos na raiz do projeto que realizam a extração de dados de PDFs e automação de processos
2. **Backend (Render)** - Localizado em `/dashboard/backend`, gerencia a API e banco de dados
3. **Frontend (Netlify)** - Localizado em `/dashboard/frontend`, interface de usuário para visualização de KPIs e outras funcionalidades

## 1. Scripts de Automação (VM)

### Arquivos Principais na Raiz

| Arquivo | Função |
|---------|--------|
| `M1_Extrator_PDF.py` | Extrai dados de arquivos PDF usando expressões regulares para identificar informações específicas |
| `M2_Orquestrador_PDFs.py` | Gerencia o fluxo de processamento de PDFs, coordenando a extração e notificações |
| `M3_Leitura_Drive.py` | Integração com Google Drive para leitura de arquivos PDF armazenados na nuvem |
| `M4_Manipulacao_Arquivos.py` | Funções para manipulação de arquivos (mover, copiar, excluir) |
| `M5_Config_Tecnicos.py` | Gerencia configurações específicas para cada técnico |
| `M6_Notificacao_Status.py` | Envia notificações sobre o status do processamento |
| `chave_servico_primaria.json` | Credenciais para acesso ao Google Drive |
| `segredo.key` | Arquivo de chave para segurança |

### Diretórios de Suporte

| Diretório | Função |
|-----------|--------|
| `/config` | Armazena arquivos de configuração do sistema |
| `/extracao_dados` | Contém dados extraídos dos PDFs |
| `/tecnicos` | Organiza dados por técnico, com subpastas para PDFs e logs |

## 2. Backend (Render)

### Estrutura Principal

| Caminho | Função |
|---------|--------|
| `/dashboard/backend/.env` | Variáveis de ambiente para configuração do backend |
| `/dashboard/backend/app` | Diretório principal da aplicação Flask |
| `/dashboard/backend/flask_monitor` | Monitoramento da aplicação Flask |
| `/dashboard/backend/requirements.txt` | Dependências do projeto backend |

### Detalhamento do Diretório `/app`

| Arquivo/Diretório | Função |
|-------------------|--------|
| `/app/auth.py` | Gerenciamento de autenticação e autorização |
| `/app/create_tables.py` | Script para criação das tabelas no banco de dados |
| `/app/database.py` | Configuração e conexão com o banco de dados |
| `/app/main.py` | Ponto de entrada da aplicação Flask |
| `/app/models.py` | Definição dos modelos de dados (ORM) |
| `/app/schemas.py` | Esquemas para validação e serialização de dados |
| `/app/routes` | Endpoints da API REST |
| `/app/services` | Lógica de negócios e serviços |

## 3. Frontend (Netlify)

### Estrutura Principal

| Caminho | Função |
|---------|--------|
| `/dashboard/frontend/public` | Arquivos estáticos públicos |
| `/dashboard/frontend/src` | Código-fonte da aplicação React |
| `/dashboard/frontend/env` | Ambiente virtual Python (possivelmente para scripts de build) |

### Detalhamento do Diretório `/src`

| Arquivo/Diretório | Função |
|-------------------|--------|
| `/src/App.jsx` | Componente principal da aplicação React |
| `/src/main.jsx` | Ponto de entrada da aplicação React |
| `/src/assets` | Recursos estáticos (imagens, ícones, etc.) |
| `/src/components` | Componentes React reutilizáveis |
| `/src/pages` | Páginas da aplicação |
| `/src/routes` | Configuração de rotas da aplicação |

## Fluxo de Dados e Interações

1. Os scripts de automação (VM) extraem dados de PDFs do Google Drive
2. Os dados extraídos são processados e enviados para o backend (Render)
3. O backend armazena os dados no banco de dados
4. O frontend (Netlify) consome a API do backend para exibir os dados em dashboards

## Pontos de Atenção

1. Múltiplos arquivos de configuração espalhados pelo projeto
2. Dependência de caminhos absolutos nos scripts de automação
3. Falta de documentação clara sobre o fluxo de dados
4. Estrutura de diretórios complexa que pode dificultar a manutenção
