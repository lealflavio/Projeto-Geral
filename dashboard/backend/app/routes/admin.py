import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone

from .. import database, models, schemas, auth
from ..services.logging_system import logging_system, LogLevel, LogCategory
from ..services.alert_system import alert_manager

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin Dashboard"],
    responses={404: {"description": "Not found"}}
)

# --- Métricas do sistema ---
@router.get("/metrics/system", response_model=Dict[str, Any])
async def get_system_metrics(
    period: str = Query("day", regex="^(hour|day|week|month)$"),
    current_user: models.User = Depends(auth.require_permission("settings:read")),
    db: Session = Depends(database.get_db)
):
    """
    Obtém métricas gerais do sistema para o dashboard administrativo.
    
    Args:
        period: Período de tempo para as métricas (hour, day, week, month)
        
    Returns:
        Dict[str, Any]: Métricas do sistema
    """
    # Define o período de tempo
    now = datetime.now(timezone.utc)
    if period == "hour":
        start_time = now - timedelta(hours=1)
    elif period == "day":
        start_time = now - timedelta(days=1)
    elif period == "week":
        start_time = now - timedelta(weeks=1)
    else:  # month
        start_time = now - timedelta(days=30)
    
    # Coleta métricas
    metrics = {
        "period": period,
        "timestamp": now.isoformat(),
        "users": {
            "total": db.query(func.count(models.User.id)).scalar(),
            "active": db.query(func.count(models.User.id)).filter(models.User.is_disabled == False).scalar(),
            "new": db.query(func.count(models.User.id)).filter(models.User.criado_em >= start_time).scalar(),
            "recent_logins": db.query(func.count(models.User.id)).filter(models.User.last_login >= start_time).scalar()
        },
        "wos": {
            "total": db.query(func.count(models.WO.id)).scalar(),
            "recent": db.query(func.count(models.WO.id)).filter(models.WO.data >= start_time).scalar(),
            "by_status": {}
        },
        "security": {
            "failed_logins": db.query(func.count(models.SecurityAuditLog.id))
                .filter(models.SecurityAuditLog.action == "login_failed")
                .filter(models.SecurityAuditLog.timestamp >= start_time)
                .scalar(),
            "account_lockouts": db.query(func.count(models.SecurityAuditLog.id))
                .filter(models.SecurityAuditLog.action == "login_rate_limit_exceeded")
                .filter(models.SecurityAuditLog.timestamp >= start_time)
                .scalar(),
            "password_resets": db.query(func.count(models.SecurityAuditLog.id))
                .filter(models.SecurityAuditLog.action == "password_reset_successful")
                .filter(models.SecurityAuditLog.timestamp >= start_time)
                .scalar()
        },
        "logs": {
            "total": db.query(func.count(models.SecurityAuditLog.id))
                .filter(models.SecurityAuditLog.timestamp >= start_time)
                .scalar(),
            "by_severity": {}
        },
        "alerts": {
            "active": len(alert_manager.get_alerts(status="active")),
            "resolved": len(alert_manager.get_alerts(status="resolved")),
            "recent": len(alert_manager.get_alert_history(start_time=start_time.isoformat()))
        }
    }
    
    # Adiciona contagem de WOs por status
    status_counts = db.query(models.WO.status, func.count(models.WO.id)) \
        .group_by(models.WO.status) \
        .all()
    
    for status, count in status_counts:
        metrics["wos"]["by_status"][status] = count
    
    # Adiciona contagem de logs por severidade
    severity_counts = db.query(models.SecurityAuditLog.severity, func.count(models.SecurityAuditLog.id)) \
        .filter(models.SecurityAuditLog.timestamp >= start_time) \
        .group_by(models.SecurityAuditLog.severity) \
        .all()
    
    for severity, count in severity_counts:
        metrics["logs"]["by_severity"][severity] = count
    
    return metrics

