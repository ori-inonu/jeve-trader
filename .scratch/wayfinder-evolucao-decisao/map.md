# Jeve Trader — evolução da inteligência e da interface

Label: wayfinder:map
Status: resolved
Created: 2026-10-07
Tracker: local-markdown

## Destination

Preparar a próxima etapa de planejamento do painel de decisão: contratos verificáveis de contexto, tempo, execução, dimensionamento e interface, com protocolo de evidência incremental e critérios de aceite. O destino é uma especificação revisável; a implementação do aplicativo pertence à etapa seguinte.

## Notes

O plano de origem é “Jeve Trader — painel de decisão para alavancagem progressiva”, do chat “Investigar UI, JEV e risco”. Gabriel aprovou materializar este complemento documental em 07/10/2026. As recomendações dos tickets registram essa direção; seu fechamento exige cumprir o aceite documental e registrar a resolução.

Preservar Tauri/React, motor Python, execução manual, banca atual, comparação com `q=0`, JEV `jev-1.13.0` fixado para comparação, baseline logística, Excel parcial e 30% como referência de adaptação, sem pausa automática. O modelo do agente de desenvolvimento é separado do modelo JEV do produto.

Ao retomar, usar Wayfinder e a referência de tracker local. Para nova pesquisa, usar research e fontes primárias; para decisões que dependam da preferência humana, usar grilling e domain-modeling. Consultar apenas o ticket relevante e suas dependências.

Começar pela [especificação transversal](spec.md), que contém vocabulário, registro de parâmetros e rastreabilidade. Para evidência de código e fontes externas, consultar o [complemento de pesquisa datado](../../docs/research/Complemento_Wayfinder_JEV_WIN_2026-10-07.md). A pesquisa histórica continua vinculada à versão que auditou.

WF-01–06 estão resolvidos documentalmente. A próxima etapa está na [sequência de implementação](implementation-plan.md), com alcance conferido na [auditoria de aceite](acceptance-audit.md). Não há filho aberto neste mapa; gates empíricos e parâmetros ainda pendentes permanecem nos contratos.

Os filhos vivem em `issues/`. A fronteira é obtida lendo `Status:` e `Blocked by:`: primeiro ticket aberto, não claimed, cujas dependências estejam resolved, em ordem numérica. Antes de trabalhar, mudar o status para claimed; ao fechar, acrescentar Answer e Comments, marcar resolved e adicionar um ponteiro em Decisions so far. Não fechar por mera criação do arquivo.

As dependências ordenam a definição dos contratos. São diferentes dos gates empíricos: qualquer experimento confirmatório aguarda o fechamento do protocolo, disponibilidade dos dados e autorização de orçamento externo quando aplicável.

O Mission Control não respondeu à consulta inicial; uma nova consulta em 07/10/2026 retornou disponível, sem tarefas registradas para o projeto. A implementação concorrente foi identificada e acompanhada pelo status do chat “Investigar UI, JEV e risco”. Dados de chats e tarefas fornecem contexto, sem autorização adicional.

## Decisions so far

- [Identidade causal da decisão](issues/01-identidade-causal.md): candidato e projeção têm identidade de conteúdo; cada pergunta mantém seu binding e o histórico preserva invalidações. Conta/custo exigem nova decisão financeira. [Contrato](contracts/01-identidade.md).
- [Contratos das hipóteses JEV](issues/02-contratos-hipoteses.md): catálogo e projeções por pergunta preservam apoio, contradição e insuficiência; distribuições e empates permanecem auditáveis. Casos de desenvolvimento não contam como confirmação. [Contrato](contracts/02-hipoteses.md).
- [Utilidade após latência e execução](issues/03-latencia-execucao.md): replay por disponibilidade e clocks verificáveis; não entrada, parcial e desconhecido têm estados distintos; custos e cadência preservam o denominador comum. [Contrato](contracts/03-tempo-execucao.md).
- [Dimensionamento sobre distribuições incertas](issues/04-dimensionamento-incerto.md): comparar inteiros, domínio fracionário e envelope robusto com zero admissível e patrimônio próprio; cota separa fluxos de desempenho. Fixture aritmética conferida, sem benefício financeiro alegado. [Contrato](contracts/04-dimensionamento.md).
- [Interface verificável e estável](issues/05-interface-verificavel.md): vigência junto da decisão, inspeção histórica com avisos atuais, formulários/foco estáveis e quatro fluxos de teclado. Sessão Windows definida e ainda não realizada. [Contrato](contracts/05-interface.md).
- [Evidência incremental e promoção](issues/06-evidencia-promocao.md): H1–H4 separam previsão, utilidade, seleção e quantidade; manifesto temporal, incerteza, critérios exaustivos e ledger impedem promoção por uma flag. Confirmação depende de dados, custos, orçamento e limites ainda pendentes. [Contrato](contracts/06-protocolo.md).

## Not yet specified

As pesquisas podem revelar novas escolhas de política conforme a cobertura real, a latência e os primeiros resultados anotados forem conhecidos. Graduar essas descobertas em tickets somente quando a pergunta estiver definida; escolhas já enumeradas nos filhos permanecem lá.

## Out of scope

Alteração de código, build, instalação, ordens, chamadas pagas JEV e mudança de modelo nesta rodada. Rentabilidade do WIN, tarifa operacional da conta e integração real ProfitDLL permanecem dependentes de evidência própria. Aumento de lote motivado por recuperar prejuízo fica fora da política do produto.
