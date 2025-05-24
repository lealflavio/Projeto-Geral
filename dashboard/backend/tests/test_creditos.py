"""
Testes para o sistema de créditos.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import User, CreditoLog
from app.auth import get_password_hash

# Configuração do banco de dados de teste
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Sobrescreve a dependência get_db para usar o banco de teste
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def test_db():
    # Cria as tabelas no banco de teste
    Base.metadata.create_all(bind=engine)
    
    # Cria usuários de teste
    db = TestingSessionLocal()
    
    # Usuário 1 - com créditos
    user1 = User(
        nome_completo="Técnico Teste 1",
        email="tecnico1@teste.com",
        senha_hash=get_password_hash("senha123"),
        whatsapp="123456789",
        creditos=10
    )
    
    # Usuário 2 - sem créditos
    user2 = User(
        nome_completo="Técnico Teste 2",
        email="tecnico2@teste.com",
        senha_hash=get_password_hash("senha123"),
        whatsapp="987654321",
        creditos=0
    )
    
    db.add(user1)
    db.add(user2)
    db.commit()
    
    yield db
    
    # Limpa o banco após os testes
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_verificar_creditos_com_saldo(test_db):
    # Login para obter token
    login_response = client.post(
        "/auth/login",
        json={"email": "tecnico1@teste.com", "senha": "senha123"}
    )
    token = login_response.json()["access_token"]
    
    # Verifica créditos
    response = client.post(
        "/api/creditos/verificar",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["creditos"] == 10

def test_verificar_creditos_sem_saldo(test_db):
    # Login para obter token
    login_response = client.post(
        "/auth/login",
        json={"email": "tecnico2@teste.com", "senha": "senha123"}
    )
    token = login_response.json()["access_token"]
    
    # Verifica créditos
    response = client.post(
        "/api/creditos/verificar",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "Créditos insuficientes" in response.json()["detail"]

def test_consumir_credito_com_saldo(test_db):
    # Login para obter token
    login_response = client.post(
        "/auth/login",
        json={"email": "tecnico1@teste.com", "senha": "senha123"}
    )
    token = login_response.json()["access_token"]
    
    # Consome crédito
    response = client.post(
        "/api/creditos/consumir",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["creditos"] == 9
    
    # Verifica se o log foi criado
    user = test_db.query(User).filter(User.email == "tecnico1@teste.com").first()
    log = test_db.query(CreditoLog).filter(CreditoLog.usuario_id == user.id).first()
    
    assert log is not None
    assert log.operacao == "consumo"
    assert log.quantidade == 1
    assert log.saldo_anterior == 10
    assert log.saldo_atual == 9

def test_consumir_credito_sem_saldo(test_db):
    # Login para obter token
    login_response = client.post(
        "/auth/login",
        json={"email": "tecnico2@teste.com", "senha": "senha123"}
    )
    token = login_response.json()["access_token"]
    
    # Tenta consumir crédito
    response = client.post(
        "/api/creditos/consumir",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "Créditos insuficientes" in response.json()["detail"]

def test_adicionar_creditos(test_db):
    # Login para obter token
    login_response = client.post(
        "/auth/login",
        json={"email": "tecnico2@teste.com", "senha": "senha123"}
    )
    token = login_response.json()["access_token"]
    
    # Adiciona créditos
    response = client.post(
        "/api/creditos/adicionar",
        headers={"Authorization": f"Bearer {token}"},
        json={"creditos": 5}
    )
    
    assert response.status_code == 200
    assert response.json()["creditos"] == 5
    
    # Verifica se o log foi criado
    user = test_db.query(User).filter(User.email == "tecnico2@teste.com").first()
    log = test_db.query(CreditoLog).filter(CreditoLog.usuario_id == user.id).first()
    
    assert log is not None
    assert log.operacao == "adicao"
    assert log.quantidade == 5
    assert log.saldo_anterior == 0
    assert log.saldo_atual == 5

def test_transferir_creditos(test_db):
    # Login para obter token
    login_response = client.post(
        "/auth/login",
        json={"email": "tecnico1@teste.com", "senha": "senha123"}
    )
    token = login_response.json()["access_token"]
    
    # Transfere créditos
    response = client.post(
        "/api/creditos/transferir",
        headers={"Authorization": f"Bearer {token}"},
        json={"email_destino": "tecnico2@teste.com", "creditos": 3}
    )
    
    assert response.status_code == 200
    # Verificar o saldo atual retornado pela API
    saldo_atual = response.json()["creditos"]
    assert saldo_atual == 7  # 10 - 3 = 7
    
    # Verifica se os logs foram criados
    user1 = test_db.query(User).filter(User.email == "tecnico1@teste.com").first()
    user2 = test_db.query(User).filter(User.email == "tecnico2@teste.com").first()
    
    log1 = test_db.query(CreditoLog).filter(
        CreditoLog.usuario_id == user1.id,
        CreditoLog.operacao == "transferencia_saida"
    ).first()
    
    log2 = test_db.query(CreditoLog).filter(
        CreditoLog.usuario_id == user2.id,
        CreditoLog.operacao == "transferencia_entrada"
    ).first()
    
    assert log1 is not None
    assert log1.quantidade == 3
    assert log1.saldo_anterior == 10
    assert log1.saldo_atual == 7
    
    assert log2 is not None
    assert log2.quantidade == 3
    assert log2.saldo_anterior == 0
    assert log2.saldo_atual == 3
    
    # Verifica se o saldo do usuário 2 foi atualizado
    user2 = test_db.query(User).filter(User.email == "tecnico2@teste.com").first()
    assert user2.creditos == 3

def test_obter_historico_creditos(test_db):
    # Criar um novo usuário para este teste específico
    user_test = User(
        nome_completo="Técnico Teste Histórico",
        email="tecnico_historico@teste.com",
        senha_hash=get_password_hash("senha123"),
        whatsapp="555555555",
        creditos=10
    )
    test_db.add(user_test)
    test_db.commit()
    
    # Login para obter token
    login_response = client.post(
        "/auth/login",
        json={"email": "tecnico_historico@teste.com", "senha": "senha123"}
    )
    token = login_response.json()["access_token"]
    
    # Consome crédito
    client.post(
        "/api/creditos/consumir",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Transfere créditos
    client.post(
        "/api/creditos/transferir",
        headers={"Authorization": f"Bearer {token}"},
        json={"email_destino": "tecnico2@teste.com", "creditos": 2}
    )
    
    # Obtém histórico
    response = client.get(
        "/api/creditos/historico",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    historico = response.json()
    
    # Deve haver pelo menos 2 operações (consumo e transferência)
    assert len(historico) >= 2
    
    # Verifica se as operações estão no histórico
    operacoes = [log["operacao"] for log in historico]
    assert "consumo" in operacoes
    assert "transferencia_saida" in operacoes