@router.get("/metrics/users", response_model=Dict[str, Any])
async def get_user_metrics(
    period: str = Query("day", regex="^(hour|day|week|month)$"),
    current_user: models.User = Depends(auth.require_permission("users:read")),
    db: Session = Depends(database.get_db)
):
    """
    Obtém métricas detalhadas sobre usuários para o dashboard administrativo.
    
    Args:
        period: Período de tempo para as métricas (hour, day, week, month)
        
    Returns:
        Dict[str, Any]: Métricas de usuários
    """
    # Define o período de tempo
    now = datetime.now(timezone.utc)
    if period == "hour":
        start_time = now - timedelta(hours=1)
    elif period == "day":
        start_time = now - timedelta(days=1)
    elif period == "week":
        start_time = now - timedelta(weeks=1)
    else:  # month
        start_time = now - timedelta(days=30)
    
    # Coleta métricas
    metrics = {
        "period": period,
        "timestamp": now.isoformat(),
        "total_users": db.query(func.count(models.User.id)).scalar(),
        "active_users": db.query(func.count(models.User.id)).filter(models.User.is_disabled == False).scalar(),
        "inactive_users": db.query(func.count(models.User.id)).filter(models.User.is_disabled == True).scalar(),
        "new_users": db.query(func.count(models.User.id)).filter(models.User.criado_em >= start_time).scalar(),
        "by_role": {},
        "login_activity": {
            "recent_logins": db.query(func.count(models.User.id)).filter(models.User.last_login >= start_time).scalar(),
            "never_logged_in": db.query(func.count(models.User.id)).filter(models.User.last_login == None).scalar(),
        },
        "most_active_users": []
    }
    
    # Adiciona contagem de usuários por papel
    role_counts = db.query(models.User.role, func.count(models.User.id)) \
        .group_by(models.User.role) \
        .all()
    
    for role, count in role_counts:
        metrics["by_role"][role.value if role else "unknown"] = count
    
    # Adiciona usuários mais ativos (com mais logins recentes)
    active_users = db.query(
            models.SecurityAuditLog.user_id,
            func.count(models.SecurityAuditLog.id).label("login_count")
        ) \
        .filter(models.SecurityAuditLog.action == "login_successful") \
        .filter(models.SecurityAuditLog.timestamp >= start_time) \
        .group_by(models.SecurityAuditLog.user_id) \
        .order_by(desc("login_count")) \
        .limit(10) \
        .all()
    
    for user_id, login_count in active_users:
        user = auth.get_user_by_id(db, user_id)
        if user:
            metrics["most_active_users"].append({
                "id": user.id,
                "name": user.nome_completo,
                "email": user.email,
                "login_count": login_count
            })
    
    return metrics

