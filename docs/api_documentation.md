# Documentação da API

## Introdução

Este documento descreve os endpoints da API REST do backend do Projeto-Geral, incluindo parâmetros, formatos de requisição e resposta, e códigos de status.

## Base URL

```
https://api.projeto-geral.render.com
```

## Autenticação

A API utiliza autenticação baseada em token JWT. Para acessar endpoints protegidos:

1. Obtenha um token através do endpoint de login
2. Inclua o token no cabeçalho de todas as requisições subsequentes:

```
Authorization: Bearer {seu_token_jwt}
```

## Endpoints

### Autenticação

#### Login

```
POST /auth/login
```

**Requisição:**
```json
{
  "email": "usuario@exemplo.com",
  "senha": "senha_segura"
}
```

**Resposta (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "usuario": {
    "id": 1,
    "nome": "Nome do Usuário",
    "email": "usuario@exemplo.com",
    "perfil": "tecnico"
  }
}
```

**Códigos de Erro:**
- 401 Unauthorized: Credenciais inválidas
- 422 Unprocessable Entity: Dados de requisição inválidos

### Dados de PDFs

#### Listar PDFs Processados

```
GET /pdfs
```

**Parâmetros de Query:**
- `tecnico_id` (opcional): Filtrar por ID do técnico
- `status` (opcional): Filtrar por status (processado, erro)
- `data_inicio` (opcional): Filtrar por data inicial (formato: YYYY-MM-DD)
- `data_fim` (opcional): Filtrar por data final (formato: YYYY-MM-DD)
- `page` (opcional): Número da página para paginação (padrão: 1)
- `per_page` (opcional): Itens por página (padrão: 20)

**Resposta (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "nome_arquivo": "relatorio_20220315.pdf",
      "tecnico_id": 2,
      "tecnico_nome": "João Silva",
      "data_processamento": "2022-03-16T14:30:45",
      "status": "processado",
      "dados_extraidos": {
        "cliente": "Empresa ABC",
        "data_visita": "2022-03-15",
        "tipo_servico": "Manutenção Preventiva",
        "equipamentos": [
          {
            "modelo": "XYZ-1000",
            "serial": "SN12345",
            "status": "Operacional"
          }
        ]
      }
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total_items": 145,
    "total_pages": 8
  }
}
```

#### Obter PDF Específico

```
GET /pdfs/{id}
```

**Resposta (200 OK):**
```json
{
  "id": 1,
  "nome_arquivo": "relatorio_20220315.pdf",
  "tecnico_id": 2,
  "tecnico_nome": "João Silva",
  "data_processamento": "2022-03-16T14:30:45",
  "status": "processado",
  "dados_extraidos": {
    "cliente": "Empresa ABC",
    "data_visita": "2022-03-15",
    "tipo_servico": "Manutenção Preventiva",
    "equipamentos": [
      {
        "modelo": "XYZ-1000",
        "serial": "SN12345",
        "status": "Operacional"
      }
    ]
  },
  "historico_processamento": [
    {
      "timestamp": "2022-03-16T14:30:40",
      "evento": "iniciado"
    },
    {
      "timestamp": "2022-03-16T14:30:45",
      "evento": "concluido"
    }
  ]
}
```

**Códigos de Erro:**
- 404 Not Found: PDF não encontrado

#### Reprocessar PDF

```
POST /pdfs/{id}/reprocessar
```

**Resposta (202 Accepted):**
```json
{
  "message": "Reprocessamento iniciado",
  "job_id": "abc123"
}
```

**Códigos de Erro:**
- 404 Not Found: PDF não encontrado
- 409 Conflict: PDF já está sendo processado

### Técnicos

#### Listar Técnicos

```
GET /tecnicos
```

**Parâmetros de Query:**
- `ativo` (opcional): Filtrar por status ativo (true/false)
- `page` (opcional): Número da página para paginação (padrão: 1)
- `per_page` (opcional): Itens por página (padrão: 20)

