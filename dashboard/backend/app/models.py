from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(Text, nullable=False)
    email = Column(Text, unique=True, index=True, nullable=False)
    senha_hash = Column(Text, nullable=False)
    whatsapp = Column(Text, unique=True, index=True, nullable=True)
    usuario_portal = Column(Text, nullable=True)
    senha_portal = Column(Text, nullable=True)
    creditos = Column(Integer, default=5)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    service_values = relationship("ServiceValue", back_populates="owner")
    wos = relationship("WO", back_populates="tecnico")

class WO(Base):
    __tablename__ = "wos"

    id = Column(Integer, primary_key=True, index=True)
    numero_wo = Column(Text, nullable=False)
    tecnico_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Text, nullable=False)
    tipo_servico = Column(String, nullable=False, default="desconhecido")
    data = Column(DateTime(timezone=True), server_default=func.now())
    causa_erro = Column(Text, nullable=True)

    tecnico = relationship("User", back_populates="wos")

class ServiceValue(Base):
    __tablename__ = "service_values"

    id = Column(Integer, primary_key=True, index=True)
    tipo_servico = Column(String, index=True, nullable=False)
    valor = Column(Float, nullable=False)
    tecnico_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="service_values")
