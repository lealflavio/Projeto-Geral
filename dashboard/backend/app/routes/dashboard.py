from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional # Import List
from .. import database, models, schemas, auth # Adjusted imports

router = APIRouter(
    prefix="/me", # All routes in this file will be under /me
    tags=["User Dashboard"],
    dependencies=[Depends(auth.get_current_active_user)] # Protect all routes here
)

@router.get("/saldo", response_model=schemas.UserResponse)
async def get_user_balance(current_user: models.User = Depends(auth.get_current_active_user)):
    """Retrieve the current authenticated user's details, including credit balance."""
    return current_user

@router.post("/adicionar_creditos", response_model=schemas.UserResponse)
async def add_credits_to_user(
    request: schemas.AddCreditsRequest, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Fictitious endpoint to add credits to the current user for testing purposes.
    """
    if request.creditos <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A quantidade de créditos a adicionar deve ser positiva.")
    
    current_user.creditos += request.creditos
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/transferir_creditos", response_model=schemas.UserResponse)
async def transfer_credits(
    request: schemas.TransferCreditsRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Transfer credits from the current authenticated user to another user (identified by email).
    """
    if request.creditos <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A quantidade de créditos a transferir deve ser positiva.")

    if current_user.email == request.email_destino:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não é permitido transferir créditos para si mesmo.")

    if current_user.creditos < request.creditos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Saldo de créditos insuficiente para realizar a transferência.")

    destination_user = auth.get_user_by_email(db, email=request.email_destino)
    if not destination_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Usuário de destino com email \'{request.email_destino}\' não encontrado.")

    current_user.creditos -= request.creditos
    destination_user.creditos += request.creditos

    db.add(current_user)
    db.add(destination_user)
    db.commit()
    db.refresh(current_user)
    return current_user

# --- WOs and KPIs Endpoints (Etapa 6) ---

@router.post("/wos", response_model=schemas.WOResponse)
async def create_wo_for_current_user(
    wo_data: schemas.WOCreate, # WOCreate now includes tipo_servico
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Create a new Work Order (WO) for the authenticated user. For testing purposes."""
    new_wo = models.WO(
        numero_wo=wo_data.numero_wo,
        tecnico_id=current_user.id, 
        status=wo_data.status,
        tipo_servico=wo_data.tipo_servico, # Ensure tipo_servico is passed from wo_data
        causa_erro=wo_data.causa_erro
    )
    db.add(new_wo)
    db.commit()
    db.refresh(new_wo)
    return new_wo

@router.get("/wos", response_model=List[schemas.WOResponse])
async def get_user_wos(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Retrieve Work Orders (WOs) for the authenticated user, optionally filtered by status."""
    query = db.query(models.WO).filter(models.WO.tecnico_id == current_user.id)
    if status_filter:
        query = query.filter(models.WO.status == status_filter)
    wos = query.order_by(models.WO.data.desc()).all()
    return wos

@router.get("/kpis")
async def get_user_kpis(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Retrieve Key Performance Indicators (KPIs) for the authenticated user's WOs."""
    total_wos = db.query(func.count(models.WO.id)).filter(models.WO.tecnico_id == current_user.id).scalar() or 0
    wos_concluidas = db.query(func.count(models.WO.id)).filter(
        models.WO.tecnico_id == current_user.id,
        models.WO.status == "concluida"
    ).scalar() or 0
    wos_erro = db.query(func.count(models.WO.id)).filter(
        models.WO.tecnico_id == current_user.id,
        models.WO.status == "erro"
    ).scalar() or 0
    percent_concluidas = (wos_concluidas / total_wos * 100) if total_wos > 0 else 0
    percent_erro = (wos_erro / total_wos * 100) if total_wos > 0 else 0
    return {
        "total_wos": total_wos,
        "wos_concluidas": wos_concluidas,
        "wos_com_erro": wos_erro,
        "percentual_concluidas": round(percent_concluidas, 2),
        "percentual_com_erro": round(percent_erro, 2)
    }

# --- Service Values for Earnings Simulator (Etapa 7) ---

@router.post("/valores_servicos", response_model=schemas.ServiceValueResponse)
async def create_or_update_service_value(
    service_value_data: schemas.ServiceValueCreate, # Changed to ServiceValueCreate
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Create a new service value or update an existing one for the authenticated user."""
    existing_value = db.query(models.ServiceValue).filter(
        models.ServiceValue.tecnico_id == current_user.id,
        models.ServiceValue.tipo_servico == service_value_data.tipo_servico
    ).first()

    if existing_value:
        existing_value.valor = service_value_data.valor
        db.add(existing_value)
        db.commit()
        db.refresh(existing_value)
        return existing_value
    else:
        new_service_value = models.ServiceValue(
            tipo_servico=service_value_data.tipo_servico,
            valor=service_value_data.valor,
            tecnico_id=current_user.id
        )
        db.add(new_service_value)
        db.commit()
        db.refresh(new_service_value)
        return new_service_value

@router.get("/valores_servicos", response_model=List[schemas.ServiceValueResponse])
async def get_user_service_values(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Retrieve all service values for the authenticated user."""
    service_values = db.query(models.ServiceValue).filter(models.ServiceValue.tecnico_id == current_user.id).all()
    return service_values

