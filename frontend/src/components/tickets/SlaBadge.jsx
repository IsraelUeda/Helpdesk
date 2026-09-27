function formatRemaining(ms) {
  const abs = Math.abs(ms)
  const minutes = Math.round(abs / 60000)
  if (minutes < 60) return `${minutes} min`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h`
  return `${Math.round(hours / 24)}d`
}

export default function SlaBadge({ slaVencimento, status }) {
  if (status === 'fechado') {
    return (
      <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-500">
        Encerrado
      </span>
    )
  }

  const diff = new Date(slaVencimento).getTime() - Date.now()
  const atrasado = diff < 0

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
        atrasado ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'
      }`}
    >
      {atrasado ? `Atrasado há ${formatRemaining(diff)}` : `${formatRemaining(diff)} para o SLA`}
    </span>
  )
}
