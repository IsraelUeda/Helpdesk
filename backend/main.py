from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionLocal
import models
from routers import auth, metrics, tickets
from seed import seed_demo_data

# Cria as tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Semeia os dados padrão de demonstração se o banco estiver vazio
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