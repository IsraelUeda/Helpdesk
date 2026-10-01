from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from database import engine, SessionLocal
import models
from routers import auth, metrics, tickets
from seed import seed_demo_data

def migrate_database_schema(db_engine):
    """
    Garante a criação de todas as tabelas e adiciona colunas que possam faltar
    caso a tabela 'tickets' tenha sido criada em versão anterior no volume do PostgreSQL.
    """
    models.Base.metadata.create_all(bind=db_engine)

    try:
        inspector = inspect(db_engine)
        if "tickets" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("tickets")]
            with db_engine.begin() as conn:
                if "titulo" not in columns:
                    conn.execute(text("ALTER TABLE tickets ADD COLUMN titulo VARCHAR"))
                if "solicitante" not in columns:
                    conn.execute(text("ALTER TABLE tickets ADD COLUMN solicitante VARCHAR DEFAULT 'Usuário'"))
                if "categoria" not in columns:
                    conn.execute(text("ALTER TABLE tickets ADD COLUMN categoria VARCHAR DEFAULT 'Geral'"))
                if "prioridade" not in columns:
                    conn.execute(text("ALTER TABLE tickets ADD COLUMN prioridade VARCHAR DEFAULT 'media'"))
                if "status" not in columns:
                    conn.execute(text("ALTER TABLE tickets ADD COLUMN status VARCHAR DEFAULT 'aberto'"))
                if "sla_vencimento" not in columns:
                    conn.execute(text("ALTER TABLE tickets ADD COLUMN sla_vencimento TIMESTAMP"))
                if "criado_em" not in columns:
                    conn.execute(text("ALTER TABLE tickets ADD COLUMN criado_em TIMESTAMP"))
                if "title" not in columns:
                    conn.execute(text("ALTER TABLE tickets ADD COLUMN title VARCHAR"))
                if "description" not in columns:
                    conn.execute(text("ALTER TABLE tickets ADD COLUMN description VARCHAR"))

                conn.execute(text("UPDATE tickets SET titulo = title WHERE titulo IS NULL AND title IS NOT NULL"))
                conn.execute(text("UPDATE tickets SET titulo = 'Chamado' WHERE titulo IS NULL"))
                conn.execute(text("UPDATE tickets SET solicitante = 'Usuário' WHERE solicitante IS NULL"))
                conn.execute(text("UPDATE tickets SET categoria = 'Geral' WHERE categoria IS NULL"))
                conn.execute(text("UPDATE tickets SET prioridade = 'media' WHERE prioridade IS NULL"))
                conn.execute(text("UPDATE tickets SET status = 'aberto' WHERE status IS NULL"))
    except Exception as exc:
        print(f"[Aviso Migração] {exc}")

# Executa migração de esquema
migrate_database_schema(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Assegura o esquema e semeia os dados na inicialização da aplicação
    migrate_database_schema(engine)
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="Help Desk API",
    description="API do Help Desk com autenticação, métricas, chamados, chat e sugestões de IA.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuração de CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão dos roteadores
app.include_router(auth.router)
app.include_router(metrics.router)
app.include_router(tickets.router)

@app.get("/")
def read_root():
    return {"mensagem": "API do Help Desk rodando com segurança e todos os 11 endpoints disponíveis!"}


@app.get("/health", tags=["Sistema"])
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        return {"status": "degraded", "database": f"error: {str(exc)}"}