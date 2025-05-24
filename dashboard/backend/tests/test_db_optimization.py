"""
Script para testar as otimizações de banco de dados.
"""
import sys
import os
import time
import statistics

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from app.models import User, CreditoLog, Base
from app.database_optimization import (
    obter_historico_creditos_otimizado,
    buscar_usuario_por_email_otimizado,
    listar_usuarios_otimizado,
    contar_total_registros
)

# Configuração do banco de dados de teste em memória
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def criar_tabelas_e_dados_teste():
    """Cria as tabelas e insere dados de teste."""
    # Cria as tabelas
    Base.metadata.create_all(bind=engine)
    
    # Cria a sessão
    db = SessionLocal()
    
    # Insere usuários de teste
    usuarios = [
        User(
            nome_completo="Técnico Teste 1",
            email="tecnico1@teste.com",
            senha_hash="hash123",
            whatsapp="123456789",
            creditos=10
        ),
        User(
            nome_completo="Técnico Teste 2",
            email="tecnico2@teste.com",
            senha_hash="hash123",
            whatsapp="987654321",
            creditos=5
        ),
        User(
            nome_completo="Admin Wondercom",
            email="admin@wondercom.com",
            senha_hash="hash123",
            whatsapp="555555555",
            creditos=100
        )
    ]
    
    db.add_all(usuarios)
    db.commit()
    
    # Busca os usuários para obter IDs
    usuario1 = db.query(User).filter(User.email == "tecnico1@teste.com").first()
    usuario2 = db.query(User).filter(User.email == "tecnico2@teste.com").first()
    
    # Insere logs de créditos
    logs = [
        CreditoLog(
            usuario_id=usuario1.id,
            operacao="consumo",
            quantidade=1,
            saldo_anterior=10,
            saldo_atual=9,
            detalhes="Processamento de PDF"
        ),
        CreditoLog(
            usuario_id=usuario1.id,
            operacao="adicao",
            quantidade=5,
            saldo_anterior=9,
            saldo_atual=14,
            detalhes="Compra de créditos"
        ),
        CreditoLog(
            usuario_id=usuario1.id,
            operacao="transferencia_saida",
            quantidade=2,
            saldo_anterior=14,
            saldo_atual=12,
            detalhes="Transferência para tecnico2@teste.com"
        ),
        CreditoLog(
            usuario_id=usuario2.id,
            operacao="transferencia_entrada",
            quantidade=2,
            saldo_anterior=5,
            saldo_atual=7,
            detalhes="Transferência de tecnico1@teste.com"
        )
    ]
    
    db.add_all(logs)
    db.commit()
    db.close()
    
    print("Tabelas e dados de teste criados com sucesso!")

def medir_tempo_execucao(func, *args, **kwargs):
    """Mede o tempo de execução de uma função."""
    inicio = time.time()
    resultado = func(*args, **kwargs)
    fim = time.time()
    return resultado, (fim - inicio) * 1000  # Tempo em milissegundos

def testar_busca_usuario():
    """Testa a performance da busca de usuário por email."""
    db = SessionLocal()
    
    # Método original
    def busca_original(email):
        return db.query(User).filter(User.email == email).first()
    
    # Método otimizado
    def busca_otimizada(email):
        return buscar_usuario_por_email_otimizado(db, email)
    
    emails = ["tecnico1@teste.com", "tecnico2@teste.com", "admin@wondercom.com"]
    
    tempos_original = []
    tempos_otimizado = []
    
    print("\n=== Teste de Busca de Usuário por Email ===")
    
    for email in emails:
        # Teste método original
        _, tempo_original = medir_tempo_execucao(busca_original, email)
        tempos_original.append(tempo_original)
        
        # Teste método otimizado
        _, tempo_otimizado = medir_tempo_execucao(busca_otimizada, email)
        tempos_otimizado.append(tempo_otimizado)
        
        print(f"Email: {email}")
        print(f"  Tempo original: {tempo_original:.2f}ms")
        print(f"  Tempo otimizado: {tempo_otimizado:.2f}ms")
        print(f"  Melhoria: {(1 - tempo_otimizado/tempo_original) * 100:.2f}%")
    
    media_original = statistics.mean(tempos_original)
    media_otimizado = statistics.mean(tempos_otimizado)
    
    print("\nMédia:")
    print(f"  Tempo original: {media_original:.2f}ms")
    print(f"  Tempo otimizado: {media_otimizado:.2f}ms")
    print(f"  Melhoria média: {(1 - media_otimizado/media_original) * 100:.2f}%")
    
    db.close()

