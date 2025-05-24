# Guia de CI/CD

Este documento descreve como implementar e utilizar o pipeline de CI/CD configurado para o Projeto Wondercom Automation.

## Estrutura de Arquivos

Os arquivos de configuração do CI/CD estão localizados no diretório `.github/workflows/` do repositório:

- `ci-cd-pipeline.yml`: Pipeline principal de CI/CD
- `quality-check.yml`: Verificação de qualidade de código
- `rollback.yml`: Estratégia de rollback

## Configuração Inicial

Para configurar o CI/CD no GitHub, os arquivos de workflow já foram adicionados ao repositório no diretório `.github/workflows/`.

É necessário configurar os seguintes secrets no GitHub:

1. Acesse as configurações do repositório
2. Vá para "Secrets and variables" > "Actions"
3. Adicione os seguintes secrets:
   - `RENDER_API_KEY`: Chave de API do Render.com
   - `RENDER_SERVICE_ID`: ID do serviço no Render.com
   - `NETLIFY_AUTH_TOKEN`: Token de autenticação do Netlify
   - `NETLIFY_SITE_ID`: ID do site no Netlify
   - `SLACK_WEBHOOK`: URL do webhook do Slack para notificações

## Uso do Pipeline

### Pipeline Principal

O pipeline principal é executado automaticamente em:
- Push para a branch `master`
- Pull requests para a branch `master`

Ele realiza:
1. Testes do backend
2. Testes do frontend
3. Deploy automático para produção (apenas na branch `master`)

### Verificação de Qualidade

A verificação de qualidade é executada em todos os pull requests e verifica:
- Formatação de código
- Linting
- Segurança
- Tipos (TypeScript/Python)

### Rollback

Para realizar um rollback:

1. Acesse a aba "Actions" no GitHub
2. Selecione o workflow "Rollback Strategy"
3. Clique em "Run workflow"
4. Informe:
   - Versão para rollback (hash do commit ou tag)
   - Serviço a ser revertido (backend, frontend ou ambos)
5. Clique em "Run workflow"

## Boas Práticas

1. **Commits Semânticos**
   - Use prefixos como `feat:`, `fix:`, `refactor:`, etc.
   - Exemplo: `feat: Adiciona autenticação via Google`

2. **Pull Requests**
   - Use títulos descritivos
   - Inclua descrição detalhada das mudanças
   - Aguarde a aprovação antes do merge

3. **Testes**
   - Garanta que todos os testes passem antes do merge
   - Adicione novos testes para novas funcionalidades

## Troubleshooting

### Falha no Deploy

Se o deploy falhar:
1. Verifique os logs na aba "Actions"
2. Corrija os problemas identificados
3. Faça um novo commit ou execute o workflow manualmente

### Rollback Falhou

Se o rollback falhar:
1. Verifique se a versão especificada existe
2. Confirme que os secrets estão configurados corretamente
3. Tente um rollback manual diretamente no Render/Netlify
