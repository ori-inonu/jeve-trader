# Contrato resolvido — quantidades, incerteza e patrimônio

Date: 2026-10-07
Version: discrete-sizing-v1
State: specified; financial_validation_pending
Ticket: [Dimensionamento sobre distribuições incertas](../issues/04-dimensionamento-incerto.md)
Depends on: [Identidade](01-identidade.md), [Tempo e execução](03-tempo-execucao.md)
Evidence: [Pesquisa de fechamento econômico](../../../docs/research/Fechamento_Wayfinder_Tempo_Economia_2026-10-07.md)

## Quantidades e admissibilidade

O estado anterior à escolha contém patrimônio W, posições/obrigações, margem livre, reserva interna, conta/custos vigentes e orçamento de risco. Dinheiro usa aritmética determinística, unidades e arredondamento declarados. A reserva interna não é margem da corretora nem garantia de perda máxima.

Q_hard contém zero e os inteiros positivos que satisfazem simultaneamente as restrições documentadas: margem disponível após obrigações/reserva, exposição, quantidade máxima, custos e limite de perda de estresse R_base. Calcular a perda de estresse K(q) por quantidade e cenário definido, incluindo execução adversa/custos. Stop não limita uma perda em gap. R_base deve ser finito, compatível com os recursos disponíveis e aprovado no escopo; ausência desses insumos impede declarar q positivo admissível. Não aplicar automaticamente a soma margem+perda da fixture abaixo à conta real.

W<=0 encerra a trajetória econômica dessa política com evento de saldo não positivo; q=0 e crescimento logarítmico finito não são calculados como se W fosse positivo. Uma eventual recapitalização inicia outro período identificado. W>0 sem recursos para o lote mínimo admite somente zero. Falta de estimativa financeira aceita mantém espera, ainda que a capacidade permita contratos.

## Distribuição conjunta por quantidade

Para cada oportunidade/candidato, Ω é um conjunto versionado de estados de mercado e execução. Cada ω liga atraso, nenhuma entrada, parcelas, preços, posição remanescente, custos e desfecho; X(q,ω) é resultado líquido daquela quantidade. Todos os q usam estados coerentes, evitando inventar retornos favoráveis independentes entre lotes. Probabilidades não negativas somam um com tolerância/schema versionados. Preservar a massa desconhecida e os limites da fonte.

Despesas de consulta já incorridas foram debitadas em W uma vez. Custos futuros dependentes da escolha entram em X; despesas comuns futuras também entram no ledger da política, sem cobrança duplicada por alternativa. q=0 tem negociação zero, podendo carregar despesa futura explicitamente necessária à política. Para a comparação desde antes da pesquisa, contam todas as tentativas de API, inclusive vencidas, conforme o contrato temporal.

Não estimar X(q)=qX(1) quando quantidade altera execução/custo. Um modelo assim simplificado pode existir como comparador identificado. Informação desconhecida sem limite de perda não produz expectativa/log-crescimento identificável: manter `not_evaluable` e q=0, sem substituir por zero ou renormalizar as observações conhecidas.

## Comparadores definidos

Com W>0, definir G(q;p)=Σ_ω p_ω log(1+X(q,ω)/W). Qualquer estado de probabilidade positiva com W+X<=0 atribui G=−∞; termos de probabilidade zero são ignorados sem avaliar log inválido. Custo financeiro usa representação determinística; o método numérico/tolerância do log é versionado. Empates no novo comparador preferem zero, depois menor q e chave causal estável de candidato; nunca posição da lista.

| Política | Definição documental | O que fica em desenvolvimento |
|---|---|---|
| S0 — comparador atual | Preservar o código/hash atual: encontra q* com crescimento positivo, aplica teto floor(q*×α/(1+DD/0,30)) e escolhe entre quantidades elegíveis sob o teto, ou zero | Conferir novamente versão, critérios e tie-break antes de reproduzir; α atual0,25 é experimental |
| S_discrete | Maximizar G em Q_hard, incluindo zero | Distribuição estimada, custos e cenários, sem fração posterior |
| S1 — domínio fracionário discreto | Q_frac={q∈Q_hard: K(q)<=f(DD)R_base}, f(DD)=α/(1+DD/0,30), 0<α<=1; maximizar G diretamente nesse conjunto | α e R_base são selecionados/aprovados antes da confirmação |
| S_robust | Maximizar min_{p∈P} G(q;p) em Q_frac, incluindo zero | Construção e tamanho do conjunto P; sensibilidade à execução e calibração |

