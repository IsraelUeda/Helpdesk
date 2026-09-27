import { Link } from 'react-router-dom'
import PriorityBadge from './PriorityBadge'
import SlaBadge from './SlaBadge'

const STATUS_LABELS = {
  aberto: 'Aberto',
  em_andamento: 'Em andamento',
  fechado: 'Fechado',
}

export default function TicketCard({ ticket }) {
  return (
    <Link
      to={`/tickets/${ticket.id}`}
      className="block rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition hover:border-slate-300 hover:shadow"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-medium text-slate-900">{ticket.titulo}</p>
          <p className="mt-1 text-sm text-slate-500">
            #{ticket.id} · {ticket.solicitante} · {ticket.categoria}
          </p>
        </div>
        <span className="whitespace-nowrap text-xs font-medium text-slate-500">
          {STATUS_LABELS[ticket.status]}
        </span>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <PriorityBadge prioridade={ticket.prioridade} />
        <SlaBadge slaVencimento={ticket.slaVencimento} status={ticket.status} />
      </div>
    </Link>
  )
}
