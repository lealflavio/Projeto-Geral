from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.services.tecnico_setup import criar_estrutura_tecnico
from .. import database, models, schemas, auth
from app.services.email_service import send_reset_email
from app.services.logging_system import logging_system, LogLevel, LogCategory
import os
from datetime import datetime, timedelta, timezone
from typing import List
import secrets
import time

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# --- Middleware de segurança ---
@router.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Adiciona cabeçalhos de segurança
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; object-src 'none'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    
    return response

# --- Função para registrar eventos de segurança ---
def log_security_event(db: Session, user_id: int = None, action: str = "", 
                      request: Request = None, details: str = "", severity: str = "info"):
    """Registra eventos de segurança no banco de dados e no sistema de logs."""
    
    # Registra no banco de dados
    security_log = models.SecurityAuditLog(
        user_id=user_id,
        action=action,
        ip_address=request.client.host if request and hasattr(request, 'client') else None,
        user_agent=request.headers.get("user-agent", "") if request else None,
        details=details,
        severity=severity
    )
    db.add(security_log)
    db.commit()
    
    # Registra no sistema de logs
    log_level = LogLevel.INFO
    if severity == "warning":
        log_level = LogLevel.WARNING
    elif severity == "error":
        log_level = LogLevel.ERROR
    elif severity == "critical":
        log_level = LogLevel.CRITICAL
        
    logging_system.log(
        message=f"Evento de segurança: {action}",
        level=log_level,
        category=LogCategory.SECURITY,
        extra={
            "user_id": user_id,
            "ip_address": request.client.host if request and hasattr(request, 'client') else None,
            "details": details
        }
    )

# --- Proteção contra ataques de força bruta ---
login_attempts = {}
MAX_ATTEMPTS_PER_IP = 10
RATE_LIMIT_WINDOW = 300  # 5 minutos

def check_rate_limit(request: Request):
    """Verifica se o IP excedeu o limite de tentativas de login."""
    client_ip = request.client.host if hasattr(request, 'client') else "unknown"
    current_time = time.time()
    
    # Limpa tentativas antigas
    for ip in list(login_attempts.keys()):
        if current_time - login_attempts[ip]["timestamp"] > RATE_LIMIT_WINDOW:
            del login_attempts[ip]
    
    # Verifica se o IP está na lista
    if client_ip in login_attempts:
        attempts = login_attempts[client_ip]
        if attempts["count"] >= MAX_ATTEMPTS_PER_IP:
            if current_time - attempts["timestamp"] < RATE_LIMIT_WINDOW:
                return False
            else:
                # Reseta se o tempo expirou
                login_attempts[client_ip] = {"count": 1, "timestamp": current_time}
        else:
            # Incrementa contador
            login_attempts[client_ip]["count"] += 1
    else:
        # Adiciona novo IP
        login_attempts[client_ip] = {"count": 1, "timestamp": current_time}
    
    return True

