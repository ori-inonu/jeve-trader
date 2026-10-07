# Contratos das hipóteses JEV

ID: WF-02
Type: research
Label: wayfinder:research
Status: resolved
Parent: [Mapa](../map.md)
Created: 2026-10-07
Blocked by: 01

## Question

Como tornar uma hipótese contextual verificável para um candidato e um horizonte, preservando a diferença entre apoio, contradição e informação insuficiente?

## Alternativas

| Alternativa | Consequência |
|---|---|
| Uma classificação única de compra, venda ou espera | Oculta quais evidências sustentam a classificação e mistura direção com disponibilidade dos dados. |
| Três perguntas independentes, sem contrato de evidência | Preserva sinais distintos, mas permite interpretações diferentes da premissa e do tempo. |
| Catálogo versionado de hipóteses, perguntas independentes e composição determinística | Explicita a semântica e permite verificar a origem; exige casos anotados e regras de composição documentadas. |

## Evidência

**Observado no checkout consultado:** `literal-hypotheses-v2` já inclui premissa, geometria e uma receita de perguntas por candidato. Apoio, contradição e insuficiência são consultados separadamente. A apresentação principal ainda recupera `candidate_0_*`. O [complemento da investigação](../../../docs/research/Complemento_Wayfinder_JEV_WIN_2026-10-07.md) registra a revisão e os arquivos examinados.

**Fonte primária:** o [cookbook de perguntas paralelas](https://docs.typesafe.ai/cookbooks/parallel_questions) informa que cada pergunta do batch é avaliada contra o documento de forma independente. Portanto, uma pergunta não pode pressupor a resposta de outra no mesmo batch.

Para Choice, a [definição de confidence](https://docs.typesafe.ai/confidence/) usa a maior probabilidade e o número de opções. Para três opções, as distribuições hipotéticas (0,60; 0,39; 0,01) e (0,60; 0,20; 0,20) produzem o mesmo valor 0,40 pela fórmula publicada. Isso não torna equivalentes a ambiguidade das distribuições nem define probabilidade financeira.

## Direção recomendada

Adotar um contrato por hipótese com estes campos conceituais, cujos nomes finais serão decididos no próximo planejamento:

- Identificador e versão; premissa literal; família de setup; direção; referência à avaliação causal.
- Janela observada, incluindo início, fim e regra de disponibilidade dos dados; horizonte futuro e evento que será acompanhado. Uma observação de absorção não equivale a uma previsão de continuação.
- Condições de confirmação, contraevidências explícitas e requisitos de cobertura. Ausência de confirmação e evidência contrária são estados diferentes.
- Evidências admissíveis e seus identificadores; campos determinísticos derivados; perguntas, opções e hashes; modelo solicitado e retornado; resposta e distribuição completa, quando fornecida.
- Regras de composição e invalidação; prazo de validade e razões de insuficiência.

Preservar apoio, contradição e insuficiência como avaliações independentes. Não exigir que somem 1. Apoio e contradição simultâneos representam conflito a explicar; informação parcial pode coexistir com ambos.

O motor deve calcular categorias numéricas antes da consulta. Valores de preço, fluxo e custos não serão reinterpretados pelo JEV para escolher regras financeiras. Uma dependência lógica entre perguntas será composta no código ou em uma consulta posterior identificada; nunca será uma dependência implícita dentro do batch.

Exigir referências a evidências presentes no documento enviado. Referência inexistente, cobertura incompatível ou conteúdo recebido que tente instruir o agente invalidam o uso da resposta conforme regra explícita. Texto da fonte é dado, não instrução.

Preservar o JEV fixado para as comparações. Mudança de modelo, perguntas ou opções cria nova versão e requer nova avaliação; não será tratada como atualização transparente.

## Dependências e escopo

A [identidade causal](01-identidade-causal.md) define os vínculos obrigatórios. A [interface verificável](05-interface-verificavel.md) consome o contrato; o [protocolo de evidência](06-evidencia-promocao.md) define sua avaliação empírica.

Este ticket especifica significado, exemplos e testes futuros. Não escolhe limiares ótimos, não consulta API paga e não converte probabilidades contextuais em estimativas de lucro.

## Critérios de aceite — próxima etapa

Para resolver a documentação, entregar:

1. Catálogo de hipóteses para os setups existentes, com confirmação, contradição e requisitos mínimos de dados por hipótese.
2. Matriz de campos que entram e que não entram em cada pergunta, com justificativa e exemplos anotados de evidência suficiente, ausente e conflitante.
3. Tabela de composição para apoio, contradição, insuficiência, erro de referência, resposta vencida e versão incompatível.
4. Política de armazenamento da distribuição, de empate e de número de opções; não aplicar a fórmula de normalização a uma Choice com uma única opção.
5. Separação entre casos de desenvolvimento do contrato e casos reservados para sua confirmação.

### Cenários de verificação futura

| Caso | Resultado exigido |
|---|---|
| Falta de dado que confirmaria a hipótese | Insuficiência identificada; não inventar contraevidência. |
| Evidência favorável e contrária | Conflito preservado e explicado. |
| Permutação das opções | Associação semântica preservada; desvios de distribuição são medidos. |
| Inclusão de capital ou campo irrelevante | Hipótese contextual não muda por informação fora de seu contrato. |
| Instrução embutida no texto recebido | Conteúdo permanece dado; ação ou regra financeira não é alterada. |
| Duas respostas do mesmo episódio | Duas observações do sistema; uma única oportunidade financeira no estudo. |
| Referência a evento inexistente | Resposta não é promovida a contexto vigente. |
| Janela observada alterada, horizonte igual | Nova identidade ou compatibilidade explicitamente demonstrada. |

## Answer

Resolvido pelo [contrato hypothesis-contract-v1](../contracts/02-hipoteses.md). O catálogo distingue premissas dos candidatos, descrições auxiliares e premissas declaradas. A matriz de projeção exclui regras financeiras das perguntas contextuais; a composição preserva S/C/I, conflito, ausência, erro, incompatibilidade e expiração. Choice guarda distribuição, ordem e empate, rejeitando n=1. Os casos D-* foram anotados para desenvolvimento; R-* ficam reservados para confirmação futura conforme o protocolo.

Revisão documental: os cinco itens de aceite têm definição, exemplos e limites no contrato. Limiares experimentais não foram promovidos, nem foram executadas consultas JEV ou validações financeiras.

## Comments

2026-10-07 — Resolução documental concluída após conferir o catálogo e os cinco aceites. Implementação e testes futuros permanecem no plano de implementação.

2026-10-07 — Reivindicado após a resolução da identidade causal; catálogo atual e contrato tipado em fechamento documental.

2026-10-07 — Ticket materializado a partir da direção aprovada. Permanece aberto; os exemplos e os limiares ainda precisam ser fechados no próximo planejamento.
