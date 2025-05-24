"""
Rotas para gerenciamento do sistema de créditos.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from .. import models, schemas, auth
from ..database import get_db
from ..services import creditos as creditos_service

router = APIRouter(
    prefix="/api/creditos",
    tags=["creditos"],
    responses={404: {"description": "Not found"}}
)

@router.get("/saldo", response_model=schemas.UserResponse)
async def obter_saldo_creditos(
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Retorna o saldo de créditos do usuário autenticado.
    """
    return current_user

@router.post("/verificar", response_model=schemas.UserResponse)
async def verificar_creditos(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Verifica se o usuário possui créditos suficientes para processar um PDF.
    Retorna erro 403 se não houver créditos suficientes.
    """
    if current_user.creditos <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Créditos insuficientes para processar PDF."
        )
    return current_user

@router.post("/consumir", response_model=schemas.UserResponse)
async def consumir_credito(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Consome um crédito do usuário autenticado.
    Retorna erro 403 se não houver créditos suficientes.
    """
    return creditos_service.consumir_credito(
        db=db,
        usuario_id=current_user.id,
        background_tasks=background_tasks
    )

@router.post("/adicionar", response_model=schemas.UserResponse)
async def adicionar_creditos(
    request: schemas.AddCreditsRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Adiciona créditos ao usuário autenticado.
    Requer permissão de administrador ou integração com sistema de pagamento.
    """
    return creditos_service.adicionar_creditos(
        db=db,
        usuario_id=current_user.id,
        quantidade=request.creditos
    )

@router.post("/transferir", response_model=schemas.UserResponse)
async def transferir_creditos(
    request: schemas.TransferCreditsRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Transfere créditos do usuário autenticado para outro usuário.
    """
    return creditos_service.transferir_creditos(
        db=db,
        usuario_origem_id=current_user.id,
        email_destino=request.email_destino,
        quantidade=request.creditos
    )

@router.get("/historico", response_model=List[schemas.CreditoLogResponse])
async def obter_historico_creditos(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Retorna o histórico de operações de crédito do usuário autenticado.
    """
    return creditos_service.obter_historico_creditos(
        db=db,
        usuario_id=current_user.id,
        limit=limit
    )
