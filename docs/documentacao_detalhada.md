# Documentação Detalhada do Projeto

## Introdução

Este documento fornece uma documentação detalhada do projeto, incluindo sua arquitetura, componentes principais e fluxo de dados. O objetivo é facilitar o entendimento do sistema para novos colaboradores e simplificar a manutenção futura.

## Arquitetura do Sistema

O sistema é composto por três pilares principais que trabalham em conjunto:

1. **Scripts de Automação (VM/Selenium)**
   - Responsável pela extração de dados de PDFs e automação de processos
   - Executa em uma máquina virtual dedicada
   - Interage com o Google Drive para obter os PDFs dos relatórios

2. **Backend (Render)**
   - API REST e banco de dados
   - Armazena os dados extraídos dos PDFs
   - Fornece endpoints para o frontend consumir

3. **Frontend (Netlify)**
   - Interface de usuário para visualização de KPIs e outras funcionalidades
   - Dashboard para técnicos visualizarem o trabalho realizado

## Fluxo de Dados

1. **Extração de Dados**
   - Os técnicos geram PDFs contendo relatórios de trabalho
   - Os PDFs são armazenados no Google Drive
   - Os scripts de automação acessam o Drive e baixam os PDFs

2. **Processamento**
   - Os PDFs são processados para extrair informações relevantes
   - Os dados extraídos são validados e formatados
   - Em caso de sucesso, os PDFs são movidos para uma pasta de processados
   - Em caso de erro, os PDFs são movidos para uma pasta de erro

3. **Armazenamento**
   - Os dados processados são enviados para o backend via API
   - O backend valida os dados e os armazena no banco de dados

4. **Visualização**
   - O frontend consome a API do backend para obter os dados
   - Os dados são apresentados em dashboards e relatórios
   - Os técnicos podem visualizar KPIs e realizar outras funções

## Componentes Detalhados

### 1. Scripts de Automação (VM)

#### Módulos Principais

- **M1_Extrator_PDF.py**
  - Função: Extrair dados de arquivos PDF
  - Métodos principais:
    - `extrair_valor_apos_rotulo`: Extrai valores após rótulos específicos
    - `extrair_secao_multilinha`: Extrai seções inteiras do texto
    - `extrair_dados_pdf_relevantes`: Função principal que coordena a extração

- **M2_Orquestrador_PDFs.py**
  - Função: Gerenciar o fluxo de processamento de PDFs
  - Métodos principais:
    - Coordenação da extração de dados
    - Gerenciamento de notificações
    - Tratamento de erros

- **M3_Leitura_Drive.py**
  - Função: Integração com Google Drive
  - Métodos principais:
    - `listar_pdfs_na_pasta`: Lista arquivos PDF em uma pasta específica
    - Autenticação com a API do Google Drive

- **M4_Manipulacao_Arquivos.py**
  - Função: Manipulação de arquivos locais
  - Métodos principais:
    - Mover arquivos entre diretórios
    - Copiar arquivos
    - Excluir arquivos

- **M5_Config_Tecnicos.py**
  - Função: Gerenciar configurações específicas para cada técnico
  - Métodos principais:
    - Leitura e escrita de configurações
    - Validação de configurações

- **M6_Notificacao_Status.py**
  - Função: Enviar notificações sobre o status do processamento
  - Métodos principais:
    - `enviar_notificacao_boas_vindas`
    - `enviar_notificacao_wo_iniciada`
    - `enviar_notificacao_wo_sucesso`
    - `enviar_notificacao_wo_erro`

#### Estrutura de Diretórios

- **/config**
  - Armazena arquivos de configuração do sistema
  - Contém `tecnicos.json` com configurações específicas para cada técnico

- **/extracao_dados**
  - Armazena dados extraídos dos PDFs
  - Serve como área intermediária antes do envio para o backend

- **/tecnicos**
  - Organiza dados por técnico
  - Cada técnico tem sua própria pasta com:
    - `/logs`: Registros de processamento
    - `/pdfs`: PDFs a serem processados
    - `/pdfs/processados`: PDFs já processados com sucesso
    - `/pdfs/erro`: PDFs com erro de processamento

### 2. Backend (Render)

#### Estrutura Principal

- **/dashboard/backend/app**
  - Diretório principal da aplicação Flask
  - Contém a lógica de negócios e endpoints da API

- **/dashboard/backend/flask_monitor**
  - Ferramentas para monitoramento da aplicação Flask
  - Logs e métricas de desempenho

#### Componentes do App

