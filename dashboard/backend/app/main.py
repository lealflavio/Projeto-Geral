from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routes import auth as auth_routes
from .routes import dashboard as dashboard_routes
from .routes import usuarios as usuarios_routes
from .routes import wondercom as wondercom_routes
from .routes import creditos as creditos_routes

app = FastAPI(
    title="Wondercom Dashboard API",
    description=(
        "API para o sistema de dashboard da Wondercom, incluindo autenticação, "
        "gestão de créditos, KPIs e simulador de ganhos."
    ),
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://zincoapp.pt"],  # Só permite seu domínio!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(usuarios_routes.router)  # NÃO coloque prefix ou tags aqui!
app.include_router(wondercom_routes.router)
app.include_router(creditos_routes.router)  # Nova rota para sistema de créditos

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bem-vindo à API do Dashboard Wondercom!"}
