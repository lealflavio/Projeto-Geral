# Correção de Erros na Integração Dashboard-VM - Projeto Wondercom

## Problemas Identificados e Soluções

### 1. Erro CORS (Cross-Origin Resource Sharing)

**Problema:**
Ao tentar alocar uma WO através da interface React, ocorria um erro de CORS:
```
Ensure CORS response header values are valid
A cross-origin resource sharing (CORS) request was blocked because of invalid or missing response headers
```

**Causa:**
A configuração CORS no backend FastAPI estava restrita apenas ao domínio `https://zincoapp.pt`, bloqueando requisições de outros domínios:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://zincoapp.pt"],  # Só permite seu domínio!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Solução:**
Atualizar a configuração CORS para incluir todos os domínios necessários:

```python
ALLOWED_ORIGINS = [
    # Domínios de produção identificados na documentação e código
    "https://zincoapp.pt",                      # Domínio original
    "https://dashboard-frontend.netlify.app",   # Frontend em testes/homologação
    "https://wondercom-automation.netlify.app", # Frontend em produção
    
    # Domínios de backend para callbacks
    "https://wondercom-automation-backend.onrender.com",
    "https://api.projeto-geral.render.com",
    
    # Domínios de desenvolvimento (opcional, remover em produção)
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Erro 404 na Rota de Alocação de WO

**Problema:**
Após corrigir o erro CORS, a requisição para `/api/wondercom/allocate` retornava 404 Not Found:
```
INFO:     34.88.3.237:0 - "POST /api/wondercom/allocate HTTP/1.1" 404 Not Found
```

**Causa:**
O router das rotas Wondercom não estava sendo incluído no app principal FastAPI. No arquivo `main.py`, apenas os routers auth, dashboard e usuarios estavam sendo registrados:

```python
app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(usuarios_routes.router)  # NÃO coloque prefix ou tags aqui!
```

**Solução:**
Adicionar a importação e inclusão do router Wondercom no app principal:

```python
from .routes import wondercom as wondercom_routes  # Importação adicionada

# ... código existente ...

app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(usuarios_routes.router)
app.include_router(wondercom_routes.router)  # Linha adicionada para incluir o router do Wondercom
```

## Implementação da Solução Completa

Para corrigir ambos os problemas, substitua o conteúdo do arquivo `Projeto-Geral/dashboard/backend/app/main.py` pelo código abaixo:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from .database import engine, Base
from .routes import auth as auth_routes
from .routes import dashboard as dashboard_routes
from .routes import usuarios as usuarios_routes
from .routes import wondercom as wondercom_routes  # Importação adicionada

# Configuração de domínios permitidos para CORS
# Em produção, especifique explicitamente todos os domínios necessários
ALLOWED_ORIGINS = [
    # Domínios de produção identificados na documentação e código
    "https://zincoapp.pt",                      # Domínio original
    "https://dashboard-frontend.netlify.app",   # Frontend em testes/homologação
    "https://wondercom-automation.netlify.app", # Frontend em produção
    
    # Domínios de backend para callbacks
    "https://wondercom-automation-backend.onrender.com",
    "https://api.projeto-geral.render.com",
    
    # Domínios de desenvolvimento (opcional, remover em produção)
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]

# Permitir configuração via variável de ambiente (opcional)
if os.getenv("ADDITIONAL_CORS_ORIGINS"):
    additional_origins = os.getenv("ADDITIONAL_CORS_ORIGINS").split(",")
    ALLOWED_ORIGINS.extend([origin.strip() for origin in additional_origins])

app = FastAPI(
    title="Wondercom Dashboard API",
    description=(
        "API para o sistema de dashboard da Wondercom, incluindo autenticação, "
        "gestão de créditos, KPIs e simulador de ganhos."
    ),
    version="0.1.0"
)

# Configuração CORS atualizada para incluir todos os domínios necessários
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(usuarios_routes.router)
app.include_router(wondercom_routes.router)  # Linha adicionada para incluir o router do Wondercom

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bem-vindo à API do Dashboard Wondercom!"}
```

## Passos para Implementação

1. Verifique se o arquivo `routes/wondercom.py` existe e contém a definição do router e das rotas necessárias
2. Substitua o conteúdo do arquivo `app/main.py` pelo código acima
3. Reinicie o servidor backend
4. Teste a integração com o frontend para confirmar que ambos os problemas foram resolvidos

## Verificações Adicionais

Se após a implementação da solução ainda houver problemas, verifique:

1. **Estrutura do router Wondercom**: Confirme que o arquivo `routes/wondercom.py` define corretamente um router FastAPI com a rota `/api/wondercom/allocate`
2. **Logs do servidor**: Monitore os logs do servidor para identificar possíveis erros durante a inicialização ou processamento de requisições
3. **Chamadas do frontend**: Verifique se o frontend está chamando a URL correta, incluindo o prefixo `/api/wondercom/allocate`
4. **Configuração de proxy**: Se estiver usando um proxy reverso, confirme que ele está configurado para encaminhar corretamente as requisições para o backend

## Recomendações para Produção

1. **Monitoramento**: Configure alertas para erros 404 e CORS nos logs do servidor
2. **Testes automatizados**: Implemente testes que validem a integração entre frontend e backend
3. **Documentação**: Mantenha a documentação da API atualizada, incluindo informações sobre as rotas disponíveis e seus parâmetros

## Referências

- [Documentação FastAPI Routers](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Documentação FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [MDN Web Docs: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
