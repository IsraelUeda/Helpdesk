from fastapi import FastAPI

app = FastAPI(title="Help Desk API")

@app.get("/")
def read_root():
    return {"mensagem": "O FastAPI subiu com sucesso!"}