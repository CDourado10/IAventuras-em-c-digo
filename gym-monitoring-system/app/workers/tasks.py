# app/workers/tasks.py
from celery import Celery
from celery.schedules import crontab
from sqlalchemy.orm import Session
from app.models.database import SessionLocal, Checkin, Aluno
from app.services.checkin_service import CheckinService
from app.ml.churn_model import ChurnPredictor
from app.ml.feature_engineering import FeatureEngineer
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar Celery
celery_app = Celery(
    'gym_tasks',
    broker=os.getenv('RABBITMQ_URL', 'pyamqp://guest@localhost//'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6380')
)

# Configuração específica para Windows
celery_app.conf.worker_pool = 'solo'  # Usar pool 'solo' em vez de 'prefork' para evitar problemas no Windows
celery_app.conf.broker_connection_retry_on_startup = True  # Tentar reconectar ao broker na inicialização

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_session():
    """Obter sessão do banco de dados"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e

@celery_app.task(bind=True, max_retries=3)
def process_checkin_batch(self, checkin_ids: list):
    """Processar checkins em lote"""
    try:
        db = get_db_session()
        
        logger.info(f"Processando {len(checkin_ids)} checkins")
        
        for checkin_id in checkin_ids:
            try:
                # Obter checkin
                checkin = db.query(Checkin).filter(Checkin.id == checkin_id).first()
                if not checkin:
                    logger.warning(f"Checkin {checkin_id} não encontrado")
                    continue
                
                # Processar informações do checkin
                logger.info(f"Processando checkin {checkin_id} do aluno {checkin.aluno_id}")
                
                # Aqui você pode adicionar lógica adicional:
                # - Atualizar estatísticas em tempo real
                # - Enviar notificações
                # - Sincronizar com sistemas externos
                
            except Exception as e:
                logger.error(f"Erro ao processar checkin {checkin_id}: {e}")
        
        db.close()
        logger.info("Processamento de checkins concluído")
        
    except Exception as exc:
        logger.error(f"Erro no processamento batch: {exc}")
        if self.request.retries < self.max_retries:
            logger.info(f"Tentativa {self.request.retries + 1} em 60 segundos")
            raise self.retry(countdown=60, exc=exc)
        else:
            logger.error("Máximo de tentativas excedido")
            raise

@celery_app.task(bind=True, max_retries=3)
def generate_daily_report(self):
    """Gerar relatório diário de frequência"""
    try:
        db = get_db_session()
        
        logger.info("Iniciando geração de relatório diário")
        
        # Gerar relatório de frequência
        checkin_service = CheckinService(db)
        relatorio = checkin_service.gerar_relatorio_frequencia()
        
        # Salvar relatório (implementar lógica de persistência)
        logger.info(f"Relatório gerado: {relatorio.total_alunos} alunos, {relatorio.total_checkins} checkins")
        
        # Iniciar tarefa de identificação de alunos em risco
        identify_at_risk_students.delay()
        
        db.close()
        logger.info("Relatório diário concluído")
        
        return {
            "status": "success",
            "total_alunos": relatorio.total_alunos,
            "total_checkins": relatorio.total_checkins,
            "data_relatorio": relatorio.data_relatorio.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Erro na geração do relatório: {exc}")
        if self.request.retries < self.max_retries:
            logger.info(f"Tentativa {self.request.retries + 1} em 300 segundos")
            raise self.retry(countdown=300, exc=exc)
        else:
            logger.error("Máximo de tentativas excedido")
            raise

@celery_app.task(bind=True, max_retries=2)
def identify_at_risk_students(self):
    """Identificar alunos em risco de churn"""
    try:
        db = get_db_session()
        
        logger.info("Identificando alunos em risco")
        
        # Obter todos os alunos ativos
        alunos_ativos = db.query(Aluno).filter(Aluno.ativo).all()
        
        predictor = ChurnPredictor()
        alunos_risco_alto = []
        alunos_risco_medio = []
        
        for aluno in alunos_ativos:
            try:
                # Extrair features (implementar método similar ao ChurnService)
                features = extract_student_features(db, aluno)
                
                # Prever risco
                probabilidade = predictor.predict_proba(features)
                
                if probabilidade >= 0.7:
                    alunos_risco_alto.append({
                        'aluno_id': aluno.id,
                        'nome': aluno.nome,
                        'probabilidade': probabilidade
                    })
                elif probabilidade >= 0.4:
                    alunos_risco_medio.append({
                        'aluno_id': aluno.id,
                        'nome': aluno.nome,
                        'probabilidade': probabilidade
                    })
                
            except Exception as e:
                logger.error(f"Erro ao analisar aluno {aluno.id}: {e}")
        
        # Enviar notificações para equipe de retenção
        if alunos_risco_alto:
            send_retention_alerts.delay(alunos_risco_alto, "alto")
        
        if alunos_risco_medio:
            send_retention_alerts.delay(alunos_risco_medio, "medio")
        
        db.close()
        
        logger.info(f"Análise concluída: {len(alunos_risco_alto)} alto risco, {len(alunos_risco_medio)} médio risco")
        
        return {
            "status": "success",
            "alunos_risco_alto": len(alunos_risco_alto),
            "alunos_risco_medio": len(alunos_risco_medio)
        }
        
    except Exception as exc:
        logger.error(f"Erro na identificação de riscos: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=600, exc=exc)
        else:
            raise

@celery_app.task
def send_retention_alerts(alunos_risco: list, nivel_risco: str):
    """Enviar alertas para equipe de retenção"""
    try:
        logger.info(f"Enviando alertas de risco {nivel_risco} para {len(alunos_risco)} alunos")
        
        # Aqui você implementaria:
        # - Envio de emails
        # - Notificações push
        # - Integração com CRM
        # - Webhooks
        
        for aluno in alunos_risco:
            logger.info(f"Alerta {nivel_risco}: Aluno {aluno['nome']} (ID: {aluno['aluno_id']}) - Probabilidade: {aluno['probabilidade']:.2%}")
        
        # Simular envio de notificação
        return {
            "status": "success",
            "alertas_enviados": len(alunos_risco),
            "nivel_risco": nivel_risco
        }
        
    except Exception as e:
        logger.error(f"Erro ao enviar alertas: {e}")
        raise

@celery_app.task(bind=True, max_retries=2)
def update_churn_model(self):
    """Atualizar modelo de previsão de churn"""
    try:
        db = get_db_session()
        
        logger.info("Iniciando atualização do modelo de churn")
        
        # Gerar dataset de treinamento
        feature_engineer = FeatureEngineer(db)
        training_data = feature_engineer.create_training_dataset(months_back=12)
        
        if len(training_data) < 100:
            logger.warning("Dados insuficientes para retreinamento. Usando dados sintéticos.")
            training_data = feature_engineer.generate_synthetic_data(1000)
        
        # Treinar modelo
        predictor = ChurnPredictor()
        metrics = predictor.train_model(training_data)
        
        db.close()
        
        logger.info(f"Modelo atualizado com acurácia: {metrics['accuracy']:.3f}")
        
        return {
            "status": "success",
            "accuracy": metrics['accuracy'],
            "training_samples": len(training_data)
        }
        
    except Exception as exc:
        logger.error(f"Erro na atualização do modelo: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=1800, exc=exc)  # 30 minutos
        else:
            raise

def extract_student_features(db: Session, aluno: Aluno) -> dict:
    """Extrair features de um aluno para previsão"""
    agora = datetime.utcnow()
    
    # Obter checkins dos últimos 90 dias
    checkins = db.query(Checkin).filter(
        Checkin.aluno_id == aluno.id,
        Checkin.data_entrada >= agora - timedelta(days=90)
    ).all()
    
    # Calcular features básicas
    features = {}
    
    if checkins:
        semanas = 13  # ~90 dias / 7
        features['frequencia_semanal'] = len(checkins) / semanas
        
        ultimo_checkin = max(checkins, key=lambda c: c.data_entrada)
        features['dias_desde_ultimo_checkin'] = (agora - ultimo_checkin.data_entrada).days
        
        checkins_com_duracao = [c for c in checkins if c.duracao_minutos is not None]
        if checkins_com_duracao:
            features['duracao_media_minutos'] = sum(c.duracao_minutos for c in checkins_com_duracao) / len(checkins_com_duracao)
        else:
            features['duracao_media_minutos'] = 0
    else:
        features['frequencia_semanal'] = 0
        features['dias_desde_ultimo_checkin'] = 999
        features['duracao_media_minutos'] = 0
    
    # Informações do plano
    features['plano_valor'] = aluno.plano.valor if aluno.plano else 0
    features['plano_duracao'] = aluno.plano.duracao_meses if aluno.plano else 0
    
    # Tempo como aluno
    features['dias_como_aluno'] = (agora - aluno.data_matricula).days
    
    return features

# Configuração de tasks periódicas

celery_app.conf.beat_schedule = {
    # Relatório diário às 6h
    'daily-report': {
        'task': 'app.workers.tasks.generate_daily_report',
        'schedule': crontab(hour=6, minute=0),
    },
    # Análise de risco às 8h e 18h
    'risk-analysis': {
        'task': 'app.workers.tasks.identify_at_risk_students',
        'schedule': crontab(hour=[8, 18], minute=0),
    },
    # Atualização do modelo semanalmente (domingo 2h)
    'model-update': {
        'task': 'app.workers.tasks.update_churn_model',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
    },
}

celery_app.conf.timezone = 'America/Sao_Paulo'
