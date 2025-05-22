import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import database, models, schemas, auth

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

# Regex: apenas letras minúsculas (sem acento), ponto obrigatório, nada mais
USUARIO_PORTAL_REGEX = re.compile(r"^[a-z]+\.[a-z]+$")

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
    Atualiza nome, email, whatsapp ou senha do usuário autenticado.
    """
    atualizou = False
    if dados.nome_completo:
        current_user.nome_completo = dados.nome_completo.strip()
        atualizou = True
    if dados.email:
        email = dados.email.strip().lower()
        if auth.get_user_by_email(db, email) and current_user.email != email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail já cadastrado."
            )
        current_user.email = email
        atualizou = True
    if dados.whatsapp:
        whatsapp = dados.whatsapp.strip()
        if auth.get_user_by_whatsapp(db, whatsapp) and current_user.whatsapp != whatsapp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="WhatsApp já cadastrado."
            )
        current_user.whatsapp = whatsapp
        atualizou = True
    if dados.senha:
        current_user.hashed_password = auth.get_password_hash(dados.senha)
        atualizou = True

    if not atualizou:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado informado para atualização."
        )
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
    Atualiza/integra usuário com o portal K1.
    Só aceita usuario_portal no formato nome.sobrenome, apenas letras minúsculas e um ponto.
    """
    atualizou = False
    if dados.usuario_portal is not None and dados.usuario_portal.strip() != "":
        valor = dados.usuario_portal.strip()
        if not USUARIO_PORTAL_REGEX.fullmatch(valor):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O usuário do portal deve ser no formato nome.sobrenome, apenas letras minúsculas e um ponto."
            )
        current_user.usuario_portal = valor
        atualizou = True
    if dados.senha_portal is not None and dados.senha_portal.strip() != "":
        current_user.senha_portal = dados.senha_portal.strip()
        atualizou = True

    if not atualizou:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe usuário e/ou senha do portal para integrar."
        )

    db.commit()
    db.refresh(current_user)
    return current_user
