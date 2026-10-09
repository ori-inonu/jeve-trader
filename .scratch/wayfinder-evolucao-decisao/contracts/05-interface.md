# Contrato resolvido — leitura, validade e navegação

Date: 2026-10-07
Version: decision-ui-v1
State: specified; native_windows_verification_pending
Ticket: [Interface verificável e estável](../issues/05-interface-verificavel.md)
Depends on: [Identidade](01-identidade.md), [Hipóteses](02-hipoteses.md), [Tempo](03-tempo-execucao.md)

## Estados independentes e origem dos números

Preservar Decisão, Capital, Pesquisa e Configuração. O cabeçalho da decisão mostra instrumento, modo, fonte/cobertura, candidato/premissa, avaliação, corte, idade e validade efetiva. A interface consome `effective_valid_until` e motivos do motor; não calcula outra validade a partir do horário do tick. WAIT pode ser uma decisão vigente, com motivo verificável, mesmo sem vantagem econômica demonstrada.

Eixos distintos: modo (`synthetic`, `replay`, `excel_partial`, `disconnected`); validade (`active`, `updating`, `expired`, `incompatible`, `unavailable`); evidência financeira (`absent`, `experimental`, `confirmed_for_scope`, `invalidated`). Não inferir confirmação porque o modo é replay ou porque uma pergunta JEV retornou. Exibir texto e ícone, sem depender só de cor.

| Natureza | Exemplo e legenda | Limite junto do número |
|---|---|---|
| Observado | Preço da fonte / parcela registrada | Fonte, hora, cobertura e origem manual quando aplicável |
| Calculado | Distância ao stop, capacidade de margem | Entradas/fórmula/conta; capacidade não é quantidade escolhida |
| Contextual JEV | Apoio, contradição, insuficiência, Choice | Proposição, janela, distribuição e versão; não é chance de lucro |
| Estimado financeiro | Distribuição líquida por oportunidade/q | Evento, execução, custo e registro/limites de validação |

Valor líquido de um alvo é resultado **condicionado àquela saída**, não retorno esperado. Null mostra “indisponível” com motivo, sem virar zero. Quantidade, geometria e estimativa na decisão principal pertencem à mesma avaliação. WAIT tem `selected_candidate=null`; alternativas podem ter contexto próprio identificado. Nenhum botão envia ordem; registrar parcela significa informar execução já realizada manualmente.

## Matriz estado × conteúdo × ação

| Estado | Conteúdo obrigatório | Ações e próximo estado |
|---|---|---|
| active, WAIT | Por que aguardar: modelo ausente, insuficiência, conflito, restrição ou falta de dado; condições concretas para reavaliar | Inspecionar evidências/alternativas e abrir configuração pertinente; atualização válida pode mudar a decisão |
| active, cenário experimental admissível | Modo experimental, premissa, versões, q versus capacidade, riscos/custos, comparação com zero e limite da evidência | Inspecionar/consultar registro; eventual anotação manual separada, sem ação de ordem |
| updating, avaliação anterior ainda válida | Avaliação anterior e seu prazo original; nova avaliação pendente identificada | Inspecionar a anterior; nova resposta compatível substitui como um conjunto; expiração anterior continua valendo |
| updating, nenhuma avaliação válida | Aguardar e motivo atual; avaliação anterior somente como histórico | Inspecionar histórico; sem preencher o painel atual com seus números |
| expired | Aguardar; horário de vencimento e motivo; números anteriores identificados como históricos | Abrir histórico/reavaliar quando houver evidência; cache não reinicia idade |
| incompatible | Aguardar; campo material alterado e relação com avaliação descartada | Inspecionar “o que mudou”; nenhuma mistura de geometria/preço/contexto de versões diferentes |
| unavailable | Campo/etapa ausente, falha ou relógio não verificável; cobertura limitada | Ir à origem do problema; não sugerir que reclicar remove falta de evidência |
| inspeção histórica congelada | Avaliação/candidato imutáveis, corte e hora de abertura; rótulo Histórico em texto persistente | Voltar ao presente; faixa de estado atual continua viva |
| formulário com revisão conflitante | Rascunho local, revisão de origem e revisão atual; mudanças explicadas | Revisar contra a versão atual ou descartar rascunho; envio rejeita revisão antiga |