- **auth.py**
  - Função: Gerenciamento de autenticação e autorização
  - Métodos principais:
    - Autenticação de usuários
    - Geração e validação de tokens
    - Controle de acesso

- **create_tables.py**
  - Função: Criação das tabelas no banco de dados
  - Métodos principais:
    - Definição do esquema do banco de dados
    - Migração e atualização de esquema

- **database.py**
  - Função: Configuração e conexão com o banco de dados
  - Métodos principais:
    - Estabelecimento de conexão
    - Gerenciamento de sessões
    - Configuração de pool de conexões

- **main.py**
  - Função: Ponto de entrada da aplicação Flask
  - Métodos principais:
    - Configuração da aplicação
    - Registro de blueprints
    - Inicialização de serviços

- **models.py**
  - Função: Definição dos modelos de dados (ORM)
  - Classes principais:
    - Modelos para dados extraídos dos PDFs
    - Modelos para usuários e autenticação
    - Modelos para configurações

- **schemas.py**
  - Função: Esquemas para validação e serialização de dados
  - Classes principais:
    - Esquemas para validação de entrada
    - Esquemas para serialização de saída

- **/app/routes**
  - Função: Endpoints da API REST
  - Arquivos principais:
    - Rotas para dados de PDFs
    - Rotas para autenticação
    - Rotas para configurações

- **/app/services**
  - Função: Lógica de negócios e serviços
  - Arquivos principais:
    - Serviços para processamento de dados
    - Serviços para geração de relatórios
    - Serviços para integração com outros sistemas

### 3. Frontend (Netlify)

#### Estrutura Principal

- **/dashboard/frontend/public**
  - Arquivos estáticos públicos
  - Favicon, robots.txt, etc.

- **/dashboard/frontend/src**
  - Código-fonte da aplicação React
  - Componentes, páginas e lógica da interface

#### Componentes do Frontend

- **App.jsx**
  - Função: Componente principal da aplicação React
  - Responsabilidades:
    - Configuração de rotas
    - Gerenciamento de estado global
    - Configuração de temas

- **main.jsx**
  - Função: Ponto de entrada da aplicação React
  - Responsabilidades:
    - Renderização do componente raiz
    - Configuração de providers

- **/src/assets**
  - Função: Recursos estáticos
  - Conteúdo:
    - Imagens
    - Ícones
    - Fontes

- **/src/components**
  - Função: Componentes React reutilizáveis
  - Componentes principais:
    - Componentes de UI (botões, inputs, etc.)
    - Componentes de gráficos e visualizações
    - Componentes de layout

- **/src/pages**
  - Função: Páginas da aplicação
  - Páginas principais:
    - Dashboard
    - Login
    - Configurações
    - Relatórios

- **/src/routes**
  - Função: Configuração de rotas da aplicação
  - Responsabilidades:
    - Definição de rotas públicas e privadas
    - Redirecionamentos
    - Proteção de rotas

## Dependências e Integrações

### Integrações Externas

1. **Google Drive API**
   - Utilizada para acessar os PDFs dos relatórios
   - Autenticação via chave de serviço

2. **Serviço de Notificações**
   - Envio de notificações sobre o status do processamento
   - Pode incluir email, SMS ou outros canais

### Dependências Principais

1. **Scripts de Automação**
   - Python 3.x
   - Bibliotecas para manipulação de PDFs
   - Google API Client

2. **Backend**
   - Flask (framework web)
   - SQLAlchemy (ORM)
   - Bibliotecas para autenticação e segurança

3. **Frontend**
   - React
   - Bibliotecas para UI (possivelmente Material-UI ou similar)
   - Bibliotecas para gráficos e visualizações

## Considerações de Segurança

1. **Autenticação e Autorização**
   - O sistema utiliza autenticação para controlar o acesso
   - Diferentes níveis de permissão para diferentes tipos de usuários

2. **Dados Sensíveis**
   - Credenciais armazenadas em arquivos seguros
   - Variáveis de ambiente para configurações sensíveis

3. **Comunicação Segura**
   - HTTPS para comunicação entre frontend e backend
   - Tokens para autenticação de API

## Processos de Manutenção

1. **Backup**
   - Backup regular do banco de dados
   - Backup dos arquivos de configuração

2. **Monitoramento**
   - Logs de atividade
   - Alertas para erros críticos

3. **Atualizações**
   - Processo para atualização de dependências
   - Testes antes de implantar atualizações

## Conclusão

Este documento fornece uma visão detalhada da arquitetura e componentes do sistema. Para informações mais específicas sobre cada componente, consulte a documentação técnica correspondente ou o código-fonte.