@router.get("/metrics/wos", response_model=Dict[str, Any])
async def get_wo_metrics(
    period: str = Query("day", regex="^(hour|day|week|month)$"),
    current_user: models.User = Depends(auth.require_permission("wos:read")),
    db: Session = Depends(database.get_db)
):
    """
    Obtém métricas detalhadas sobre WOs para o dashboard administrativo.
    
    Args:
        period: Período de tempo para as métricas (hour, day, week, month)
        
    Returns:
        Dict[str, Any]: Métricas de WOs
    """
    # Define o período de tempo
    now = datetime.now(timezone.utc)
    if period == "hour":
        start_time = now - timedelta(hours=1)
    elif period == "day":
        start_time = now - timedelta(days=1)
    elif period == "week":
        start_time = now - timedelta(weeks=1)
    else:  # month
        start_time = now - timedelta(days=30)
    
    # Coleta métricas
    metrics = {
        "period": period,
        "timestamp": now.isoformat(),
        "total_wos": db.query(func.count(models.WO.id)).scalar(),
        "recent_wos": db.query(func.count(models.WO.id)).filter(models.WO.data >= start_time).scalar(),
        "by_status": {},
        "by_tipo_servico": {},
        "by_tecnico": [],
        "recent_activity": []
    }
    
    # Adiciona contagem de WOs por status
    status_counts = db.query(models.WO.status, func.count(models.WO.id)) \
        .group_by(models.WO.status) \
        .all()
    
    for status, count in status_counts:
        metrics["by_status"][status] = count
    
    # Adiciona contagem de WOs por tipo de serviço
    tipo_counts = db.query(models.WO.tipo_servico, func.count(models.WO.id)) \
        .group_by(models.WO.tipo_servico) \
        .all()
    
    for tipo, count in tipo_counts:
        metrics["by_tipo_servico"][tipo] = count
    
    # Adiciona contagem de WOs por técnico
    tecnico_counts = db.query(
            models.WO.tecnico_id,
            func.count(models.WO.id).label("wo_count")
        ) \
        .group_by(models.WO.tecnico_id) \
        .order_by(desc("wo_count")) \
        .limit(10) \
        .all()
    
    for tecnico_id, wo_count in tecnico_counts:
        tecnico = auth.get_user_by_id(db, tecnico_id)
        if tecnico:
            metrics["by_tecnico"].append({
                "id": tecnico.id,
                "name": tecnico.nome_completo,
                "email": tecnico.email,
                "wo_count": wo_count
            })
    
    # Adiciona atividade recente de WOs
    recent_wos = db.query(models.WO) \
        .filter(models.WO.data >= start_time) \
        .order_by(desc(models.WO.data)) \
        .limit(10) \
        .all()
    
    for wo in recent_wos:
        tecnico = auth.get_user_by_id(db, wo.tecnico_id)
        metrics["recent_activity"].append({
            "id": wo.id,
            "numero_wo": wo.numero_wo,
            "status": wo.status,
            "tipo_servico": wo.tipo_servico,
            "data": wo.data.isoformat() if wo.data else None,
            "tecnico": tecnico.nome_completo if tecnico else "Unknown"
        })
    
    return metrics

@router.get("/metrics/security", response_model=Dict[str, Any])
async def get_security_metrics(
    period: str = Query("day", regex="^(hour|day|week|month)$"),
    current_user: models.User = Depends(auth.require_permission("logs:read")),
    db: Session = Depends(database.get_db)
):
    """
    Obtém métricas de segurança para o dashboard administrativo.
    
    Args:
        period: Período de tempo para as métricas (hour, day, week, month)
        
    Returns:
        Dict[str, Any]: Métricas de segurança
    """
    # Define o período de tempo
    now = datetime.now(timezone.utc)
    if period == "hour":
        start_time = now - timedelta(hours=1)
    elif period == "day":
        start_time = now - timedelta(days=1)
    elif period == "week":
        start_time = now - timedelta(weeks=1)
    else:  # month
        start_time = now - timedelta(days=30)
    
    # Coleta métricas
    metrics = {
        "period": period,
        "timestamp": now.isoformat(),
        "total_events": db.query(func.count(models.SecurityAuditLog.id))
            .filter(models.SecurityAuditLog.timestamp >= start_time)
            .scalar(),
        "by_severity": {},
        "by_action": {},
        "failed_logins": db.query(func.count(models.SecurityAuditLog.id))
            .filter(models.SecurityAuditLog.action == "login_failed")
            .filter(models.SecurityAuditLog.timestamp >= start_time)
            .scalar(),
        "account_lockouts": db.query(func.count(models.SecurityAuditLog.id))
            .filter(models.SecurityAuditLog.action == "login_rate_limit_exceeded")
            .filter(models.SecurityAuditLog.timestamp >= start_time)
            .scalar(),
        "password_resets": db.query(func.count(models.SecurityAuditLog.id))
            .filter(models.SecurityAuditLog.action == "password_reset_successful")
            .filter(models.SecurityAuditLog.timestamp >= start_time)
            .scalar(),
        "suspicious_ips": [],
        "recent_events": []
    }
    
    # Adiciona contagem de eventos por severidade
    severity_counts = db.query(models.SecurityAuditLog.severity, func.count(models.SecurityAuditLog.id)) \
        .filter(models.SecurityAuditLog.timestamp >= start_time) \
        .group_by(models.SecurityAuditLog.severity) \
        .all()
    
    for severity, count in severity_counts:
        metrics["by_severity"][severity] = count
    
    # Adiciona contagem de eventos por ação
    action_counts = db.query(models.SecurityAuditLog.action, func.count(models.SecurityAuditLog.id)) \
        .filter(models.SecurityAuditLog.timestamp >= start_time) \
        .group_by(models.SecurityAuditLog.action) \
        .all()
    
    for action, count in action_counts:
        metrics["by_action"][action] = count
    
    # Adiciona IPs suspeitos (com mais falhas de login)
    suspicious_ips = db.query(
            models.SecurityAuditLog.ip_address,
            func.count(models.SecurityAuditLog.id).label("failure_count")
        ) \
        .filter(models.SecurityAuditLog.action.in_(["login_failed", "login_rate_limit_exceeded"])) \
        .filter(models.SecurityAuditLog.timestamp >= start_time) \
        .filter(models.SecurityAuditLog.ip_address != None) \
        .group_by(models.SecurityAuditLog.ip_address) \
        .order_by(desc("failure_count")) \
        .limit(10) \
        .all()
    
    for ip, count in suspicious_ips:
        metrics["suspicious_ips"].append({
            "ip_address": ip,
            "failure_count": count
        })
    
    # Adiciona eventos recentes
    recent_events = db.query(models.SecurityAuditLog) \
        .filter(models.SecurityAuditLog.timestamp >= start_time) \
        .order_by(desc(models.SecurityAuditLog.timestamp)) \
        .limit(10) \
        .all()
    
    for event in recent_events:
        user = auth.get_user_by_id(db, event.user_id) if event.user_id else None
        metrics["recent_events"].append({
            "id": event.id,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "action": event.action,
            "severity": event.severity,
            "user": user.email if user else None,
            "ip_address": event.ip_address
        })
    
    return metrics

