# app/ml/feature_engineering.py
from sqlalchemy.orm import Session
from app.models.database import Aluno, Checkin, Plano
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class FeatureEngineer:
    def __init__(self, db: Session):
        self.db = db
    
    def create_training_dataset(self, months_back: int = 6) -> pd.DataFrame:
        """Criar dataset de treinamento com features e targets"""
        # Definir período de análise
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months_back * 30)
        
        # Obter alunos que estavam ativos no início do período
        alunos = self.db.query(Aluno).filter(
            Aluno.data_matricula <= start_date
        ).all()
        
        training_data = []
        
        for aluno in alunos:
            # Calcular features baseadas nos primeiros 3 meses
            feature_end_date = start_date + timedelta(days=90)
            
            # Obter checkins para cálculo de features
            checkins = self.db.query(Checkin).filter(
                Checkin.aluno_id == aluno.id,
                Checkin.data_entrada >= start_date,
                Checkin.data_entrada <= feature_end_date
            ).all()
            
            # Calcular features
            features = self._calculate_features(aluno, checkins, start_date, feature_end_date)
            
            # Determinar se houve churn nos próximos 3 meses
            churn_check_date = feature_end_date + timedelta(days=90)
            
            # Verificar se houve checkins após o período de features
            future_checkins = self.db.query(Checkin).filter(
                Checkin.aluno_id == aluno.id,
                Checkin.data_entrada > feature_end_date,
                Checkin.data_entrada <= churn_check_date
            ).count()
            
            # Definir churn (se não houve checkins em 90 dias)
            features['churn'] = 1 if future_checkins == 0 else 0
            features['aluno_id'] = aluno.id
            
            training_data.append(features)
        
        return pd.DataFrame(training_data)
    
    def _calculate_features(self, aluno: Aluno, checkins: list, start_date: datetime, end_date: datetime) -> dict:
        """Calcular features para um aluno específico"""
        features = {}
        
        # Frequência semanal
        if checkins:
            days_period = (end_date - start_date).days
            weeks_period = max(1, days_period / 7)
            features['frequencia_semanal'] = len(checkins) / weeks_period
        else:
            features['frequencia_semanal'] = 0
        
        # Tempo desde último checkin
        if checkins:
            ultimo_checkin = max(checkins, key=lambda c: c.data_entrada)
            features['dias_desde_ultimo_checkin'] = (end_date - ultimo_checkin.data_entrada).days
        else:
            features['dias_desde_ultimo_checkin'] = 999
        
        # Duração média das visitas
        checkins_com_duracao = [c for c in checkins if c.duracao_minutos is not None]
        if checkins_com_duracao:
            features['duracao_media_minutos'] = sum(c.duracao_minutos for c in checkins_com_duracao) / len(checkins_com_duracao)
        else:
            features['duracao_media_minutos'] = 0
        
        # Informações do plano
        plano = self.db.query(Plano).filter(Plano.id == aluno.plano_id).first()
        features['plano_valor'] = plano.valor if plano else 0
        features['plano_duracao'] = plano.duracao_meses if plano else 0
        
        # Tempo como aluno
        features['dias_como_aluno'] = (end_date - aluno.data_matricula).days
        
        # Features adicionais
        features['checkins_fins_semana'] = len([c for c in checkins if c.data_entrada.weekday() >= 5])
        features['checkins_manha'] = len([c for c in checkins if c.data_entrada.hour < 12])
        features['checkins_tarde'] = len([c for c in checkins if 12 <= c.data_entrada.hour < 18])
        features['checkins_noite'] = len([c for c in checkins if c.data_entrada.hour >= 18])
        
        # Tendência de frequência (primeiros 45 dias vs últimos 45 dias)
        mid_date = start_date + timedelta(days=45)
        checkins_primeira_metade = [c for c in checkins if c.data_entrada <= mid_date]
        checkins_segunda_metade = [c for c in checkins if c.data_entrada > mid_date]
        
        freq_primeira = len(checkins_primeira_metade) / 6.43  # 45 dias / 7 dias
        freq_segunda = len(checkins_segunda_metade) / 6.43
        
        features['tendencia_frequencia'] = freq_segunda - freq_primeira
        
        return features
    
    def generate_synthetic_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """Gerar dados sintéticos para treinamento inicial"""
        np.random.seed(42)
        
        data = []
        
        for i in range(n_samples):
            # Gerar features com distribuições realistas
            frequencia_semanal = np.random.gamma(2, 1.5)  # Média ~3
            dias_desde_ultimo = np.random.exponential(7)  # Média 7 dias
            duracao_media = np.random.normal(60, 20)  # Média 60 min
            plano_valor = np.random.choice([50, 80, 120, 200])
            plano_duracao = np.random.choice([1, 6, 12])
            dias_como_aluno = np.random.uniform(30, 365)
            
            # Definir churn baseado em regras
            churn_prob = 0.1  # Base 10%
            
            if frequencia_semanal < 1:
                churn_prob += 0.4
            elif frequencia_semanal < 2:
                churn_prob += 0.2
            
            if dias_desde_ultimo > 14:
                churn_prob += 0.3
            elif dias_desde_ultimo > 7:
                churn_prob += 0.1
            
            if duracao_media < 30:
                churn_prob += 0.2
            
            if dias_como_aluno > 180 and frequencia_semanal < 2:
                churn_prob += 0.2
            
            churn = 1 if np.random.random() < churn_prob else 0
            
            data.append({
                'frequencia_semanal': frequencia_semanal,
                'dias_desde_ultimo_checkin': dias_desde_ultimo,
                'duracao_media_minutos': max(0, duracao_media),
                'plano_valor': plano_valor,
                'plano_duracao': plano_duracao,
                'dias_como_aluno': dias_como_aluno,
                'churn': churn
            })
        
        return pd.DataFrame(data)