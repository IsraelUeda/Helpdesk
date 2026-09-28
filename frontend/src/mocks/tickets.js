export const PRIORITIES = ['baixa', 'media', 'alta', 'urgente']

export const tickets = [
  {
    id: 1,
    titulo: 'Impressora do 2º andar não imprime',
    solicitante: 'Marina Alves',
    categoria: 'Hardware',
    prioridade: 'media',
    status: 'aberto',
    slaVencimento: '2026-09-27T18:00:00',
    criadoEm: '2026-09-27T09:12:00',
  },
  {
    id: 2,
    titulo: 'Sistema de vendas fora do ar',
    solicitante: 'Carlos Nunes',
    categoria: 'Sistemas',
    prioridade: 'urgente',
    status: 'em_andamento',
    slaVencimento: '2026-09-27T11:00:00',
    criadoEm: '2026-09-27T08:40:00',
  },
  {
    id: 3,
    titulo: 'Solicitação de acesso à VPN',
    solicitante: 'Juliana Prado',
    categoria: 'Acessos',
    prioridade: 'baixa',
    status: 'aberto',
    slaVencimento: '2026-09-29T18:00:00',
    criadoEm: '2026-09-26T14:05:00',
  },
  {
    id: 4,
    titulo: 'Notebook não conecta ao Wi-Fi corporativo',
    solicitante: 'Roberto Lima',
    categoria: 'Rede',
    prioridade: 'alta',
    status: 'em_andamento',
    slaVencimento: '2026-09-27T13:30:00',
    criadoEm: '2026-09-27T07:55:00',
  },
  {
    id: 5,
    titulo: 'E-mail retornando erro de autenticação',
    solicitante: 'Fernanda Costa',
    categoria: 'Sistemas',
    prioridade: 'media',
    status: 'fechado',
    slaVencimento: '2026-09-26T18:00:00',
    criadoEm: '2026-09-25T10:20:00',
  },
]

export function getTicketById(id) {
  return tickets.find((t) => t.id === Number(id))
}
