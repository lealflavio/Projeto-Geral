# Guia de Configuração de Ambientes

Este documento descreve como configurar e utilizar os diferentes ambientes para o Projeto Wondercom Automation.

## Estrutura de Ambientes

O projeto utiliza três ambientes distintos:

1. **Ambiente de Desenvolvimento**: Para desenvolvimento local
2. **Ambiente de Staging**: Para testes antes da produção
3. **Ambiente de Produção**: Para o sistema em produção (Render.com e Netlify.com)

## Ambiente de Desenvolvimento

### Pré-requisitos
- Docker e Docker Compose instalados
- Git configurado

### Configuração

1. Clone o repositório:
   ```bash
   git clone https://github.com/lealflavio/Projeto-Geral.git
   cd Projeto-Geral
   ```

2. Inicie o ambiente de desenvolvimento:
   ```bash
   cd devops/ambientes/desenvolvimento
   docker-compose up -d
   ```

3. Acesse os serviços:
   - Backend: http://localhost:8000
   - Frontend: http://localhost:3000
   - Banco de dados: localhost:5432

### Características
- Hot-reload para desenvolvimento rápido
- Banco de dados PostgreSQL local
- Volumes para persistência de dados

## Ambiente de Staging

### Configuração

1. Inicie o ambiente de staging:
   ```bash
   cd devops/ambientes/staging
   docker-compose up -d
   ```

2. Acesse os serviços:
   - Backend: http://localhost:8000
   - Frontend: http://localhost:3000
   - Banco de dados: localhost:5432

### Características
- Configuração próxima à produção
- Frontend em modo de produção
- Ambiente isolado para testes

## Ambiente de Produção

### Render.com (Backend)

A configuração do backend em produção utiliza o Render.com conforme detalhado em `producao/render-config.md`.

Principais pontos:
- Serviço web com auto-scaling
- Banco de dados PostgreSQL gerenciado
- Variáveis de ambiente seguras
- Deploy automático a partir da branch main

### Netlify.com (Frontend)

A configuração do frontend em produção utiliza o Netlify.com conforme detalhado em `producao/netlify-config.md`.

Principais pontos:
- Build e deploy automáticos
- CDN para entrega rápida
- Previews para pull requests
- Integração com GitHub

## Variáveis de Ambiente

### Desenvolvimento e Staging
As variáveis de ambiente estão definidas nos arquivos `docker-compose.yml` de cada ambiente.

### Produção
As variáveis de ambiente são configuradas nos dashboards do Render.com e Netlify.com.

## Boas Práticas

1. **Consistência entre Ambientes**
   - Mantenha as mesmas versões de dependências
   - Use Docker para garantir consistência
   - Documente diferenças específicas de cada ambiente

2. **Segurança**
   - Nunca armazene credenciais no código
   - Use variáveis de ambiente para configurações sensíveis
   - Utilize secrets para credenciais em produção

3. **Testes**
   - Teste completamente em staging antes de ir para produção
   - Verifique a integração entre todos os componentes
   - Valide fluxos de usuário completos

## Troubleshooting

### Problemas Comuns no Ambiente de Desenvolvimento

1. **Erro de conexão com o banco de dados**
   - Verifique se o container do PostgreSQL está rodando
   - Confirme as credenciais no arquivo docker-compose.yml
   - Verifique se a porta 5432 está disponível

2. **Frontend não conecta ao backend**
   - Confirme que a variável VITE_API_URL está correta
   - Verifique se o backend está rodando e acessível

### Problemas em Produção

1. **Falha no deploy**
   - Verifique os logs no dashboard do Render/Netlify
   - Confirme que todas as variáveis de ambiente estão configuradas
   - Verifique se o build está passando localmente