def testar_historico_creditos():
    """Testa a performance da obtenção de histórico de créditos."""
    db = SessionLocal()
    
    # Método original
    def historico_original(usuario_id, limit=50):
        return db.query(CreditoLog).filter(
            CreditoLog.usuario_id == usuario_id
        ).order_by(
            CreditoLog.data.desc()
        ).limit(limit).all()
    
    # Método otimizado
    def historico_otimizado(usuario_id, limit=50):
        return obter_historico_creditos_otimizado(db, usuario_id, limit)
    
    # Obter IDs de usuários para teste
    usuarios = db.query(User).limit(3).all()
    
    tempos_original = []
    tempos_otimizado = []
    
    print("\n=== Teste de Histórico de Créditos ===")
    
    for usuario in usuarios:
        # Teste método original
        _, tempo_original = medir_tempo_execucao(historico_original, usuario.id)
        tempos_original.append(tempo_original)
        
        # Teste método otimizado
        _, tempo_otimizado = medir_tempo_execucao(historico_otimizado, usuario.id)
        tempos_otimizado.append(tempo_otimizado)
        
        print(f"Usuário ID: {usuario.id}")
        print(f"  Tempo original: {tempo_original:.2f}ms")
        print(f"  Tempo otimizado: {tempo_otimizado:.2f}ms")
        print(f"  Melhoria: {(1 - tempo_otimizado/tempo_original) * 100:.2f}%")
    
    media_original = statistics.mean(tempos_original)
    media_otimizado = statistics.mean(tempos_otimizado)
    
    print("\nMédia:")
    print(f"  Tempo original: {media_original:.2f}ms")
    print(f"  Tempo otimizado: {media_otimizado:.2f}ms")
    print(f"  Melhoria média: {(1 - media_otimizado/media_original) * 100:.2f}%")
    
    db.close()

def testar_listagem_usuarios():
    """Testa a performance da listagem de usuários."""
    db = SessionLocal()
    
    # Método original
    def listagem_original(limit=50, offset=0):
        return db.query(User).order_by(User.nome_completo).offset(offset).limit(limit).all()
    
    # Método otimizado
    def listagem_otimizada(limit=50, offset=0):
        return listar_usuarios_otimizado(db, limit, offset)
    
    tempos_original = []
    tempos_otimizado = []
    
    print("\n=== Teste de Listagem de Usuários ===")
    
    for limit in [1, 2, 3]:  # Ajustado para o número de usuários de teste
        # Teste método original
        _, tempo_original = medir_tempo_execucao(listagem_original, limit)
        tempos_original.append(tempo_original)
        
        # Teste método otimizado
        _, tempo_otimizado = medir_tempo_execucao(listagem_otimizada, limit)
        tempos_otimizado.append(tempo_otimizado)
        
        print(f"Limit: {limit}")
        print(f"  Tempo original: {tempo_original:.2f}ms")
        print(f"  Tempo otimizado: {tempo_otimizado:.2f}ms")
        print(f"  Melhoria: {(1 - tempo_otimizado/tempo_original) * 100:.2f}%")
    
    media_original = statistics.mean(tempos_original)
    media_otimizado = statistics.mean(tempos_otimizado)
    
    print("\nMédia:")
    print(f"  Tempo original: {media_original:.2f}ms")
    print(f"  Tempo otimizado: {media_otimizado:.2f}ms")
    print(f"  Melhoria média: {(1 - media_otimizado/media_original) * 100:.2f}%")
    
    db.close()

def executar_testes():
    """Executa todos os testes de performance."""
    print("Iniciando testes de performance do banco de dados...")
    
    # Cria tabelas e dados de teste
    criar_tabelas_e_dados_teste()
    
    # Executa os testes
    testar_busca_usuario()
    testar_historico_creditos()
    testar_listagem_usuarios()
    
    print("\nTestes de performance concluídos!")

if __name__ == "__main__":
    executar_testes()
