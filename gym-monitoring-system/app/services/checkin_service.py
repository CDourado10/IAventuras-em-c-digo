# app/services/checkin_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.database import Checkin, Aluno
from app.api.schemas import CheckinCreate, FrequenciaResponse, RelatorioFrequenciaResponse
from datetime import datetime, timedelta

class CheckinService:
    def __init__(self, db: Session):
        self.db = db
    
    def criar_checkin(self, checkin_data: CheckinCreate) -> Checkin:
        # Verificar se o aluno existe
        aluno = self.db.query(Aluno).filter(Aluno.id == checkin_data.aluno_id).first()
        if not aluno:
            raise ValueError("Aluno não encontrado")
        
        if not aluno.ativo:
            raise ValueError("Aluno não está ativo")
        
        # Verificar se já existe um checkin ativo (sem saída)
        checkin_ativo = self.db.query(Checkin).filter(
            and_(
                Checkin.aluno_id == checkin_data.aluno_id,
                Checkin.data_saida.is_(None)
            )
        ).first()
        
        if checkin_ativo:
            raise ValueError("Aluno já possui um checkin ativo")
        
        # Criar novo checkin
        novo_checkin = Checkin(**checkin_data.dict())
        self.db.add(novo_checkin)
        self.db.commit()
        self.db.refresh(novo_checkin)
        
        return novo_checkin
    
    def registrar_saida(self, checkin_id: int) -> Checkin:
        checkin = self.db.query(Checkin).filter(Checkin.id == checkin_id).first()
        if not checkin:
            raise ValueError("Checkin não encontrado")
        
        if checkin.data_saida:
            raise ValueError("Checkin já possui saída registrada")
        
        checkin.data_saida = datetime.utcnow()
        if checkin.data_entrada:
            duracao = checkin.data_saida - checkin.data_entrada
            checkin.duracao_minutos = int(duracao.total_seconds() / 60)
        
        self.db.commit()
        self.db.refresh(checkin)
        
        return checkin
    
    def obter_frequencia_aluno(self, aluno_id: int) -> FrequenciaResponse:
        # Verificar se o aluno existe
        aluno = self.db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if not aluno:
            raise ValueError("Aluno não encontrado")
        
        # Obter todos os checkins
        checkins = self.db.query(Checkin).filter(Checkin.aluno_id == aluno_id).all()
        
        # Calcular estatísticas
        agora = datetime.utcnow()
        trinta_dias_atras = agora - timedelta(days=30)
        sete_dias_atras = agora - timedelta(days=7)
        
        checkins_30_dias = [c for c in checkins if c.data_entrada >= trinta_dias_atras]
        checkins_7_dias = [c for c in checkins if c.data_entrada >= sete_dias_atras]
        
        # Calcular média de checkins por semana
        data_matricula = aluno.data_matricula
        semanas_desde_matricula = max(1, (agora - data_matricula).days / 7)
        media_checkins_semana = len(checkins) / semanas_desde_matricula
        
        # Último checkin
        ultimo_checkin = None
        if checkins:
            ultimo_checkin = max(checkins, key=lambda c: c.data_entrada).data_entrada
        
        # Média de duração
        checkins_com_duracao = [c for c in checkins if c.duracao_minutos is not None]
        media_duracao = None
        if checkins_com_duracao:
            media_duracao = sum(c.duracao_minutos for c in checkins_com_duracao) / len(checkins_com_duracao)
        
        return FrequenciaResponse(
            aluno_id=aluno_id,
            total_checkins=len(checkins),
            checkins_ultimos_30_dias=len(checkins_30_dias),
            checkins_ultimos_7_dias=len(checkins_7_dias),
            media_checkins_semana=media_checkins_semana,
            ultimo_checkin=ultimo_checkin,
            media_duracao_minutos=media_duracao,
            checkins=[CheckinResponse.from_orm(c) for c in checkins[-10:]]  # Últimos 10
        )
    
    def gerar_relatorio_frequencia(self) -> RelatorioFrequenciaResponse:
        agora = datetime.utcnow()
        
        # Estatísticas gerais
        total_alunos = self.db.query(Aluno).filter(Aluno.ativo == True).count()
        total_checkins = self.db.query(Checkin).count()
        
        media_checkins_por_aluno = 0
        if total_alunos > 0:
            media_checkins_por_aluno = total_checkins / total_alunos
        
        # Contagem de riscos (implementação simplificada)
        alunos_risco_alto = 0
        alunos_risco_medio = 0
        alunos_risco_baixo = 0
        
        return RelatorioFrequenciaResponse(
            data_relatorio=agora,
            total_alunos=total_alunos,
            total_checkins=total_checkins,
            media_checkins_por_aluno=media_checkins_por_aluno,
            alunos_risco_alto=alunos_risco_alto,
            alunos_risco_medio=alunos_risco_medio,
            alunos_risco_baixo=alunos_risco_baixo
        )
