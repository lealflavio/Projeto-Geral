from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    whatsapp = Column(String, nullable=True)
    creditos = Column(Integer, default=0)
    criado_em = Column(DateTime)
    usuario_portal = Column(String, nullable=True)
    senha_portal = Column(String, nullable=True)

class WO(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    numero_wo = Column(String, nullable=False)
    tecnico_id = Column(Integer, ForeignKey("usuarios.id"))
    status = Column(String, nullable=False)
    tipo_servico = Column(String, nullable=False)
    data = Column(DateTime)
    causa_erro = Column(String, nullable=True)

class ServiceValue(Base):
    __tablename__ = "service_values"

    id = Column(Integer, primary_key=True, index=True)
    tipo_servico = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    tecnico_id = Column(Integer, ForeignKey("usuarios.id"))
