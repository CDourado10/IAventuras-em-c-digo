# app/models/database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Usar a porta 5433 explicitamente, ignorando variáveis de ambiente que possam estar sobrescrevendo
DATABASE_URL = "postgresql://user:password@localhost:5433/gym_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Plano(Base):
    __tablename__ = "planos"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    duracao_meses = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    alunos = relationship("Aluno", back_populates="plano")

class Aluno(Base):
    __tablename__ = "alunos"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    telefone = Column(String)
    data_nascimento = Column(DateTime)
    data_matricula = Column(DateTime, default=datetime.utcnow)
    plano_id = Column(Integer, ForeignKey("planos.id"))
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    plano = relationship("Plano", back_populates="alunos")
    checkins = relationship("Checkin", back_populates="aluno")

class Checkin(Base):
    __tablename__ = "checkins"
    
    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"))
    data_entrada = Column(DateTime, default=datetime.utcnow)
    data_saida = Column(DateTime, nullable=True)
    duracao_minutos = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    aluno = relationship("Aluno", back_populates="checkins")

# Função para criar as tabelas
def create_tables():
    Base.metadata.create_all(bind=engine)

# Função para obter sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()