from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# A URL vem do ambiente do Docker (definido no docker-compose.yml)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:senha_segura@db:5432/helpdesk_db")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()