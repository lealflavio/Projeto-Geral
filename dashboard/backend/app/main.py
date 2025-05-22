from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routes import auth as auth_routes
from .routes import dashboard as dashboard_routes
from .routes import usuarios as usuarios_routes

# Instancia o app FastAPI com metadados
app = FastAPI(
    title="Wondercom Dashboard API",
    description=(
        "API para o sistema de dashboard da Wondercom, incluindo autenticação, "
        "gestão de créditos, KPIs e simulador de ganhos."
    ),
    version="0.1.0"
)

# Configuração de CORS: só permite seu frontend em produção!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://zincoapp.pt"],  # Permite apenas seu domínio!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui os routers do sistema
app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(usuarios_routes.router, prefix="/usuarios", tags=["usuarios"])

# Cria as tabelas do banco de dados (somente para desenvolvimento)
# Em produção, use um sistema de migrations como Alembic
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Endpoint raiz
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bem-vindo à API do Dashboard Wondercom!"}
