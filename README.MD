# HelpDesk API

## Visão geral

O **HelpDesk** é uma aplicação de gerenciamento de chamados (tickets) construída com **FastAPI** (backend) e **React** (frontend). Ela oferece:
- Autenticação via JWT.
- CRUD completo de tickets.
- Mensagens de chat nos tickets.
- Sugestões de IA para categoria/prioridade.
- Métricas de desempenho (tickets abertos, SLA, tickets por dia).
- **Rate limiting**: máximo de **25 tickets criados por minuto** por IP/usuário.
- Validações rigorosas usando **Pydantic** (enum, email‑validator, limites de tamanho, datas ISO).
- Docker‑compose com PostgreSQL (fallback SQLite para desenvolvimento).

A aplicação segue boas práticas de API (OpenAPI/Swagger, tratamento de erros, documentação) e está pronta para ser estendida.

---

##  Principais funcionalidades
- **Login** (`/auth/login`) com validação de e‑mail e senha (mínimo 6 caracteres).
- **Listagem de tickets** com paginação (`limit`/`offset`) – limit padrão 25.
- **Criação de tickets** com checagem de taxa (25/min).
- **Atualização** de status, prioridade, descrição etc.
- **Mensagens** dentro do ticket (validação de texto não vazio).
- **Sugestão de IA** – gera/salva/aceita/ignora sugestões.
- **Métricas**:
  - Resumo (`/metricas/resumo`).
  - Tickets por dia (`/metricas/tickets-por-dia?dias=N`).
- **Health‑check** (`/health`) e **Swagger UI** (`/docs`).

---

##  Arquitetura
```
HelpDesk (Docker Compose)
├─ db (PostgreSQL)            <-- dados persistentes
└─ api (FastAPI)              <-- backend
    ├─ routers/               # endpoints (auth, tickets, métricas)
    ├─ models.py              # SQLAlchemy models
    ├─ schemas.py             # Pydantic schemas + Enums
    ├─ security.py            # hashing, JWT
    ├─ rate_limiter.py        # sliding‑window limiter (25/min)
    └─ main.py                # FastAPI app, CORS, lifespan
```

---

##  Começando (quick start)
### Pré‑requisitos
- Docker & Docker‑Compose
- Python 3.13 (para desenvolvimento local)

### 1. Clone o repositório
```bash
git clone https://github.com/IsraelUeda/Helpdesk.git
cd Helpdesk
```

### 2. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz (ou copie o exemplo abaixo):
```dotenv
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=helpdesk_db
DB_HOST=db          # não mudar quando usar Docker
SECRET_KEY=helpdesk-secret-key-super-safe-2026
```

### 3. Suba os containers
```bash
docker compose up -d   # sobe db e api
```
A API ficará disponível em `http://localhost:8000`.

### 4. Teste a aplicação
```bash
# Verificar health‑check
curl -s http://localhost:8000/health

# Ver Swagger UI
open http://localhost:8000/docs
```

---

## Endpoints principais
| Método | Rota | Descrição | Auth? |
|--------|------|-----------|-------|
| `GET`  | `/health` | Health‑check e status da conexão com o banco. | Não |
| `POST` | `/auth/register` | Cadastro de novo usuário (`email`, `name`, `password`, `role`). | Não |
| `POST` | `/auth/login` | Login – recebe `email` e `password`. | Não |
| `GET`  | `/auth/me` | Dados do usuário autenticado. | Sim |
| `GET`  | `/tickets` | Lista tickets (paginação). | Sim |
| `POST` | `/tickets` | Cria ticket (rate‑limited). | Sim |
| `GET`  | `/tickets/{id}` | Detalha ticket. | Sim |
| `PUT`  | `/tickets/{id}` | Atualiza ticket (JSON body ou query `status`). | Sim |
| `GET`  | `/tickets/{id}/mensagens` | Mensagens do ticket. | Sim |
| `POST` | `/tickets/{id}/mensagens` | Envia mensagem. | Sim |
| `GET`  | `/tickets/{id}/sugestao-ia` | Obtém sugestão IA. | Sim |
| `POST` | `/tickets/{id}/sugestao-ia/aceitar` | Aplica sugestão. | Sim |
| `POST` | `/tickets/{id}/sugestao-ia/ignorar` | Ignora sugestão. | Sim |
| `GET`  | `/metricas/resumo` | Resumo de tickets e SLA. | Sim |
| `GET`  | `/metricas/tickets-por-dia?dias=N` | Série histórica (1‑90 dias). | Sim |

---

##  Testes automatizados
Um conjunto de testes com **pytest** está em `tests/`. Para rodar:
```bash
pip install -r backend/requirements.txt -r dev-requirements.txt
pytest -v
```
Os testes cobrem:
- Validação de login.
- Criação/listagem de tickets.
- Rate limiting (25 tickets/min).
- Validação de campos (`slaVencimento`, `status`, `prioridade`).
- Mensagens vazias e métricas.

---

##  Deploy e produção
1. **Docker multi‑stage** – já configurado em `backend/Dockerfile` (Gunicorn + Uvicorn workers).
2. **Variáveis secretas** – nunca armazenar `SECRET_KEY` no repo; use secrets do Docker/Kubernetes.
3. **HTTPS** – colocar um reverse‑proxy (NGINX) com TLS na frente ou usar o Docker‑compose com `traefik`.
4. **Monitoramento** – o endpoint `/health` pode ser consumido por Prometheus/Alertmanager.
5. **Escalabilidade** – aumente `workers` no Gunicorn ou ajuste `replicas` no orquestrador.

---

##  Contribuindo
1. Fork o repositório.
2. Crie uma branch para sua feature: `git checkout -b feature/minha-feature`.
3. Abra um Pull Request descrevendo a mudança.
4. Certifique‑se que os testes passam (`pytest`).

---

## Licença
Este projeto está licenciado sob a **MIT License** – sinta‑se livre para usar, modificar e distribuir.
