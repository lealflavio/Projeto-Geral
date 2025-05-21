from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routes import auth as auth_routes
from .routes import dashboard as dashboard_routes
from app.routes import auth, usuarios

app = FastAPI(
    title="Wondercom Dashboard API",
    description="API para o sistema de dashboard da Wondercom, incluindo autenticação, gestão de créditos, KPIs e simulador de ganhos.",
    version="0.1.0"
)
app.include_router(auth.router)
app.include_router(usuarios.router)

# Create all tables in the database.
# This is useful for development but for production, you might want to use migrations (e.g., Alembic).
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Em produção, troque "*" por ["http://seu-front-url"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router) # Now including dashboard routes

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bem-vindo à API do Dashboard Wondercom!"}

# Placeholder for dashboard routes - to be created in app/routes/dashboard.py
# For now, the file ~/Sistema/dashboard/backend/app/routes/dashboard.py is empty.
# We will populate it in later stages (Etapa 5, 6, 7).

