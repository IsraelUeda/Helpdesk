import { useState } from 'react'
import PriorityBadge from '../tickets/PriorityBadge'

export default function AiSuggestionBanner({ sugestao }) {
  const [status, setStatus] = useState('pendente')

  if (!sugestao || status !== 'pendente') {
    return status === 'pendente' ? null : (
      <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
        {status === 'aceito'
          ? 'Sugestão da IA aplicada a este chamado.'
          : 'Sugestão da IA ignorada.'}
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-violet-200 bg-violet-50 px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2 text-sm text-violet-900">
          <span className="font-medium">Sugestão da IA:</span>
          <span>categoria {sugestao.categoria}</span>
          <PriorityBadge prioridade={sugestao.prioridade} />
          <span className="text-xs text-violet-500">
            ({Math.round(sugestao.confianca * 100)}% de confiança)
          </span>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setStatus('aceito')}
            className="rounded-md bg-violet-600 px-3 py-1 text-xs font-medium text-white hover:bg-violet-700"
          >
            Aceitar
          </button>
          <button
            type="button"
            onClick={() => setStatus('ignorado')}
            className="rounded-md border border-violet-300 px-3 py-1 text-xs font-medium text-violet-700 hover:bg-violet-100"
          >
            Ignorar
          </button>
        </div>
      </div>
    </div>
  )
}
