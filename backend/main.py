from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import engine, get_db
import models, schemas

# O comando mágico que cria as tabelas no Postgres se elas não existirem
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Help Desk API")

@app.get("/")
def read_root():
    return {"mensagem": "Conectado ao PostgreSQL com sucesso!"}

# Rota para CRIAR um novo ticket
@app.post("/tickets/", response_model=schemas.TicketResponse)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    novo_ticket = models.Ticket(title=ticket.title, description=ticket.description)
    db.add(novo_ticket)
    db.commit()
    db.refresh(novo_ticket)
    return novo_ticket