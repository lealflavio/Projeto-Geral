# Projeto-Geral

![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)
![Versão](https://img.shields.io/badge/versão-1.0.0-blue)
![Licença](https://img.shields.io/badge/licença-MIT-green)

## Visão Geral

O Projeto-Geral é um sistema integrado para extração, processamento e visualização de dados de relatórios técnicos em formato PDF. O sistema automatiza o fluxo de trabalho desde a coleta dos PDFs até a apresentação de KPIs em dashboards interativos.

O projeto é composto por três pilares principais:

1. **Scripts de Automação (VM/Selenium)** - Responsáveis pela extração de dados de PDFs e automação de processos
2. **Backend (Render)** - API REST e banco de dados para armazenamento e disponibilização dos dados
3. **Frontend (Netlify)** - Interface de usuário para visualização de KPIs e outras funcionalidades

## Arquitetura

![Arquitetura do Sistema](docs/diagramas/diagrama_arquitetura.md)

### Fluxo de Dados

1. Os técnicos geram PDFs contendo relatórios de trabalho
2. Os PDFs são armazenados no Google Drive
3. Os scripts de automação acessam o Drive e baixam os PDFs
4. Os dados são extraídos, processados e validados
5. Os dados processados são enviados para o backend via API
6. O frontend consome a API do backend para exibir os dados em dashboards

Para mais detalhes sobre o fluxo de dados, consulte [este diagrama](docs/diagramas/diagrama_fluxo_dados.md).

## Componentes Principais

### Scripts de Automação (VM)

Módulos principais localizados na raiz do projeto:

- **M1_Extrator_PDF.py** - Extrai dados de arquivos PDF
- **M2_Orquestrador_PDFs.py** - Gerencia o fluxo de processamento de PDFs
- **M3_Leitura_Drive.py** - Integração com Google Drive
- **M4_Manipulacao_Arquivos.py** - Manipulação de arquivos locais
- **M5_Config_Tecnicos.py** - Gerencia configurações específicas para cada técnico
- **M6_Notificacao_Status.py** - Envia notificações sobre o status do processamento

### Backend (Render)

Localizado em `/dashboard/backend`:

- API REST desenvolvida em Flask
- Banco de dados para armazenamento dos dados extraídos
- Sistema de autenticação e autorização

### Frontend (Netlify)

Localizado em `/dashboard/frontend`:

- Interface de usuário desenvolvida em React
- Dashboards para visualização de KPIs
- Painéis de controle para técnicos e administradores

## Instalação e Configuração

### Pré-requisitos

- Python 3.8+
- Node.js 14+
- Acesso ao Google Drive API
- Conta no Render (para backend)
- Conta no Netlify (para frontend)

### Configuração do Ambiente

1. Clone o repositório:
   ```bash
   git clone https://github.com/lealflavio/Projeto-Geral.git
   cd Projeto-Geral
   ```

2. Configure o ambiente para os scripts de automação:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure as credenciais do Google Drive:
   - Coloque o arquivo `chave_servico_primaria.json` na raiz do projeto
   - Ou configure o caminho no sistema centralizado de configurações

4. Configure o backend:
   ```bash
   cd dashboard/backend
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. Configure o frontend:
   ```bash
   cd dashboard/frontend
   npm install
   ```

### Sistema Centralizado de Configurações

O projeto utiliza um sistema centralizado de configurações que unifica todas as configurações em um único local. Para mais detalhes, consulte o [Guia de Migração para o Sistema Centralizado de Configurações](docs/migracao_configuracoes.md).

## Uso

### Scripts de Automação

Para iniciar o processamento de PDFs:

```bash
python M2_Orquestrador_PDFs.py
```

### Backend

Para iniciar o servidor de desenvolvimento:

```bash
cd dashboard/backend
python app/main.py
```

### Frontend

Para iniciar o servidor de desenvolvimento:

```bash
cd dashboard/frontend
npm run dev
```

## Estrutura de Diretórios

```
Projeto-Geral/
├── M1_Extrator_PDF.py
├── M2_Orquestrador_PDFs.py
├── M3_Leitura_Drive.py
├── M4_Manipulacao_Arquivos.py
├── M5_Config_Tecnicos.py
├── M6_Notificacao_Status.py
├── config/                  # Configurações centralizadas
├── docs/                    # Documentação
│   ├── diagramas/
│   ├── documentacao_detalhada.md
│   ├── mapeamento_estrutura.md
│   ├── migracao_configuracoes.md
│   ├── propostas_melhorias.md
│   └── scripts_monitoramento.md
├── extracao_dados/          # Dados extraídos dos PDFs
├── tecnicos/                # Dados organizados por técnico
│   ├── tecnico1/
│   │   ├── logs/
│   │   └── pdfs/
│   └── tecnico2/
│       ├── logs/
│       └── pdfs/
└── dashboard/
    ├── backend/             # API e banco de dados
    │   ├── app/
    │   └── flask_monitor/
    └── frontend/            # Interface de usuário
        ├── public/
        └── src/
```

Para uma descrição mais detalhada da estrutura, consulte o [Mapeamento da Estrutura do Projeto](docs/mapeamento_estrutura.md).

## Considerações Importantes

### Refatoração para Caminhos Relativos

O projeto está passando por uma refatoração para substituir caminhos absolutos por caminhos relativos, o que melhorará a portabilidade entre diferentes ambientes. Esta refatoração está sendo realizada pelo Agente 1.

### Sistema Centralizado de Configurações

Recentemente foi implementado um sistema centralizado de configurações (PR #2) que unifica todas as configurações em um único local. Todas as novas implementações devem utilizar este sistema em vez de arquivos de configuração separados.

## Documentação Adicional

- [Documentação Detalhada](docs/documentacao_detalhada.md)
- [Mapeamento da Estrutura](docs/mapeamento_estrutura.md)
- [Migração de Configurações](docs/migracao_configuracoes.md)
- [Propostas de Melhorias](docs/propostas_melhorias.md)
- [Scripts de Monitoramento](docs/scripts_monitoramento.md)

## Contribuição

Para contribuir com o projeto, consulte o guia de contribuição em [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.

## Contato

Para mais informações, entre em contato com a equipe de desenvolvimento.
