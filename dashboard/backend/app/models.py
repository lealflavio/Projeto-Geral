from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from .auth import UserRole
import enum

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
    
    # --- Campos para controle de acesso e segurança ---
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_disabled = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(Text, nullable=True)
    last_login_user_agent = Column(Text, nullable=True)

    # --- Campos para reset de senha ---
    reset_token = Column(Text, nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)

    service_values = relationship("ServiceValue", back_populates="owner")
    wos = relationship("WO", back_populates="tecnico")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

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

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token_jti = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User", back_populates="refresh_tokens")

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(Text, nullable=False)
    ip_address = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    severity = Column(Text, nullable=False, default="info")
