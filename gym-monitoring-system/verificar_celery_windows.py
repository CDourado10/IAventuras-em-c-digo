"""
Script para verificar e diagnosticar problemas do Celery no Windows
"""
import os
import sys
import platform
import subprocess
import socket
from dotenv import load_dotenv
import time

# Carregar variáveis de ambiente
load_dotenv()

def verificar_sistema():
    """Verifica informações do sistema operacional"""
    print("\n=== INFORMAÇÕES DO SISTEMA ===")
    print(f"Sistema Operacional: {platform.system()} {platform.version()}")
    print(f"Python: {platform.python_version()}")
    print(f"Diretório atual: {os.getcwd()}")
    
    # Verificar se estamos em um ambiente virtual
    in_venv = sys.prefix != sys.base_prefix
    print(f"Ambiente virtual ativo: {'Sim' if in_venv else 'Não'}")
    
    return in_venv

def verificar_dependencias():
    """Verifica se as dependências necessárias estão instaladas"""
    print("\n=== VERIFICANDO DEPENDÊNCIAS ===")
    
    dependencias = ['celery', 'redis', 'sqlalchemy', 'fastapi', 'pika']
    instaladas = []
    faltando = []
    
    for dep in dependencias:
        try:
            # Tenta importar a dependência
            __import__(dep)
            instaladas.append(dep)
        except ImportError:
            faltando.append(dep)
    
    if instaladas:
        print(f"Dependências instaladas: {', '.join(instaladas)}")
    
    if faltando:
        print(f"Dependências faltando: {', '.join(faltando)}")
        print("Execute: pip install -r requirements.txt")
    
    return len(faltando) == 0

def verificar_conexao_rabbitmq():
    """Verifica se é possível conectar ao RabbitMQ"""
    print("\n=== VERIFICANDO CONEXÃO COM RABBITMQ ===")
    
    # Obter URL do RabbitMQ do ambiente
    rabbitmq_url = os.getenv('RABBITMQ_URL', 'pyamqp://guest@localhost//')
    
    # Extrair host e porta
    if '@' in rabbitmq_url:
        host = rabbitmq_url.split('@')[1].split('/')[0]
    else:
        host = 'localhost'
    
    porta = 5672  # Porta padrão do RabbitMQ
    
    try:
        # Tentar conectar ao socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((host, porta))
        s.close()
        print(f"Conexão com RabbitMQ em {host}:{porta} bem-sucedida!")
        return True
    except Exception as e:
        print(f"Erro ao conectar ao RabbitMQ em {host}:{porta}: {e}")
        print("Verifique se o container Docker do RabbitMQ está em execução.")
        print("Execute: docker ps | findstr rabbitmq")
        return False

def verificar_conexao_redis():
    """Verifica se é possível conectar ao Redis"""
    print("\n=== VERIFICANDO CONEXÃO COM REDIS ===")
    
    # Obter URL do Redis do ambiente
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6380')
    
    # Extrair host e porta
    if '//' in redis_url:
        host_port = redis_url.split('//')[1].split('/')[0]
        if ':' in host_port:
            host, porta = host_port.split(':')
            porta = int(porta)
        else:
            host = host_port
            porta = 6379  # Porta padrão do Redis
    else:
        host = 'localhost'
        porta = 6380  # Porta alternativa que estamos usando
    
    try:
        # Tentar conectar ao socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((host, porta))
        s.close()
        print(f"Conexão com Redis em {host}:{porta} bem-sucedida!")
        return True
    except Exception as e:
        print(f"Erro ao conectar ao Redis em {host}:{porta}: {e}")
        print("Verifique se o container Docker do Redis está em execução.")
        print("Execute: docker ps | findstr redis")
        return False

def configurar_ambiente_windows():
    """Configura o ambiente para o Celery no Windows"""
    print("\n=== CONFIGURANDO AMBIENTE PARA WINDOWS ===")
    
    # Definir variável de ambiente para multiprocessing no Windows
    os.environ['FORKED_BY_MULTIPROCESSING'] = '1'
    print("Variável de ambiente FORKED_BY_MULTIPROCESSING definida como 1")
    
    # Verificar se o arquivo .env existe e contém as configurações necessárias
    if os.path.exists('.env'):
        print("Arquivo .env encontrado")
        
        # Verificar se as configurações necessárias estão presentes
        with open('.env', 'r') as f:
            conteudo = f.read()
            
        if 'RABBITMQ_URL' not in conteudo:
            print("Adicionando RABBITMQ_URL ao arquivo .env")
            with open('.env', 'a') as f:
                f.write('\nRABBITMQ_URL=pyamqp://guest@localhost//\n')
        
        if 'REDIS_URL' not in conteudo:
            print("Adicionando REDIS_URL ao arquivo .env")
            with open('.env', 'a') as f:
                f.write('\nREDIS_URL=redis://localhost:6380\n')
    else:
        print("Arquivo .env não encontrado. Criando...")
        with open('.env', 'w') as f:
            f.write('RABBITMQ_URL=pyamqp://guest@localhost//\n')
            f.write('REDIS_URL=redis://localhost:6380\n')
    
    print("Ambiente configurado para Windows")

