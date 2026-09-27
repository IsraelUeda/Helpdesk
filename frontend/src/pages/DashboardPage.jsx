import StatCard from '../components/dashboard/StatCard'
import TicketsChart from '../components/dashboard/TicketsChart'
import { summary, ticketsPorDia } from '../mocks/metrics'

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-500">Visão geral do atendimento</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Tickets abertos" value={summary.ticketsAbertos} />
        <StatCard label="Tempo médio de resposta" value={summary.tempoMedioResposta} />
        <StatCard
          label="SLA cumprido"
          value={`${summary.slaCumprido}%`}
          hint="Últimos 7 dias"
        />
      </div>

      <TicketsChart data={ticketsPorDia} />
    </div>
  )
}
