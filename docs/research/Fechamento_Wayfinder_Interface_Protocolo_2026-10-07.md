# Fechamento de pesquisa — interface e evidência incremental

Date: 2026-10-07
Scope: pesquisa e especificação; sem alteração de código
Parent: [Complemento Wayfinder](Complemento_Wayfinder_JEV_WIN_2026-10-07.md)
Contracts: [Interface](../../.scratch/wayfinder-evolucao-decisao/contracts/05-interface.md), [Protocolo](../../.scratch/wayfinder-evolucao-decisao/contracts/06-protocolo.md)

## Fatos observados e limites

O painel em [App.tsx](../../desktop/src/App.tsx) já oferece as quatro áreas e inspeção por ID no snapshot. A avaliação causal precisa ir além desse ID de apresentação. O serviço em [desktop_service.py](../../app/desktop_service.py) mantém espera financeira sem estimativa aceita; o contexto principal ainda parte do primeiro candidato. Existem regras visuais de idade e formulários cuja revisão pode provocar remontagem. Esses pontos justificam contratar validade efetiva e estabilidade de leitura, sem declarar que toda a interface é defeituosa.

O [laboratório](../../app/decision_lab.py) já tem baseline logística, junção por disponibilidade, calibração temporal e comparadores. Rótulos stop/alvo/fim de horizonte e execução por proxy não comprovam resultado líquido real. A implementação aceita seleção de qualquer candidato admissível retornado, não somente desempate. Um número de sessões ou metadado de validação isolado não supre evidência temporal, custos e execução.

Nesta pesquisa não houve sessão de usabilidade, medição com Narrator, teste da janela nativa, experimento financeiro ou consulta paga. Resultados de implementação registrados em outro chat têm seus próprios limites; não são resultado desta rodada.

## Fontes primárias e inferências de engenharia

[HAX sobre explicações](https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-why-the-system-did-what-it-did/) sustenta oferecer acesso à explicação do comportamento. [WCAG sobre atualização automática](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html), [status](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html), [teclado](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html) e [foco](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html) orientam leitura estável e navegação. Aplicar essas referências exige verificar o produto; elas não certificam Tauri/React automaticamente.

A inferência adotada é separar estado atual de inspeção histórica: congelar uma avaliação completa, preservando avisos atuais e ação de retorno ao presente. Atualizações não podem trocar candidato, sobrescrever rascunho de conta ou interromper continuamente a leitura com ticks. Natureza dos números, modo, idade e motivo da espera devem estar próximos à decisão.

[Cawley e Talbot](https://www.jmlr.org/papers/v11/cawley10a.html) fundamentam separar seleção de modelo e confirmação. A [descoberta de atributos TypeSafe](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery) oferece um fluxo de desenvolvimento, sem evidência transferível de benefício no WIN. A [definição de Brier](https://scikit-learn.org/stable/modules/model_evaluation.html#brier-score-loss) exige explicitar escala/evento. A pesquisa de [Politis e Romano](https://www.tandfonline.com/doi/abs/10.1080/01621459.1994.10476870) motiva blocos dependentes; não resolve por si só mudança de regime ou pequena amostra.

## Propostas resolvidas, ainda não confirmadas

O contrato visual define matriz de estados, avisos por prioridade, freeze, conflito de revisão e quatro fluxos de teclado. A proposta Windows usa participantes qualitativos, escala125/150/200%, Narrator, eventos controlados e bloqueio por erro crítico. Recrutamento/datas/resultados permanecem pendentes; amostra pequena não prova ausência de risco.

O protocolo separa H1 previsão, H2 utilidade líquida dos atributos, H3 seleção tipada e H4 quantidade. O novo alvo financeiro H1 distingue sinal líquido negativo/zero/positivo por oportunidade; o rótulo existente permanece diagnóstico próprio. H3 fixa quantidade admissível e instante de execução comum. H4 compara o domínio fracionário discreto com o teto atual, preservando bancas próprias. Políticas robustas ficam secundárias predeclaradas.

Stationary bootstrap pareado de sessões, seeds/10.000 reamostragens e controle de quatro contrastes são propostas de laboratório, não parâmetros financeiros otimizados. Métodos, efeito, precisão e risco serão congelados antes da confirmação. Custos, dados autorizados, relógios, orçamento e limites pessoais ausentes mantêm `not_ready_for_confirmation`.

Conclusão documental: explicar validade e origem, preservar a leitura e separar os efeitos torna a investigação revisável. Sua utilidade no produto e benefício econômico dependem da implementação e das verificações futuras.
