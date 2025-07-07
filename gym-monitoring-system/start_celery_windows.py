"""
Script para iniciar o Celery no Windows com configurações apropriadas
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def start_celery_worker():
    """Inicia o worker do Celery com configurações compatíveis com Windows"""
    print("Iniciando Celery worker com configurações para Windows...")
    
    # Configurar variáveis de ambiente para o Celery
    os.environ['FORKED_BY_MULTIPROCESSING'] = '1'
    
    # Comando para iniciar o worker
    worker_cmd = [
        "celery", 
        "-A", "app.workers.tasks", 
        "worker", 
        "--pool=solo",  # Usar pool solo para Windows
        "--loglevel=info"
    ]
    
    try:
        # Executar o worker
        subprocess.run(worker_cmd)
    except KeyboardInterrupt:
        print("\nCelery worker encerrado.")
    except Exception as e:
        print(f"Erro ao iniciar o Celery worker: {e}")
        sys.exit(1)

def start_celery_beat():
    """Inicia o Celery beat para tarefas agendadas"""
    print("Iniciando Celery beat para tarefas agendadas...")
    
    # Comando para iniciar o beat
    beat_cmd = [
        "celery", 
        "-A", "app.workers.tasks", 
        "beat", 
        "--loglevel=info"
    ]
    
    try:
        # Executar o beat
        subprocess.run(beat_cmd)
    except KeyboardInterrupt:
        print("\nCelery beat encerrado.")
    except Exception as e:
        print(f"Erro ao iniciar o Celery beat: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Iniciar componentes do Celery no Windows")
    parser.add_argument("--worker", action="store_true", help="Iniciar apenas o worker")
    parser.add_argument("--beat", action="store_true", help="Iniciar apenas o beat")
    
    args = parser.parse_args()
    
    if args.worker:
        start_celery_worker()
    elif args.beat:
        start_celery_beat()
    else:
        print("Escolha uma opção: --worker ou --beat")
        print("Exemplo: python start_celery_windows.py --worker")
