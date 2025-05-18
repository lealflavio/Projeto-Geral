from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database, models, schemas, auth
from app.services.tecnico_setup import criar_estrutura_tecnico
from app.services.notificacoes import enviar_notificacao_boas_vindas

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

@router.put("/integrar", response_model=schemas.UserResponse)
def integrar_portal(
    dados: schemas.PortalIntegrationRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Atualiza os dados do usuário
    current_user.usuario_portal = dados.usuario_portal
    current_user.senha_portal = dados.senha_portal
    current_user.whatsapp = dados.whatsapp
    db.commit()

    try:
        criar_estrutura_tecnico(
            nome_completo=current_user.nome_completo,
            email=current_user.email,
            usuario_portal=dados.usuario_portal,
            senha_portal=dados.senha_portal
        )

        # Envia WhatsApp com link da pasta
        enviar_notificacao_boas_vindas(dados.whatsapp, current_user.nome_completo)

    except Exception as e:
        print(f"[ERRO] Integração falhou: {e}")
        raise HTTPException(status_code=500, detail="Erro ao integrar técnico")

    return current_user
