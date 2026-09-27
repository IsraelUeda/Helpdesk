export default function ChatBubble({ mensagem }) {
  const isAtendente = mensagem.papel === 'atendente'

  return (
    <div className={`flex ${isAtendente ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[75%] rounded-lg px-3 py-2 text-sm ${
          isAtendente ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-800'
        }`}
      >
        <p className="mb-1 text-xs font-medium opacity-70">{mensagem.autor}</p>
        <p>{mensagem.texto}</p>
        <p className="mt-1 text-right text-[10px] opacity-60">
          {new Date(mensagem.enviadoEm).toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  )
}
