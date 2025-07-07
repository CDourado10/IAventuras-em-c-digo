# test_env.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Mostrar diretório atual
current_dir = os.getcwd()
print(f"Diretório atual: {current_dir}")

# Procurar arquivo .env
dotenv_path = find_dotenv()
print(f"Arquivo .env encontrado em: {dotenv_path if dotenv_path else 'Não encontrado'}")

# Carregar variáveis de ambiente do arquivo .env explicitamente
env_file = os.path.join(current_dir, '.env')
print(f"Tentando carregar arquivo .env de: {env_file}")
print(f"Arquivo existe: {os.path.exists(env_file)}")

if os.path.exists(env_file):
    # Mostrar conteúdo do arquivo .env
    print("\nConteúdo do arquivo .env:")
    with open(env_file, 'r') as f:
        print(f.read())
    
    # Carregar variáveis de ambiente do arquivo .env
    load_dotenv(env_file)

# Imprimir a URL do banco de dados
print(f"\nDATABASE_URL: {os.getenv('DATABASE_URL', 'Não definido')}")

