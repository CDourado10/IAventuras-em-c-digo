# app/api/schemas.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# Schemas para Plano
class PlanoBase(BaseModel):
    nome: str
    valor: float
    duracao_meses: int

class PlanoCreate(PlanoBase):
    pass

class PlanoResponse(PlanoBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Schemas para Aluno
class AlunoBase(BaseModel):
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    data_nascimento: Optional[datetime] = None
    plano_id: int

class AlunoCreate(AlunoBase):
    pass

class AlunoResponse(AlunoBase):
    id: int
    data_matricula: datetime
    ativo: bool
    created_at: datetime
    updated_at: datetime
    plano: Optional[PlanoResponse] = None
    
    class Config:
        from_attributes = True

# Schemas para Checkin
class CheckinBase(BaseModel):
    aluno_id: int

class CheckinCreate(CheckinBase):
    pass

class CheckinResponse(CheckinBase):
    id: int
    data_entrada: datetime
    data_saida: Optional[datetime] = None
    duracao_minutos: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Schemas para Frequência
class FrequenciaResponse(BaseModel):
    aluno_id: int
    total_checkins: int
    checkins_ultimos_30_dias: int
    checkins_ultimos_7_dias: int
    media_checkins_semana: float
    ultimo_checkin: Optional[datetime] = None
    media_duracao_minutos: Optional[float] = None
    checkins: List[CheckinResponse] = []

# Schemas para Previsão de Churn
class ChurnPredictionResponse(BaseModel):
    aluno_id: int
    probabilidade_churn: float
    risco_nivel: str  # "baixo", "médio", "alto"
    fatores_risco: List[str]
    recomendacoes: List[str]

# Schemas para Relatórios
class RelatorioFrequenciaResponse(BaseModel):
    data_relatorio: datetime
    total_alunos: int
    total_checkins: int
    media_checkins_por_aluno: float
    alunos_risco_alto: int
    alunos_risco_medio: int
    alunos_risco_baixo: int

# Schemas para Autenticação
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str