import os
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from ..services.alert_system import alert_manager, Alert, AlertCondition, ThresholdAlertCondition, PatternAlertCondition
from ..services.logging_system import LogLevel, LogCategory
from ..auth import get_current_user

router = APIRouter(
    prefix="/api/alerts",
    tags=["alerts"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def get_alerts(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém todos os alertas, opcionalmente filtrados por status.
    
    Args:
        status: Status para filtrar alertas (inactive, active, resolved)
        
    Returns:
        List[Dict[str, Any]]: Lista de alertas
    """
    # Verifica se o usuário tem permissão para acessar alertas
    if current_user.get("role") not in ["admin", "support"]:
        raise HTTPException(status_code=403, detail="Sem permissão para acessar alertas")
    
    try:
        alerts = alert_manager.get_alerts(status=status)
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter alertas: {str(e)}")

@router.get("/history")
async def get_alert_history(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém histórico de alertas com filtros opcionais.
    
    Args:
        start_date: Data inicial (formato ISO)
        end_date: Data final (formato ISO)
        severity: Severidade para filtrar
        limit: Número máximo de alertas a retornar
        
    Returns:
        List[Dict[str, Any]]: Lista de alertas históricos
    """
    # Verifica se o usuário tem permissão para acessar alertas
    if current_user.get("role") not in ["admin", "support"]:
        raise HTTPException(status_code=403, detail="Sem permissão para acessar histórico de alertas")
    
    try:
        history = alert_manager.get_alert_history(
            start_time=start_date,
            end_time=end_date,
            severity=severity,
            limit=limit
        )
        return {"alerts": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter histórico de alertas: {str(e)}")

@router.get("/{alert_id}")
async def get_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém um alerta pelo ID.
    
    Args:
        alert_id: ID do alerta
        
    Returns:
        Dict[str, Any]: Alerta encontrado
    """
    # Verifica se o usuário tem permissão para acessar alertas
    if current_user.get("role") not in ["admin", "support"]:
        raise HTTPException(status_code=403, detail="Sem permissão para acessar alertas")
    
    try:
        alert = alert_manager.get_alert(alert_id)
        if alert is None:
            raise HTTPException(status_code=404, detail=f"Alerta não encontrado: {alert_id}")
        
        return alert.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter alerta: {str(e)}")

@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Resolve um alerta manualmente.
    
    Args:
        alert_id: ID do alerta
        
    Returns:
        Dict[str, Any]: Resultado da operação
    """
    # Verifica se o usuário tem permissão para resolver alertas
    if current_user.get("role") not in ["admin", "support"]:
        raise HTTPException(status_code=403, detail="Sem permissão para resolver alertas")
    
    try:
        alert = alert_manager.get_alert(alert_id)
        if alert is None:
            raise HTTPException(status_code=404, detail=f"Alerta não encontrado: {alert_id}")
        
        if alert.resolve():
            return {"success": True, "message": "Alerta resolvido com sucesso"}
        else:
            return {"success": False, "message": "Alerta não pôde ser resolvido"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao resolver alerta: {str(e)}")

@router.post("/threshold")
async def create_threshold_alert(
    name: str,
    description: str,
    metric_name: str,
    threshold: float,
    comparison: str = Query(..., regex="^(greater_than|less_than|equal_to|greater_than_or_equal|less_than_or_equal|not_equal_to)$"),
    severity: str = Query(..., regex="^(info|warning|error|critical)$"),
    auto_resolve: bool = True,
    auto_resolve_after: int = 3600,
    current_user: dict = Depends(get_current_user)
):
    """
    Cria um novo alerta baseado em limiar.
    
    Args:
        name: Nome do alerta
        description: Descrição do alerta
        metric_name: Nome da métrica a ser monitorada
        threshold: Valor limiar para comparação
        comparison: Tipo de comparação
        severity: Severidade do alerta
        auto_resolve: Se o alerta deve ser resolvido automaticamente
        auto_resolve_after: Tempo em segundos para resolução automática
        
    Returns:
        Dict[str, Any]: Alerta criado
    """
    # Verifica se o usuário tem permissão para criar alertas
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão para criar alertas")
    
    try:
        condition = ThresholdAlertCondition(
            name=name,
            description=description,
            metric_name=metric_name,
            threshold=threshold,
            comparison=comparison,
            severity=severity
        )
        
        from ..services.alert_system import Alert, log_alert_action, notification_alert_action
        
        alert = Alert(
            condition=condition,
            actions=[log_alert_action, notification_alert_action],
            auto_resolve=auto_resolve,
            auto_resolve_after=auto_resolve_after
        )
        
        alert_id = alert_manager.register_alert(alert)
        
        return {
            "success": True,
            "alert_id": alert_id,
            "alert": alert.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar alerta: {str(e)}")

@router.post("/pattern")
async def create_pattern_alert(
    name: str,
    description: str,
    log_pattern: str,
    log_level: Optional[str] = None,
    log_category: Optional[str] = None,
    severity: str = Query(..., regex="^(info|warning|error|critical)$"),
    auto_resolve: bool = False,
    auto_resolve_after: int = 3600,
    current_user: dict = Depends(get_current_user)
):
    """
    Cria um novo alerta baseado em padrão de texto.
    
    Args:
        name: Nome do alerta
        description: Descrição do alerta
        log_pattern: Padrão de texto a ser procurado nos logs
        log_level: Nível de log a ser filtrado (opcional)
        log_category: Categoria de log a ser filtrada (opcional)
        severity: Severidade do alerta
        auto_resolve: Se o alerta deve ser resolvido automaticamente
        auto_resolve_after: Tempo em segundos para resolução automática
        
    Returns:
        Dict[str, Any]: Alerta criado
    """
    # Verifica se o usuário tem permissão para criar alertas
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão para criar alertas")
    
    try:
        condition = PatternAlertCondition(
            name=name,
            description=description,
            log_pattern=log_pattern,
            log_level=log_level,
            log_category=log_category,
            severity=severity
        )
        
        from ..services.alert_system import Alert, log_alert_action, notification_alert_action, whatsapp_alert_action
        
        actions = [log_alert_action, notification_alert_action]
        
        # Para alertas críticos, adiciona notificação via WhatsApp
        if severity == "critical":
            actions.append(lambda a, c: whatsapp_alert_action(
                a, c, phone_numbers=["+5511999999999"]  # Número do administrador
            ))
        
        alert = Alert(
            condition=condition,
            actions=actions,
            auto_resolve=auto_resolve,
            auto_resolve_after=auto_resolve_after
        )
        
        alert_id = alert_manager.register_alert(alert)
        
        return {
            "success": True,
            "alert_id": alert_id,
            "alert": alert.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar alerta: {str(e)}")

@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Remove um alerta.
    
    Args:
        alert_id: ID do alerta
        
    Returns:
        Dict[str, Any]: Resultado da operação
    """
    # Verifica se o usuário tem permissão para remover alertas
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão para remover alertas")
    
    try:
        if alert_manager.unregister_alert(alert_id):
            return {"success": True, "message": "Alerta removido com sucesso"}
        else:
            raise HTTPException(status_code=404, detail=f"Alerta não encontrado: {alert_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover alerta: {str(e)}")

@router.get("/check")
async def check_alerts(
    current_user: dict = Depends(get_current_user)
):
    """
    Verifica todos os alertas registrados.
    
    Returns:
        List[Dict[str, Any]]: Lista de alertas disparados
    """
    # Verifica se o usuário tem permissão para verificar alertas
    if current_user.get("role") not in ["admin", "support"]:
        raise HTTPException(status_code=403, detail="Sem permissão para verificar alertas")
    
    try:
        triggered_alerts = alert_manager.check_alerts()
        return {"triggered_alerts": triggered_alerts, "count": len(triggered_alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar alertas: {str(e)}")
