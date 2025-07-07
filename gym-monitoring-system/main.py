# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import redis
import json
from datetime import datetime, timedelta

from app.models.database import get_db, create_tables
from app.api.schemas import *
from app.services.aluno_service import AlunoService
from app.services.checkin_service import CheckinService
from app.services.churn_service import ChurnService
from app.workers.tasks import process_checkin_batch, generate_daily_report
from app.ml.churn_model import ChurnPredictor

# Inicializar aplicação
app = FastAPI(
    title="Gym Monitoring System",
    description="Sistema de monitoramento de academia com previsão de churn",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar Redis para cache
redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)

# Configurar autenticação
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Implementação simplificada do JWT
    # Em produção, usar biblioteca como python-jose
    if credentials.credentials != "valid_token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# Inicializar banco de dados
@app.on_event("startup")
async def startup_event():
    create_tables()

# Endpoints da API

@app.get("/")
async def root():
    return {"message": "Gym Monitoring System API"}

@app.post("/aluno/registro", response_model=AlunoResponse)
async def registrar_aluno(
    aluno: AlunoCreate,
    db: Session = Depends(get_db)
):
    """Registrar um novo aluno"""
    try:
        aluno_service = AlunoService(db)
        novo_aluno = aluno_service.criar_aluno(aluno)
        return novo_aluno
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/aluno/checkin", response_model=CheckinResponse)
async def registrar_checkin(
    checkin: CheckinCreate,
    db: Session = Depends(get_db)
):
    """Registrar entrada do aluno na academia"""
    try:
        checkin_service = CheckinService(db)
        novo_checkin = checkin_service.criar_checkin(checkin)
        
        # Adicionar à fila para processamento assíncrono
        process_checkin_batch.delay([novo_checkin.id])
        
        return novo_checkin
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/aluno/{aluno_id}/frequencia", response_model=FrequenciaResponse)
async def obter_frequencia(
    aluno_id: int,
    db: Session = Depends(get_db)
):
    """Obter histórico de frequência do aluno"""
    try:
        # Verificar cache primeiro
        cache_key = f"frequencia:{aluno_id}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        checkin_service = CheckinService(db)
        frequencia = checkin_service.obter_frequencia_aluno(aluno_id)
        
        # Armazenar no cache por 15 minutos
        redis_client.setex(cache_key, 900, json.dumps(frequencia, default=str))
        
        return frequencia
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/aluno/{aluno_id}/risco-churn", response_model=ChurnPredictionResponse)
async def obter_risco_churn(
    aluno_id: int,
    db: Session = Depends(get_db)
):
    """Obter probabilidade de desistência do aluno"""
    try:
        # Verificar cache primeiro
        cache_key = f"churn:{aluno_id}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        churn_service = ChurnService(db)
        predicao = churn_service.prever_churn(aluno_id)
        
        # Armazenar no cache por 1 hora
        redis_client.setex(cache_key, 3600, json.dumps(predicao, default=str))
        
        return predicao
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/alunos", response_model=List[AlunoResponse])
async def listar_alunos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    """Listar todos os alunos (requer autenticação)"""
    try:
        aluno_service = AlunoService(db)
        alunos = aluno_service.listar_alunos(skip=skip, limit=limit)
        return alunos
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/relatorio/frequencia", response_model=RelatorioFrequenciaResponse)
async def obter_relatorio_frequencia(
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    """Obter relatório de frequência (requer autenticação)"""
    try:
        checkin_service = CheckinService(db)
        relatorio = checkin_service.gerar_relatorio_frequencia()
        return relatorio
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/processar-checkins-batch")
async def processar_checkins_batch(
    checkin_ids: List[int],
    token: str = Depends(verify_token)
):
    """Processar checkins em lote (requer autenticação)"""
    try:
        # Enviar para fila de processamento
        process_checkin_batch.delay(checkin_ids)
        return {"message": f"Processamento de {len(checkin_ids)} checkins iniciado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/gerar-relatorio-diario")
async def gerar_relatorio_diario(
    token: str = Depends(verify_token)
):
    """Gerar relatório diário (requer autenticação)"""
    try:
        # Enviar para fila de processamento
        generate_daily_report.delay()
        return {"message": "Geração de relatório diário iniciada"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login", response_model=Token)
async def login(user: UserLogin):
    """Endpoint de login para obter token JWT"""
    # Implementação simplificada
    if user.username == "admin" and user.password == "password":
        return {"access_token": "valid_token", "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)