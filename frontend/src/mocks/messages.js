export const messagesByTicket = {
  1: [
    { id: 1, autor: 'Marina Alves', papel: 'cliente', texto: 'A impressora do 2º andar está com uma luz vermelha piscando e não imprime nada.', enviadoEm: '2026-09-27T09:12:00' },
    { id: 2, autor: 'Suporte TI', papel: 'atendente', texto: 'Bom dia! Já é possível verificar se há papel encravado dentro da bandeja?', enviadoEm: '2026-09-27T09:20:00' },
  ],
  2: [
    { id: 1, autor: 'Carlos Nunes', papel: 'cliente', texto: 'O sistema de vendas caiu para todo o time, ninguém consegue emitir pedido.', enviadoEm: '2026-09-27T08:40:00' },
    { id: 2, autor: 'Suporte TI', papel: 'atendente', texto: 'Estamos verificando com a equipe de infraestrutura, retorno em instantes.', enviadoEm: '2026-09-27T08:45:00' },
    { id: 3, autor: 'Carlos Nunes', papel: 'cliente', texto: 'Ok, é urgente pois estamos perdendo vendas agora.', enviadoEm: '2026-09-27T08:47:00' },
  ],
  3: [
    { id: 1, autor: 'Juliana Prado', papel: 'cliente', texto: 'Preciso de acesso à VPN para trabalhar remotamente na sexta.', enviadoEm: '2026-09-26T14:05:00' },
  ],
  4: [
    { id: 1, autor: 'Roberto Lima', papel: 'cliente', texto: 'Meu notebook não conecta no Wi-Fi corporativo desde ontem.', enviadoEm: '2026-09-27T07:55:00' },
    { id: 2, autor: 'Suporte TI', papel: 'atendente', texto: 'Pode tentar esquecer a rede e reconectar informando a senha novamente?', enviadoEm: '2026-09-27T08:02:00' },
  ],
  5: [
    { id: 1, autor: 'Fernanda Costa', papel: 'cliente', texto: 'Meu e-mail está retornando erro de autenticação ao tentar logar.', enviadoEm: '2026-09-25T10:20:00' },
    { id: 2, autor: 'Suporte TI', papel: 'atendente', texto: 'Redefinimos sua senha, o problema foi resolvido. Fechando o chamado.', enviadoEm: '2026-09-25T11:00:00' },
  ],
}

export const aiSuggestions = {
  1: { categoria: 'Hardware', prioridade: 'media', confianca: 0.82 },
  2: { categoria: 'Sistemas', prioridade: 'urgente', confianca: 0.95 },
  3: { categoria: 'Acessos', prioridade: 'baixa', confianca: 0.7 },
  4: { categoria: 'Rede', prioridade: 'alta', confianca: 0.88 },
  5: { categoria: 'Sistemas', prioridade: 'media', confianca: 0.6 },
}
