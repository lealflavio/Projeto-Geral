# /home/ubuntu/Sistema/dashboard/backend/app/create_tables.py
import os
import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Adjust the import path based on your project structure
# Assuming create_tables.py is in the same directory as main.py and database.py is in app/
from database import Base # If database.py is in the same dir as create_tables.py
from models import User, WO, ServiceValue # If models.py is in the same dir

# If your main.py, database.py, models.py are inside an 'app' subdirectory relative to where create_tables.py is
# from app.database import Base 
# from app.models import User, WO, ServiceValue

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Erro: DATABASE_URL não está definida. Verifique seu arquivo .env ou variáveis de ambiente do servidor.")
    exit(1)

# Render can take a moment for the DB to be ready, add retries
MAX_RETRIES = 10
RETRY_DELAY = 5 # seconds

print(f"Tentando conectar ao banco de dados: {DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL}") # Mascara a senha

for i in range(MAX_RETRIES):
    try:
        engine = create_engine(DATABASE_URL)
        # Test connection
        with engine.connect() as connection:
            print(f"Conexão com o banco de dados bem-sucedida na tentativa {i+1}.")
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print(f"Tabelas criadas com sucesso (ou já existiam) após {i+1} tentativas.")
        break
    except OperationalError as e:
        print(f"Tentativa {i+1} de {MAX_RETRIES}: Erro operacional ao conectar ou criar tabelas: {e}")
        if i < MAX_RETRIES - 1:
            print(f"Aguardando {RETRY_DELAY} segundos antes de tentar novamente...")
            time.sleep(RETRY_DELAY)
        else:
            print("Máximo de tentativas atingido. Falha ao criar tabelas.")
            exit(1)
    except Exception as e:
        print(f"Um erro inesperado ocorreu durante a configuração do banco de dados: {e}")
        exit(1)

print("Script create_tables.py concluído.")

