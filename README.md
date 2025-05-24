# Projeto-Geral

Sistema integrado para automação de processamento de relatórios técnicos em PDF, com extração de dados, armazenamento e visualização em dashboards.

## Visão Geral

O Projeto-Geral é uma solução completa para automatizar o fluxo de trabalho de processamento de relatórios técnicos em formato PDF. O sistema extrai dados relevantes dos documentos, armazena-os em um banco de dados estruturado e disponibiliza visualizações através de dashboards interativos.

### Componentes Principais

O projeto é composto por três componentes principais:

1. **Scripts de Automação (VM/Selenium)**
   - Extração automatizada de dados de relatórios técnicos em formato PDF
   - Processamento e normalização dos dados extraídos
   - Integração com Google Drive para obtenção de novos relatórios

2. **Backend (Render)**
   - API REST para armazenamento e recuperação de dados extraídos
   - Autenticação e autorização de usuários
   - Processamento de regras de negócio

3. **Frontend (Netlify)**
   - Interface de usuário para visualização de KPIs e dashboards
   - Filtros e configurações personalizáveis
   - Exportação de relatórios e visualizações

## Arquitetura

![Arquitetura do Sistema](docs/images/arquitetura.png)

A arquitetura do sistema segue um modelo de três camadas:

1. **Camada de Extração**: Scripts Python que utilizam Selenium e PyPDF para extrair dados de relatórios técnicos.
2. **Camada de API**: Backend Flask que fornece endpoints RESTful para armazenamento e recuperação de dados.
3. **Camada de Apresentação**: Frontend React que consome a API e apresenta dashboards interativos.

## Instalação e Configuração

### Pré-requisitos

- Python 3.8+
- Node.js 14+
- PostgreSQL 12+
- Google Chrome (para Selenium)

### Configuração do Ambiente

1. Clone o repositório:
   ```bash
   git clone https://github.com/lealflavio/Projeto-Geral.git
   cd Projeto-Geral
   ```

2. Configure o sistema centralizado de configurações:
   ```bash
   cp config/config.example.json config/config.json
   # Edite config/config.json com suas configurações
   ```

3. Instale as dependências:
   ```bash
   # Para os scripts de automação
   pip install -r requirements.txt
   
   # Para o backend
   cd dashboard/backend
   pip install -r requirements.txt
   
   # Para o frontend
   cd dashboard/frontend
   npm install
   ```

4. Configure o banco de dados:
   ```bash
   cd dashboard/backend
   python create_tables.py
   ```

## Uso

### Extração de Dados

Para iniciar o processo de extração de dados de PDFs:

```bash
python M2_Orquestrador_PDFs.py
```

Este script coordena o processo de extração, utilizando o `M1_Extrator_PDF.py` para processar cada documento.

### Execução do Backend

Para iniciar o servidor backend:

```bash
cd dashboard/backend
python app.py
```

O servidor estará disponível em `http://localhost:5000`.

### Execução do Frontend

Para iniciar o servidor de desenvolvimento do frontend:

```bash
cd dashboard/frontend
npm start
```

O frontend estará disponível em `http://localhost:3000`.

## Monitoramento e Manutenção

O projeto inclui scripts de monitoramento e manutenção para garantir a saúde e confiabilidade do sistema:

```bash
# Verificar saúde do sistema
python scripts/monitoramento/system_health.py

# Realizar backup automático
python scripts/monitoramento/backup.py

# Monitorar logs
python scripts/monitoramento/log_monitor.py
```

## Estrutura do Projeto

```
Projeto-Geral/
├── config/                  # Configurações centralizadas
│   ├── config.py            # Sistema de configuração
│   └── path_utils.py        # Utilitários para caminhos relativos
├── dashboard/
│   ├── backend/             # API REST (Flask)
│   │   ├── app/
│   │   │   ├── models/      # Modelos de dados
│   │   │   ├── routes/      # Endpoints da API
│   │   │   └── services/    # Lógica de negócio
│   │   └── app.py           # Ponto de entrada do backend
│   └── frontend/            # Interface de usuário (React)
│       ├── public/
│       ├── src/
│       │   ├── components/  # Componentes React
│       │   ├── pages/       # Páginas da aplicação
│       │   └── services/    # Serviços de API
│       └── package.json
├── docs/                    # Documentação detalhada
├── extracao_dados/          # Dados extraídos dos PDFs
├── scripts/
│   └── monitoramento/       # Scripts de monitoramento
├── tecnicos/                # Configurações de técnicos
├── tests/                   # Testes automatizados
├── M1_Extrator_PDF.py       # Extração de dados de PDFs
├── M2_Orquestrador_PDFs.py  # Coordenação do processamento
├── M3_Leitura_Drive.py      # Acesso ao Google Drive
├── M4_Manipulacao_Arquivos.py # Manipulação de arquivos PDF
└── M5_Config_Tecnicos.py    # Configuração de técnicos
```

## Fluxo de Dados

1. Novos relatórios técnicos em PDF são obtidos do Google Drive (`M3_Leitura_Drive.py`)
2. O orquestrador (`M2_Orquestrador_PDFs.py`) coordena o processamento dos PDFs
3. O extrator (`M1_Extrator_PDF.py`) extrai dados relevantes de cada PDF
4. Os dados extraídos são armazenados no banco de dados através da API backend
5. O frontend consome a API para apresentar dashboards e visualizações
6. Os scripts de monitoramento verificam a saúde do sistema e geram alertas quando necessário

## Contribuição

### Fluxo de Trabalho

1. Crie um branch a partir do `master` para sua feature ou correção:
   ```bash
   git checkout -b feature/nome-da-feature
   ```

2. Faça suas alterações seguindo as convenções de código do projeto

3. Execute os testes para garantir que não há regressões:
   ```bash
   pytest
   ```

4. Envie um Pull Request para o branch `master`

### Convenções de Código

- Python: Seguimos o PEP 8 e utilizamos Black para formatação
- JavaScript: Seguimos o Airbnb Style Guide e utilizamos ESLint
- Commits: Utilizamos mensagens de commit semânticas (feat, fix, docs, etc.)

## Troubleshooting

### Problemas Comuns

#### Erro de conexão com o banco de dados

**Sintoma**: Mensagem de erro "Could not connect to database"

**Solução**: 
1. Verifique se o PostgreSQL está em execução
2. Confirme as credenciais em `config/config.json`
3. Verifique se o banco de dados existe

#### Falha na extração de dados de PDFs

**Sintoma**: O extrator não consegue processar determinados PDFs

**Solução**:
1. Verifique se o Chrome está instalado e atualizado
2. Confirme que o ChromeDriver está na versão compatível
3. Verifique se o PDF está corrompido ou protegido

#### Frontend não consegue se conectar ao backend

**Sintoma**: Mensagens de erro CORS ou falha de conexão

**Solução**:
1. Verifique se o backend está em execução
2. Confirme a URL da API em `dashboard/frontend/src/services/api.js`
3. Verifique se o CORS está configurado corretamente no backend

## Licença

Este projeto é proprietário e confidencial. Todos os direitos reservados.

## Contato

Para questões relacionadas ao projeto, entre em contato com a equipe de desenvolvimento.

---

Documentação atualizada em: Maio de 2025
