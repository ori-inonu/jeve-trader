# Interface verificável e estável

ID: WF-05
Type: research
Label: wayfinder:research
Status: resolved
Parent: [Mapa](../map.md)
Created: 2026-10-07
Blocked by: 01, 02, 03

## Question

Como permitir que a pessoa entenda uma decisão atual e inspecione sua evidência sem perder o lugar durante atualizações ou confundir um estado histórico com uma recomendação vigente?

## Alternativas

| Alternativa | Consequência |
|---|---|
| Painel dinâmico com alerta de idade separado | Atualização simples; a decisão pode continuar parecendo vigente quando sua evidência venceu. |
| Congelamento integral da interface | Leitura estável, mas pode ocultar mudanças atuais de fonte, conta ou validade. |
| Decisão atual com inspeção histórica identificada e alertas atuais persistentes | Preserva leitura e vigência; exige estados visuais e navegação por identidade estável. |

## Evidência

**Observado:** existem quatro áreas em React/Tauri e uma explicação de espera quando falta modelo financeiro aceito. A inspeção agora recupera a alternativa pelo ID no snapshot atual. O contexto por candidato, a estabilidade dessa identidade quando o conteúdo muda e o tratamento visual da validade requerem contrato explícito. A existência de componentes não comprova uso por teclado, escala ampliada ou compreensão no Windows.

A diretriz [HAX sobre explicações](https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-why-the-system-did-what-it-did/) recomenda acesso à explicação do comportamento do sistema. A orientação [WCAG para atualização automática](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html) descreve pausa, ocultação ou controle da frequência, com exceção para atividade essencial. Essas referências orientam o desenho; esta pesquisa não certifica conformidade.

## Direção recomendada

Preservar Decisão, Capital, Pesquisa e Configuração.

| Área | Informação prioritária |
|---|---|
| Decisão | Ação ou espera; modo; candidato e premissa; idade/validade; origem dos números; motivos e condições de reavaliação. |
| Capital | Banca conciliada, instante e origem manual; exposição, capacidade e quantidade escolhida; custos/margem/reserva distintos; trajetória e fluxos externos. |
| Pesquisa | Alternativas com contexto próprio; avaliação e versões; respostas descartadas e motivos; registros do laboratório e limites de evidência. |
| Configuração | Fonte/capacidades, conta, parâmetros e sua origem/vigência; valores experimentais identificados. |

Exibir modo junto à decisão: sintético, replay, Excel parcial ou desconectado, conforme estados efetivamente suportados. Cobertura parcial permanece visível. Distinguir observado, calculado, contextual JEV e estimado financeiro no lugar onde o número é usado.

A ação principal deve apresentar “por que aguardar”, “o que mudou” e “condições para reavaliar”. Falta de modelo financeiro, resposta vencida, conflito contextual e falta de dados são motivos diferentes. Evitar percentuais de lucro quando só existe apoio contextual.

Especificar estados de decisão vigente, em atualização, vencida, incompatível e indisponível. Uma decisão vencida não permanece visualmente atual apoiada apenas por um banner distante. Expiração deve usar a validade efetiva da avaliação, sem uma segunda regra visual divergente.

A inspeção congelada captura uma avaliação identificada, com horário e indicação inequívoca de histórico. Ela não interrompe a captura nem os avisos atuais de desconexão, conta ou validade. A pessoa pode retornar ao presente por uma ação explícita. Ao abrir outra alternativa, usar a identidade causal, nunca índice ou objeto antigo sem estado de vigência.

Preservar foco de teclado, seleção e valores ainda não submetidos em formulários quando o snapshot muda. Definir comportamento para candidato removido ou revisão de conta alterada durante edição. Não substituir silenciosamente o conteúdo que a pessoa está examinando.

Agrupar anúncios acessíveis de mudanças materiais; ticks não devem interromper a leitura. Usar texto e ícone além de cor para modo, espera e validade. Especificar ordem de foco, nomes acessíveis e condições de contraste. A inspeção histórica pode ser estável sem ocultar alertas atuais.

### Exemplos de conteúdo, sem dados operacionais

- “Aguardar — não há estimativa financeira aceita para este cenário.”
- “Contexto histórico de 14:03:12 — a geometria atual mudou.”
- “Excel parcial — continuidade da fita não comprovada.”
- “Reavaliar quando a conta for conciliada e a fonte fornecer dados atuais.”

Os exemplos expressam estados, não previsões ou instruções de operação.

## Dependências e escopo

Depende da [identidade causal](01-identidade-causal.md), dos [contratos JEV](02-contratos-hipoteses.md) e de [validade e disponibilidade](03-latencia-execucao.md). Relaciona JT-005, JT-006, JT-014 e JT-015.

A entrega é especificação de estados, conteúdo e critérios. Não cria tela, protótipo em código, instalação ou alegação de validação Windows.

## Critérios de aceite — próxima etapa

Entregar matriz estado × conteúdo × ação, prioridade dos avisos, regras de inspeção histórica e fluxo de teclado para as quatro áreas. Definir uma sessão futura de verificação Windows com tarefas observáveis e participantes/condições documentados.

### Cenários de verificação futura

| Tarefa | Resultado exigido |
|---|---|
| Identificar modo, idade e motivo da espera | Informação disponível junto à decisão, com fonte e natureza dos números. |
| Abrir B depois de reordenar A/B | Contexto de B, ligado à sua avaliação. |
| Congelar e receber perda de cobertura | Histórico permanece legível; aviso atual permanece visível. |
| Expirar uma decisão enquanto está aberta | Estado histórico/vencido explícito e ação atual coerente. |
| Navegar somente por teclado | Sem perda de foco ou armadilha de navegação. |
| Usar escala Windows de 125%, 150% e 200% | Campos essenciais legíveis, sem sobreposição; rolagem e zoom definidos. |
| Ler com tecnologia assistiva durante atualizações | Mudanças materiais anunciadas sem sequência contínua de ticks. |
| Editar conta durante novo snapshot | Entrada preservada ou conflito explícito; sem atualização silenciosa. |
| Examinar “probabilidade” e “capacidade” | Contexto JEV, estimativa financeira e teto de margem distinguíveis. |

## Answer

Resolvido pelo [contrato decision-ui-v1](../contracts/05-interface.md). A matriz separa modo, validade e evidência financeira; os avisos têm prioridade/persistência; a inspeção histórica congela a leitura mantendo o estado atual. Identidade causal, revisão de formulário, foco e navegação de teclado foram definidos para as quatro áreas.

O protocolo Windows futuro contém participantes propostos, condições nativas, tarefas observáveis, registro de erros e bloqueios de aprovação. Os nove cenários do ticket estão cobertos documentalmente. Nenhuma tela foi alterada, nem a acessibilidade ou compreensão do aplicativo foram declaradas verificadas.

## Comments

2026-10-07 — Resolução documental concluída; execução da sessão nativa, recrutamento e resultados permanecem pendentes.

2026-10-07 — Reivindicado com WF-01–03 resolvidos; estados, estabilidade, teclado e protocolo Windows em fechamento documental.

2026-10-07 — Quatro áreas preservadas. Os critérios descrevem uma verificação futura, sem certificar a interface que está sendo implementada em outro chat.
