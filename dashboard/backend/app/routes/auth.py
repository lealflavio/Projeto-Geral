from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.services.tecnico_setup import criar_estrutura_tecnico
from .. import database, models, schemas, auth
from app.services.email_service import send_reset_email
import os

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user_email = auth.get_user_by_email(db, email=user.email)
    if db_user_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    if user.whatsapp:
        db_user_whatsapp = auth.get_user_by_whatsapp(db, whatsapp=user.whatsapp)
        if db_user_whatsapp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="WhatsApp number already registered")

    hashed_password = auth.get_password_hash(user.senha)

    new_user = models.User(
        nome_completo=user.nome_completo,
        email=user.email,
        senha_hash=hashed_password,
        whatsapp=user.whatsapp,
        usuario_portal=user.usuario_portal,
        senha_portal=user.senha_portal
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if user.usuario_portal and user.senha_portal:
        try:
            criar_estrutura_tecnico(
                nome_completo=user.nome_completo,
                email=user.email,
                usuario_portal=user.usuario_portal,
                senha_portal=user.senha_portal
            )
        except Exception as e:
            print(f"[ERRO] Falha ao criar estrutura de técnico: {e}")

    return new_user

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    user = auth.get_user_by_email(db, email=form_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not auth.verify_password(form_data.senha, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user

# --- Esqueci minha senha ---
@router.post("/forgot-password")
def forgot_password(request: schemas.ForgotPasswordRequest, db: Session = Depends(database.get_db)):
    user = auth.get_user_by_email(db, email=request.email)
    # Sempre retorna sucesso, mesmo se o usuário não existe (para evitar enumeração)
    if not user:
        return {"message": "Se o e-mail existir, enviaremos instruções para recuperação."}

    token, expires = auth.set_reset_token_for_user(db, user)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/resetar-senha?token={token}"
    send_reset_email(user.email, reset_link)
    return {"message": "Se o e-mail existir, enviaremos instruções para recuperação."}

@router.post("/reset-password")
def reset_password(request: schemas.ResetPasswordRequest, db: Session = Depends(database.get_db)):
    user = auth.verify_reset_token(db, request.token)
    if not user:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    user.senha_hash = auth.get_password_hash(request.nova_senha)
    auth.clear_reset_token(user, db)
    db.commit()
    return {"message": "Senha alterada com sucesso."}
