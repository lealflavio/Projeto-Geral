from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import json
import logging
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from . import models, schemas, database

import secrets

load_dotenv()

# Configurar logging detalhado
logger = logging.getLogger("auth_debug")
logger.setLevel(logging.DEBUG)
# Garantir que o logger tenha um handler para console
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# --- Configurações de segurança ---
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_dev_only_0123456789abcdef")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Criptografia ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- OAuth2 ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# --- Utilitários de senha ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- Token JWT ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Utilitários de usuário ---
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_whatsapp(db: Session, whatsapp: str):
    return db.query(models.User).filter(models.User.whatsapp == whatsapp).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email=email)
    if not user or not verify_password(password, user.senha_hash):
        return False
    return user

# --- Dependências de autenticação com logs detalhados ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db), request: Request = None):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Log da rota atual
    if request:
        logger.debug(f"Autenticando requisição para: {request.url.path}")
        logger.debug(f"Headers da requisição: {dict(request.headers)}")
    
    logger.debug(f"Iniciando validação de token: {token[:15]}...")
    
    try:
        logger.debug(f"Tentando decodificar token com SECRET_KEY: {SECRET_KEY[:5]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Token decodificado com sucesso. Payload: {json.dumps(payload)}")
        
        email: str = payload.get("sub")
        logger.debug(f"Email extraído do token: {email}")
        
        if email is None:
            logger.error("Campo 'sub' não encontrado no payload do token")
            raise credentials_exception
            
        token_data = schemas.TokenData(email=email)
        logger.debug(f"TokenData criado: {token_data}")
        
    except JWTError as e:
        logger.error(f"Erro ao decodificar JWT: {str(e)}")
        raise credentials_exception

    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        logger.error(f"Usuário com email {token_data.email} não encontrado no banco de dados")
        raise credentials_exception
        
    logger.debug(f"Usuário autenticado com sucesso: {user.email}")
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    return current_user

# --- Funções de reset de senha ---
def generate_password_reset_token():
    return secrets.token_urlsafe(48)

def set_reset_token_for_user(db: Session, user: models.User):
    # Gera e salva token + expiração
    token = generate_password_reset_token()
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
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
