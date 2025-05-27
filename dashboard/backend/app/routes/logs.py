import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from ..services.logging_system import logging_system, LogLevel, LogCategory
from ..auth import get_current_user

router = APIRouter(
    prefix="/api/logs",
    tags=["logs"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def get_logs(
    level: Optional[str] = None,
    category: Optional[str] = None,
    user_id: Optional[int] = None,
    request_id: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém logs com filtros opcionais.
    
    Args:
        level: Filtrar por nível de log (debug, info, warning, error, critical)
        category: Filtrar por categoria
        user_id: Filtrar por ID de usuário
        request_id: Filtrar por ID de requisição
        start_time: Timestamp inicial (formato ISO)
        end_time: Timestamp final (formato ISO)
        limit: Número máximo de logs a retornar
        
    Returns:
        List[Dict[str, Any]]: Lista de logs filtrados
    """
    # Verifica se o usuário tem permissão para acessar logs
    if current_user.get("role") not in ["admin", "support"]:
        raise HTTPException(status_code=403, detail="Sem permissão para acessar logs")
    
    try:
        logs = logging_system.get_logs(
            level=level,
            category=category,
            user_id=user_id,
            request_id=request_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logging_system.error(f"Erro ao obter logs: {str(e)}", category=LogCategory.API)
        raise HTTPException(status_code=500, detail=f"Erro ao obter logs: {str(e)}")

@router.get("/file/{date}")
async def get_logs_from_file(
    date: str,
    level: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém logs de um arquivo específico.
    
    Args:
        date: Data no formato YYYY-MM-DD
        level: Filtrar por nível de log
        category: Filtrar por categoria
        limit: Número máximo de logs a retornar
        
    Returns:
        List[Dict[str, Any]]: Lista de logs filtrados
    """
    # Verifica se o usuário tem permissão para acessar logs
    if current_user.get("role") not in ["admin", "support"]:
        raise HTTPException(status_code=403, detail="Sem permissão para acessar logs")
    
    try:
        logs = logging_system.get_logs_from_file(
            date=date,
            level=level,
            category=category,
            limit=limit
        )
        
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logging_system.error(f"Erro ao obter logs do arquivo: {str(e)}", category=LogCategory.API)
        raise HTTPException(status_code=500, detail=f"Erro ao obter logs do arquivo: {str(e)}")

@router.get("/dates")
async def get_log_dates(
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém datas disponíveis para arquivos de log.
    
    Returns:
        List[str]: Lista de datas disponíveis no formato YYYY-MM-DD
    """
    # Verifica se o usuário tem permissão para acessar logs
    if current_user.get("role") not in ["admin", "support"]:
        raise HTTPException(status_code=403, detail="Sem permissão para acessar logs")
    
    try:
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        dates = []
        
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                if file.startswith("wondercom-") and file.endswith(".log"):
                    date_str = file[10:-4]  # Extrai YYYY-MM-DD de wondercom-YYYY-MM-DD.log
                    dates.append(date_str)
        
        return {"dates": sorted(dates, reverse=True)}
    except Exception as e:
        logging_system.error(f"Erro ao obter datas de logs: {str(e)}", category=LogCategory.API)
        raise HTTPException(status_code=500, detail=f"Erro ao obter datas de logs: {str(e)}")

@router.get("/statistics")
async def get_log_statistics(
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém estatísticas de logs para os últimos N dias.
    
    Args:
        days: Número de dias para análise
        
    Returns:
        Dict[str, Any]: Estatísticas de logs
    """
    # Verifica se o usuário tem permissão para acessar logs
    if current_user.get("role") not in ["admin", "support"]:
        raise HTTPException(status_code=403, detail="Sem permissão para acessar estatísticas")
    
    try:
        # Calcula data inicial
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Inicializa estatísticas
        stats = {
            "total_logs": 0,
            "by_level": {},
            "by_category": {},
            "by_day": {},
            "error_rate": 0.0
        }
        
        # Processa cada dia
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            day_logs = logging_system.get_logs_from_file(date=date_str)
            
            # Inicializa contagem para o dia
            stats["by_day"][date_str] = {
                "total": len(day_logs),
                "by_level": {},
                "by_category": {}
            }
            
            # Atualiza contagem total
            stats["total_logs"] += len(day_logs)
            
            # Processa cada log
            for log in day_logs:
                level = log.get("level", "unknown")
                category = log.get("category", "unknown")
                
                # Atualiza contagem por nível
                stats["by_level"][level] = stats["by_level"].get(level, 0) + 1
                stats["by_day"][date_str]["by_level"][level] = stats["by_day"][date_str]["by_level"].get(level, 0) + 1
                
                # Atualiza contagem por categoria
                stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
                stats["by_day"][date_str]["by_category"][category] = stats["by_day"][date_str]["by_category"].get(category, 0) + 1
            
            # Avança para o próximo dia
            current_date += timedelta(days=1)
        
        # Calcula taxa de erro
        error_count = stats["by_level"].get(LogLevel.ERROR, 0) + stats["by_level"].get(LogLevel.CRITICAL, 0)
        if stats["total_logs"] > 0:
            stats["error_rate"] = (error_count / stats["total_logs"]) * 100
        
        return stats
    except Exception as e:
        logging_system.error(f"Erro ao obter estatísticas de logs: {str(e)}", category=LogCategory.API)
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas de logs: {str(e)}")

@router.post("/test")
async def create_test_log(
    level: str = Query(LogLevel.INFO),
    category: str = Query(LogCategory.SYSTEM),
    message: str = Query("Teste de log via API"),
    current_user: dict = Depends(get_current_user)
):
    """
    Cria um log de teste.
    
    Args:
        level: Nível do log
        category: Categoria do log
        message: Mensagem do log
        
    Returns:
        Dict[str, Any]: Detalhes do log criado
    """
    # Verifica se o usuário tem permissão para criar logs
    if current_user.get("role") not in ["admin", "support"]:
        raise HTTPException(status_code=403, detail="Sem permissão para criar logs")
    
    try:
        # Valida nível do log
        if level not in [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]:
            raise ValueError(f"Nível de log inválido: {level}")
        
        # Cria log
        log_id = logging_system.log(
            message=message,
            level=level,
            category=category,
            user_id=current_user.get("id"),
            extra={"source": "api", "test": True}
        )
        
        return {"success": True, "log_id": log_id, "message": "Log de teste criado com sucesso"}
    except Exception as e:
        logging_system.error(f"Erro ao criar log de teste: {str(e)}", category=LogCategory.API)
        raise HTTPException(status_code=500, detail=f"Erro ao criar log de teste: {str(e)}")
