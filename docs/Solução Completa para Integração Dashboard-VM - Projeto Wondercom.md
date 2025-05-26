# Solução Completa para Integração Dashboard-VM - Projeto Wondercom

## Problemas Identificados e Soluções

### 1. Erro CORS (Cross-Origin Resource Sharing)

**Problema:**
Ao tentar alocar uma WO através da interface React, ocorria um erro de CORS:
```
Ensure CORS response header values are valid
A cross-origin resource sharing (CORS) request was blocked because of invalid or missing response headers
```

**Causa:**
A configuração CORS no backend FastAPI estava restrita apenas ao domínio `https://zincoapp.pt`, bloqueando requisições de outros domínios.

**Solução:**
Atualizar a configuração CORS para incluir todos os domínios necessários, incluindo ambientes de desenvolvimento, homologação e produção.

### 2. Erro 404 na Rota de Alocação de WO

**Problema:**
Após corrigir o erro CORS, a requisição para `/api/wondercom/allocate` retornava 404 Not Found:
```
INFO:     34.88.3.237:0 - "POST /api/wondercom/allocate HTTP/1.1" 404 Not Found
```

**Causa:**
O router das rotas Wondercom não estava sendo incluído no app principal FastAPI.

### 3. Conflito de Frameworks (Flask vs FastAPI)

**Problema:**
Ao tentar incluir o router Wondercom no app FastAPI, ocorria um erro de importação:
```
ImportError: cannot import name 'url_quote' from 'werkzeug.urls'
```

**Causa:**
O módulo de rotas Wondercom estava implementado em Flask (usando Blueprint), enquanto o app principal utilizava FastAPI, causando incompatibilidade entre frameworks.

**Solução:**
Reimplementar as rotas Wondercom usando FastAPI em vez de Flask, mantendo a mesma funcionalidade mas com a sintaxe e os decoradores do FastAPI.

## Implementação da Solução Completa

### 1. Configuração CORS Atualizada

```python
# Configuração de domínios permitidos para CORS
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Conversão das Rotas Wondercom de Flask para FastAPI

O arquivo original `routes/wondercom.py` usava Flask:

```python
from flask import Blueprint, request, jsonify
# ...

wondercom_bp = Blueprint('wondercom', __name__)

@wondercom_bp.route('/api/wondercom/allocate', methods=['POST'])
@jwt_required()
def allocate_work_order():
    # ...
```

Convertido para FastAPI em `routes/wondercom_fastapi.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
# ...

router = APIRouter(tags=["Wondercom"])

@router.post("/api/wondercom/allocate")
async def allocate_work_order(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    # ...
```

### 3. Inclusão do Router no App Principal

```python
from .routes import auth as auth_routes
from .routes import dashboard as dashboard_routes
from .routes import usuarios as usuarios_routes
from .routes.wondercom_fastapi import router as wondercom_router  # Importação do novo router FastAPI

# ...

app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(usuarios_routes.router)
app.include_router(wondercom_router)  # Inclusão do router Wondercom
```

## Passos para Implementação

1. **Substituir o arquivo `main.py`**:
   - Substitua o conteúdo do arquivo `Projeto-Geral/dashboard/backend/app/main.py` pelo código do arquivo `main_py_final.py`

2. **Criar o novo arquivo de rotas FastAPI**:
   - Crie o arquivo `Projeto-Geral/dashboard/backend/app/routes/wondercom_fastapi.py` com o conteúdo do arquivo `wondercom_fastapi.py`

3. **Manter o arquivo original como referência**:
   - Mantenha o arquivo `routes/wondercom.py` original como referência, mas não o importe no `main.py`

4. **Reiniciar o servidor backend**:
   - Reinicie o servidor backend para aplicar as alterações

5. **Testar a integração**:
   - Teste a integração com o frontend para confirmar que ambos os problemas foram resolvidos

## Principais Diferenças entre Flask e FastAPI

Para futuras manutenções, é importante entender as principais diferenças entre Flask e FastAPI que foram consideradas na conversão:

1. **Definição de rotas**:
   - Flask: `@app.route('/path', methods=['GET'])`
   - FastAPI: `@app.get("/path")` ou `@router.get("/path")`

2. **Obtenção de dados da requisição**:
   - Flask: `request.get_json()`
   - FastAPI: `await request.json()` (assíncrono)

3. **Retorno de respostas**:
   - Flask: `return jsonify(data), 200`
   - FastAPI: `return data` (status 200 implícito) ou `raise HTTPException(status_code=400, detail="Erro")`

4. **Autenticação**:
   - Flask: `@jwt_required()`
   - FastAPI: `current_user: User = Depends(get_current_user)`

5. **Organização**:
   - Flask: `Blueprint`
   - FastAPI: `APIRouter`

## Verificações Adicionais

Se após a implementação da solução ainda houver problemas, verifique:

1. **Dependências do FastAPI**:
   - Certifique-se de que todas as dependências necessárias estão instaladas: `fastapi`, `uvicorn`, etc.

2. **Compatibilidade de autenticação**:
   - Verifique se a função `get_current_user` está implementada corretamente para FastAPI

3. **Logs do servidor**:
   - Monitore os logs do servidor para identificar possíveis erros durante a inicialização ou processamento de requisições

4. **Versões das bibliotecas**:
   - Verifique se há conflitos de versão entre as bibliotecas instaladas

## Recomendações para Produção

1. **Padronização de frameworks**:
   - Padronize o uso de frameworks em todo o projeto, evitando misturar Flask e FastAPI
   - Se possível, migre gradualmente todo o código Flask para FastAPI

2. **Gerenciamento de dependências**:
   - Mantenha um arquivo `requirements.txt` atualizado com versões específicas das dependências
   - Considere usar ambientes virtuais isolados para desenvolvimento e produção

3. **Monitoramento**:
   - Configure alertas para erros 404, 500 e CORS nos logs do servidor
   - Implemente health checks para verificar o status dos serviços

4. **Testes automatizados**:
   - Implemente testes que validem a integração entre frontend e backend
   - Adicione testes específicos para verificar a configuração CORS

5. **Documentação**:
   - Mantenha a documentação da API atualizada, incluindo informações sobre as rotas disponíveis e seus parâmetros
   - Documente claramente qual framework está sendo usado em cada parte do sistema

## Referências

- [Documentação FastAPI](https://fastapi.tiangolo.com/)
- [Documentação FastAPI Routers](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Documentação FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [Migrando de Flask para FastAPI](https://fastapi.tiangolo.com/project-generation/#flask-users)
- [MDN Web Docs: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
