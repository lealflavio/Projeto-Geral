from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from .database import engine, Base
from .routes import auth as auth_routes
from .routes import dashboard as dashboard_routes
from .routes import usuarios as usuarios_routes
# Importar o novo router FastAPI em vez do Flask
# Certifique-se de que o arquivo wondercom_fastapi.py esteja no diretório routes
from .routes.wondercom_fastapi import router as wondercom_router

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
app.include_router(wondercom_router)  # Usar o router FastAPI do Wondercom

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bem-vindo à API do Dashboard Wondercom!"}
