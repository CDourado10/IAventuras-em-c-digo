# app/workers/worker.py
import os
import platform
from app.workers.tasks import celery_app

# Configurações específicas para Windows
if platform.system() == 'Windows':
    # Definir variável de ambiente para evitar problemas de multiprocessing no Windows
    os.environ['FORKED_BY_MULTIPROCESSING'] = '1'
    
    # Configurar para usar o pool 'solo' no Windows
    celery_app.conf.worker_pool = 'solo'

if __name__ == '__main__':
    # Iniciar o worker com argumentos específicos para Windows se necessário
    if platform.system() == 'Windows':
        # No Windows, é melhor iniciar com argumentos específicos
        import sys
        sys.argv.extend(['--pool=solo', '--loglevel=info'])
    
    celery_app.start()