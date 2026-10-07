# Identidade causal da decisão

ID: WF-01
Type: research
Label: wayfinder:research
Status: resolved
Parent: [Evolução da inteligência e da interface](../map.md)
Created: 2026-10-07
Blocked by: none

## Question

Que contrato impede uma resposta, um cache ou uma seleção antiga de aparecer como evidência vigente de outro candidato, mesmo com IDs reutilizados, reordenação ou reinício do motor?

## Alternativas

| Alternativa | Benefício | Limite |
|---|---|---|
| Índice de lista, ID textual e idade | Menor mudança | Índice e ID reutilizado não identificam o conteúdo avaliado |
| ID mais geração da fonte e revisão da conta | Rejeita parte das mudanças | Custos, geometria, horizonte e catálogo precisam de identidade própria |
| Avaliação imutável com identidade de conteúdo e versões | Associação auditável e histórico reproduzível | Exige serialização canônica e regras de compatibilidade explícitas |

## Evidência

**Observado:** o serviço já compara ID, premissa, versão de hipótese e preços, além de geração da fonte, revisão da conta e idade. A extração visual continua usando `candidate_0`. Essa correção parcial substitui o diagnóstico anterior de aceitação apenas por geração/revisão. Ver [auditoria datada](../../../docs/research/Complemento_Wayfinder_JEV_WIN_2026-10-07.md).

**Inferência de engenharia:** correspondência de preços não comprova igualdade de horizonte, evidências, custos ou instante de disponibilidade. A associação visual deve usar a mesma identidade que o motor aceitou.

## Direção recomendada

Adotar avaliação imutável. `MarketSnapshot` referencia sessão do motor, sessão de mercado, contrato, fonte e geração, capacidades/cobertura, evidências e seus horários. `DecisionPlan` referencia candidato e sua versão, avaliação, política, conta, custos e, quando presente, estimativa financeira.

A identidade de conteúdo do candidato inclui premissa literal, família, lado, geometria, janela observada, horizonte, regra de entrada/saída, referências e versão do gerador. Definir representação canônica, unidades e precisão antes de calcular o hash. IDs textuais e índices continuam como apresentação; não substituem a identidade semântica.

A avaliação registra snapshot utilizado, conjunto de evidências, perguntas e sua versão/hash, modelo solicitado e retornado, versões de conta/custos/política, tempos de submissão/resposta/apresentação e regra de validade. A disponibilidade individual das evidências permanece verificável.

`context_by_candidate` usa identidade do candidato e horizonte; a decisão e a inspeção de alternativas recuperam o contexto correspondente. Reordenar a apresentação não muda a associação. Reutilizar um ID com novo conteúdo cria uma avaliação nova.

Registrar cada tentativa e sua classificação: vigente, substituída, vencida, incompatível ou falha, com código de motivo. Preservar resposta original e motivo no histórico. Cache conserva idade e versões originais; uma leitura nova não renova evidência antiga. Reinício produz nova identidade de sessão, sem aceitar sequência de uma sessão anterior.

Mudança de conta/custo pode preservar o julgamento contextual como histórico ou reutilizável sob regra explícita, mas exige novo cálculo financeiro e nova identidade de decisão. O reaproveitamento contextual nunca faz a decisão antiga voltar a ser vigente.

## Dependências

Fundamenta os demais tickets. Estende E01/E02/E04/E05/E09; a disponibilidade temporal detalhada pertence a [Utilidade após latência e execução](03-latencia-execucao.md).

## Critérios de aceite

Aceite para resolução documental: especificação de campos, representação canônica, matriz de compatibilidade e motivos de descarte, com exemplos de associação e histórico. O fechamento documental não comprova implementação.

| Cenário reproduzível | Resultado exigido na futura verificação |
|---|---|
| A e B reordenados após a submissão | Resposta de A permanece ligada a A; a interface não usa posição zero |
| Mesmo ID com stop, alvo, premissa ou horizonte alterado | Contexto incompatível sai do estado vigente, com motivo |
| Custo C1 passa a C2 durante a consulta | Resultado financeiro C1 fica histórico; novo plano aponta para C2 |
| Resposta recebida depois da validade | Tentativa registrada como vencida, sem nova validade por recebimento |
| Cache lido em outro instante | Mantém disponibilidade, expiração e identidade originais |
| Reinício e sequência que volta a 1 | Identidade de sessão impede associação entre execuções |
| Evidência corrigida ou cobertura perdida | Nova revisão ou invalidação; passado original permanece reconstruível |
| Campo obrigatório ausente ou referência inexistente | Falha verificável; nenhuma associação presumida |

## Comments

2026-10-07 — Ticket criado com a direção do plano aprovado. Não reivindicado; decisão final e verificação de software pendentes.

2026-10-07 — Reivindicado por esta sessão para fechar o contrato e seus exemplos. O escopo continua documental; os cenários de software serão tarefas da implementação.

## Answer

Resolvida documentalmente pelo [contrato causal-identity-v1](../contracts/01-identidade.md): campos e fronteiras, JCS com unidades exatas, instrumento/sessão e projeção calculada, binding imutável do batch, matriz de compatibilidade, motivos de descarte e exemplos para os oito cenários. Os digests do vetor fictício foram recalculados e a reordenação preserva o hash. A revisão independente encontrou três lacunas, incorporadas antes deste fechamento.

2026-10-07 — Resolved: contrato e exemplos verificáveis entregues. Implementação e testes do aplicativo permanecem pendentes; este fechamento não comprova comportamento Windows.
