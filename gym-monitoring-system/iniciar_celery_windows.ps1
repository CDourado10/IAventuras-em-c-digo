# Script PowerShell para iniciar o Celery no Windows
Write-Host "Iniciando Celery Worker para Windows" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Definir variável de ambiente para multiprocessing no Windows
$env:FORKED_BY_MULTIPROCESSING = "1"

# Verificar se o ambiente virtual existe
if (Test-Path -Path ".\venv\Scripts\activate.ps1") {
    Write-Host "Ativando ambiente virtual..." -ForegroundColor Cyan
    & .\venv\Scripts\activate.ps1
} else {
    Write-Host "Ambiente virtual não encontrado. Criando novo ambiente..." -ForegroundColor Yellow
    python -m venv venv
    if (Test-Path -Path ".\venv\Scripts\activate.ps1") {
        Write-Host "Ativando ambiente virtual..." -ForegroundColor Cyan
        & .\venv\Scripts\activate.ps1
        
        Write-Host "Instalando dependências..." -ForegroundColor Cyan
        pip install -r requirements.txt
    } else {
        Write-Host "Falha ao criar ambiente virtual. Verifique se o Python está instalado corretamente." -ForegroundColor Red
        exit 1
    }
}

# Verificar se o Celery está instalado
try {
    $celeryVersion = python -c "import celery; print(celery.__version__)"
    Write-Host "Celery versão $celeryVersion encontrado." -ForegroundColor Green
} catch {
    Write-Host "Celery não encontrado. Instalando..." -ForegroundColor Yellow
    pip install celery
}

# Iniciar o worker do Celery com o pool solo
Write-Host "Iniciando Celery worker com pool=solo..." -ForegroundColor Green
celery -A app.workers.tasks worker --pool=solo --loglevel=info

# Manter a janela aberta
Read-Host -Prompt "Pressione ENTER para sair"