# --- Gerenciamento de usuários ---
@router.get("/users", response_model=List[schemas.UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: models.User = Depends(auth.require_permission("users:read")),
    db: Session = Depends(database.get_db)
):
    """
    Obtém lista de usuários com filtros opcionais.
    
    Args:
        skip: Número de registros para pular (paginação)
        limit: Número máximo de registros a retornar
        role: Filtro por papel do usuário
        is_active: Filtro por status ativo/inativo
        search: Termo de busca para nome ou email
        
    Returns:
        List[schemas.UserResponse]: Lista de usuários
    """
    query = db.query(models.User)
    
    # Aplica filtros
    if role:
        try:
            role_enum = auth.UserRole(role)
            query = query.filter(models.User.role == role_enum)
        except ValueError:
            pass
    
    if is_active is not None:
        query = query.filter(models.User.is_disabled == (not is_active))
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.User.nome_completo.ilike(search_term)) | 
            (models.User.email.ilike(search_term))
        )
    
    # Aplica paginação
    users = query.offset(skip).limit(limit).all()
    
    return users

@router.get("/users/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    current_user: models.User = Depends(auth.require_permission("users:read")),
    db: Session = Depends(database.get_db)
):
    """
    Obtém detalhes de um usuário específico.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        schemas.UserResponse: Detalhes do usuário
    """
    user = auth.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return user

@router.put("/users/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    request: Request,
    current_user: models.User = Depends(auth.require_permission("users:write")),
    db: Session = Depends(database.get_db)
):
    """
    Atualiza dados de um usuário.
    
    Args:
        user_id: ID do usuário
        user_data: Dados atualizados do usuário
        
    Returns:
        schemas.UserResponse: Usuário atualizado
    """
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
    from ..routes.auth import log_security_event
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
    """
    Desativa um usuário.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Dict[str, str]: Mensagem de sucesso
    """
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
    from ..routes.auth import log_security_event
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
    """
    Ativa um usuário.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Dict[str, str]: Mensagem de sucesso
    """
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
    from ..routes.auth import log_security_event
    log_security_event(
        db=db, 
        user_id=current_user.id,
        action="user_enabled", 
        request=request, 
        details=f"Usuário {user_id} ativado por: {current_user.email}",
        severity="info"
    )
    
    return {"message": "Usuário ativado com sucesso"}

