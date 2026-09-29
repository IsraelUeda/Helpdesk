from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# --- Enums para valores controlados ---
class TicketStatus(str, Enum):
    aberto = "aberto"
    em_andamento = "em_andamento"
    fechado = "fechado"


class TicketPriority(str, Enum):
    baixa = "baixa"
    media = "media"
    alta = "alta"
    urgente = "urgente"


class MessageRole(str, Enum):
    atendente = "atendente"
    cliente = "cliente"


class AiSuggestionStatus(str, Enum):
    pendente = "pendente"
    aceito = "aceito"
    ignorado = "ignorado"


# --- Auth Schemas ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128, description="Senha com no mínimo 6 caracteres")

    @field_validator("email")
    @classmethod
    def sanitize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str = "atendente"

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# --- Métricas Schemas ---
class MetricResumoResponse(BaseModel):
    ticketsAbertos: int
    tempoMedioResposta: str
    slaCumprido: int


class TicketPorDiaResponse(BaseModel):
    dia: str
    abertos: int
    fechados: int


# --- Tickets Schemas ---
class TicketCreate(BaseModel):
    titulo: Optional[str] = Field(None, max_length=150, description="Título do chamado")
    title: Optional[str] = Field(None, max_length=150, description="Compatibilidade com title")
    description: Optional[str] = Field(None, max_length=5000, description="Descrição detalhada")
    solicitante: Optional[str] = Field("Usuário", max_length=100)
    categoria: Optional[str] = Field("Geral", max_length=50)
    prioridade: Optional[TicketPriority] = TicketPriority.media
    status: Optional[TicketStatus] = TicketStatus.aberto
    slaVencimento: Optional[str] = Field(None, description="Data limite de SLA no formato ISO")

    @field_validator("slaVencimento")
    @classmethod
    def validate_sla_date(cls, v: Optional[str]) -> Optional[str]:
        if v and v.strip():
            try:
                datetime.fromisoformat(v.replace("Z", "+00:00"))
            except Exception:
                raise ValueError("O campo slaVencimento deve estar em formato ISO válido (ex: 2026-03-30T18:00:00Z).")
            return v.strip()
        return None

    @field_validator("solicitante", "categoria")
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v

    @model_validator(mode="after")
    def validate_titulo(self):
        nome_titulo = (self.titulo or self.title or "").strip()
        if not nome_titulo:
            # Se não fornecido nem titulo nem title válido com texto real
            self.titulo = "Novo Chamado"
            self.title = "Novo Chamado"
        else:
            self.titulo = nome_titulo
            self.title = nome_titulo

        if self.description:
            self.description = self.description.strip()
        return self


class TicketUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=2, max_length=150)
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=5000)
    solicitante: Optional[str] = Field(None, min_length=2, max_length=100)
    categoria: Optional[str] = Field(None, min_length=2, max_length=50)
    prioridade: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    slaVencimento: Optional[str] = None

    @field_validator("slaVencimento")
    @classmethod
    def validate_sla_update(cls, v: Optional[str]) -> Optional[str]:
        if v and v.strip():
            try:
                datetime.fromisoformat(v.replace("Z", "+00:00"))
            except Exception:
                raise ValueError("O campo slaVencimento deve estar em formato ISO válido.")
            return v.strip()
        return None

    @field_validator("titulo", "title", "description", "solicitante", "categoria")
    @classmethod
    def sanitize_optional_text(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v is not None else None


class TicketResponse(BaseModel):
    id: int
    titulo: str
    solicitante: str
    categoria: str
    prioridade: str
    status: str
    slaVencimento: Optional[str] = None
    criadoEm: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


# --- Mensagens Schemas ---
class MessageCreate(BaseModel):
    texto: str = Field(..., min_length=1, max_length=3000, description="Conteúdo da mensagem")
    autor: Optional[str] = Field("Suporte TI", min_length=2, max_length=100)
    papel: Optional[MessageRole] = MessageRole.atendente

    @field_validator("texto")
    @classmethod
    def validate_texto(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("O texto da mensagem não pode ser vazio ou conter apenas espaços.")
        return cleaned

    @field_validator("autor")
    @classmethod
    def sanitize_autor(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else "Suporte TI"


class MessageResponse(BaseModel):
    id: int
    ticketId: int
    autor: str
    papel: str
    texto: str
    enviadoEm: str

    class Config:
        from_attributes = True


# --- Sugestao IA Schemas ---
class AiSuggestionResponse(BaseModel):
    id: int
    ticketId: int
    categoria: str
    prioridade: str
    confianca: float
    status: str

    class Config:
        from_attributes = True


class AiSuggestionActionResponse(BaseModel):
    sucesso: bool
    mensagem: str
    ticket: Optional[TicketResponse] = None