# --- Rotas de autenticação ---
@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, request: Request, db: Session = Depends(database.get_db)):
    # Verifica força da senha
    password_check = auth.validate_password_strength(user.senha)
    if not password_check["valid"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=password_check["message"])
    
    # Verifica se o email já existe
    db_user_email = auth.get_user_by_email(db, email=user.email)
    if db_user_email:
        # Registra tentativa de registro com email duplicado
        log_security_event(
            db=db, 
            action="register_attempt_duplicate_email", 
            request=request, 
            details=f"Tentativa de registro com email já existente: {user.email}",
            severity="warning"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Verifica se o WhatsApp já existe
    if user.whatsapp:
        db_user_whatsapp = auth.get_user_by_whatsapp(db, whatsapp=user.whatsapp)
        if db_user_whatsapp:
            log_security_event(
                db=db, 
                action="register_attempt_duplicate_whatsapp", 
                request=request, 
                details=f"Tentativa de registro com WhatsApp já existente: {user.whatsapp}",
                severity="warning"
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="WhatsApp number already registered")

    # Cria hash da senha
    hashed_password = auth.get_password_hash(user.senha)

    # Cria novo usuário
    new_user = models.User(
        nome_completo=user.nome_completo,
        email=user.email,
        senha_hash=hashed_password,
        whatsapp=user.whatsapp,
        usuario_portal=user.usuario_portal,
        senha_portal=user.senha_portal,
        role=auth.UserRole.TECHNICIAN if user.usuario_portal and user.senha_portal else auth.UserRole.USER
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Tenta criar estrutura de técnico se aplicável
    if user.usuario_portal and user.senha_portal:
        try:
            criar_estrutura_tecnico(
                nome_completo=user.nome_completo,
                email=user.email,
                usuario_portal=user.usuario_portal,
                senha_portal=user.senha_portal
            )
        except Exception as e:
            log_security_event(
                db=db, 
                user_id=new_user.id,
                action="technician_setup_failed", 
                request=request, 
                details=f"Falha ao criar estrutura de técnico: {str(e)}",
                severity="error"
            )
    
    # Registra sucesso
    log_security_event(
        db=db, 
        user_id=new_user.id,
        action="user_registered", 
        request=request, 
        details=f"Novo usuário registrado: {user.email}",
        severity="info"
    )

    return new_user

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    form_data: schemas.UserLogin, 
    request: Request, 
    response: Response,
    db: Session = Depends(database.get_db)
):
    # Verifica limite de taxa
    if not check_rate_limit(request):
        log_security_event(
            db=db, 
            action="login_rate_limit_exceeded", 
            request=request, 
            details=f"Limite de tentativas de login excedido para IP: {request.client.host if hasattr(request, 'client') else 'unknown'}",
            severity="warning"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": "300"},
        )
    
    # Autentica usuário
    user = auth.authenticate_user(db, email=form_data.email, password=form_data.senha, request=request)
    if not user:
        log_security_event(
            db=db, 
            action="login_failed", 
            request=request, 
            details=f"Tentativa de login falhou para email: {form_data.email}",
            severity="warning"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verifica se a conta está desativada
    if user.is_disabled:
        log_security_event(
            db=db, 
            user_id=user.id,
            action="login_disabled_account", 
            request=request, 
            details=f"Tentativa de login em conta desativada: {user.email}",
            severity="warning"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    
    # Cria tokens
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role.value if user.role else auth.UserRole.USER.value}, 
        expires_delta=access_token_expires
    )
    
    refresh_token, jti, expires = auth.create_refresh_token(
        data={"sub": user.email}
    )
    
    # Armazena refresh token
    db_refresh_token = models.RefreshToken(
        token_jti=jti,
        user_id=user.id,
        expires_at=expires
    )
    db.add(db_refresh_token)
    db.commit()
    
    # Registra login bem-sucedido
    log_security_event(
        db=db, 
        user_id=user.id,
        action="login_successful", 
        request=request, 
        details=f"Login bem-sucedido para: {user.email}",
        severity="info"
    )
    
    # Define cookie seguro para CSRF
    csrf_token = secrets.token_hex(32)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=1800  # 30 minutos
    )
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/refresh", response_model=schemas.Token)
def refresh_access_token(
    refresh_request: schemas.RefreshTokenRequest, 
    request: Request,
    response: Response,
    db: Session = Depends(database.get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodifica o token
        payload = auth.jwt.decode(refresh_request.refresh_token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email = payload.get("sub")
        token_type = payload.get("type")
        jti = payload.get("jti")
        
        if email is None or token_type != "refresh" or jti is None:
            raise credentials_exception
        
        # Verifica se o token está na lista de revogados
        if auth.is_token_revoked(db, jti):
            log_security_event(
                db=db, 
                action="refresh_token_revoked", 
                request=request, 
                details=f"Tentativa de uso de refresh token revogado para: {email}",
                severity="warning"
            )
            raise credentials_exception
        
        # Busca o token no banco
        db_token = db.query(models.RefreshToken).filter(
            models.RefreshToken.token_jti == jti,
            models.RefreshToken.is_revoked == False
        ).first()
        
        if not db_token:
            raise credentials_exception
        
        # Verifica se o token expirou
        if db_token.expires_at < datetime.now(timezone.utc):
            db_token.is_revoked = True
            db_token.revoked_at = datetime.now(timezone.utc)
            db.commit()
            raise credentials_exception
        
        # Busca o usuário
        user = auth.get_user_by_email(db, email=email)
        if user is None or user.is_disabled:
            raise credentials_exception
        
        # Cria novo access token
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.email, "role": user.role.value if user.role else auth.UserRole.USER.value}, 
            expires_delta=access_token_expires
        )
        
        # Registra refresh bem-sucedido
        log_security_event(
            db=db, 
            user_id=user.id,
            action="token_refreshed", 
            request=request, 
            details=f"Token refreshed para: {user.email}",
            severity="info"
        )
        
        # Define cookie seguro para CSRF
        csrf_token = secrets.token_hex(32)
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=1800  # 30 minutos
        )
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "expires_in": auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except auth.JWTError:
        log_security_event(
            db=db, 
            action="invalid_refresh_token", 
            request=request, 
            details="Tentativa de uso de refresh token inválido",
            severity="warning"
        )
        raise credentials_exception

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    # Revoga todos os refresh tokens do usuário
    db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == current_user.id,
        models.RefreshToken.is_revoked == False
    ).update({
        "is_revoked": True,
        "revoked_at": datetime.now(timezone.utc)
    })
    db.commit()
    
    # Limpa o cookie CSRF
    response.delete_cookie(key="csrf_token")
    
    # Registra logout
    log_security_event(
        db=db, 
        user_id=current_user.id,
        action="user_logout", 
        request=request, 
        details=f"Logout para: {current_user.email}",
        severity="info"
    )
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(
    request: Request,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    # Registra acesso ao perfil
    log_security_event(
        db=db, 
        user_id=current_user.id,
        action="profile_access", 
        request=request, 
        details=f"Acesso ao perfil: {current_user.email}",
        severity="info"
    )
    return current_user

@router.post("/change-password")
async def change_password(
    password_data: schemas.ChangePasswordRequest,
    request: Request,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    # Verifica senha atual
    if not auth.verify_password(password_data.senha_atual, current_user.senha_hash):
        log_security_event(
            db=db, 
            user_id=current_user.id,
            action="change_password_failed", 
            request=request, 
            details=f"Tentativa de alteração de senha com senha atual incorreta: {current_user.email}",
            severity="warning"
        )
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    
    # Verifica força da nova senha
    password_check = auth.validate_password_strength(password_data.nova_senha)
    if not password_check["valid"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=password_check["message"])
    
    # Atualiza senha
    current_user.senha_hash = auth.get_password_hash(password_data.nova_senha)
    db.commit()
    
    # Revoga todos os refresh tokens do usuário
    db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == current_user.id,
        models.RefreshToken.is_revoked == False
    ).update({
        "is_revoked": True,
        "revoked_at": datetime.now(timezone.utc)
    })
    db.commit()
    
    # Registra alteração de senha
    log_security_event(
        db=db, 
        user_id=current_user.id,
        action="password_changed", 
        request=request, 
        details=f"Senha alterada com sucesso: {current_user.email}",
        severity="info"
    )
    
    return {"message": "Senha alterada com sucesso"}

# --- Esqueci minha senha ---
@router.post("/forgot-password")
def forgot_password(
    request: schemas.ForgotPasswordRequest, 
    req: Request,
    db: Session = Depends(database.get_db)
):
    user = auth.get_user_by_email(db, email=request.email)
    # Sempre retorna sucesso, mesmo se o usuário não existe (para evitar enumeração)
    if not user:
        # Simula atraso para evitar timing attacks
        time.sleep(1)
        return {"message": "Se o e-mail existir, enviaremos instruções para recuperação."}

    token, expires = auth.set_reset_token_for_user(db, user)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/resetar-senha?token={token}"
    
    try:
        send_reset_email(user.email, reset_link)
        
        # Registra solicitação de reset
        log_security_event(
            db=db, 
            user_id=user.id,
            action="password_reset_requested", 
            request=req, 
            details=f"Solicitação de reset de senha: {user.email}",
            severity="info"
        )
    except Exception as e:
        log_security_event(
            db=db, 
            user_id=user.id,
            action="password_reset_email_failed", 
            request=req, 
            details=f"Falha ao enviar email de reset: {str(e)}",
            severity="error"
        )
    
    return {"message": "Se o e-mail existir, enviaremos instruções para recuperação."}

@router.post("/reset-password")
def reset_password(
    request: schemas.ResetPasswordRequest, 
    req: Request,
    db: Session = Depends(database.get_db)
):
    # Verifica token
    user = auth.verify_reset_token(db, request.token)
    if not user:
        log_security_event(
            db=db, 
            action="invalid_reset_token", 
            request=req, 
            details=f"Tentativa de reset com token inválido ou expirado",
            severity="warning"
        )
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    
    # Verifica força da nova senha
    password_check = auth.validate_password_strength(request.nova_senha)
    if not password_check["valid"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=password_check["message"])
    
    # Atualiza senha
    user.senha_hash = auth.get_password_hash(request.nova_senha)
    auth.clear_reset_token(user, db)
    
    # Revoga todos os refresh tokens do usuário
    db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == user.id,
        models.RefreshToken.is_revoked == False
    ).update({
        "is_revoked": True,
        "revoked_at": datetime.now(timezone.utc)
    })
    db.commit()
    
    # Registra reset de senha
    log_security_event(
        db=db, 
        user_id=user.id,
        action="password_reset_successful", 
        request=req, 
        details=f"Reset de senha bem-sucedido: {user.email}",
        severity="info"
    )
    
    return {"message": "Senha alterada com sucesso."}