@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: int,
    request: Request,
    current_user: models.User = Depends(auth.require_permission("users:write")),
    db: Session = Depends(database.get_db)
):
    """
    Reseta a senha de um usuário (gera token de reset).
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Dict[str, str]: Token de reset e mensagem de sucesso
    """
    # Busca usuário
    user = auth.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Gera token de reset
    token, expires = auth.set_reset_token_for_user(db, user)
    
    # Registra reset de senha
    from ..routes.auth import log_security_event
    log_security_event(
        db=db, 
        user_id=current_user.id,
        action="admin_password_reset", 
        request=request, 
        details=f"Reset de senha administrativo para usuário {user_id} por: {current_user.email}",
        severity="warning"
    )
    
    # Constrói link de reset
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/resetar-senha?token={token}"
    
    return {
        "message": "Token de reset gerado com sucesso",
        "token": token,
        "expires": expires.isoformat(),
        "reset_link": reset_link
    }

# --- Monitoramento de sistema ---
@router.get("/logs", response_model=List[schemas.SecurityAuditLogResponse])
async def get_security_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: models.User = Depends(auth.require_permission("logs:read")),
    db: Session = Depends(database.get_db)
):
    """
    Obtém logs de segurança com filtros opcionais.
    
    Args:
        skip: Número de registros para pular (paginação)
        limit: Número máximo de registros a retornar
        user_id: Filtro por ID de usuário
        action: Filtro por tipo de ação
        severity: Filtro por severidade
        start_date: Data inicial (formato ISO)
        end_date: Data final (formato ISO)
        
    Returns:
        List[schemas.SecurityAuditLogResponse]: Lista de logs de segurança
    """
    # Constrói query base
    query = db.query(models.SecurityAuditLog)
    
    # Aplica filtros
    if user_id is not None:
        query = query.filter(models.SecurityAuditLog.user_id == user_id)
    if action is not None:
        query = query.filter(models.SecurityAuditLog.action == action)
    if severity is not None:
        query = query.filter(models.SecurityAuditLog.severity == severity)
    if start_date is not None:
        query = query.filter(models.SecurityAuditLog.timestamp >= start_date)
    if end_date is not None:
        query = query.filter(models.SecurityAuditLog.timestamp <= end_date)
    
    # Ordena por timestamp (mais recentes primeiro)
    query = query.order_by(desc(models.SecurityAuditLog.timestamp))
    
    # Aplica paginação
    logs = query.offset(skip).limit(limit).all()
    
    return logs

