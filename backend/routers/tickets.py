from datetime import datetime, timezone, timedelta
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

SLA_HOURS_BY_PRIORITY = {
    "urgente": 4,
    "alta": 12,
    "media": 24,
    "baixa": 48,
}


def utc_now():
    return datetime.now(timezone.utc)


def record_ticket_history(
    db: Session,
    ticket_id: int,
    user_id: Optional[int],
    acao: str,
    campo: Optional[str] = None,
    valor_antigo: Optional[str] = None,
    valor_novo: Optional[str] = None,
):
    """Registra uma alteração na linha do tempo / auditoria do chamado."""
    entry = models.TicketHistory(
        ticket_id=ticket_id,
        user_id=user_id,
        acao=acao,
        campo=campo,
        valor_antigo=str(valor_antigo) if valor_antigo is not None else None,
        valor_novo=str(valor_novo) if valor_novo is not None else None,
        criado_em=utc_now(),
    )
    db.add(entry)


def check_ticket_access(ticket: models.Ticket, current_user: models.User):
    """
    Regra RBAC:
    - Atendentes e Administradores têm acesso a qualquer chamado.
    - Clientes só podem acessar chamados criados por eles mesmos.
    """
    if current_user.role in ["atendente", "admin"]:
        return
    if ticket.user_id == current_user.id:
        return
    if ticket.solicitante and (ticket.solicitante == current_user.name or ticket.solicitante == current_user.email):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Acesso negado: você não tem permissão para acessar este chamado.",
    )


# 5. GET /tickets?status=&prioridade=&assigned_to_id=&limit=25&offset=0
@router.get("", response_model=list[schemas.TicketResponse])
@router.get("/", response_model=list[schemas.TicketResponse], include_in_schema=False)
def list_tickets(
    status: Optional[str] = Query(None, description="Filtrar por status ('aberto', 'em_andamento', 'fechado')"),
    prioridade: Optional[str] = Query(None, description="Filtrar por prioridade ('baixa', 'media', 'alta', 'urgente')"),
    assigned_to_id: Optional[int] = Query(None, description="Filtrar por técnico/atendente atribuído"),
    limit: int = Query(25, ge=1, le=100, description="Quantidade máxima de tickets a retornar por página (máximo 100, padrão 25)"),
    offset: int = Query(0, ge=0, description="Offset de paginação"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Ticket)

    # RBAC: Clientes só veem seus próprios tickets
    if current_user.role == "cliente":
        query = query.filter(
            (models.Ticket.user_id == current_user.id)
            | (models.Ticket.solicitante == current_user.name)
            | (models.Ticket.solicitante == current_user.email)
        )
    elif assigned_to_id is not None:
        query = query.filter(models.Ticket.assigned_to_id == assigned_to_id)

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
        criado_em=utc_now(),
        user_id=current_user.id,
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
    else:
        # Regra de negócio: cálculo automático do SLA baseado na prioridade
        horas_sla = SLA_HOURS_BY_PRIORITY.get(prioridade_final, 24)
        novo_ticket.sla_vencimento = novo_ticket.criado_em + timedelta(hours=horas_sla)

    db.add(novo_ticket)
    db.flush()

    # Registra no histórico a criação do chamado
    record_ticket_history(
        db=db,
        ticket_id=novo_ticket.id,
        user_id=current_user.id,
        acao="criacao",
        campo=None,
        valor_antigo=None,
        valor_novo=titulo_final,
    )

    db.commit()
    db.refresh(novo_ticket)
    return novo_ticket


# 6. GET /tickets/:id
@router.get("/{ticket_id}", response_model=schemas.TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if ticket_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de ticket inválido")

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    check_ticket_access(ticket, current_user)
    return ticket


# Atualizar ticket (PUT /tickets/:id) - Suporta JSON Body ou Query Param legado
@router.put("/{ticket_id}", response_model=schemas.TicketResponse)
def update_ticket(
    ticket_id: int,
    payload: Optional[schemas.TicketUpdate] = None,
    status_query: Optional[str] = Query(None, alias="status", description="Status legado via query"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if ticket_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de ticket inválido")

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    check_ticket_access(ticket, current_user)

    # RBAC: Clientes só podem editar descrição ou fechar/cancelar o chamado
    if current_user.role == "cliente" and payload:
        if payload.prioridade is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Clientes não têm permissão para alterar a prioridade.",
            )
        if payload.slaVencimento is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Clientes não têm permissão para alterar o SLA.",
            )
        if payload.assigned_to_id is not None or payload.assignedToId is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Clientes não têm permissão para atribuir atendentes.",
            )

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

        if current_user.role == "cliente" and ticket.status == "fechado" and novo_status != "fechado":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Clientes não têm permissão para reabrir chamados já encerrados. Contate o suporte.",
            )

        if ticket.status != novo_status:
            acao_hist = "reabertura" if ticket.status == "fechado" else "alteracao_status"
            record_ticket_history(
                db=db,
                ticket_id=ticket.id,
                user_id=current_user.id,
                acao=acao_hist,
                campo="status",
                valor_antigo=ticket.status,
                valor_novo=novo_status,
            )
            ticket.status = novo_status
            if novo_status == "fechado":
                ticket.fechado_em = utc_now()
            else:
                ticket.fechado_em = None

    if payload:
        if payload.prioridade is not None:
            pri = payload.prioridade.value if hasattr(payload.prioridade, "value") else str(payload.prioridade)
            if pri in ALLOWED_PRIORITIES and ticket.prioridade != pri:
                record_ticket_history(
                    db=db,
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                    acao="alteracao_prioridade",
                    campo="prioridade",
                    valor_antigo=ticket.prioridade,
                    valor_novo=pri,
                )
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

        target_assigned_to = payload.assigned_to_id or payload.assignedToId
        if target_assigned_to is not None and ticket.assigned_to_id != target_assigned_to:
            resp_user = db.query(models.User).filter(models.User.id == target_assigned_to).first()
            if resp_user and resp_user.role in ["atendente", "admin"]:
                valor_antigo = ticket.responsavel.name if ticket.responsavel else None
                ticket.assigned_to_id = target_assigned_to
                record_ticket_history(
                    db=db,
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                    acao="atribuicao_responsavel",
                    campo="assigned_to_id",
                    valor_antigo=valor_antigo,
                    valor_novo=resp_user.name,
                )

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


