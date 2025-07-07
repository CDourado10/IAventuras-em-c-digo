# tests/test_models.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, Aluno, Plano, Checkin
from datetime import datetime

# Usar banco em memória para testes
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_test_db():
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()

def test_create_plano():
    """Testar criação de plano"""
    db = setup_test_db()
    
    plano = Plano(nome="Teste", valor=100.0, duracao_meses=12)
    db.add(plano)
    db.commit()
    
    assert plano.id is not None
    assert plano.nome == "Teste"
    
    db.close()

def test_create_aluno():
    """Testar criação de aluno"""
    db = setup_test_db()
    
    # Criar plano primeiro
    plano = Plano(nome="Teste", valor=100.0, duracao_meses=12)
    db.add(plano)
    db.commit()
    
    aluno = Aluno(
        nome="Teste Aluno",
        email="teste@email.com",
        plano_id=plano.id
    )
    db.add(aluno)
    db.commit()
    
    assert aluno.id is not None
    assert aluno.nome == "Teste Aluno"
    assert aluno.ativo == True
    
    db.close()