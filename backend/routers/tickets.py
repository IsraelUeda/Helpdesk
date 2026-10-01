from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from rate_limiter import limit_ticket_creation
from security import get_current_user

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
    dependencies=[Depends(get_current_user)],
)

ALLOWED_STATUSES = {"aberto", "em_andamento", "fechado"}
ALLOWED_PRIORITIES = {"baixa", "media", "alta", "urgente"}


# 5. GET /tickets?status=&prioridade=&limit=25&offset=0
@router.get("", response_model=list[schemas.TicketResponse])
@router.get("/", response_model=list[schemas.TicketResponse], include_in_schema=False)
def list_tickets(
    status: Optional[str] = Query(None, description="Filtrar por status ('aberto', 'em_andamento', 'fechado')"),
    prioridade: Optional[str] = Query(None, description="Filtrar por prioridade ('baixa', 'media', 'alta', 'urgente')"),
    limit: int = Query(25, ge=1, le=100, description="Quantidade máxima de tickets a retornar por página (máximo 100, padrão 25)"),
    offset: int = Query(0, ge=0, description="Offset de paginação"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Ticket)

    if status and status.strip() and status.lower() != "todos":
        status_clean = status.strip().lower()
        if status_clean in ALLOWED_STATUSES:
            query = query.filter(models.Ticket.status == status_clean)

    if prioridade and prioridade.strip() and prioridade.lower() != "todas":
        prioridade_clean = prioridade.strip().lower()
        if prioridade_clean in ALLOWED_PRIORITIES:
            query = query.filter(models.Ticket.prioridade == prioridade_clean)

    tickets = (
        query.order_by(models.Ticket.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return tickets


# POST /tickets - Criação com Rate Limit de no máximo 25 tickets por minuto
@router.post(
    "",
    response_model=schemas.TicketResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_ticket_creation)],
)
@router.post(
    "/",
    response_model=schemas.TicketResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
    dependencies=[Depends(limit_ticket_creation)],
)
def create_ticket(
    ticket_data: schemas.TicketCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    titulo_final = (ticket_data.titulo or ticket_data.title or "Novo Chamado").strip()
    status_final = ticket_data.status.value if hasattr(ticket_data.status, "value") else (ticket_data.status or "aberto")
    prioridade_final = ticket_data.prioridade.value if hasattr(ticket_data.prioridade, "value") else (ticket_data.prioridade or "media")
    solicitante_final = (ticket_data.solicitante if ticket_data.solicitante and ticket_data.solicitante != "Usuário" else (current_user.name or "Usuário")).strip()

    novo_ticket = models.Ticket(
        titulo=titulo_final,
        solicitante=solicitante_final,
        categoria=(ticket_data.categoria or "Geral").strip(),
        prioridade=prioridade_final,
        status=status_final,
        title=titulo_final,
        description=(ticket_data.description or titulo_final).strip(),
        criado_em=datetime.utcnow(),
    )

    if ticket_data.slaVencimento:
        try:
            iso_date = ticket_data.slaVencimento.replace("Z", "+00:00")
            novo_ticket.sla_vencimento = datetime.fromisoformat(iso_date)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Formato inválido de slaVencimento. Utilize o padrão ISO 8601.",
            )

    db.add(novo_ticket)
    db.commit()
    db.refresh(novo_ticket)
    return novo_ticket


# 6. GET /tickets/:id
@router.get("/{ticket_id}", response_model=schemas.TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    if ticket_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de ticket inválido")

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    return ticket


# Atualizar ticket (PUT /tickets/:id) - Suporta JSON Body ou Query Param legado
@router.put("/{ticket_id}", response_model=schemas.TicketResponse)
def update_ticket(
    ticket_id: int,
    payload: Optional[schemas.TicketUpdate] = None,
    status_query: Optional[str] = Query(None, alias="status", description="Status legado via query"),
    db: Session = Depends(get_db),
):
    if ticket_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de ticket inválido")

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    # Define valores a serem atualizados a partir do body ou query param
    novo_status = None
    if payload and payload.status is not None:
        novo_status = payload.status.value if hasattr(payload.status, "value") else str(payload.status)
    elif status_query:
        novo_status = status_query.strip().lower()

    if novo_status:
        if novo_status not in ALLOWED_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Status '{novo_status}' inválido. Valores aceitos: {', '.join(sorted(ALLOWED_STATUSES))}",
            )
        ticket.status = novo_status

    if payload:
        if payload.prioridade is not None:
            pri = payload.prioridade.value if hasattr(payload.prioridade, "value") else str(payload.prioridade)
            if pri in ALLOWED_PRIORITIES:
                ticket.prioridade = pri
        if payload.titulo:
            ticket.titulo = payload.titulo
            ticket.title = payload.titulo
        elif payload.title:
            ticket.titulo = payload.title
            ticket.title = payload.title
        if payload.description is not None:
            ticket.description = payload.description
        if payload.categoria is not None:
            ticket.categoria = payload.categoria
        if payload.solicitante is not None:
            ticket.solicitante = payload.solicitante
        if payload.slaVencimento:
            try:
                ticket.sla_vencimento = datetime.fromisoformat(payload.slaVencimento.replace("Z", "+00:00"))
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Formato inválido de slaVencimento.",
                )

    db.commit()
    db.refresh(ticket)
    return ticket


# 7. GET /tickets/:id/mensagens
@router.get("/{ticket_id}/mensagens", response_model=list[schemas.MessageResponse])
def get_ticket_messages(ticket_id: int, db: Session = Depends(get_db)):
    if ticket_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de ticket inválido")

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
@router.post(
    "/{ticket_id}/mensagens",
    response_model=schemas.MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_message(
    ticket_id: int,
    mensagem: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if ticket_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de ticket inválido")

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    papel_final = mensagem.papel.value if hasattr(mensagem.papel, "value") else (mensagem.papel or current_user.role or "atendente")
    autor_final = (mensagem.autor or current_user.name or "Suporte TI").strip()

    nova_mensagem = models.Message(
        ticket_id=ticket_id,
        autor=autor_final,
        papel=papel_final,
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
    if ticket_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de ticket inválido")

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    sugestao = (
        db.query(models.AiSuggestion)
        .filter(models.AiSuggestion.ticket_id == ticket_id)
        .first()
    )
    if not sugestao:
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
    if ticket_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de ticket inválido")

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
    if ticket_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de ticket inválido")

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
