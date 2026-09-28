from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/tickets", tags=["Tickets"])

# 5. GET /tickets?status=&prioridade=
@router.get("", response_model=list[schemas.TicketResponse])
@router.get("/", response_model=list[schemas.TicketResponse], include_in_schema=False)
def list_tickets(
    status: Optional[str] = Query(None, description="Filtrar por status ('aberto', 'em_andamento', 'fechado')"),
    prioridade: Optional[str] = Query(None, description="Filtrar por prioridade ('baixa', 'media', 'alta', 'urgente')"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Ticket)

    if status and status.strip() and status.lower() != "todos":
        query = query.filter(models.Ticket.status == status.strip().lower())

    if prioridade and prioridade.strip() and prioridade.lower() != "todas":
        query = query.filter(models.Ticket.prioridade == prioridade.strip().lower())

    tickets = query.order_by(models.Ticket.id.asc()).all()
    return tickets


# Rota de criar (POST) para compatibilidade e novos tickets
@router.post("", response_model=schemas.TicketResponse)
@router.post("/", response_model=schemas.TicketResponse, include_in_schema=False)
def create_ticket(ticket_data: schemas.TicketCreate, db: Session = Depends(get_db)):
    titulo_final = ticket_data.titulo or ticket_data.title or "Novo Chamado"
    novo_ticket = models.Ticket(
        titulo=titulo_final,
        solicitante=ticket_data.solicitante or "Usuário",
        categoria=ticket_data.categoria or "Geral",
        prioridade=ticket_data.prioridade or "media",
        status=ticket_data.status or "aberto",
        title=titulo_final,
        description=ticket_data.description or titulo_final,
        criado_em=datetime.utcnow(),
    )
    if ticket_data.slaVencimento:
        try:
            novo_ticket.sla_vencimento = datetime.fromisoformat(ticket_data.slaVencimento)
        except ValueError:
            pass

    db.add(novo_ticket)
    db.commit()
    db.refresh(novo_ticket)
    return novo_ticket


# 6. GET /tickets/:id
@router.get("/{ticket_id}", response_model=schemas.TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    return ticket


# Atualizar status do ticket (PUT /tickets/:id)
@router.put("/{ticket_id}", response_model=schemas.TicketResponse)
def update_ticket(ticket_id: int, status: str, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    ticket.status = status
    db.commit()
    db.refresh(ticket)
    return ticket


# 7. GET /tickets/:id/mensagens
@router.get("/{ticket_id}/mensagens", response_model=list[schemas.MessageResponse])
def get_ticket_messages(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    mensagens = (
        db.query(models.Message)
        .filter(models.Message.ticket_id == ticket_id)
        .order_by(models.Message.id.asc())
        .all()
    )
    return mensagens


# 8. POST /tickets/:id/mensagens
@router.post("/{ticket_id}/mensagens", response_model=schemas.MessageResponse)
def create_ticket_message(
    ticket_id: int,
    mensagem: schemas.MessageCreate,
    db: Session = Depends(get_db),
):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    nova_mensagem = models.Message(
        ticket_id=ticket_id,
        autor=mensagem.autor or "Suporte TI",
        papel=mensagem.papel or "atendente",
        texto=mensagem.texto,
        enviado_em=datetime.utcnow(),
    )
    db.add(nova_mensagem)
    db.commit()
    db.refresh(nova_mensagem)
    return nova_mensagem


# 9. GET /tickets/:id/sugestao-ia
@router.get("/{ticket_id}/sugestao-ia", response_model=schemas.AiSuggestionResponse)
def get_ai_suggestion(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    sugestao = (
        db.query(models.AiSuggestion)
        .filter(models.AiSuggestion.ticket_id == ticket_id)
        .first()
    )
    if not sugestao:
        # Se não houver sugestão prévia, gera uma sugestão padrão inteligente
        sugestao = models.AiSuggestion(
            ticket_id=ticket_id,
            categoria=ticket.categoria or "Sistemas",
            prioridade=ticket.prioridade or "media",
            confianca=0.85,
            status="pendente",
        )
        db.add(sugestao)
        db.commit()
        db.refresh(sugestao)

    return sugestao


# 10. POST /tickets/:id/sugestao-ia/aceitar
@router.post("/{ticket_id}/sugestao-ia/aceitar", response_model=schemas.AiSuggestionActionResponse)
def accept_ai_suggestion(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    sugestao = (
        db.query(models.AiSuggestion)
        .filter(models.AiSuggestion.ticket_id == ticket_id)
        .first()
    )
    if not sugestao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sugestão não encontrada")

    sugestao.status = "aceito"
    # Aplica sugestão da IA ao chamado
    ticket.categoria = sugestao.categoria
    ticket.prioridade = sugestao.prioridade
    db.commit()
    db.refresh(ticket)

    return {
        "sucesso": True,
        "mensagem": "Sugestão da IA aplicada com sucesso.",
        "ticket": ticket,
    }


# 11. POST /tickets/:id/sugestao-ia/ignorar
@router.post("/{ticket_id}/sugestao-ia/ignorar", response_model=schemas.AiSuggestionActionResponse)
def ignore_ai_suggestion(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    sugestao = (
        db.query(models.AiSuggestion)
        .filter(models.AiSuggestion.ticket_id == ticket_id)
        .first()
    )
    if not sugestao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sugestão não encontrada")

    sugestao.status = "ignorado"
    db.commit()

    return {
        "sucesso": True,
        "mensagem": "Sugestão da IA ignorada.",
        "ticket": ticket,
    }
