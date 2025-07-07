@echo off
echo Iniciando Celery Worker para Windows
echo =====================================

:: Ativar ambiente virtual (ajuste o caminho se necessário)
call venv\Scripts\activate.bat

:: Definir variável de ambiente para multiprocessing no Windows
set FORKED_BY_MULTIPROCESSING=1

:: Iniciar o worker do Celery com o pool solo
python start_celery_windows.py --worker

pause
