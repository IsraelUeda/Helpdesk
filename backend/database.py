import os
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

# Pega as peças separadas do ambiente (injetadas pelo Docker via .env)
DB_USER = os.getenv("DB_USER", "sprusr")
DB_PASSWORD = os.getenv("DB_PASSWORD", "KJH12")
DB_NAME = os.getenv("DB_NAME", "helpdesk_db")
DB_HOST = os.getenv("DB_HOST") # No Docker Compose é definido como "db"

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    host_target = DB_HOST or "localhost"
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{host_target}:5432/{DB_NAME}"

# Se estiver no Docker (DB_HOST == "db"), aguarda o contêiner do Postgres ficar pronto
engine = None
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
elif DB_HOST == "db":
    max_retries = 10
    for attempt in range(max_retries):
        try:
            eng = create_engine(DATABASE_URL)
            with eng.connect():
                engine = eng
                logger.info("Conexão com PostgreSQL estabelecida com sucesso!")
                break
        except Exception as exc:
            if attempt < max_retries - 1:
                logger.info("Aguardando contêiner do PostgreSQL iniciar (%d/%d)...", attempt + 1, max_retries)
                time.sleep(2)
            else:
                logger.warning("PostgreSQL não respondeu. Usando SQLite local como fallback.")
                DATABASE_URL = "sqlite:///./helpdesk.db"
                engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    try:
        eng = create_engine(DATABASE_URL)
        with eng.connect():
            engine = eng
    except Exception as exc:
        logger.warning("PostgreSQL local indisponível (%s). Usando SQLite local para desenvolvimento.", exc)
        DATABASE_URL = "sqlite:///./helpdesk.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Função para abrir e fechar a sessão do banco a cada requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()