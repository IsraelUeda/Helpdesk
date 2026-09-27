from pydantic import BaseModel

class TicketCreate(BaseModel):
    title: str
    description: str

class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str

    class Config:
        from_attributes = True # Permite ler dados do SQLAlchemy