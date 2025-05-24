from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserBase(BaseModel):
    nome_completo: str
    email: EmailStr
    whatsapp: Optional[str] = None
    usuario_portal: Optional[str] = None
    senha_portal: Optional[str] = None

class UserCreate(UserBase):
    senha: str
    
    @validator('senha')
    def senha_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('A senha deve ter pelo menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('A senha deve conter pelo menos uma letra maiúscula')
        if not any(c.islower() for c in v):
            raise ValueError('A senha deve conter pelo menos uma letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('A senha deve conter pelo menos um número')
        if not any(not c.isalnum() for c in v):
            raise ValueError('A senha deve conter pelo menos um caractere especial')
        return v

class UserUpdate(BaseModel):
    nome_completo: Optional[str] = None
    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = None
    usuario_portal: Optional[str] = None
    senha_portal: Optional[str] = None
    role: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    nome_completo: str
    email: str
    whatsapp: Optional[str] = None
    usuario_portal: Optional[str] = None
    creditos: int
    role: str
    is_disabled: bool
    criado_em: datetime
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    senha: str

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: Optional[int] = None

class TokenData(BaseModel):
    email: Optional[str] = None
    permissions: Optional[List[str]] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    nova_senha: str
    
    @validator('nova_senha')
    def senha_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('A senha deve ter pelo menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('A senha deve conter pelo menos uma letra maiúscula')
        if not any(c.islower() for c in v):
            raise ValueError('A senha deve conter pelo menos uma letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('A senha deve conter pelo menos um número')
        if not any(not c.isalnum() for c in v):
            raise ValueError('A senha deve conter pelo menos um caractere especial')
        return v

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    senha_atual: str
    nova_senha: str
    
    @validator('nova_senha')
    def senha_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('A senha deve ter pelo menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('A senha deve conter pelo menos uma letra maiúscula')
        if not any(c.islower() for c in v):
            raise ValueError('A senha deve conter pelo menos uma letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('A senha deve conter pelo menos um número')
        if not any(not c.isalnum() for c in v):
            raise ValueError('A senha deve conter pelo menos um caractere especial')
        return v

class SecurityAuditLogCreate(BaseModel):
    user_id: Optional[int] = None
    action: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[str] = None
    severity: str = "info"

class SecurityAuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    user_id: Optional[int] = None
    action: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[str] = None
    severity: str

    class Config:
        orm_mode = True
