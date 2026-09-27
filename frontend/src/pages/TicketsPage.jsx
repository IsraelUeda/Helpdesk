import { useMemo, useState } from 'react'
import TicketCard from '../components/tickets/TicketCard'
import { PRIORITIES, tickets } from '../mocks/tickets'

const STATUS_OPTIONS = [
  { value: 'todos', label: 'Todos os status' },
  { value: 'aberto', label: 'Aberto' },
  { value: 'em_andamento', label: 'Em andamento' },
  { value: 'fechado', label: 'Fechado' },
]

export default function TicketsPage() {
  const [status, setStatus] = useState('todos')
  const [prioridade, setPrioridade] = useState('todas')

  const filtrados = useMemo(() => {
    return tickets.filter((ticket) => {
      const statusOk = status === 'todos' || ticket.status === status
      const prioridadeOk = prioridade === 'todas' || ticket.prioridade === prioridade
      return statusOk && prioridadeOk
    })
  }, [status, prioridade])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Chamados</h1>
        <p className="text-sm text-slate-500">{filtrados.length} chamado(s) encontrado(s)</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <select
          value={prioridade}
          onChange={(e) => setPrioridade(e.target.value)}
          className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
        >
          <option value="todas">Todas as prioridades</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p[0].toUpperCase() + p.slice(1)}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-3">
        {filtrados.map((ticket) => (
          <TicketCard key={ticket.id} ticket={ticket} />
        ))}
        {filtrados.length === 0 && (
          <p className="text-sm text-slate-400">Nenhum chamado com esses filtros.</p>
        )}
      </div>
    </div>
  )
}
