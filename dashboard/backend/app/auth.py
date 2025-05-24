from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from . import models, schemas, database
import secrets
import logging
import uuid
from enum import Enum

load_dotenv()

# --- Configurações de segurança ---
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_dev_only_0123456789abcdef")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
PASSWORD_RESET_EXPIRE_HOURS = int(os.getenv("PASSWORD_RESET_EXPIRE_HOURS", "1"))
MAX_FAILED_LOGIN_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
ACCOUNT_LOCKOUT_MINUTES = int(os.getenv("ACCOUNT_LOCKOUT_MINUTES", "15"))

# --- Criptografia ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- OAuth2 ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# --- Definição de papéis (RBAC) ---
class UserRole(str, Enum):
    ADMIN = "admin"
    SUPPORT = "support"
    TECHNICIAN = "technician"
    USER = "user"

# Mapeamento de permissões por papel
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        "users:read", "users:write", "users:delete",
        "wos:read", "wos:write", "wos:delete",
        "logs:read", "logs:write",
        "alerts:read", "alerts:write", "alerts:delete",
        "settings:read", "settings:write"
    ],
    UserRole.SUPPORT: [
        "users:read",
        "wos:read", "wos:write",
        "logs:read",
        "alerts:read",
        "settings:read"
    ],
    UserRole.TECHNICIAN: [
        "wos:read", "wos:write",
        "logs:read"
    ],
    UserRole.USER: [
        "wos:read"
    ]
}

# --- Utilitários de senha ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- Token JWT ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    
    # Adiciona um identificador único ao token para rastreamento
    to_encode.update({"jti": str(uuid.uuid4())})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    # Adiciona um identificador único ao token para rastreamento
    jti = str(uuid.uuid4())
    to_encode.update({"jti": jti})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti, expire

# --- Utilitários de usuário ---
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_whatsapp(db: Session, whatsapp: str):
    return db.query(models.User).filter(models.User.whatsapp == whatsapp).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def authenticate_user(db: Session, email: str, password: str, request: Optional[Request] = None):
    user = get_user_by_email(db, email=email)
    
    # Verifica se o usuário existe
    if not user:
        return False
    
    # Verifica se a conta está bloqueada
    if user.account_locked_until and user.account_locked_until > datetime.now(timezone.utc):
        remaining_time = (user.account_locked_until - datetime.now(timezone.utc)).total_seconds() / 60
        logging.warning(f"Tentativa de login em conta bloqueada: {email}. Desbloqueio em {remaining_time:.1f} minutos.")
        return False
    
    # Verifica a senha
    if not verify_password(password, user.senha_hash):
        # Incrementa contador de falhas
        if not user.failed_login_attempts:
            user.failed_login_attempts = 1
        else:
            user.failed_login_attempts += 1
        
        # Bloqueia a conta se exceder o limite de tentativas
        if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            user.account_locked_until = datetime.now(timezone.utc) + timedelta(minutes=ACCOUNT_LOCKOUT_MINUTES)
            logging.warning(f"Conta bloqueada por {ACCOUNT_LOCKOUT_MINUTES} minutos: {email}")
        
        db.commit()
        return False
    
    # Reseta contador de falhas após login bem-sucedido
    user.failed_login_attempts = 0
    user.account_locked_until = None
    user.last_login = datetime.now(timezone.utc)
    
    # Registra informações do dispositivo/navegador se disponíveis
    if request:
        user.last_login_ip = request.client.host if hasattr(request, 'client') else None
        user.last_login_user_agent = request.headers.get("user-agent", "")
    
    db.commit()
    return user

# --- Dependências de autenticação ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "access":
            raise credentials_exception
            
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
        
    # Verifica se o token está na lista de revogados
    jti = payload.get("jti")
    if jti and is_token_revoked(db, jti):
        raise credentials_exception
        
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if current_user.is_disabled:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user

# --- Funções de controle de acesso baseado em papéis (RBAC) ---
def get_user_permissions(user: models.User) -> List[str]:
    """Retorna a lista de permissões do usuário com base em seu papel."""
    role = user.role if hasattr(user, 'role') and user.role else UserRole.USER
    return ROLE_PERMISSIONS.get(role, [])

def has_permission(permission: str, user: models.User) -> bool:
    """Verifica se o usuário tem uma permissão específica."""
    user_permissions = get_user_permissions(user)
    return permission in user_permissions

def require_permission(permission: str):
    """Dependência para verificar se o usuário tem uma permissão específica."""
    def permission_dependency(current_user: models.User = Depends(get_current_active_user)):
        if not has_permission(permission, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão insuficiente: {permission}"
            )
        return current_user
    return permission_dependency

# --- Funções de reset de senha ---
def generate_password_reset_token():
    return secrets.token_urlsafe(48)

def set_reset_token_for_user(db: Session, user: models.User):
    # Gera e salva token + expiração
    token = generate_password_reset_token()
    expires = datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)
    user.reset_token = token
    user.reset_token_expires = expires
    db.commit()
    db.refresh(user)
    return token, expires

def verify_reset_token(db: Session, token: str):
    user = db.query(models.User).filter(models.User.reset_token == token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.now(timezone.utc):
        return None
    return user

def clear_reset_token(user: models.User, db: Session):
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    db.refresh(user)

# --- Gestão de tokens revogados ---
def revoke_token(db: Session, jti: str, expires_at: datetime):
    """Adiciona um token à lista de revogados."""
    revoked_token = models.RevokedToken(
        jti=jti,
        expires_at=expires_at
    )
    db.add(revoked_token)
    db.commit()

def is_token_revoked(db: Session, jti: str) -> bool:
    """Verifica se um token está na lista de revogados."""
    token = db.query(models.RevokedToken).filter(models.RevokedToken.jti == jti).first()
    return token is not None

def cleanup_expired_tokens(db: Session):
    """Remove tokens expirados da lista de revogados."""
    now = datetime.now(timezone.utc)
    db.query(models.RevokedToken).filter(models.RevokedToken.expires_at < now).delete()
    db.commit()

# --- Validação de força de senha ---
def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Valida a força da senha e retorna um dicionário com o resultado.
    
    Returns:
        Dict com 'valid' (bool) e 'message' (str) explicando o motivo se inválida
    """
    if len(password) < 8:
        return {"valid": False, "message": "A senha deve ter pelo menos 8 caracteres"}
        
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return {
            "valid": False, 
            "message": "A senha deve conter pelo menos uma letra maiúscula, uma minúscula e um número"
        }
        
    if not has_special:
        return {
            "valid": False, 
            "message": "A senha deve conter pelo menos um caractere especial"
        }
        
    return {"valid": True, "message": "Senha válida"}
