from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Help Desk API")

# Permite que o frontend (React) consiga fazer requisições para a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, substitua por "http://localhost:5173"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API do Help Desk rodando com FastAPI!"}