“O que mudou” lista mudanças materiais desde a avaliação anterior, não cada tick. “Condições para reavaliar” deriva de motivos: conta conciliada, dados atuais/cobertura necessária, estimativa aceita para o cenário, avaliação compatível dentro do prazo. Não prometer nova consulta como solução de um modelo ausente.

## Avisos e anúncios

| Prioridade | Exemplo | Persistência e anúncio |
|---|---|---|
| P0 — invalida a decisão atual | Vencimento, fonte/cobertura perdida, conta/versão incompatível | Junto da decisão e na faixa atual da inspeção congelada; anunciar uma vez por transição/materialidade |
| P1 — ação necessária | Conciliação, custo não conferido, configuração/modelo rejeitado | Agrupar por causa; link para correção, sem roubar foco |
| P2 — mudança material compatível | Nova avaliação/candidato, nova parcela/revisão | Resumo agrupado e acessível; usuário pode abrir detalhes |
| P3 — atualização contínua | Ticks, idade, heartbeat | Visível sem anúncio contínuo; disponível ao inspecionar |

Deduplicar a mesma causa presente em vários componentes. Confirmar leitura não restaura vigência. Usar região de status e anúncio agrupado, normalmente não interruptivo; testar prioridade e ordem com tecnologia assistiva. Não transformar a sequência de preços em live region. Aviso não depende de toast temporário. Alertas atuais persistem mesmo com Pesquisa/histórico congelados.

As diretrizes [HAX para explicar decisões](https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-why-the-system-did-what-it-did/), [WCAG sobre status](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html) e [uso de cor](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) orientam esse desenho; conformidade precisa de verificação do produto.

## Inspeção estável

“Inspecionar” captura uma avaliação completa identificada, com candidato, geometria, respostas/evidências, validade conhecida no corte e versões. A seleção usa chave causal, nunca índice. Reorder não muda o objeto lido. Remoção ou alteração de geometria não substitui seu conteúdo silenciosamente: a inspeção passa a histórica e explica a incompatibilidade.

“Congelar leitura” fixa o conteúdo de inspeção, não a captura/conta nem a faixa de estado atual. Mostrar avaliação/corte e hora de congelamento. Ao vencer/desconectar, o conteúdo permanece legível e o aviso atual muda. “Voltar ao presente” abre o último estado completo, sem reproduzir ticks acumulados. Controle fica acessível por teclado. Essa estratégia segue [WCAG sobre atualização automática](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html), mantendo avisos essenciais atuais.

Preservar foco, seleção de texto, rolagem e escala do gráfico durante atualização. Evitar remount do formulário por revisão de conta. Rascunho guarda revisão de origem; nova revisão não sobrescreve valores ainda não enviados. Ao salvar, verificar conflito e oferecer revisão explícita, sem merge automático de capital. Aporte/retirada e PnL são registros distintos.

Ao fechar detalhe, devolver foco ao controle que o abriu. Se foi removido, focar o título/lista de alternativas e anunciar a remoção; não saltar para outro candidato com o mesmo índice. Troca explícita de área/candidato pode mudar seleção; atualização automática não pode.

## Fluxo de teclado nas quatro áreas

Global: link de pular para conteúdo → navegação nomeada das quatro áreas → título/estado → ações principais → detalhes. Tab/Shift+Tab seguem ordem visual e semântica; Enter/Space ativam controles; foco sempre visível. Detalhe modal, se usado, tem nome, fechamento e retorno de foco; nunca prende a navegação sem saída. Gráficos têm descrição e tabela acessível dos dados, sem depender de hover.

