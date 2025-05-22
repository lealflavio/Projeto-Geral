from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database, models, schemas, auth

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

@router.get("/me", response_model=schemas.UserResponse)
def get_me(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Retorna os dados do usuário autenticado.
    """
    return current_user

@router.put("/atualizar", response_model=schemas.UserResponse)
def atualizar_perfil(
    dados: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Atualiza nome, email ou whatsapp do usuário autenticado.
    """
    if dados.nome_completo:
        current_user.nome_completo = dados.nome_completo
    if dados.email:
        if auth.get_user_by_email(db, dados.email) and current_user.email != dados.email:
            raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
        current_user.email = dados.email
    if dados.whatsapp:
        if auth.get_user_by_whatsapp(db, dados.whatsapp) and current_user.whatsapp != dados.whatsapp:
            raise HTTPException(status_code=400, detail="WhatsApp já cadastrado.")
        current_user.whatsapp = dados.whatsapp
    if dados.senha:
        current_user.hashed_password = auth.get_password_hash(dados.senha)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/integrar", response_model=schemas.UserResponse)
def integrar_portal_k1(
    dados: schemas.UpdatePortalCredentials,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Atualiza ou integra usuário com o portal K1.
    """
    if dados.usuario_portal is not None:
        current_user.usuario_portal = dados.usuario_portal
    if dados.senha_portal is not None:
        current_user.senha_portal = dados.senha_portal
    db.commit()
    db.refresh(current_user)
    return current_user