**Resposta (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "nome": "João Silva",
      "email": "joao.silva@exemplo.com",
      "ativo": true,
      "total_relatorios": 45,
      "ultimo_relatorio": "2022-03-16T14:30:45"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total_items": 8,
    "total_pages": 1
  }
}
```

#### Obter Técnico Específico

```
GET /tecnicos/{id}
```

**Resposta (200 OK):**
```json
{
  "id": 1,
  "nome": "João Silva",
  "email": "joao.silva@exemplo.com",
  "telefone": "+5511999999999",
  "ativo": true,
  "data_cadastro": "2022-01-10T09:00:00",
  "configuracoes": {
    "notificacoes_email": true,
    "notificacoes_sms": false
  },
  "estatisticas": {
    "total_relatorios": 45,
    "relatorios_ultimo_mes": 12,
    "taxa_sucesso": 0.98
  }
}
```

**Códigos de Erro:**
- 404 Not Found: Técnico não encontrado

#### Criar Técnico

```
POST /tecnicos
```

**Requisição:**
```json
{
  "nome": "Novo Técnico",
  "email": "novo.tecnico@exemplo.com",
  "telefone": "+5511999999999",
  "senha": "senha_segura",
  "configuracoes": {
    "notificacoes_email": true,
    "notificacoes_sms": false
  }
}
```

**Resposta (201 Created):**
```json
{
  "id": 9,
  "nome": "Novo Técnico",
  "email": "novo.tecnico@exemplo.com",
  "telefone": "+5511999999999",
  "ativo": true,
  "data_cadastro": "2022-04-01T10:15:30",
  "configuracoes": {
    "notificacoes_email": true,
    "notificacoes_sms": false
  }
}
```

**Códigos de Erro:**
- 400 Bad Request: Dados inválidos
- 409 Conflict: Email já cadastrado

#### Atualizar Técnico

```
PUT /tecnicos/{id}
```

**Requisição:**
```json
{
  "nome": "Nome Atualizado",
  "telefone": "+5511888888888",
  "configuracoes": {
    "notificacoes_email": true,
    "notificacoes_sms": true
  }
}
```

**Resposta (200 OK):**
```json
{
  "id": 1,
  "nome": "Nome Atualizado",
  "email": "joao.silva@exemplo.com",
  "telefone": "+5511888888888",
  "ativo": true,
  "data_cadastro": "2022-01-10T09:00:00",
  "configuracoes": {
    "notificacoes_email": true,
    "notificacoes_sms": true
  }
}
```

**Códigos de Erro:**
- 400 Bad Request: Dados inválidos
- 404 Not Found: Técnico não encontrado

### Dashboard

#### Obter Estatísticas Gerais

```
GET /dashboard/estatisticas
```

**Parâmetros de Query:**
- `periodo` (opcional): Período de análise (dia, semana, mes, ano) - padrão: mes
- `data_inicio` (opcional): Data inicial para filtro (formato: YYYY-MM-DD)
- `data_fim` (opcional): Data final para filtro (formato: YYYY-MM-DD)

**Resposta (200 OK):**
```json
{
  "periodo": {
    "inicio": "2022-03-01",
    "fim": "2022-03-31"
  },
  "total_relatorios": 145,
  "relatorios_processados": 142,
  "relatorios_com_erro": 3,
  "taxa_sucesso": 0.979,
  "tempo_medio_processamento": 12.5,
  "por_tecnico": [
    {
      "tecnico_id": 1,
      "tecnico_nome": "João Silva",
      "total_relatorios": 45,
      "taxa_sucesso": 0.98
    },
    {
      "tecnico_id": 2,
      "tecnico_nome": "Maria Oliveira",
      "total_relatorios": 38,
      "taxa_sucesso": 1.0
    }
  ]
}
```

## Códigos de Status

- 200 OK: Requisição bem-sucedida
- 201 Created: Recurso criado com sucesso
- 202 Accepted: Requisição aceita para processamento assíncrono
- 400 Bad Request: Parâmetros inválidos ou ausentes
- 401 Unauthorized: Autenticação necessária ou inválida
- 403 Forbidden: Sem permissão para acessar o recurso
- 404 Not Found: Recurso não encontrado
- 409 Conflict: Conflito com o estado atual do recurso
- 422 Unprocessable Entity: Dados de requisição semanticamente inválidos
- 429 Too Many Requests: Limite de taxa excedido
- 500 Internal Server Error: Erro interno do servidor

## Limites de Taxa

A API possui os seguintes limites de requisições:

- Endpoints públicos: 60 requisições por minuto por IP
- Endpoints autenticados: 300 requisições por minuto por usuário

Ao exceder esses limites, a API retornará o código de status 429 Too Many Requests.

## Versionamento

O versionamento da API é feito através do cabeçalho HTTP:

```
Accept: application/vnd.projeto-geral.v1+json
```

A versão atual é v1. Futuras versões serão anunciadas com antecedência.

## Suporte

Para suporte relacionado à API, entre em contato com a equipe de desenvolvimento.