# POST /tickets/:id/atribuir - Atribui o ticket a um técnico/atendente
@router.post("/{ticket_id}/atribuir", response_model=schemas.TicketResponse)
def assign_ticket(
    ticket_id: int,
    assign_data: schemas.AssignTicketRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in ["atendente", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas atendentes ou administradores podem atribuir chamados.",
        )

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    target_user = db.query(models.User).filter(models.User.id == assign_data.assigned_to_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário para atribuição não encontrado.")

    if target_user.role not in ["atendente", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O usuário selecionado não possui papel de atendente ou administrador.",
        )

    valor_antigo = ticket.responsavel.name if ticket.responsavel else None
    ticket.assigned_to_id = target_user.id

    record_ticket_history(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id,
        acao="atribuicao_responsavel",
        campo="assigned_to_id",
        valor_antigo=valor_antigo,
        valor_novo=target_user.name,
    )

    db.commit()
    db.refresh(ticket)
    return ticket


# POST /tickets/:id/assumir - Atendente/Admin assume o chamado diretamente
@router.post("/{ticket_id}/assumir", response_model=schemas.TicketResponse)
def take_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in ["atendente", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas atendentes ou administradores podem assumir chamados.",
        )

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    valor_antigo = ticket.responsavel.name if ticket.responsavel else None
    ticket.assigned_to_id = current_user.id

    if ticket.status == "aberto":
        ticket.status = "em_andamento"
        record_ticket_history(
            db=db,
            ticket_id=ticket.id,
            user_id=current_user.id,
            acao="alteracao_status",
            campo="status",
            valor_antigo="aberto",
            valor_novo="em_andamento",
        )

    record_ticket_history(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id,
        acao="atribuicao_responsavel",
        campo="assigned_to_id",
        valor_antigo=valor_antigo,
        valor_novo=current_user.name,
    )

    db.commit()
    db.refresh(ticket)
    return ticket


# GET /tickets/:id/historico - Linha do tempo / histórico de auditoria
@router.get("/{ticket_id}/historico", response_model=list[schemas.TicketHistoryResponse])
def get_ticket_history(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if ticket_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de ticket inválido")

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    check_ticket_access(ticket, current_user)

    historico = (
        db.query(models.TicketHistory)
        .filter(models.TicketHistory.ticket_id == ticket_id)
        .order_by(models.TicketHistory.id.asc())
        .all()
    )
    return historico


# 7. GET /tickets/:id/mensagens
@router.get("/{ticket_id}/mensagens", response_model=list[schemas.MessageResponse])
def get_ticket_messages(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if ticket_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de ticket inválido")

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    check_ticket_access(ticket, current_user)

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

    check_ticket_access(ticket, current_user)

    # Regra de negócio: não é possível enviar mensagem em chamado fechado
    if ticket.status == "fechado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível enviar mensagens em um chamado já fechado.",
        )

    papel_final = mensagem.papel.value if hasattr(mensagem.papel, "value") else (mensagem.papel or current_user.role or "atendente")
    autor_final = (mensagem.autor or current_user.name or "Suporte TI").strip()

    nova_mensagem = models.Message(
        ticket_id=ticket_id,
        autor=autor_final,
        papel=papel_final,
        texto=mensagem.texto,
        enviado_em=utc_now(),
    )
    db.add(nova_mensagem)

    # Regra de negócio: se um atendente responde pela primeira vez em ticket 'aberto', transiciona para 'em_andamento'
    if current_user.role in ["atendente", "admin"] and ticket.status == "aberto":
        ticket.status = "em_andamento"
        record_ticket_history(
            db=db,
            ticket_id=ticket.id,
            user_id=current_user.id,
            acao="alteracao_status",
            campo="status",
            valor_antigo="aberto",
            valor_novo="em_andamento",
        )

    db.commit()
    db.refresh(nova_mensagem)
    return nova_mensagem


# 9. GET /tickets/:id/sugestao-ia
@router.get("/{ticket_id}/sugestao-ia", response_model=schemas.AiSuggestionResponse)
def get_ai_suggestion(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if ticket_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de ticket inválido")

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    check_ticket_access(ticket, current_user)

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
def accept_ai_suggestion(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role == "cliente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas atendentes ou administradores podem aplicar sugestões da IA.",
        )

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

    record_ticket_history(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id,
        acao="aplicacao_sugestao_ia",
        campo="categoria_e_prioridade",
        valor_antigo=None,
        valor_novo=f"{sugestao.categoria} / {sugestao.prioridade}",
    )

    db.commit()
    db.refresh(ticket)

    return {
        "sucesso": True,
        "mensagem": "Sugestão da IA aplicada com sucesso.",
        "ticket": ticket,
    }


# 11. POST /tickets/:id/sugestao-ia/ignorar
@router.post("/{ticket_id}/sugestao-ia/ignorar", response_model=schemas.AiSuggestionActionResponse)
def ignore_ai_suggestion(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role == "cliente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas atendentes ou administradores podem ignorar sugestões da IA.",
        )

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
