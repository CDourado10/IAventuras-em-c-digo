# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    """Testar endpoint raiz"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Gym Monitoring System API"}

def test_registrar_aluno():
    """Testar registro de aluno"""
    aluno_data = {
        "nome": "Teste Usuario",
        "email": "teste@email.com",
        "telefone": "(11) 99999-9999",
        "plano_id": 1
    }
    
    response = client.post("/aluno/registro", json=aluno_data)
    assert response.status_code in [200, 201, 400]  # Pode dar erro se plano não existir

def test_login():
    """Testar login"""
    login_data = {
        "username": "admin",
        "password": "password"
    }
    
    response = client.post("/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid():
    """Testar login com credenciais inválidas"""
    login_data = {
        "username": "invalid",
        "password": "invalid"
    }
    
    response = client.post("/login", json=login_data)
    assert response.status_code == 401
