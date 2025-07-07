# scripts/init_db.py
"""
Script para inicializar o banco de dados com dados de exemplo
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adicionar o diretório raiz ao sys.path para garantir que os módulos sejam encontrados
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

from sqlalchemy.orm import Session
from app.models.database import SessionLocal, create_tables, Plano, Aluno, Checkin
from datetime import datetime, timedelta
import random

def create_sample_data():
    """Criar dados de exemplo para teste"""
    db = SessionLocal()
    
    try:
        # Criar tabelas
        create_tables()
        print("Tabelas criadas com sucesso!")
        
        # Verificar se já existem dados
        if db.query(Plano).count() > 0:
            print("Dados já existem no banco!")
            return
        
        # Criar planos
        planos = [
            Plano(nome="Básico", valor=50.0, duracao_meses=1),
            Plano(nome="Semestral", valor=80.0, duracao_meses=6),
            Plano(nome="Anual", valor=120.0, duracao_meses=12),
            Plano(nome="Premium", valor=200.0, duracao_meses=12)
        ]
        
        for plano in planos:
            db.add(plano)
        
        db.commit()
        print(f"Criados {len(planos)} planos")
        
        # Criar alunos de exemplo
        nomes_exemplo = [
            "João Silva", "Maria Santos", "Pedro Oliveira", "Ana Costa",
            "Carlos Ferreira", "Lucia Pereira", "Rafael Lima", "Juliana Souza",
            "Fernando Alves", "Patricia Rocha", "Ricardo Martins", "Camila Dias",
            "Bruno Nascimento", "Fernanda Castro", "Leonardo Torres"
        ]
        
        alunos = []
        for i, nome in enumerate(nomes_exemplo):
            aluno = Aluno(
                nome=nome,
                email=f"aluno{i+1}@email.com",
                telefone=f"(11) 9999-{1000+i:04d}",
                data_nascimento=datetime.now() - timedelta(days=random.randint(6570, 14600)),  # 18-40 anos
                data_matricula=datetime.now() - timedelta(days=random.randint(30, 365)),
                plano_id=random.choice([1, 2, 3, 4]),
                ativo=True
            )
            alunos.append(aluno)
            db.add(aluno)
        
        db.commit()
        print(f"Criados {len(alunos)} alunos")
        
        # Criar checkins de exemplo
        checkins_count = 0
        for aluno in alunos:
            # Simular padrão de frequência diferente para cada aluno
            freq_base = random.uniform(1, 4)  # 1-4 vezes por semana
            
            # Gerar checkins dos últimos 90 dias
            data_inicio = aluno.data_matricula
            data_fim = datetime.now()
            
            current_date = data_inicio
            while current_date <= data_fim:
                # Probabilidade de ir à academia baseada na frequência
                if random.random() < (freq_base / 7):  # Converter para probabilidade diária
                    # Hora de entrada aleatória (6h às 22h)
                    hora_entrada = random.randint(6, 22)
                    minuto_entrada = random.randint(0, 59)
                    
                    data_checkin = current_date.replace(
                        hour=hora_entrada, 
                        minute=minuto_entrada
                    )
                    
                    # Duração do treino (30-120 minutos)
                    duracao = random.randint(30, 120)
                    data_saida = data_checkin + timedelta(minutes=duracao)
                    
                    checkin = Checkin(
                        aluno_id=aluno.id,
                        data_entrada=data_checkin,
                        data_saida=data_saida,
                        duracao_minutos=duracao
                    )
                    
                    db.add(checkin)
                    checkins_count += 1
                
                current_date += timedelta(days=1)
        
        db.commit()
        print(f"Criados {checkins_count} checkins")
        print("Dados de exemplo criados com sucesso!")
        
    except Exception as e:
        print(f"Erro ao criar dados: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()
