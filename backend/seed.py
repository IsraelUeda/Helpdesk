from datetime import datetime
from sqlalchemy.orm import Session
import models
from security import hash_password

def seed_demo_data(db: Session):
    # 1. Usuário padrão
    existing_user = db.query(models.User).filter(models.User.email == "admin@empresa.com").first()
    if not existing_user:
        user = models.User(
            email="admin@empresa.com",
            name="Suporte TI",
            hashed_password=hash_password("123456"),
            role="atendente",
        )
        db.add(user)
        db.flush()

    # 2. Tickets de demonstração
    demo_tickets = [
        {
            "id": 1,
            "titulo": "Impressora do 2º andar não imprime",
            "solicitante": "Marina Alves",
            "categoria": "Hardware",
            "prioridade": "media",
            "status": "aberto",
            "sla_vencimento": datetime.fromisoformat("2026-09-27T18:00:00"),
            "criado_em": datetime.fromisoformat("2026-09-27T09:12:00"),
            "title": "Impressora do 2º andar não imprime",
            "description": "A impressora do 2º andar está com uma luz vermelha piscando e não imprime nada.",
        },
        {
            "id": 2,
            "titulo": "Sistema de vendas fora do ar",
            "solicitante": "Carlos Nunes",
            "categoria": "Sistemas",
            "prioridade": "urgente",
            "status": "em_andamento",
            "sla_vencimento": datetime.fromisoformat("2026-09-27T11:00:00"),
            "criado_em": datetime.fromisoformat("2026-09-27T08:40:00"),
            "title": "Sistema de vendas fora do ar",
            "description": "O sistema de vendas caiu para todo o time, ninguém consegue emitir pedido.",
        },
        {
            "id": 3,
            "titulo": "Solicitação de acesso à VPN",
            "solicitante": "Juliana Prado",
            "categoria": "Acessos",
            "prioridade": "baixa",
            "status": "aberto",
            "sla_vencimento": datetime.fromisoformat("2026-09-29T18:00:00"),
            "criado_em": datetime.fromisoformat("2026-09-26T14:05:00"),
            "title": "Solicitação de acesso à VPN",
            "description": "Preciso de acesso à VPN para trabalhar remotamente na sexta.",
        },
        {
            "id": 4,
            "titulo": "Notebook não conecta ao Wi-Fi corporativo",
            "solicitante": "Roberto Lima",
            "categoria": "Rede",
            "prioridade": "alta",
            "status": "em_andamento",
            "sla_vencimento": datetime.fromisoformat("2026-09-27T13:30:00"),
            "criado_em": datetime.fromisoformat("2026-09-27T07:55:00"),
            "title": "Notebook não conecta ao Wi-Fi corporativo",
            "description": "Meu notebook não conecta no Wi-Fi corporativo desde ontem.",
        },
        {
            "id": 5,
            "titulo": "E-mail retornando erro de autenticação",
            "solicitante": "Fernanda Costa",
            "categoria": "Sistemas",
            "prioridade": "media",
            "status": "fechado",
            "sla_vencimento": datetime.fromisoformat("2026-09-26T18:00:00"),
            "criado_em": datetime.fromisoformat("2026-09-25T10:20:00"),
            "title": "E-mail retornando erro de autenticação",
            "description": "Meu e-mail está retornando erro de autenticação ao tentar logar.",
        },
    ]

    for t_data in demo_tickets:
        existing_ticket = db.query(models.Ticket).filter(models.Ticket.id == t_data["id"]).first()
        if not existing_ticket:
            db.add(models.Ticket(**t_data))
        else:
            if not existing_ticket.titulo:
                existing_ticket.titulo = t_data["titulo"]
            if not existing_ticket.solicitante:
                existing_ticket.solicitante = t_data["solicitante"]
            if not existing_ticket.categoria:
                existing_ticket.categoria = t_data["categoria"]
            if not existing_ticket.prioridade:
                existing_ticket.prioridade = t_data["prioridade"]
            if not existing_ticket.status:
                existing_ticket.status = t_data["status"]
            if not existing_ticket.sla_vencimento:
                existing_ticket.sla_vencimento = t_data["sla_vencimento"]
            if not existing_ticket.criado_em:
                existing_ticket.criado_em = t_data["criado_em"]
    db.flush()

    # 3. Mensagens
    demo_messages = [
        # Ticket 1
        {"ticket_id": 1, "autor": "Marina Alves", "papel": "cliente", "texto": "A impressora do 2º andar está com uma luz vermelha piscando e não imprime nada.", "enviado_em": datetime.fromisoformat("2026-09-27T09:12:00")},
        {"ticket_id": 1, "autor": "Suporte TI", "papel": "atendente", "texto": "Bom dia! Já é possível verificar se há papel encravado dentro da bandeja?", "enviado_em": datetime.fromisoformat("2026-09-27T09:20:00")},
        # Ticket 2
        {"ticket_id": 2, "autor": "Carlos Nunes", "papel": "cliente", "texto": "O sistema de vendas caiu para todo o time, ninguém consegue emitir pedido.", "enviado_em": datetime.fromisoformat("2026-09-27T08:40:00")},
        {"ticket_id": 2, "autor": "Suporte TI", "papel": "atendente", "texto": "Estamos verificando com a equipe de infraestrutura, retorno em instantes.", "enviado_em": datetime.fromisoformat("2026-09-27T08:45:00")},
        {"ticket_id": 2, "autor": "Carlos Nunes", "papel": "cliente", "texto": "Ok, é urgente pois estamos perdendo vendas agora.", "enviado_em": datetime.fromisoformat("2026-09-27T08:47:00")},
        # Ticket 3
        {"ticket_id": 3, "autor": "Juliana Prado", "papel": "cliente", "texto": "Preciso de acesso à VPN para trabalhar remotamente na sexta.", "enviado_em": datetime.fromisoformat("2026-09-26T14:05:00")},
        # Ticket 4
        {"ticket_id": 4, "autor": "Roberto Lima", "papel": "cliente", "texto": "Meu notebook não conecta no Wi-Fi corporativo desde ontem.", "enviado_em": datetime.fromisoformat("2026-09-27T07:55:00")},
        {"ticket_id": 4, "autor": "Suporte TI", "papel": "atendente", "texto": "Pode tentar esquecer a rede e reconectar informando a senha novamente?", "enviado_em": datetime.fromisoformat("2026-09-27T08:02:00")},
        # Ticket 5
        {"ticket_id": 5, "autor": "Fernanda Costa", "papel": "cliente", "texto": "Meu e-mail está retornando erro de autenticação ao tentar logar.", "enviado_em": datetime.fromisoformat("2026-09-25T10:20:00")},
        {"ticket_id": 5, "autor": "Suporte TI", "papel": "atendente", "texto": "Redefinimos sua senha, o problema foi resolvido. Fechando o chamado.", "enviado_em": datetime.fromisoformat("2026-09-25T11:00:00")},
    ]

    for m_data in demo_messages:
        existing_msg = db.query(models.Message).filter(
            models.Message.ticket_id == m_data["ticket_id"],
            models.Message.texto == m_data["texto"],
        ).first()
        if not existing_msg:
            db.add(models.Message(**m_data))
    db.flush()

    # 4. Sugestões de IA
    demo_suggestions = [
        {"ticket_id": 1, "categoria": "Hardware", "prioridade": "media", "confianca": 0.82, "status": "pendente"},
        {"ticket_id": 2, "categoria": "Sistemas", "prioridade": "urgente", "confianca": 0.95, "status": "pendente"},
        {"ticket_id": 3, "categoria": "Acessos", "prioridade": "baixa", "confianca": 0.70, "status": "pendente"},
        {"ticket_id": 4, "categoria": "Rede", "prioridade": "alta", "confianca": 0.88, "status": "pendente"},
        {"ticket_id": 5, "categoria": "Sistemas", "prioridade": "media", "confianca": 0.60, "status": "pendente"},
    ]

    for s_data in demo_suggestions:
        existing_sug = db.query(models.AiSuggestion).filter(
            models.AiSuggestion.ticket_id == s_data["ticket_id"]
        ).first()
        if not existing_sug:
            db.add(models.AiSuggestion(**s_data))

    db.commit()