| Área | Sequência e ações essenciais |
|---|---|
| Decisão | Estado/motivo → Inspecionar → Congelar/Voltar ao presente → lista de alternativas com controles nomeados → detalhes da escolhida e evidências |
| Capital | Conta/revisão → valores conciliados e capacidade/q → editar → revisar alterações/conflitos → salvar registro manual → parcelas e fluxos externos históricos |
| Pesquisa | Escopo/evidência → seleção de avaliação/experimento → métricas com denominadores → respostas descartadas/motivos → tentativas e fontes |
| Configuração | Fonte/capacidades → conta/custos/vigência → parâmetros/origem → orçamento de consulta → opções avançadas com efeito e estado experimental |

Controles têm nome acessível e mensagens ligadas ao campo. Não exigir mouse, rapidez de digitação ou atalho exclusivo para funções essenciais. Números têm unidade/lado/denominador claros. Os critérios [WCAG de teclado](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html), [ordem de foco](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html) e [texto acessível Windows](https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessible-text-requirements) são referências para a verificação.

## Sessão futura de verificação Windows

**Não realizada nesta rodada.** Proposta qualitativa: seis participantes, incluindo Gabriel, pelo menos dois usuários de Profit e experiência em teclado/Narrator/ampliação, com papéis que podem se sobrepor. Nomes, recrutamento, consentimento e datas ficam pendentes. Se o perfil pretendido não for coberto, registrar a limitação e não generalizar compreensão. Seis participantes não certificam acessibilidade nem segurança financeira.

Moderador e observador, aproximadamente45min por sessão, conta de teste isolada, fixtures ou replay autorizado, sem API paga. Registrar hash/build, Windows/WebView, Narrator e dispositivo. Verificar janela Tauri nativa, não só preview React; resoluções1366×768 e1920×1080 quando disponíveis, escalas Windows125/150/200%, teclado sem mouse, leitor de tela, contraste e movimento reduzido. Não alegar que alguma combinação já passou.

| Tarefa observável | Evento controlado | Evidência a registrar |
|---|---|---|
| Identificar modo, idade e por que aguardar | Modelo ausente/dado insuficiente | Interpretação correta e localização das condições de reavaliação |
| Explicar probabilidade, capacidade e valor de alvo | Campos das quatro naturezas | Não confundir apoio JEV com lucro, teto com escolha ou alvo com expectativa |
| Abrir B após reorder A/B | Identidades preservadas | Evidência de B e foco estável |
| Congelar, perder cobertura e expirar | Atualização determinística | Histórico legível, aviso atual percebido; estado antigo não interpretado como vigente |
| Retornar ao presente | Nova avaliação compatível | Último estado completo, sem reprodução de ticks/foco perdido |
| Editar conta durante revisão externa | Novo snapshot/revisão | Rascunho preservado, conflito e correção compreendidos |
| Navegar todas as áreas | Apenas teclado | Sem controle inacessível, armadilha ou perda de foco |
| Ler enquanto chegam ticks | Narrator e anúncios materiais | Sem interrupção contínua; mudança importante anunciada |
| Usar escala ampliada |125/150/200% | Informação essencial legível sem sobreposição; rolagem disponível |

Registrar sucesso/erro/ajuda, tempo descritivo, caminho de foco e interpretação verbal; gravação só com consentimento, sem dados privados de trading. Erro crítico: interpretar histórico como vigente, confidence como chance de lucro, registro manual como envio de ordem, ou não perceber invalidação atual. Qualquer erro crítico, função essencial inacessível ou sobreposição que esconda informação bloqueia aprovação daquele fluxo; corrigir e repetir tarefas afetadas. Zero erros nessa amostra não demonstra ausência de risco geral.

## Aceite

Matriz, prioridade, freeze/revisões, quatro fluxos de teclado e condições/tarefas/participantes da futura sessão resolvem o aceite documental e os nove cenários do ticket. Implementação e teste nativo continuam pendentes. A aprovação visual não aprova modelo financeiro, dados ou ordens.
