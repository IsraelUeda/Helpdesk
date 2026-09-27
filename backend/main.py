from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, get_db
import models, schemas

# Cria as tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Help Desk API")

@app.get("/")
def read_root():
    return {"mensagem": "API do Help Desk rodando com segurança!"}

# 1. ROTA DE CRIAR (POST) - Você já tinha feito essa!
@app.post("/tickets/", response_model=schemas.TicketResponse)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    novo_ticket = models.Ticket(title=ticket.title, description=ticket.description)
    db.add(novo_ticket)
    db.commit()
    db.refresh(novo_ticket)
    return novo_ticket

# 2. ROTA DE LISTAR (GET) - Traz todos os tickets do banco
@app.get("/tickets/", response_model=list[schemas.TicketResponse])
def read_tickets(db: Session = Depends(get_db)):
    tickets = db.query(models.Ticket).all()
    return tickets

# 3. ROTA DE ATUALIZAR (PUT) - Muda o status do ticket
@app.put("/tickets/{ticket_id}", response_model=schemas.TicketResponse)
def update_ticket(ticket_id: int, status: str, db: Session = Depends(get_db)):
    # Busca o ticket no banco pelo ID
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    
    # Se não achar, retorna erro 404
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")
    
    # Se achar, atualiza o status e salva
    ticket.status = status
    db.commit()
    db.refresh(ticket)
    return ticket