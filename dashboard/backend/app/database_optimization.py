"""
Otimizações de queries e performance do banco de dados.
"""
from sqlalchemy import Index, func, desc, select
from sqlalchemy.orm import joinedload, contains_eager
from sqlalchemy.ext.declarative import declared_attr

from app.database import Base, engine
from app.models import User, CreditoLog

# Adiciona índices para colunas frequentemente consultadas
Index('ix_user_email', User.email)
Index('ix_user_whatsapp', User.whatsapp)
Index('ix_creditolog_usuario_id', CreditoLog.usuario_id)
Index('ix_creditolog_data', CreditoLog.data)  # Corrigido: usando 'data' em vez de 'data_operacao'

# Função para obter histórico de créditos com paginação otimizada
def obter_historico_creditos_otimizado(db, usuario_id, limit=50, offset=0):
    """
    Versão otimizada da função para obter histórico de créditos.
    Utiliza select específico, índices e paginação.
    
    Args:
        db: Sessão do banco de dados
        usuario_id: ID do usuário
        limit: Limite de registros (padrão: 50)
        offset: Deslocamento para paginação
        
    Returns:
        Lista de registros de log de créditos
    """
    query = (
        select(CreditoLog)
        .where(CreditoLog.usuario_id == usuario_id)
        .order_by(desc(CreditoLog.data))  # Corrigido: usando 'data' em vez de 'data_operacao'
        .limit(limit)
        .offset(offset)
    )
    
    result = db.execute(query)
    return result.scalars().all()

# Função para buscar usuário por email de forma otimizada
def buscar_usuario_por_email_otimizado(db, email):
    """
    Versão otimizada da função para buscar usuário por email.
    Utiliza select específico e índice.
    
    Args:
        db: Sessão do banco de dados
        email: Email do usuário
        
    Returns:
        Usuário encontrado ou None
    """
    query = (
        select(User)
        .where(User.email == email)
    )
    
    result = db.execute(query)
    return result.scalar_one_or_none()

# Função para listar usuários com paginação
def listar_usuarios_otimizado(db, limit=50, offset=0, busca=None):
    """
    Versão otimizada da função para listar usuários.
    Utiliza select específico, filtros eficientes e paginação.
    
    Args:
        db: Sessão do banco de dados
        limit: Limite de registros (padrão: 50)
        offset: Deslocamento para paginação
        busca: Termo de busca opcional
        
    Returns:
        Lista de usuários
    """
    query = select(User)
    
    if busca:
        query = query.where(
            (User.nome_completo.ilike(f"%{busca}%")) |
            (User.email.ilike(f"%{busca}%")) |
            (User.whatsapp.ilike(f"%{busca}%"))
        )
    
    query = query.order_by(User.nome_completo).limit(limit).offset(offset)
    
    result = db.execute(query)
    return result.scalars().all()

# Função para contar total de registros (para paginação)
def contar_total_registros(db, model, filtro=None):
    """
    Função otimizada para contar total de registros.
    Utiliza count() diretamente no banco.
    
    Args:
        db: Sessão do banco de dados
        model: Modelo a ser contado
        filtro: Filtro opcional
        
    Returns:
        Total de registros
    """
    query = select(func.count()).select_from(model)
    
    if filtro:
        query = query.where(filtro)
    
    result = db.execute(query)
    return result.scalar_one()

# Função para criar índices no banco de dados
def criar_indices():
    """
    Cria índices no banco de dados.
    Deve ser chamada durante a inicialização da aplicação.
    """
    # Cria os índices definidos acima
    Base.metadata.create_all(bind=engine)
