from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    nome_completo: str
    email: EmailStr
    senha: str
    whatsapp: Optional[str] = Field(None, pattern=r'^\d{9,15}$')
    usuario_portal: Optional[str] = None
    senha_portal: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    senha: str

class UserResponse(BaseModel):
    id: int
    nome_completo: str
    email: EmailStr
    whatsapp: Optional[str]
    creditos: int
    criado_em: datetime
    usuario_portal: Optional[str] = None
    senha_portal: Optional[str] = None  # <-- ESSENCIAL! Adicionado aqui

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Esqueci/resetar senha ---
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    nova_senha: str

# --- Editar perfil ---
class UserUpdate(BaseModel):
    nome_completo: Optional[str]
    email: Optional[EmailStr]
    whatsapp: Optional[str]

# --- Atualizar credenciais do portal ---
class UpdatePortalCredentials(BaseModel):
    usuario_portal: Optional[str]
    senha_portal: Optional[str]

class AddCreditsRequest(BaseModel):
    creditos: int

class TransferCreditsRequest(BaseModel):
    email_destino: EmailStr
    creditos: int

class WOCreate(BaseModel):
    numero_wo: str
    status: str
    tipo_servico: str
    causa_erro: Optional[str] = None

class WOResponse(BaseModel):
    id: int
    numero_wo: str
    tecnico_id: int
    status: str
    tipo_servico: str
    data: datetime
    causa_erro: Optional[str] = None

    class Config:
        from_attributes = True

class ServiceValueCreate(BaseModel):
    tipo_servico: str
    valor: float

class ServiceValueResponse(BaseModel):
    id: int
    tipo_servico: str
    valor: float
    tecnico_id: int

    class Config:
        from_attributes = True

# Requisição para integração com o portal
class PortalIntegrationRequest(BaseModel):
    usuario_portal: str
    senha_portal: str
    whatsapp: str
