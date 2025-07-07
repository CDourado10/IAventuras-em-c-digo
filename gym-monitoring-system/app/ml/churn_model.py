# app/ml/churn_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os
from datetime import datetime

class ChurnPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.feature_names = [
            'frequencia_semanal',
            'dias_desde_ultimo_checkin',
            'duracao_media_minutos',
            'plano_valor',
            'plano_duracao',
            'dias_como_aluno'
        ]
        self.is_trained = False
        self.model_path = "models/churn_model.pkl"
        self.scaler_path = "models/scaler.pkl"
        
        # Tentar carregar modelo existente
        self.load_model()
    
    def prepare_features(self, features_dict: dict) -> np.array:
        """Preparar features para o modelo"""
        # Garantir que todas as features estejam presentes
        feature_values = []
        for feature_name in self.feature_names:
            value = features_dict.get(feature_name, 0)
            feature_values.append(value)
        
        # Converter para array numpy
        features_array = np.array(feature_values).reshape(1, -1)
        
        # Aplicar normalização se o modelo foi treinado
        if self.is_trained:
            features_array = self.scaler.transform(features_array)
        
        return features_array
    
    def predict_proba(self, features_dict: dict) -> float:
        """Predizer probabilidade de churn"""
        if not self.is_trained:
            # Se não tiver modelo treinado, usar heurística simples
            return self._heuristic_prediction(features_dict)
        
        features = self.prepare_features(features_dict)
        probabilities = self.model.predict_proba(features)
        
        # Retornar probabilidade da classe positiva (churn)
        return probabilities[0][1]
    
    def _heuristic_prediction(self, features_dict: dict) -> float:
        """Heurística simples para quando não há modelo treinado"""
        score = 0.0
        
        # Frequência semanal
        freq_semanal = features_dict.get('frequencia_semanal', 0)
        if freq_semanal < 1:
            score += 0.3
        elif freq_semanal < 2:
            score += 0.2
        elif freq_semanal < 3:
            score += 0.1
        
        # Dias desde último checkin
        dias_ultimo = features_dict.get('dias_desde_ultimo_checkin', 0)
        if dias_ultimo > 30:
            score += 0.4
        elif dias_ultimo > 14:
            score += 0.3
        elif dias_ultimo > 7:
            score += 0.1
        
        # Duração média
        duracao_media = features_dict.get('duracao_media_minutos', 0)
        if duracao_media < 30:
            score += 0.2
        elif duracao_media < 45:
            score += 0.1
        
        # Tempo como aluno
        dias_aluno = features_dict.get('dias_como_aluno', 0)
        if dias_aluno > 90 and freq_semanal < 2:
            score += 0.2
        
        return min(score, 1.0)
    
    def train_model(self, training_data: pd.DataFrame):
        """Treinar o modelo com dados históricos"""
        # Preparar features
        X = training_data[self.feature_names]
        y = training_data['churn']
        
        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Normalizar features
        self.scaler.fit(X_train)
        X_train_scaled = self.scaler.transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Treinar modelo
        self.model.fit(X_train_scaled, y_train)
        
        # Avaliar modelo
        y_pred = self.model.predict(X_test_scaled)
        print("Relatório de Classificação:")
        print(classification_report(y_test, y_pred))
        
        # Importância das features
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nImportância das Features:")
        print(feature_importance)
        
        self.is_trained = True
        self.save_model()
        
        return {
            'accuracy': self.model.score(X_test_scaled, y_test),
            'feature_importance': feature_importance.to_dict('records')
        }
    
    def save_model(self):
        """Salvar modelo treinado"""
        os.makedirs("models", exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
    
    def load_model(self):
        """Carregar modelo existente"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
            self.is_trained = False
