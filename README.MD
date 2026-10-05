# HelpDesk API

## Visão geral

O **HelpDesk** é uma aplicação completa de gerenciamento de chamados (tickets) construída com **FastAPI** (backend) e **React** (frontend). Ela oferece:
- **Autenticação e RBAC**: Controle de acesso baseado em papéis (`cliente`, `atendente` e `admin`) via JWT.
- **Isolamento de Chamados**: Clientes acessam apenas seus próprios chamados; atendentes e administradores gerenciam a fila global.
- **Ciclo de Vida do Chamado**: Atribuição de técnicos, encerramento com carimbo de data/hora, reabertura controlada e bloqueio de mensagens em chamados fechados.
- **SLA Inteligente**: Cálculo automático de prazo de SLA com base na prioridade caso não informado.
- **Linha do Tempo e Auditoria**: Rastreamento completo de eventos e alterações nos chamados (`TicketHistory`).
- **Mensagens e Chat**: Troca de mensagens vinculadas ao chamado com avanço automático para "em andamento" na primeira resposta do suporte.
- **Sugestões de IA**: Classificação e sugestão de categorias/prioridades (com fluxo de aceitar/ignorar).
- **Métricas de Desempenho**: Resumo de tickets abertos, SLA cumprido e série histórica diária.
- **Rate Limiting**: Limite deslizante de até **25 tickets criados por minuto** por IP/usuário.
- **Validações Rigorosas**: Validações de esquema com **Pydantic** e compatibilidade com SQLAlchemy 2.0.
- **Docker Compose**: Ambiente pré-configurado com PostgreSQL e fallback automático para SQLite em desenvolvimento.

---

## 👥 Papéis e Permissões (RBAC)

| Papel | Permissões |
|---|---|
| **`cliente`** | Cria chamados, visualiza e envia mensagens **apenas** nos seus próprios chamados. Pode fechar seus chamados, mas **não** pode alterar prioridade, prazos de SLA nem reabrir chamados encerrados. |
| **`atendente`** | Acesso a todos os chamados, pode alterar status e prioridades, assumir chamados para si (`/assumir`), atribuir a outros técnicos (`/atribuir`), aplicar/ignorar sugestões de IA e consultar histórico de auditoria. |
| **`admin`** | Acesso irrestrito a todas as operações de chamados e métricas, além de permissão exclusiva para gerenciar papéis de usuários (`PUT /auth/users/{id}/role`). |

---

## ⏱️ Regras de SLA Automático

Quando um chamado é criado sem um prazo `slaVencimento` explícito, o sistema calcula automaticamente a data limite com base na prioridade:

- **Urgente**: 4 horas a partir da criação.
- **Alta**: 12 horas a partir da criação.
- **Média**: 24 horas a partir da criação.
- **Baixa**: 48 horas a partir da criação.

---

## 🏛️ Arquitetura

```
HelpDesk (Docker Compose)
├─ db (PostgreSQL)            <-- banco de dados relacional
└─ api (FastAPI)              <-- backend
    ├─ routers/
    │   ├─ auth.py            # autenticação, usuários e controle de papéis
    │   ├─ tickets.py         # CRUD, auditoria, atribuição, chat e IA
    │   └─ metrics.py         # métricas e SLA
    ├─ models.py              # entidades SQLAlchemy (User, Ticket, Message, TicketHistory, AiSuggestion)
    ├─ schemas.py             # esquemas Pydantic v2
    ├─ security.py            # criptografia, tokens JWT e dependências RBAC
    ├─ rate_limiter.py        # sliding-window limiter (25 tickets/min)
    ├─ seed.py                # carga inicial de demonstração
    └─ main.py                # inicialização FastAPI, CORS, migrações dinâmicas
```

---

## 🚀 Começando (Quick Start)

### Pré-requisitos
- Docker & Docker Compose
- Python 3.13 (para desenvolvimento local)

### 1. Clone o repositório
```bash
git clone https://github.com/IsraelUeda/Helpdesk.git
cd Helpdesk
```

### 2. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz:
```dotenv
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=helpdesk_db
DB_HOST=db          # não alterar se estiver usando Docker
SECRET_KEY=helpdesk-secret-key-super-safe-2026
```

### 3. Suba os containers
```bash
docker compose up -d   # sobe db e api
```
A API ficará disponível em `http://localhost:8000`.

