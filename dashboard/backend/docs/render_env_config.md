# Configuração de Variáveis de Ambiente no Render.com

Este documento contém instruções detalhadas para configurar as variáveis de ambiente necessárias para o backend do Projeto Wondercom Automation no Render.com.

## Variáveis de Ambiente Obrigatórias

| Variável | Descrição | Valor Recomendado |
|----------|-----------|-------------------|
| `DATABASE_URL` | URL de conexão com o banco de dados PostgreSQL | `postgresql://postgres:${DB_PASSWORD}@${DB_HOST}:5432/${DB_NAME}` |
| `SECRET_KEY` | Chave secreta para tokens JWT (deve ser longa e aleatória) | Gerar com `openssl rand -hex 32` |
| `ALGORITHM` | Algoritmo de criptografia para JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Tempo de expiração do token JWT | `1440` (24 horas) |
| `FRONTEND_URL` | URL do frontend para CORS | `https://wondercom-dashboard.netlify.app` |

## Variáveis para Integração com Google Drive

| Variável | Descrição | Valor |
|----------|-----------|-------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Caminho para o arquivo de credenciais | `/etc/secrets/google-credentials.json` |
| `GOOGLE_DRIVE_BASE_FOLDER` | ID da pasta raiz no Google Drive | `1TNTB2QBYBM94LU_52Cjqx69FeWHomY8G` |

## Passos para Configuração no Render.com

1. Acesse o [Dashboard do Render](https://dashboard.render.com/)
2. Selecione o serviço Web do backend Wondercom
3. Navegue até a aba "Environment"
4. Para cada variável na tabela acima:
   - Clique em "Add Environment Variable"
   - Insira o nome da variável e seu valor
   - Marque "Secret" para valores sensíveis

### Configuração do Arquivo de Credenciais do Google

Para o arquivo de credenciais do Google Service Account:

1. Na aba "Environment", role até "Secret Files"
2. Clique em "Add Secret File"
3. Configure:
   - **Filename**: `/etc/secrets/google-credentials.json`
   - **Contents**: Cole o conteúdo do arquivo JSON de credenciais do Google Service Account

## Verificação da Configuração

Após configurar todas as variáveis:

1. Clique em "Save Changes"
2. Aguarde o redeploy automático do serviço
3. Verifique os logs para confirmar que o serviço iniciou corretamente
4. Teste a API com endpoints básicos como `/api/health` ou `/api/drive/setup`

## Observações de Segurança

- Nunca compartilhe valores de variáveis secretas em repositórios ou comunicações não seguras
- Utilize senhas fortes e chaves secretas longas e aleatórias
- Restrinja as permissões do Service Account do Google apenas ao necessário
- Considere rotacionar periodicamente as credenciais e chaves secretas

## Suporte

Em caso de problemas com a configuração, entre em contato com o time de DevOps ou abra um ticket no sistema interno de suporte.
