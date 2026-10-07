# Revisão independente — mesa de fluxo

2026-10-07, Windows x64. Skill `code-review`, baseline fixa `7dcfafd64311353c893bec69eb1d5ca3e07c4d4b`; escopo somente do incremento próprio e especificação [ready](spec.md). Dois agentes leitores, sem edições ou chamadas pagas. A documentação geral mantida por outra conversa não foi incorporada ao incremento.

## Standards

Revisão inicial, dois P2:

- Livro rejeitado pelo engine era promovido ao painel/histórico. Corrigido: validar primeiro, preservar a observação aceita; teste com horário regressivo e quantidade divergente.
- Parser aceitava 256 níveis, engine limitava 50. Corrigido: limite compartilhado de 256; contexto JEV continua limitado a 20 níveis por lado, evitando egress desnecessário.

Reverificação do agente: “nenhum achado duro permanece aberto”. 22 testes focados passaram. O recorte compartilhado exclui OCR/dados privados e distingue alterações materiais dos relógios. Região OCR é obrigatória e nenhuma política do Windows é contornada.

Observação separada: mensagem específica de bloqueio OCR era substituída por diagnóstico genérico. Corrigido com exceção tipada de mensagem constante, publicada no estado público e teste de comportamento. Demonstração explícita também passou a publicar os livros já presentes na fixture e os negócios aceitos no gráfico; tudo continua identificado como sintético, JEV OFF.

Follow-up independente desses dois ajustes: ambos os testes passaram; nenhum novo achado duro, sem API paga. A label local foi ajustada para “avaliação local”, evitando afirmar ocorrência do fenômeno quando o estado é `not_observed`.

## Spec

Revisão inicial, dois P2:

- FW-02/07: projeção de agendamento não incluía livro/corretoras. Corrigido com o mesmo helper observado de `build_context`; mudanças materiais disparam avaliação, horários isolados não.
- FW-05: intervalos calculados não chegavam ao estado. Corrigido: `polling_effective_ms` e `rtd_change_interval_ms` publicados; teste confirma 250 ms de polling e 500 ms entre mudanças da amostra.

Reverificação do agente: “os dois problemas anteriores foram resolvidos”; 10 testes passaram sem chamadas pagas. Nenhum novo bug ou ampliação indevida de escopo.

Aceites ainda abertos: FW-06 é snapshot textual auxiliar, sem extração estruturada validada de Times & Trades/livro; FW-11 exige piloto real de 30 minutos e p95 visual; FW-12 exige comparação de inferências contextualizadas, além dos casos offline. Instalação/animação não encerram esses aceites.

## Configuração de revisão

`docs/agents/issue-tracker.md` não existe. A skill recomenda `/setup-matt-pocock-skills` para configurar o rastreador; isso não bloqueou a revisão local nem autorizou alterações em documentação de outro chat. Os achados ficaram neste registro e no ticket canônico 04, sem criar duplicatas externas.