@router.get("/alerts", response_model=Dict[str, Any])
async def get_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    current_user: models.User = Depends(auth.require_permission("alerts:read")),
    db: Session = Depends(database.get_db)
):
    """
    Obtém alertas do sistema com filtros opcionais.
    
    Args:
        status: Filtro por status (active, inactive, resolved)
        severity: Filtro por severidade
        start_date: Data inicial (formato ISO)
        end_date: Data final (formato ISO)
        limit: Número máximo de alertas a retornar
        
    Returns:
        Dict[str, Any]: Alertas do sistema
    """
    # Obtém alertas ativos
    active_alerts = alert_manager.get_alerts(status=status)
    
    # Obtém histórico de alertas
    alert_history = alert_manager.get_alert_history(
        start_time=start_date,
        end_time=end_date,
        severity=severity,
        limit=limit
    )
    
    return {
        "active_alerts": active_alerts,
        "alert_history": alert_history,
        "counts": {
            "active": len(alert_manager.get_alerts(status="active")),
            "inactive": len(alert_manager.get_alerts(status="inactive")),
            "resolved": len(alert_manager.get_alerts(status="resolved")),
            "total_history": len(alert_history)
        }
    }

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    request: Request,
    current_user: models.User = Depends(auth.require_permission("alerts:write")),
    db: Session = Depends(database.get_db)
):
    """
    Resolve um alerta manualmente.
    
    Args:
        alert_id: ID do alerta
        
    Returns:
        Dict[str, Any]: Resultado da operação
    """
    try:
        alert = alert_manager.get_alert(alert_id)
        if alert is None:
            raise HTTPException(status_code=404, detail=f"Alerta não encontrado: {alert_id}")
        
        if alert.resolve():
            # Registra resolução de alerta
            from ..routes.auth import log_security_event
            log_security_event(
                db=db, 
                user_id=current_user.id,
                action="alert_resolved", 
                request=request, 
                details=f"Alerta {alert_id} resolvido por: {current_user.email}",
                severity="info"
            )
            
            return {"success": True, "message": "Alerta resolvido com sucesso"}
        else:
            return {"success": False, "message": "Alerta não pôde ser resolvido"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao resolver alerta: {str(e)}")

# --- Configurações administrativas ---
@router.get("/settings", response_model=Dict[str, Any])
async def get_settings(
    current_user: models.User = Depends(auth.require_permission("settings:read")),
    db: Session = Depends(database.get_db)
):
    """
    Obtém configurações do sistema.
    
    Returns:
        Dict[str, Any]: Configurações do sistema
    """
    # Obtém configurações do ambiente
    settings = {
        "auth": {
            "access_token_expire_minutes": auth.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": auth.REFRESH_TOKEN_EXPIRE_DAYS,
            "password_reset_expire_hours": auth.PASSWORD_RESET_EXPIRE_HOURS,
            "max_failed_login_attempts": auth.MAX_FAILED_LOGIN_ATTEMPTS,
            "account_lockout_minutes": auth.ACCOUNT_LOCKOUT_MINUTES
        },
        "alerts": {
            "check_interval": alert_manager.check_interval,
            "max_history_size": alert_manager.max_history_size
        },
        "system": {
            "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:5173"),
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    }
    
    return settings

@router.put("/settings", response_model=Dict[str, Any])
async def update_settings(
    settings: Dict[str, Any],
    request: Request,
    current_user: models.User = Depends(auth.require_permission("settings:write")),
    db: Session = Depends(database.get_db)
):
    """
    Atualiza configurações do sistema.
    
    Args:
        settings: Novas configurações
        
    Returns:
        Dict[str, Any]: Configurações atualizadas
    """
    # Atualiza configurações de alerta
    if "alerts" in settings:
        alerts_config = settings["alerts"]
        if "check_interval" in alerts_config:
            alert_manager.check_interval = int(alerts_config["check_interval"])
        if "max_history_size" in alerts_config:
            alert_manager.max_history_size = int(alerts_config["max_history_size"])
    
    # Registra atualização de configurações
    from ..routes.auth import log_security_event
    log_security_event(
        db=db, 
        user_id=current_user.id,
        action="settings_updated", 
        request=request, 
        details=f"Configurações atualizadas por: {current_user.email}",
        severity="info"
    )
    
    # Retorna configurações atualizadas
    return await get_settings(current_user, db)

@router.post("/maintenance/cleanup-tokens")
async def cleanup_tokens(
    request: Request,
    current_user: models.User = Depends(auth.require_permission("settings:write")),
    db: Session = Depends(database.get_db)
):
    """
    Limpa tokens expirados do sistema.
    
    Returns:
        Dict[str, Any]: Resultado da operação
    """
    # Limpa tokens de refresh expirados
    now = datetime.now(timezone.utc)
    refresh_result = db.query(models.RefreshToken).filter(
        models.RefreshToken.expires_at < now
    ).delete()
    
    # Limpa tokens revogados expirados
    revoked_result = auth.cleanup_expired_tokens(db)
    
    # Registra limpeza de tokens
    from ..routes.auth import log_security_event
    log_security_event(
        db=db, 
        user_id=current_user.id,
        action="tokens_cleanup", 
        request=request, 
        details=f"Limpeza de tokens expirados por: {current_user.email}",
        severity="info"
    )
    
    return {
        "success": True,
        "message": "Tokens expirados removidos com sucesso",
        "refresh_tokens_removed": refresh_result,
        "revoked_tokens_removed": revoked_result
    }
