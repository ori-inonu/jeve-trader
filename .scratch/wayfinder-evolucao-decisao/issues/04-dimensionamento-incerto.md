# Dimensionamento sobre distribuições incertas

ID: WF-04
Type: research
Label: wayfinder:research
Status: resolved
Parent: [Mapa](../map.md)
Created: 2026-10-07
Blocked by: 01, 03

## Question

Como comparar quantidades inteiras, incluindo zero, quando execução, custos e distribuição financeira são incertos e cada política altera sua própria trajetória de patrimônio?

## Alternativas

| Alternativa | Consequência |
|---|---|
| Fórmula atual: melhor quantidade, fração e arredondamento | Comparador simples; a aplicação da fração depois da escolha pode zerar lotes admissíveis. |
| Otimização discreta sobre distribuição pontual | Compara diretamente as quantidades; continua sensível a erro na distribuição estimada. |
| Política fracionária ou robusta com distribuição incerta e limites de trajetória | Explicita o risco de estimativa; depende da escolha e da validação do conjunto de incerteza. |

## Evidência

A sonda histórica encontrou capacidades 2/4/3 e escolhas 0/1/0 para bancas R$400/R$800/R$600. A nova leitura reproduziu capacidade e arredondamento em aritmética isolada, mas o motor atual rejeita os metadados antigos de validação e escolhe zero nos três casos. Não houve vantagem econômica demonstrada. A [auditoria atualizada](../../../docs/research/Complemento_Wayfinder_JEV_WIN_2026-10-07.md) documenta entradas, fórmulas, escopo e essa diferença.

A pesquisa de [Sun e Boyd](https://stanford.edu/~boyd/papers/robust_kelly.html) estuda crescimento logarítmico no pior caso de um conjunto de distribuições. Serve de alternativa metodológica; não determina a fração, a distribuição ou os limites apropriados para WIN.

## Direção recomendada

Definir o conjunto de quantidades admissíveis em cada oportunidade a partir de patrimônio atual, posições, margem, reserva interna e restrições documentadas. Incluir `q=0`. Capacidade não é recomendação.

Comparar o resultado líquido `X(q)` por quantidade. Sua distribuição depende da execução e do custo daquela quantidade, não apenas de `q × resultado de um contrato`. Para capital positivo `W`, o critério logarítmico ilustrativo é `E[log((W + X(q))/W)]`; declarar como tratar cenários com patrimônio final não positivo antes de qualquer uso desse critério.

Manter a política atual como comparador. Investigar separadamente:

- Otimização discreta em todos os inteiros admissíveis.
- Política fracionária cuja definição indique se atua na exposição, no conjunto admissível ou no critério. Não presumir que multiplicar o ótimo contínuo e arredondar seja equivalente a otimizar o problema discreto.
- Alternativa robusta que avalia o pior resultado esperado em um conjunto coerente de distribuições, com probabilidades normalizadas e dependências entre execução e retorno.
- Adaptação ao drawdown com a referência existente de 30%, sem pausa automática e sem aumentar lote para recuperar perda.

Documentar como o conjunto de incerteza será desenvolvido: dados usados, erro de calibração, cobertura, execução adversa e resolução temporal. Intervalos independentes arbitrários não definem automaticamente uma distribuição conjunta válida. O tamanho desse conjunto e a fração permanecem parâmetros em seleção, não defaults novos.

Simular cada política cronologicamente com seu próprio patrimônio. A quantidade admissível da oportunidade seguinte depende do patrimônio dessa política. Comparar políticas nas mesmas oportunidades e no mesmo calendário, mantendo os casos em que uma política não consegue admitir um contrato.

Separar aportes, retiradas e PnL. Especificar a referência de patrimônio e pico para drawdown, inclusive o ajuste de fluxos externos; reportar retorno de investimento com convenção explícita, para um aporte não parecer lucro ou recuperação. Não misturar drawdown em relação ao capital inicial com drawdown a partir do pico.

Registrar crescimento líquido, drawdown, tempo de recuperação, perdas de cauda, saldo não positivo e incapacidade de admitir o lote mínimo. Quando `q=0`, o retorno de negociação é zero; despesas de consulta seguem o contrato da política. Um zero escolhido não será corrigido impondo um contrato.

## Dependências e escopo

A [identidade causal](01-identidade-causal.md) e o [replay de latência e execução](03-latencia-execucao.md) definem as entradas. Estende E06, E09 e E10.

Este ticket resolve o desenho da comparação. Qualquer confirmação aguarda o [protocolo de evidência](06-evidencia-promocao.md), dados e critérios congelados. Não recomenda quantidades para a conta real e não prova rentabilidade por uma simulação.

## Critérios de aceite — próxima etapa

Entregar:

1. Definições matemáticas dos comparadores, do conjunto admissível e do tratamento de patrimônio não positivo.
2. Contrato da distribuição por quantidade e construção do conjunto de incerteza, com limites identificados.
3. Registro dos parâmetros a selecionar em desenvolvimento, critérios de risco e procedimento de confirmação.
4. Exemplo cronológico com políticas que escolhem quantidades diferentes, PnL próprio e fluxos externos separados.
5. Critérios que aceitam resultado favorável, desfavorável ou inconclusivo sem impor lote mínimo.

### Cenários de verificação futura

| Caso | Resultado exigido |
|---|---|
| Bancas R$400, R$800 e R$600 | Capacidade e escolha separadas; inputs artificiais identificados. |
| Ótimo fracionado menor que um contrato | Zero é resultado admissível, com motivo verificável. |
| Aporte e retirada no meio da trajetória | Fluxo externo separado de desempenho e ajuste do pico explícito. |
| Custos ou preenchimento mudam com quantidade | Cada quantidade usa sua distribuição e custo próprios. |
| Duas políticas têm PnL diferente | Próximas decisões usam patrimônios próprios, sem banca comum artificial. |
| Perda de cauda torna saldo não positivo | Evento registrado; logaritmo não calculado como se fosse finito. |
| Pouca evidência ou intervalo muito amplo | Incerteza visível; não forçar uma escolha positiva. |
| Drawdown de 30% ou perda recente | Não introduzir pausa automática nem progressão para recuperação. |

## Answer

Resolvido pelo [contrato discrete-sizing-v1](../contracts/04-dimensionamento.md). S0 preserva o comparador atual; S_discrete otimiza os inteiros admissíveis; S1 aplica a fração ao domínio de risco; S_robust usa um envelope de distribuições conjuntas válidas. Zero, custos por quantidade, saldo não positivo e dados não identificáveis têm regras explícitas. Parâmetros e limites de risco continuam em desenvolvimento, congelados antes da confirmação.

O exemplo A/B mantém patrimônios próprios e separa fluxos de PnL, retorno por cota e drawdown desde o pico. Sua aritmética foi reproduzida isoladamente com Decimal, incluindo capacidades 2/4/3, teto 0/1/0 e lote mínimo inadmissível. Os cinco aceites documentais estão cobertos; o protocolo aceita resultado favorável, desfavorável e inconclusivo sem impor quantidade positiva.

## Comments

2026-10-07 — Resolução documental e conferência aritmética concluídas. Nenhum resultado foi atribuído ao motor atual ou promovido a política operacional.

2026-10-07 — Reivindicado com WF-01 e WF-03 resolvidos. Comparadores, parâmetros e trajetória aritmética em fechamento documental.

2026-10-07 — Alternativas especificadas para a próxima decisão. Os números da sonda são demonstração estrutural, não validação da política.