### 4. Teste a aplicação
```bash
# Verificar health-check
curl -s http://localhost:8000/health

# Ver Swagger UI interativo
open http://localhost:8000/docs
```

---

## 📌 Endpoints da API

### Autenticação e Usuários
| Método | Rota | Descrição | Auth? | Perfil Mínimo |
|---|---|---|---|---|
| `POST` | `/auth/register` | Cadastro de novo usuário (`email`, `name`, `password`, `role`). | Não | Público |
| `POST` | `/auth/login` | Login – retorna token JWT de acesso. | Não | Público |
| `GET`  | `/auth/me` | Dados do usuário autenticado. | Sim | Qualquer |
| `GET`  | `/auth/users` | Lista usuários (filtro opcional por `?role=`). | Sim | `atendente` / `admin` |
| `PUT`  | `/auth/users/{id}/role` | Altera o papel de um usuário. | Sim | `admin` |

### Chamados (Tickets)
| Método | Rota | Descrição | Auth? | Perfil Mínimo |
|---|---|---|---|---|
| `GET`  | `/tickets` | Lista tickets (filtro por `status`, `prioridade`, `assigned_to_id` e paginação). | Sim | Qualquer (clientes veem apenas os seus) |
| `POST` | `/tickets` | Cria chamado com SLA automático e rate-limiting (25/min). | Sim | Qualquer |
| `GET`  | `/tickets/{id}` | Detalhes do chamado. | Sim | Proprietário / Atendente |
| `PUT`  | `/tickets/{id}` | Atualiza status, dados ou prioridade. | Sim | Proprietário (limitado) / Atendente |
| `POST` | `/tickets/{id}/assumir` | Atendente/Admin assume o chamado para si. | Sim | `atendente` / `admin` |
| `POST` | `/tickets/{id}/atribuir` | Atribui chamado a um atendente específico. | Sim | `atendente` / `admin` |
| `GET`  | `/tickets/{id}/historico` | Linha do tempo e histórico de auditoria do chamado. | Sim | Proprietário / Atendente |
| `GET`  | `/tickets/{id}/mensagens` | Lista mensagens do chat do chamado. | Sim | Proprietário / Atendente |
| `POST` | `/tickets/{id}/mensagens` | Envia mensagem (avança ticket para 'em_andamento'). | Sim | Proprietário / Atendente |
| `GET`  | `/tickets/{id}/sugestao-ia` | Obtém sugestão de categoria e prioridade por IA. | Sim | Proprietário / Atendente |
| `POST` | `/tickets/{id}/sugestao-ia/aceitar` | Aplica sugestão da IA no chamado. | Sim | `atendente` / `admin` |
| `POST` | `/tickets/{id}/sugestao-ia/ignorar` | Ignora sugestão da IA. | Sim | `atendente` / `admin` |

### Métricas e Sistema
| Método | Rota | Descrição | Auth? | Perfil Mínimo |
|---|---|---|---|---|
| `GET`  | `/metricas/resumo` | Total de tickets abertos, tempo médio e SLA cumprido. | Sim | Qualquer autenticado |
| `GET`  | `/metricas/tickets-por-dia` | Histórico diário de chamados abertos/fechados (`?dias=N`). | Sim | Qualquer autenticado |
| `GET`  | `/health` | Health-check da API e conexão com banco de dados. | Não | Público |

---

## 🧪 Testes Automatizados

A suíte de testes com **pytest** cobre 100% dos fluxos críticos de negócio e segurança. Para executar:

```bash
python -m pytest -v
```

### O que é testado (24 testes):
- Autenticação, login inválido, emails duplicados e token JWT.
- Isolamento RBAC de clientes (chamados inacessíveis para outros clientes).
- Restrições de clientes (proibição de alterar prioridade ou SLA).
- Cálculo automático de SLA com base na prioridade do chamado.
- Atribuição manual (`/atribuir`) e assunção direta de chamados (`/assumir`).
- Auditoria e linha do tempo (`/historico`) com registro de criação, status e reabertura.
- Avanço automático de status para `em_andamento` após primeira resposta de suporte.
- Bloqueio de envio de mensagens em chamados fechados.
- Gerenciamento de usuários e restrição de promoção de papéis apenas para `admin`.
- Rate limiting com janela deslizante de 25 tickets/minuto.
- Métricas e validações de parâmetros.

---

## 📄 Licença
Este projeto está sob a licença **MIT** – sinta-se livre para usar, modificar e distribuir.
