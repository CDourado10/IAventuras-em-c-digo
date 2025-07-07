# app/services/aluno_service.py
from sqlalchemy.orm import Session
from app.models.database import Aluno, Plano
from app.api.schemas import AlunoCreate
from datetime import datetime

class AlunoService:
    def __init__(self, db: Session):
        self.db = db
    
    def criar_aluno(self, aluno_data: AlunoCreate) -> Aluno:
        # Verificar se o plano existe
        plano = self.db.query(Plano).filter(Plano.id == aluno_data.plano_id).first()
        if not plano:
            raise ValueError("Plano não encontrado")
        
        # Verificar se o email já existe
        existing_aluno = self.db.query(Aluno).filter(Aluno.email == aluno_data.email).first()
        if existing_aluno:
            raise ValueError("Email já cadastrado")
        
        # Criar novo aluno
        novo_aluno = Aluno(**aluno_data.dict())
        self.db.add(novo_aluno)
        self.db.commit()
        self.db.refresh(novo_aluno)
        
        return novo_aluno
    
    def obter_aluno(self, aluno_id: int) -> Aluno:
        aluno = self.db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if not aluno:
            raise ValueError("Aluno não encontrado")
        return aluno
    
    def listar_alunos(self, skip: int = 0, limit: int = 100):
        return self.db.query(Aluno).offset(skip).limit(limit).all()
    
    def atualizar_aluno(self, aluno_id: int, aluno_data: dict):
        aluno = self.obter_aluno(aluno_id)
        for key, value in aluno_data.items():
            setattr(aluno, key, value)
        aluno.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(aluno)
        return aluno
    
    def desativar_aluno(self, aluno_id: int):
        aluno = self.obter_aluno(aluno_id)
        aluno.ativo = False
        aluno.updated_at = datetime.utcnow()
        self.db.commit()
        return aluno