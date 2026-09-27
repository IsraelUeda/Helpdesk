import { useState } from 'react'
import ChatBubble from './ChatBubble'

export default function ChatPanel({ mensagensIniciais }) {
  const [mensagens, setMensagens] = useState(mensagensIniciais)
  const [texto, setTexto] = useState('')

  function enviar(e) {
    e.preventDefault()
    if (!texto.trim()) return

    setMensagens((atual) => [
      ...atual,
      {
        id: atual.length + 1,
        autor: 'Suporte TI',
        papel: 'atendente',
        texto: texto.trim(),
        enviadoEm: new Date().toISOString(),
      },
    ])
    setTexto('')
  }

  return (
    <div className="flex h-[420px] flex-col rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-3">
        <p className="text-sm font-medium text-slate-700">Conversa com o solicitante</p>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
        {mensagens.map((mensagem) => (
          <ChatBubble key={mensagem.id} mensagem={mensagem} />
        ))}
      </div>
      <form onSubmit={enviar} className="flex gap-2 border-t border-slate-100 p-3">
        <input
          type="text"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Digite uma mensagem..."
          className="flex-1 rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
        />
        <button
          type="submit"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Enviar
        </button>
      </form>
    </div>
  )
}
