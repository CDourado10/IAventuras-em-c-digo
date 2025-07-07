# app/services/churn_service.py
from sqlalchemy.orm import Session
from app.models.database import Aluno, Checkin, Plano
from app.api.schemas import ChurnPredictionResponse
from app.ml.churn_model import ChurnPredictor
from datetime import datetime, timedelta

class ChurnService:
    def __init__(self, db: Session):
        self.db = db
        self.predictor = ChurnPredictor()
    
    def prever_churn(self, aluno_id: int) -> ChurnPredictionResponse:
        # Verificar se o aluno existe
        aluno = self.db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if not aluno:
            raise ValueError("Aluno não encontrado")
        
        # Obter features do aluno
        features = self._extrair_features(aluno)
        
        # Fazer previsão
        probabilidade = self.predictor.predict_proba(features)
        
        # Classificar risco
        if probabilidade >= 0.7:
            risco_nivel = "alto"
        elif probabilidade >= 0.4:
            risco_nivel = "médio"
        else:
            risco_nivel = "baixo"
        
        # Identificar fatores de risco
        fatores_risco = self._identificar_fatores_risco(features)
        
        # Gerar recomendações
        recomendacoes = self._gerar_recomendacoes(risco_nivel, fatores_risco)
        
        return ChurnPredictionResponse(
            aluno_id=aluno_id,
            probabilidade_churn=probabilidade,
            risco_nivel=risco_nivel,
            fatores_risco=fatores_risco,
            recomendacoes=recomendacoes
        )
    
    def _extrair_features(self, aluno: Aluno) -> dict:
        agora = datetime.utcnow()
        
        # Obter checkins
        checkins = self.db.query(Checkin).filter(Checkin.aluno_id == aluno.id).all()
        
        # Calcular features
        features = {}
        
        # Frequência semanal
        if checkins:
            semanas_desde_matricula = max(1, (agora - aluno.data_matricula).days / 7)
            features['frequencia_semanal'] = len(checkins) / semanas_desde_matricula
        else:
            features['frequencia_semanal'] = 0
        
        # Tempo desde último checkin
        if checkins:
            ultimo_checkin = max(checkins, key=lambda c: c.data_entrada)
            features['dias_desde_ultimo_checkin'] = (agora - ultimo_checkin.data_entrada).days
        else:
            features['dias_desde_ultimo_checkin'] = 999
        
        # Duração média das visitas
        checkins_com_duracao = [c for c in checkins if c.duracao_minutos is not None]
        if checkins_com_duracao:
            features['duracao_media_minutos'] = sum(c.duracao_minutos for c in checkins_com_duracao) / len(checkins_com_duracao)
        else:
            features['duracao_media_minutos'] = 0
        
        # Tipo de plano
        plano = self.db.query(Plano).filter(Plano.id == aluno.plano_id).first()
        features['plano_valor'] = plano.valor if plano else 0
        features['plano_duracao'] = plano.duracao_meses if plano else 0
        
        # Tempo como aluno
        features['dias_como_aluno'] = (agora - aluno.data_matricula).days
        
        return features
    
    def _identificar_fatores_risco(self, features: dict) -> list:
        fatores = []
        
        if features['frequencia_semanal'] < 1:
            fatores.append("Baixa frequência semanal")
        
        if features['dias_desde_ultimo_checkin'] > 14:
            fatores.append("Muito tempo sem visitar a academia")
        
        if features['duracao_media_minutos'] < 30:
            fatores.append("Sessões de treino muito curtas")
        
        if features['dias_como_aluno'] > 90 and features['frequencia_semanal'] < 2:
            fatores.append("Declínio na frequência após período inicial")
        
        return fatores
    
    def _gerar_recomendacoes(self, risco_nivel: str, fatores_risco: list) -> list:
        recomendacoes = []
        
        if risco_nivel == "alto":
            recomendacoes.append("Contato imediato da equipe de retenção")
            recomendacoes.append("Oferecer avaliação física gratuita")
            recomendacoes.append("Propor desconto ou benefício especial")
        elif risco_nivel == "médio":
            recomendacoes.append("Agendar conversa com personal trainer")
            recomendacoes.append("Convidar para aulas em grupo")
            recomendacoes.append("Enviar dicas de motivação")
        else:
            recomendacoes.append("Manter engajamento com conteúdo motivacional")
            recomendacoes.append("Parabenizar pela consistência")
        
        # Recomendações específicas baseadas nos fatores
        if "Baixa frequência semanal" in fatores_risco:
            recomendacoes.append("Criar plano de treino mais flexível")
        
        if "Muito tempo sem visitar a academia" in fatores_risco:
            recomendacoes.append("Entrar em contato para verificar se está tudo bem")
        
        if "Sessões de treino muito curtas" in fatores_risco:
            recomendacoes.append("Sugerir treinos mais dinâmicos e variados")
        
        return recomendacoes