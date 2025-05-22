from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database, models, schemas, auth
from app.services.tecnico_setup import criar_estrutura_tecnico
from app.services.notificacoes import enviar_notificacao_boas_vindas

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

@router.put("/editar", response_model=schemas.UserResponse)
def editar_perfil(
    dados: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Atualizar campos permitidos
    if dados.nome_completo:
        current_user.nome_completo = dados.nome_completo
    if dados.email:
        # Verifica se o novo e-mail já existe
        if auth.get_user_by_email(db, dados.email) and current_user.email != dados.email:
            raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
        current_user.email = dados.email
    if dados.whatsapp:
        if auth.get_user_by_whatsapp(db, dados.whatsapp) and current_user.whatsapp != dados.whatsapp:
            raise HTTPException(status_code=400, detail="WhatsApp já cadastrado.")
        current_user.whatsapp = dados.whatsapp
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/atualizar-credenciais", response_model=schemas.UserResponse)
def atualizar_credenciais_portal(
    dados: schemas.UpdatePortalCredentials,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Atualizar apenas os campos permitidos
    if dados.usuario_portal:
        current_user.usuario_portal = dados.usuario_portal
    if dados.senha_portal:
        current_user.senha_portal = dados.senha_portal
    db.commit()
    db.refresh(current_user)
    # (Opcional) chamar integração/estrutura ou notificações se quiser
    return current_user
