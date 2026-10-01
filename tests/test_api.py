import uuid
import pytest
from fastapi.testclient import TestClient
import main, rate_limiter

client = TestClient(main.app)

@pytest.fixture(scope="module")
def auth_token():
    # Cadastra o usuário de teste caso não exista e faz login
    client.post(
        "/auth/register",
        json={
            "email": "tester@example.com",
            "name": "Tester User",
            "password": "senhaSegura123",
            "role": "atendente",
        },
    )
    resp = client.post(
        "/auth/login",
        json={"email": "tester@example.com", "password": "senhaSegura123"},
    )
    assert resp.status_code == 200, f"Login falhou: {resp.text}"
    return resp.json()["access_token"]

@pytest.fixture(scope="function")
def auth_header(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "mensagem" in resp.json()

def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"

def test_login_invalid_email():
    resp = client.post(
        "/auth/login",
        json={"email": "invalid-email", "password": "123456"},
    )
    assert resp.status_code == 422

def test_login_invalid_password():
    resp = client.post(
        "/auth/login",
        json={"email": "valid@example.com", "password": "123"},
    )
    assert resp.status_code == 422

def test_login_unregistered_user_fails():
    resp = client.post(
        "/auth/login",
        json={"email": "naoexiste@example.com", "password": "senhaSegura123"},
    )
    assert resp.status_code == 401

def test_register_user_success():
    email = f"novo_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/auth/register",
        json={
            "email": email,
            "name": "Novo Usuario",
            "password": "senhaSegura123",
            "role": "cliente",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == email
    assert data["name"] == "Novo Usuario"
    assert data["role"] == "cliente"

def test_register_duplicate_email():
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    resp1 = client.post(
        "/auth/register",
        json={
            "email": email,
            "name": "Primeiro",
            "password": "senhaSegura123",
        },
    )
    assert resp1.status_code == 201

    resp2 = client.post(
        "/auth/register",
        json={
            "email": email,
            "name": "Duplicado",
            "password": "senhaSegura123",
        },
    )
    assert resp2.status_code == 400
    assert "E-mail já cadastrado" in resp2.json()["detail"]

def test_unauthenticated_tickets_forbidden():
    resp = client.get("/tickets")
    assert resp.status_code == 401

def test_unauthenticated_metrics_forbidden():
    resp = client.get("/metricas/resumo")
    assert resp.status_code == 401

def test_list_tickets_limit(auth_header):
    resp = client.get("/tickets?limit=25", headers=auth_header)
    assert resp.status_code == 200
    assert len(resp.json()) <= 25

def test_create_ticket_success(auth_header):
    resp = client.post(
        "/tickets",
        json={"titulo": "Teste de criação", "prioridade": "media"},
        headers=auth_header,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["titulo"] == "Teste de criação"
    assert data["prioridade"] == "media"

def test_create_ticket_invalid_sla(auth_header):
    resp = client.post(
        "/tickets",
        json={"titulo": "Teste SLA", "slaVencimento": "data-errada"},
        headers=auth_header,
    )
    assert resp.status_code == 422

def test_create_ticket_invalid_status(auth_header):
    resp = client.post(
        "/tickets",
        json={"titulo": "Teste status", "status": "inexistente"},
        headers=auth_header,
    )
    assert resp.status_code == 422

def test_message_empty_text(auth_header):
    ticket_resp = client.post(
        "/tickets",
        json={"titulo": "Ticket para mensagem"},
        headers=auth_header,
    )
    ticket_id = ticket_resp.json()["id"]
    resp = client.post(
        f"/tickets/{ticket_id}/mensagens",
        json={"texto": "   "},
        headers=auth_header,
    )
    assert resp.status_code == 422

def test_metrics_invalid_dias(auth_header):
    resp = client.get("/metricas/tickets-por-dia?dias=-1", headers=auth_header)
    assert resp.status_code == 422
    resp = client.get("/metricas/tickets-por-dia?dias=100", headers=auth_header)
    assert resp.status_code == 422

def test_rate_limiting(auth_header):
    # Reset internal state for a clean test
    rate_limiter.ticket_creation_limiter.requests.clear()
    successes = 0
    blocked = 0
    for i in range(27):
        r = client.post(
            "/tickets",
            json={"titulo": f"Ticket {i}"},
            headers=auth_header,
        )
        if r.status_code == 201:
            successes += 1
        elif r.status_code == 429:
            blocked += 1
    assert successes == 25, f"Deve permitir exatamente 25 criações, permitiu {successes}"
    assert blocked == 2, f"Deve bloquear 2 criações, bloqueou {blocked}"
