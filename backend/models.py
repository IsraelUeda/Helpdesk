from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="atendente")
    created_at = Column(DateTime, default=datetime.utcnow)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True, nullable=False)
    solicitante = Column(String, nullable=False, default="Usuário")
    categoria = Column(String, nullable=False, default="Geral")
    prioridade = Column(String, default="media") # baixa, media, alta, urgente
    status = Column(String, default="aberto")    # aberto, em_andamento, fechado
    sla_vencimento = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    # Campos de compatibilidade legada
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)

    mensagens = relationship("Message", back_populates="ticket", cascade="all, delete-orphan", order_by="Message.id")
    sugestao = relationship("AiSuggestion", back_populates="ticket", uselist=False, cascade="all, delete-orphan")

    @property
    def slaVencimento(self):
        return self.sla_vencimento.isoformat() if self.sla_vencimento else None

    @property
    def criadoEm(self):
        return self.criado_em.isoformat() if self.criado_em else None


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    autor = Column(String, nullable=False)
    papel = Column(String, default="atendente") # 'atendente' ou 'cliente'
    texto = Column(Text, nullable=False)
    enviado_em = Column(DateTime, default=datetime.utcnow)

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
    criado_em = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="sugestao")

    @property
    def ticketId(self):
        return self.ticket_id