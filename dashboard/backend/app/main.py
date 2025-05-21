from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routes import auth as auth_routes
from .routes import dashboard as dashboard_routes
from app.routes import auth, usuarios

# Instancia o app FastAPI com metadados
app = FastAPI(
    title="Wondercom Dashboard API",
    description=(
        "API para o sistema de dashboard da Wondercom, incluindo autenticação, "
        "gestão de créditos, KPIs e simulador de ganhos."
    ),
    version="0.1.0"
)

# Configura o CORS (boas práticas: restringir em produção)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Em produção, troque "*" pelo endereço do seu frontend ex: ["https://seu-front.netlify.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui os routers do sistema
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(usuarios.router, prefix="/usuarios", tags=["usuarios"])
app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router)

# Cria as tabelas do banco de dados (somente para desenvolvimento)
# Em produção, use um sistema de migrations como Alembic
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Endpoint raiz
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bem-vindo à API do Dashboard Wondercom!"}