# --- Gerenciamento de usuários (admin) ---
@router.get("/users", response_model=List[schemas.UserResponse])
async def get_users(
    request: Request,
    skip: int = 0, 
    limit: int = 100,
    current_user: models.User = Depends(auth.require_permission("users:read")),
    db: Session = Depends(database.get_db)
):
    users = db.query(models.User).offset(skip).limit(limit).all()
    
    # Registra acesso à lista de usuários
    log_security_event(
        db=db, 
        user_id=current_user.id,
        action="users_list_access", 
        request=request, 
        details=f"Acesso à lista de usuários por: {current_user.email}",
        severity="info"
    )
    
    return users

@router.put("/users/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    request: Request,
    current_user: models.User = Depends(auth.require_permission("users:write")),
    db: Session = Depends(database.get_db)
):
    # Busca usuário
    user = auth.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Atualiza campos
    if user_data.nome_completo is not None:
        user.nome_completo = user_data.nome_completo
    if user_data.email is not None:
        # Verifica se o email já existe
        existing = auth.get_user_by_email(db, user_data.email)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Email já está em uso")
        user.email = user_data.email
    if user_data.whatsapp is not None:
        # Verifica se o whatsapp já existe
        if user_data.whatsapp:
            existing = auth.get_user_by_whatsapp(db, user_data.whatsapp)
            if existing and existing.id != user_id:
                raise HTTPException(status_code=400, detail="WhatsApp já está em uso")
        user.whatsapp = user_data.whatsapp
    if user_data.usuario_portal is not None:
        user.usuario_portal = user_data.usuario_portal
    if user_data.senha_portal is not None:
        user.senha_portal = user_data.senha_portal
    if user_data.role is not None:
        # Verifica se o papel é válido
        try:
            user.role = auth.UserRole(user_data.role)
        except ValueError:
            raise HTTPException(status_code=400, detail="Papel inválido")
    
    db.commit()
    db.refresh(user)
    
    # Registra atualização de usuário
    log_security_event(
        db=db, 
        user_id=current_user.id,
        action="user_updated", 
        request=request, 
        details=f"Usuário {user_id} atualizado por: {current_user.email}",
        severity="info"
    )
    
    return user

