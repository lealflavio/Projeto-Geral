from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração para ambiente de produção ou desenvolvimento
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Configuração para ambiente de testes
# Se estamos em modo de teste ou a variável DATABASE_URL não está definida,
# usamos SQLite em memória
if os.getenv("TESTING") == "True" or SQLALCHEMY_DATABASE_URL is None:
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
