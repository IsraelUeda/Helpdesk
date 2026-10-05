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

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    rate_limiter.ticket_creation_limiter.requests.clear()
    yield
    rate_limiter.ticket_creation_limiter.requests.clear()


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


def test_client_ticket_isolation_and_ownership():
    # Cria Cliente 1
    c1_email = f"client1_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/register", json={"email": c1_email, "name": "Cliente Um", "password": "senhaSegura123", "role": "cliente"})
    r1 = client.post("/auth/login", json={"email": c1_email, "password": "senhaSegura123"})
    c1_header = {"Authorization": f"Bearer {r1.json()['access_token']}"}

    # Cria Cliente 2
    c2_email = f"client2_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/register", json={"email": c2_email, "name": "Cliente Dois", "password": "senhaSegura123", "role": "cliente"})
    r2 = client.post("/auth/login", json={"email": c2_email, "password": "senhaSegura123"})
    c2_header = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    # Cliente 1 cria ticket
    t1_resp = client.post("/tickets", json={"titulo": "Chamado do Cliente 1"}, headers=c1_header)
    assert t1_resp.status_code == 201
    t1_id = t1_resp.json()["id"]

    # Cliente 2 cria ticket
    t2_resp = client.post("/tickets", json={"titulo": "Chamado do Cliente 2"}, headers=c2_header)
    assert t2_resp.status_code == 201
    t2_id = t2_resp.json()["id"]

    # Cliente 1 lista tickets -> deve ver t1_id e não deve ver t2_id
    c1_list = client.get("/tickets", headers=c1_header).json()
    c1_ids = [t["id"] for t in c1_list]
    assert t1_id in c1_ids
    assert t2_id not in c1_ids

    # Cliente 1 tenta acessar t2 diretamente -> 403 Forbidden
    forbidden_resp = client.get(f"/tickets/{t2_id}", headers=c1_header)
    assert forbidden_resp.status_code == 403

    # Cliente 1 acessa seu próprio ticket -> 200 OK
    ok_resp = client.get(f"/tickets/{t1_id}", headers=c1_header)
    assert ok_resp.status_code == 200


def test_client_cannot_change_priority():
    c_email = f"client_pri_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/register", json={"email": c_email, "name": "Cliente Prioridade", "password": "senhaSegura123", "role": "cliente"})
    r = client.post("/auth/login", json={"email": c_email, "password": "senhaSegura123"})
    c_header = {"Authorization": f"Bearer {r.json()['access_token']}"}

    ticket_resp = client.post("/tickets", json={"titulo": "Ticket Cliente Prioridade"}, headers=c_header)
    t_id = ticket_resp.json()["id"]

    # Tentativa de alterar prioridade pelo cliente -> 403
    update_resp = client.put(f"/tickets/{t_id}", json={"prioridade": "urgente"}, headers=c_header)
    assert update_resp.status_code == 403


def test_assign_technician_and_history(auth_header):
    # Cria atendente auxiliar
    tech_email = f"tech_{uuid.uuid4().hex[:8]}@example.com"
    r_tech = client.post("/auth/register", json={"email": tech_email, "name": "Tecnico Suporte", "password": "senhaSegura123", "role": "atendente"})
    tech_id = r_tech.json()["id"]

    ticket_resp = client.post("/tickets", json={"titulo": "Ticket para atribuir"}, headers=auth_header)
    t_id = ticket_resp.json()["id"]

    # Atribui o chamado ao técnico
    assign_resp = client.post(f"/tickets/{t_id}/atribuir", json={"assigned_to_id": tech_id}, headers=auth_header)
    assert assign_resp.status_code == 200
    assert assign_resp.json()["assignedToId"] == tech_id
    assert assign_resp.json()["tecnicoResponsavel"] == "Tecnico Suporte"

    # Consulta histórico
    hist_resp = client.get(f"/tickets/{t_id}/historico", headers=auth_header)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    acoes = [h["acao"] for h in history]
    assert "criacao" in acoes
    assert "atribuicao_responsavel" in acoes


