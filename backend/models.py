from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="atendente")  # cliente, atendente, admin
    created_at = Column(DateTime, default=utc_now)

    tickets_criados = relationship("Ticket", foreign_keys="[Ticket.user_id]", back_populates="criador")
    tickets_atribuidos = relationship("Ticket", foreign_keys="[Ticket.assigned_to_id]", back_populates="responsavel")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True, nullable=False)
    solicitante = Column(String, nullable=False, default="Usuário")
    categoria = Column(String, nullable=False, default="Geral")
    prioridade = Column(String, default="media") # baixa, media, alta, urgente
    status = Column(String, default="aberto")    # aberto, em_andamento, fechado
    sla_vencimento = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=utc_now)
    fechado_em = Column(DateTime, nullable=True)

    # Vínculo com usuários (RBAC e atribuição de técnicos)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Campos de compatibilidade legada
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)

    criador = relationship("User", foreign_keys=[user_id], back_populates="tickets_criados")
    responsavel = relationship("User", foreign_keys=[assigned_to_id], back_populates="tickets_atribuidos")

    mensagens = relationship("Message", back_populates="ticket", cascade="all, delete-orphan", order_by="Message.id")
    sugestao = relationship("AiSuggestion", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
    historico = relationship("TicketHistory", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketHistory.id.asc()")

    @property
    def slaVencimento(self):
        return self.sla_vencimento.isoformat() if self.sla_vencimento else None

    @property
    def criadoEm(self):
        return self.criado_em.isoformat() if self.criado_em else None

    @property
    def fechadoEm(self):
        return self.fechado_em.isoformat() if self.fechado_em else None

    @property
    def userId(self):
        return self.user_id


    @property
    def assignedToId(self):
        return self.assigned_to_id

    @property
    def tecnicoResponsavel(self):
        return self.responsavel.name if self.responsavel else None


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    autor = Column(String, nullable=False)
    papel = Column(String, default="atendente") # 'atendente' ou 'cliente'
    texto = Column(Text, nullable=False)
    enviado_em = Column(DateTime, default=utc_now)

    ticket = relationship("Ticket", back_populates="mensagens")

    @property
    def ticketId(self):
        return self.ticket_id

    @property
    def enviadoEm(self):
        return self.enviado_em.isoformat() if self.enviado_em else None


class AiSuggestion(Base):
    __tablename__ = "ai_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, unique=True)
    categoria = Column(String, nullable=False)
    prioridade = Column(String, nullable=False)
    confianca = Column(Float, default=0.8)
    status = Column(String, default="pendente") # 'pendente', 'aceito', 'ignorado'
    criado_em = Column(DateTime, default=utc_now)

    ticket = relationship("Ticket", back_populates="sugestao")

    @property
    def ticketId(self):
        return self.ticket_id


class TicketHistory(Base):
    __tablename__ = "ticket_history"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acao = Column(String, nullable=False)  # criacao, alteracao_status, alteracao_prioridade, atribuicao_responsavel, alteracao_dados
    campo = Column(String, nullable=True)  # ex: status, prioridade, assigned_to_id
    valor_antigo = Column(String, nullable=True)
    valor_novo = Column(String, nullable=True)
    criado_em = Column(DateTime, default=utc_now)

    ticket = relationship("Ticket", back_populates="historico")
    usuario = relationship("User")

    @property
    def ticketId(self):
        return self.ticket_id

    @property
    def userId(self):
        return self.user_id

    @property
    def usuarioNome(self):
        return self.usuario.name if self.usuario else "Sistema"

    @property
    def criadoEm(self):
        return self.criado_em.isoformat() if self.criado_em else None