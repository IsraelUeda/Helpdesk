import { Link, useParams } from 'react-router-dom'
import AiSuggestionBanner from '../components/ai/AiSuggestionBanner'
import ChatPanel from '../components/chat/ChatPanel'
import PriorityBadge from '../components/tickets/PriorityBadge'
import SlaBadge from '../components/tickets/SlaBadge'
import { aiSuggestions, messagesByTicket } from '../mocks/messages'
import { getTicketById } from '../mocks/tickets'

export default function TicketDetailPage() {
  const { id } = useParams()
  const ticket = getTicketById(id)

  if (!ticket) {
    return (
      <div className="space-y-4">
        <p className="text-slate-600">Chamado não encontrado.</p>
        <Link to="/tickets" className="text-sm text-blue-600 hover:underline">
          Voltar para chamados
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/tickets" className="text-sm text-blue-600 hover:underline">
          ← Voltar para chamados
        </Link>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">{ticket.titulo}</h1>
            <p className="text-sm text-slate-500">
              #{ticket.id} · {ticket.solicitante} · {ticket.categoria}
            </p>
          </div>
          <div className="flex gap-2">
            <PriorityBadge prioridade={ticket.prioridade} />
            <SlaBadge slaVencimento={ticket.slaVencimento} status={ticket.status} />
          </div>
        </div>
      </div>

      <AiSuggestionBanner sugestao={aiSuggestions[ticket.id]} />

      <ChatPanel mensagensIniciais={messagesByTicket[ticket.id] ?? []} />
    </div>
  )
}