def testar_celery():
    """Testa se o Celery está funcionando corretamente"""
    print("\n=== TESTANDO CELERY ===")
    
    # Verificar se o Celery está instalado
    try:
        import celery
        print(f"Celery versão {celery.__version__} encontrado")
        
        # Criar um arquivo de teste temporário para o Celery
        with open('celery_test.py', 'w') as f:
            f.write("""
from celery import Celery
import os

# Configurar Celery para teste
app = Celery('test_app', broker='pyamqp://guest@localhost//')
app.conf.worker_pool = 'solo'

@app.task
def add(x, y):
    return x + y

if __name__ == '__main__':
    # Definir variável de ambiente para Windows
    os.environ['FORKED_BY_MULTIPROCESSING'] = '1'
    
    # Tentar executar uma tarefa
    result = add.delay(4, 4)
    print("Tarefa enviada. ID:", result.id)
    print("Aguardando resultado...")
    try:
        output = result.get(timeout=5)
        print(f"Resultado: {output}")
        print("Celery está funcionando corretamente!")
    except Exception as e:
        print(f"Erro ao obter resultado: {e}")
        print("Verifique se o worker do Celery está em execução.")
""")
        
        print("Arquivo de teste criado. Executando teste...")
        
        # Executar o teste
        print("\nResultado do teste:")
        subprocess.run([sys.executable, 'celery_test.py'], check=True)
        
    except ImportError:
        print("Celery não está instalado. Execute: pip install celery")
        return False
    except subprocess.CalledProcessError:
        print("Erro ao executar o teste do Celery")
        return False
    
    return True

def gerar_script_inicializacao():
    """Gera um script de inicialização para o Celery no Windows"""
    print("\n=== GERANDO SCRIPT DE INICIALIZAÇÃO ===")
    
    # Criar script PowerShell
    with open('iniciar_celery.ps1', 'w') as f:
        f.write("""# Script PowerShell para iniciar o Celery no Windows
Write-Host "Iniciando Celery Worker para Windows" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Definir variável de ambiente para multiprocessing no Windows
$env:FORKED_BY_MULTIPROCESSING = "1"

# Iniciar o worker do Celery com o pool solo
Write-Host "Iniciando Celery worker com pool=solo..." -ForegroundColor Green
celery -A app.workers.tasks worker --pool=solo --loglevel=info
""")
    
    # Criar script batch
    with open('iniciar_celery.bat', 'w') as f:
        f.write("""@echo off
echo Iniciando Celery Worker para Windows
echo =====================================

:: Definir variável de ambiente para multiprocessing no Windows
set FORKED_BY_MULTIPROCESSING=1

:: Iniciar o worker do Celery com o pool solo
celery -A app.workers.tasks worker --pool=solo --loglevel=info

pause
""")
    
    print("Scripts de inicialização gerados:")
    print("- iniciar_celery.ps1 (PowerShell)")
    print("- iniciar_celery.bat (Batch)")
    print("\nPara iniciar o Celery, execute um dos scripts acima.")

def main():
    """Função principal"""
    print("=== DIAGNÓSTICO DO CELERY NO WINDOWS ===")
    print("Este script verifica e configura o ambiente para o Celery no Windows")
    
    # Verificar sistema
    in_venv = verificar_sistema()
    
    # Verificar dependências
    deps_ok = verificar_dependencias()
    
    # Verificar conexões
    rabbitmq_ok = verificar_conexao_rabbitmq()
    redis_ok = verificar_conexao_redis()
    
    # Configurar ambiente para Windows
    if platform.system() == 'Windows':
        configurar_ambiente_windows()
    
    # Gerar scripts de inicialização
    gerar_script_inicializacao()
    
    # Resumo
    print("\n=== RESUMO DO DIAGNÓSTICO ===")
    print(f"Sistema Windows: {'Sim' if platform.system() == 'Windows' else 'Não'}")
    print(f"Ambiente virtual: {'Ativo' if in_venv else 'Inativo'}")
    print(f"Dependências: {'OK' if deps_ok else 'Faltando'}")
    print(f"RabbitMQ: {'Conectado' if rabbitmq_ok else 'Erro de conexão'}")
    print(f"Redis: {'Conectado' if redis_ok else 'Erro de conexão'}")
    
    print("\n=== PRÓXIMOS PASSOS ===")
    if not in_venv:
        print("1. Ative o ambiente virtual: .\\venv\\Scripts\\activate")
    
    if not deps_ok:
        print("2. Instale as dependências: pip install -r requirements.txt")
    
    if not rabbitmq_ok:
        print("3. Verifique se o container do RabbitMQ está em execução")
        print("   docker ps | findstr rabbitmq")
        print("   Se não estiver, inicie-o: docker start gym-rabbitmq")
    
    if not redis_ok:
        print("4. Verifique se o container do Redis está em execução")
        print("   docker ps | findstr redis")
        print("   Se não estiver, inicie-o: docker start gym-redis")
    
    print("\nPara iniciar o Celery, execute: .\\iniciar_celery.ps1")
    print("Ou: .\\iniciar_celery.bat")

if __name__ == "__main__":
    main()
