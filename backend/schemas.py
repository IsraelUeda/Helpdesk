from typing import Optional
from pydantic import BaseModel

# --- Auth Schemas ---
class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str = "atendente"

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# --- Metricas Schemas ---
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
    titulo: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    solicitante: Optional[str] = "Usuário"
    categoria: Optional[str] = "Geral"
    prioridade: Optional[str] = "media"
    status: Optional[str] = "aberto"
    slaVencimento: Optional[str] = None

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
    texto: str
    autor: Optional[str] = "Suporte TI"
    papel: Optional[str] = "atendente"

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