@router.post("/users/{user_id}/disable")
async def disable_user(
    user_id: int,
    request: Request,
    current_user: models.User = Depends(auth.require_permission("users:write")),
    db: Session = Depends(database.get_db)
):
    # Busca usuário
    user = auth.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Impede desativação do próprio usuário
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Não é possível desativar seu próprio usuário")
    
    # Desativa usuário
    user.is_disabled = True
    db.commit()
    
    # Revoga todos os refresh tokens do usuário
    db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == user.id,
        models.RefreshToken.is_revoked == False
    ).update({
        "is_revoked": True,
        "revoked_at": datetime.now(timezone.utc)
    })
    db.commit()
    
    # Registra desativação de usuário
    log_security_event(
        db=db, 
        user_id=current_user.id,
        action="user_disabled", 
        request=request, 
        details=f"Usuário {user_id} desativado por: {current_user.email}",
        severity="warning"
    )
    
    return {"message": "Usuário desativado com sucesso"}

@router.post("/users/{user_id}/enable")
async def enable_user(
    user_id: int,
    request: Request,
    current_user: models.User = Depends(auth.require_permission("users:write")),
    db: Session = Depends(database.get_db)
):
    # Busca usuário
    user = auth.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Ativa usuário
    user.is_disabled = False
    user.failed_login_attempts = 0
    user.account_locked_until = None
    db.commit()
    
    # Registra ativação de usuário
    log_security_event(
        db=db, 
        user_id=current_user.id,
        action="user_enabled", 
        request=request, 
        details=f"Usuário {user_id} ativado por: {current_user.email}",
        severity="info"
    )
    
    return {"message": "Usuário ativado com sucesso"}

# --- Logs de segurança (admin) ---
@router.get("/security-logs", response_model=List[schemas.SecurityAuditLogResponse])
async def get_security_logs(
    request: Request,
    skip: int = 0, 
    limit: int = 100,
    user_id: int = None,
    severity: str = None,
    start_date: str = None,
    end_date: str = None,
    current_user: models.User = Depends(auth.require_permission("logs:read")),
    db: Session = Depends(database.get_db)
):
    # Constrói query base
    query = db.query(models.SecurityAuditLog)
    
    # Aplica filtros
    if user_id is not None:
        query = query.filter(models.SecurityAuditLog.user_id == user_id)
    if severity is not None:
        query = query.filter(models.SecurityAuditLog.severity == severity)
    if start_date is not None:
        query = query.filter(models.SecurityAuditLog.timestamp >= start_date)
    if end_date is not None:
        query = query.filter(models.SecurityAuditLog.timestamp <= end_date)
    
    # Ordena por timestamp (mais recentes primeiro)
    query = query.order_by(models.SecurityAuditLog.timestamp.desc())
    
    # Aplica paginação
    logs = query.offset(skip).limit(limit).all()
    
    # Registra acesso aos logs de segurança
    log_security_event(
        db=db, 
        user_id=current_user.id,
        action="security_logs_access", 
        request=request, 
        details=f"Acesso aos logs de segurança por: {current_user.email}",
        severity="info"
    )
    
    return logs
