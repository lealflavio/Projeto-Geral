"""
Serviço para gerenciamento do sistema de créditos.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, BackgroundTasks
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from .. import models, schemas

def verificar_creditos(db: Session, usuario_id: int) -> Tuple[bool, int, str]:
    """
    Verifica se o usuário possui créditos suficientes.
    Retorna uma tupla com (tem_creditos_suficientes, saldo_atual, mensagem).
    """
    usuario = db.query(models.User).filter(models.User.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )
    
    tem_creditos = usuario.creditos > 0
    mensagem = (
        f"Usuário possui {usuario.creditos} créditos disponíveis." 
        if tem_creditos else 
        "Créditos insuficientes para processar PDF."
    )
    
    return tem_creditos, usuario.creditos, mensagem

def consumir_credito(
    db: Session, 
    usuario_id: int, 
    background_tasks: BackgroundTasks,
    detalhes: str = "Consumo de crédito para processamento de PDF"
) -> models.User:
    """
    Consome um crédito do usuário.
    Registra a operação no log e envia alerta se necessário.
    Retorna o usuário atualizado.
    """
    usuario = db.query(models.User).filter(models.User.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )
    
    if usuario.creditos <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Créditos insuficientes para processar PDF."
        )
    
    saldo_anterior = usuario.creditos
    usuario.creditos -= 1
    
    # Registra a operação no log
    log = models.CreditoLog(
        usuario_id=usuario.id,
        operacao="consumo",
        quantidade=1,
        saldo_anterior=saldo_anterior,
        saldo_atual=usuario.creditos,
        detalhes=detalhes
    )
    
    db.add(log)
    db.commit()
    db.refresh(usuario)
    
    # Verifica se é necessário enviar alerta de créditos baixos
    if usuario.creditos <= 2:
        background_tasks.add_task(
            enviar_alerta_creditos_baixos, 
            usuario.email, 
            usuario.whatsapp, 
            usuario.creditos
        )
    
    return usuario

def adicionar_creditos(
    db: Session, 
    usuario_id: int, 
    quantidade: int,
    detalhes: str = "Adição de créditos via API"
) -> models.User:
    """
    Adiciona créditos ao usuário.
    Registra a operação no log.
    Retorna o usuário atualizado.
    """
    if quantidade <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A quantidade de créditos a adicionar deve ser positiva."
        )
    
    usuario = db.query(models.User).filter(models.User.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )
    
    saldo_anterior = usuario.creditos
    usuario.creditos += quantidade
    
    # Registra a operação no log
    log = models.CreditoLog(
        usuario_id=usuario.id,
        operacao="adicao",
        quantidade=quantidade,
        saldo_anterior=saldo_anterior,
        saldo_atual=usuario.creditos,
        detalhes=detalhes
    )
    
    db.add(log)
    db.commit()
    db.refresh(usuario)
    
    return usuario

def transferir_creditos(
    db: Session, 
    usuario_origem_id: int, 
    email_destino: str, 
    quantidade: int
) -> models.User:
    """
    Transfere créditos entre usuários.
    Registra a operação no log para ambos os usuários.
    Retorna o usuário de origem atualizado.
    """
    if quantidade <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A quantidade de créditos a transferir deve ser positiva."
        )
    
    usuario_origem = db.query(models.User).filter(models.User.id == usuario_origem_id).first()
    if not usuario_origem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário de origem não encontrado."
        )
    
    usuario_destino = db.query(models.User).filter(models.User.email == email_destino).first()
    if not usuario_destino:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário de destino com email '{email_destino}' não encontrado."
        )
    
    if usuario_origem.id == usuario_destino.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é permitido transferir créditos para si mesmo."
        )
    
    if usuario_origem.creditos < quantidade:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Saldo de créditos insuficiente para realizar a transferência."
        )
    
    saldo_anterior_origem = usuario_origem.creditos
    saldo_anterior_destino = usuario_destino.creditos
    
    usuario_origem.creditos -= quantidade
    usuario_destino.creditos += quantidade
    
    # Registra a operação no log para o usuário de origem
    log_origem = models.CreditoLog(
        usuario_id=usuario_origem.id,
        operacao="transferencia_saida",
        quantidade=quantidade,
        saldo_anterior=saldo_anterior_origem,
        saldo_atual=usuario_origem.creditos,
        detalhes=f"Transferência de créditos para {usuario_destino.email}"
    )
    
    # Registra a operação no log para o usuário de destino
    log_destino = models.CreditoLog(
        usuario_id=usuario_destino.id,
        operacao="transferencia_entrada",
        quantidade=quantidade,
        saldo_anterior=saldo_anterior_destino,
        saldo_atual=usuario_destino.creditos,
        detalhes=f"Transferência de créditos recebida de {usuario_origem.email}"
    )
    
    db.add(log_origem)
    db.add(log_destino)
    db.add(usuario_origem)
    db.add(usuario_destino)
    db.commit()
    db.refresh(usuario_origem)
    
    return usuario_origem

def obter_historico_creditos(db: Session, usuario_id: int, limit: int = 50):
    """
    Retorna o histórico de operações de crédito do usuário.
    """
    return db.query(models.CreditoLog).filter(
        models.CreditoLog.usuario_id == usuario_id
    ).order_by(models.CreditoLog.data.desc()).limit(limit).all()

async def enviar_alerta_creditos_baixos(email: str, whatsapp: Optional[str], saldo: int):
    """
    Envia alerta de créditos baixos por email e WhatsApp (se disponível).
    Esta função é executada em background.
    """
    # Implementação do envio de email
    print(f"Enviando alerta de créditos baixos para {email}. Saldo atual: {saldo}")
    
    # Implementação do envio de WhatsApp (se disponível)
    if whatsapp:
        print(f"Enviando alerta de créditos baixos por WhatsApp para {whatsapp}. Saldo atual: {saldo}")
