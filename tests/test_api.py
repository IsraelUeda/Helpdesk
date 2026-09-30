import pytest
from fastapi.testclient import TestClient
from backend import main, rate_limiter

client = TestClient(main.app)

@pytest.fixture(scope="module")
def auth_token():
    # Login with valid credentials (the login endpoint auto‑creates the user if needed)
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

def test_list_tickets_limit(auth_header):
    resp = client.get("/tickets?limit=25", headers=auth_header)
    assert resp.status_code == 200
    # Pode retornar menos, mas nunca mais que 25
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
    # Primeiro cria um ticket válido
    ticket_resp = client.post(
        "/tickets",
        json={"titulo": "Ticket para mensagem"},
        headers=auth_header,
    )
    ticket_id = ticket_resp.json()["id"]
    # Tenta enviar mensagem vazia
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

# Optional health endpoint test (if you add one later)
# def test_health_check():
#     resp = client.get("/health")
#     assert resp.status_code == 200