S1 atua no conjunto admissível. Não multiplicar G por uma constante positiva: isso não muda seu argmax. Não impor um contrato quando o orçamento fracionário só permite zero. α=1 e DD=0 recuperam Q_hard se K/R_base são os mesmos. A referência de 30% reduz f pela metade nesse ponto; não cria pausa automática. Uma perda recente não ativa aumento de quantidade para recuperação.

O novo protocolo usa S1 versus S0 como comparação primária de dimensionamento. S_discrete e S_robust são comparadores secundários previamente declarados; não escolher o vencedor no teste final. Isso define políticas pesquisáveis, sem substituir a política do aplicativo nesta rodada.

### Construção de P

A alternativa de [Kelly robusto de Sun e Boyd](https://stanford.edu/~boyd/papers/robust_kelly.html) orienta o problema max-min. Aqui, a construção proposta é um envelope convexo de distribuições **conjuntas válidas** sobre Ω: estimativa pontual, variantes de calibração/reajuste obtidas no desenvolvimento e cenários adversos de execução com pesos/limites desenvolvidos antes da confirmação. A definição de Ω e o envelope são congelados no manifesto. Não tomar o produto de intervalos marginais independentes como distribuição válida.

Dimensionar variantes a partir de erros de calibração por regime/cobertura, dependência entre latência e preenchimento, custos por quantidade e resolução temporal. Registrar dados, método e escolhas recusadas. Um envelope de cenários não é automaticamente uma região de confiança com cobertura estatística conhecida. Não afirmar que contém a distribuição real. Sem evidência suficiente, informar sensibilidade e inconclusão; não escolher raio/peso conveniente depois do holdout. Risco de drawdown e crescimento são objetivos diferentes, como explicita a pesquisa de [Kelly com restrição de risco](https://www.web.stanford.edu/~boyd/papers/kelly.html).

## Registro dos parâmetros e riscos

| Parâmetro/unidade | Origem/estado | Escolha e invalidação |
|---|---|---|
| W, posições, fluxos e moeda | Conta manual conciliada; dados operacionais pendentes | Revisão de conta gera decisão nova; fonte/horário e responsabilidade preservados |
| Margem por q, reserva, R_base em dinheiro | Conta documentada e limite de risco pessoal; pendentes | Não inferir da página educativa; mudança recalcula admissibilidade |
| K(q), distribuição/Ω e custos por q | Desenvolvimento com fonte/cobertura/execução identificadas | Nova execução, tarifa, horizonte ou fonte requer revisão no escopo |
| α e referência DD0,30 | α0,25 e DD0,30 são comparadores atuais | Selecionar α em desenvolvimento dentro do domínio declarado; referência preservada sem promessa de ótimo |
| Conjunto P e variantes | Proposta metodológica, tamanho/pesos pendentes | Congelar antes de confirmar; alteração exige outra tentativa |
| Limites de DD, perdas de cauda, precisão e efeito mínimo | Requisitos de risco e planejamento amostral pendentes | Aprovação informada antes do teste; não usar resultados finais para escolher limites |

O registro transversal acrescenta unidade, fonte, vigência, responsável, versão, dados usados e motivo de invalidação. Critérios empíricos estão no [protocolo](06-protocolo.md). Parâmetros faltantes bloqueiam confirmação, não a definição documental.

## Trajetórias próprias e fluxos externos

Cada política π possui W_π,t+1=W_π,t+F_t+X_π,t−D_π,t, com F positivo para aporte e negativo para retirada. X já é líquido das despesas de negociação; D contém apenas despesas da política ainda não incluídas. O calendário de oportunidades e fluxos externos é comum; q e custos de execução podem diferir. Preservar oportunidades nas quais a política não consegue negociar e períodos adversos. Posições abertas consomem seus próprios recursos, sem banca compartilhada artificial entre braços.

Para separar desempenho de aportes/retiradas, usar cota v=W/n, iniciando v0=1 e n0=W0. No fluxo F, n'=n+F/v e W'=W+F; v permanece. Em resultados/despesas, n permanece e v muda. Pico h=max(v histórico), DD=1−v/h e referência monetária H=n h. Um fluxo altera H para H(W+F)/W, não simplesmente H+F se houver drawdown. Exige W>0, cota válida e retirada que não extinga o período; fechamento/recapitalização são eventos próprios. Essa convenção inspirada em [ajustes por fluxos externos](https://www.gipsstandards.org/standards/gips-standards-for-firms/gips-standards-handbook-for-firms/) não afirma conformidade GIPS.

### Fixture cronológica reproduzível

Tudo abaixo é artificial: W0=R$400; margem100q e perda de estresse80q+C(q); C(q)=2q+2q² reais para q>0, C(0)=0. Nesta fixture somente, exigir margem+estresse<=W. Despesas JEV D=0, sem posição entre oportunidades. A escolhe um contrato quando admissível; B escolhe a capacidade. **Não são políticas Kelly nem evidência de rentabilidade.**

| Etapa | Bruto por contrato / fluxo | A: q, X, W após etapa | B: q, X, W após etapa |
|---|---|---|---|
| Inicial | — | —; R$400 | —; R$400 |
| Oportunidade1 | +R$40 | 1; +R$36; R$436 | 2; +R$68; R$468 |
| Aporte | +R$200 | W=R$636, PnL=0 | W=R$668, PnL=0 |
| Oportunidade2 | −R$80 | 1; −R$84; R$552 | 3; −R$264; R$404 |
| Retirada | −R$100 | W=R$452, PnL=0 | W=R$304, PnL=0 |
| Oportunidade3 | +R$30 | 1; +R$26; R$478 | 1; +R$26; R$330 |
| Oportunidade4 | −R$30 | 1; −R$34; R$444 | 1; −R$34; R$296 |

PnL A=−56 e B=−204; W_final=400+200−100+PnL. DD após oportunidade2: A13,2075% e B39,5210%; retirada mantém esses valores. DD final máximo: A14,7437% e B41,1125%. Retorno da cota final: A−7,0706% e B−31,1016%. B perde capacidade após sua própria perda, sem alterar a banca de A.

Na mesma restrição artificial, capacidades para W400/800/600 são 2/4/3. Aplicar somente o teto atual com α0,25/DD0 a q*=2/4/3 produz 0/1/0. Isso ilustra arredondamento **se** esses q* fossem escolhidos pelo critério; capacidade não prova que sejam ótimos. O motor atual não aceita o antigo registro da sonda, conforme a pesquisa. Com W180, q=1 exige184; Q_hard={0}. Não forçar entrada.

## Aceite e resultado possível

Os cinco aceites documentais estão definidos: objetivos/domínios, distribuição conjunta/incerteza, registro de parâmetros/risco, trajetória com fluxos e critérios de confirmação. A aritmética da fixture foi conferida em Python com Decimal, em memória e sem importar o motor: capacidades, quantidades, PnL, patrimônio, retorno por cota e drawdown reproduziram a tabela. Isso não testa o aplicativo. A implementação deverá testar custos não lineares, cauda com saldo<=0, domínio só-zero, insumos ausentes e ausência de progressão por perda.

Reportar crescimento líquido por cota, PnL, drawdown desde o pico, duração/recuperação, perdas de cauda, saldo não positivo e incapacidade de lote mínimo. Resultado favorável exige efeito, precisão, custos e limites de risco predefinidos; desfavorável e inconclusivo são resultados válidos. Incerteza ampla ou nenhum q com utilidade demonstrável mantém zero. Essa conclusão documental não autoriza uso financeiro da política.