def test_automatic_sla_by_priority(auth_header):
    # Cria chamado com prioridade urgente sem passar slaVencimento
    r_urgente = client.post(
        "/tickets",
        json={"titulo": "Chamado Urgente SLA", "prioridade": "urgente"},
        headers=auth_header,
    )
    assert r_urgente.status_code == 201
    sla_urgente = r_urgente.json()["slaVencimento"]
    assert sla_urgente is not None

    # Cria chamado com prioridade baixa sem passar slaVencimento
    r_baixa = client.post(
        "/tickets",
        json={"titulo": "Chamado Baixa SLA", "prioridade": "baixa"},
        headers=auth_header,
    )
    assert r_baixa.status_code == 201
    sla_baixa = r_baixa.json()["slaVencimento"]
    assert sla_baixa is not None
    # SLA de baixa deve vencer depois do urgente
    assert sla_baixa > sla_urgente


def test_technician_take_ticket(auth_header):
    ticket_resp = client.post("/tickets", json={"titulo": "Ticket para assumir", "status": "aberto"}, headers=auth_header)
    t_id = ticket_resp.json()["id"]

    # Atendente assume o chamado
    resp = client.post(f"/tickets/{t_id}/assumir", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "em_andamento"
    assert data["assignedToId"] is not None


def test_auto_transition_on_technician_reply(auth_header):
    # Cria ticket 'aberto'
    t_resp = client.post("/tickets", json={"titulo": "Ticket Aberto para Resposta", "status": "aberto"}, headers=auth_header)
    t_id = t_resp.json()["id"]

    # Atendente envia mensagem
    msg_resp = client.post(f"/tickets/{t_id}/mensagens", json={"texto": "Olá, estou analisando seu problema."}, headers=auth_header)
    assert msg_resp.status_code == 201

    # Ticket deve ter mudado automaticamente para 'em_andamento'
    check_resp = client.get(f"/tickets/{t_id}", headers=auth_header)
    assert check_resp.json()["status"] == "em_andamento"


def test_closed_ticket_rules_and_reopen(auth_header):
    t_resp = client.post("/tickets", json={"titulo": "Ticket para Fechar"}, headers=auth_header)
    t_id = t_resp.json()["id"]

    # Fecha o ticket
    close_resp = client.put(f"/tickets/{t_id}", json={"status": "fechado"}, headers=auth_header)
    assert close_resp.status_code == 200
    assert close_resp.json()["fechadoEm"] is not None

    # Tenta enviar mensagem em ticket fechado -> 400 Bad Request
    msg_resp = client.post(f"/tickets/{t_id}/mensagens", json={"texto": "Mensagem atrasada"}, headers=auth_header)
    assert msg_resp.status_code == 400
    assert "já fechado" in msg_resp.json()["detail"]

    # Atendente reabre o ticket
    reopen_resp = client.put(f"/tickets/{t_id}", json={"status": "em_andamento"}, headers=auth_header)
    assert reopen_resp.status_code == 200
    assert reopen_resp.json()["fechadoEm"] is None

    # Histórico deve registrar reabertura
    h_resp = client.get(f"/tickets/{t_id}/historico", headers=auth_header)
    acoes = [h["acao"] for h in h_resp.json()]
    assert "reabertura" in acoes


def test_user_management_and_admin_role_change(auth_header):
    # Atendente lista usuários
    u_list = client.get("/auth/users", headers=auth_header)
    assert u_list.status_code == 200
    assert len(u_list.json()) >= 1

    # Cria usuário comum
    user_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    r_user = client.post("/auth/register", json={"email": user_email, "name": "Usuario Teste", "password": "senhaSegura123", "role": "cliente"})
    user_id = r_user.json()["id"]

    # Cria admin
    admin_email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/register", json={"email": admin_email, "name": "Super Admin", "password": "senhaSegura123", "role": "admin"})
    l_admin = client.post("/auth/login", json={"email": admin_email, "password": "senhaSegura123"})
    admin_header = {"Authorization": f"Bearer {l_admin.json()['access_token']}"}

    # Atendente comum tenta alterar papel -> 403
    fail_role = client.put(f"/auth/users/{user_id}/role", json={"role": "atendente"}, headers=auth_header)
    assert fail_role.status_code == 403

    # Admin altera papel -> 200 OK
    ok_role = client.put(f"/auth/users/{user_id}/role", json={"role": "atendente"}, headers=admin_header)
    assert ok_role.status_code == 200
    assert ok_role.json()["role"] == "atendente"


