import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

# Pega as peças separadas do ambiente (que o Docker injetou do .env)
DB_USER = os.getenv("DB_USER", "sprusr")
DB_PASSWORD = os.getenv("DB_PASSWORD", "KJH12")
DB_NAME = os.getenv("DB_NAME", "helpdesk_db")
DB_HOST = os.getenv("DB_HOST", "db")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

# Cria engine com fallback para SQLite caso PostgreSQL não esteja disponível no ambiente local
try:
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(DATABASE_URL)
        # Testa a conexão
        with engine.connect():
            pass
except Exception as exc:
    logger.warning("Falha ao conectar no PostgreSQL (%s). Utilizando SQLite local para desenvolvimento.", exc)
    DATABASE_URL = "sqlite:///./helpdesk.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Função para abrir e fechar o banco a cada requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()