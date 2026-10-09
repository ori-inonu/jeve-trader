# Expansão — contas e protocolo econômico

Data: 2026-10-09. Cálculos locais reproduzíveis, não resultados de estratégia. As fórmulas não atribuem probabilidade de lucro ao JEV e não recomendam operações. Critério: AM-03. Valores de payout, taxa, odds, stop e participação da banca abaixo são hipóteses didáticas, não condições vigentes.

## Meta de R$400 para R$4.000

Fator final = 4.000/400 = **10**; lucro líquido necessário = R$3.600, retorno líquido de **900%**. Com crescimento constante composto, antes de diferenças de calendário, `r = 10^(1/n) - 1`:

| Horizonte ilustrativo | Crescimento líquido composto necessário por período |
|---|---:|
| 5 sessões | 58,489319% por sessão |
| 7 dias | 38,949549% por dia |

“Menos de uma semana” exige prazo menor que sete dias; sete é apenas referência, não simplificação do pedido. Custos, spreads, derrapagem, dias sem oportunidade, perdas e retiradas tornam mais difícil a trajetória. Esses percentuais descrevem a meta; não demonstram que um mercado a permita com probabilidade aceitável.

## Payoff e vantagem são perguntas diferentes

**Futuro B3:** `PnL bruto = direção × contratos × variação_em_pontos × valor_do_ponto`. No WIN, a especificação oficial usa R$0,20 por ponto por contrato; um movimento de 1.000 pontos equivale a R$200 brutos por contrato, favorável ou desfavorável. Não confundir margem com perda máxima, nem usar a margem exemplar do código como vigente. A ordem de stop não garante preço em gap. Fonte: [especificação B3 WIN](https://www.b3.com.br/lumis/portal/file/fileDownload.jsp?fileId=8A828D2951C9C377015221CF257F5253), consulta 2026-10-09.

**Spot e derivativos cripto:** spot comprado sem crédito varia com o ativo, descontados custos. Em uma posição linear, exposição nocional/capital pode aproximar a sensibilidade `L × retorno_do_ativo`; contratos inversos e mecanismos de liquidação exigem fórmula específica. Um anúncio de L elevado não define ganho máximo realizável, edge, acesso brasileiro ou perda admissível. Financiamento/funding, mark, collateral e manutenção precisam ser observados; a API spot não fornece uma licença de operar perpétuos.

**Binária com ganho líquido `b` por real apostado:** com perda integral do stake na derrota e sem empates/custos, `E[resultado]/stake = p × b − (1−p)`; o ponto de equilíbrio é `p* = 1/(1+b)`. Para ganho líquido hipotético de 80%, `p* = 55,555556%`, antes de custo. O retorno do stake vencedor é `1+b`; chamar retorno total de 180% de “lucro de 180%” distorceria a conta. Mudanças de payout, atraso, strike, regras de expiração/anulação e preço da plataforma alteram o modelo. A direção futura da cotação e o payoff negociado são variáveis separadas.

Uma sequência ideal sem derrota, com fração constante `f` da banca apostada, multiplica por `(1+b f)^k`. Para `b=.8`, seriam pelo menos 30 vitórias sem perda com `f=.10`, ou 146 com `f=.02`, para atingir 10×. São limites algébricos sob hipóteses artificiais, não planos de aposta. Arriscar toda a banca poderia multiplicar por `1.8^4 = 10,4976` em quatro vitórias, mas uma única derrota zera a banca neste modelo: esse é um contraexemplo ao ranking por “velocidade da alavancagem”. Não há p real disponível para calcular a chance dessa sequência.

**Exchange esportiva:** um back de stake `s` e odds decimais `o` ganha `s(o−1)` se vencer e perde `s` se perder. Um lay com stake `s` arrisca responsabilidade `s(o−1)`; o stake exibido não é a perda máxima. Exemplo hipotético: lay de R$100 a odds 5 envolve R$400 de responsabilidade. Odds não oferecem multiplicador livre com chance de vitória invariável.

Se, por simplificação, comissão `c` incidir apenas no lucro daquela única aposta vencedora, back tem `E/s = p(o−1)(1−c) − (1−p)` e `p* = 1/[1+(o−1)(1−c)]`. A cobrança real pode incidir no resultado líquido do mercado e depende das regras da conta; não generalizar essa fórmula a posições combinadas. `1/o` é probabilidade implícita do preço; odds de casas incorporam margem, exchange incorpora spreads/comissão/liquidez. Isso não é probabilidade verdadeira/calibrada. Trading com entrada/saída exige preço executável dos dois lados, delay, suspensões e liquidação, não apenas resultado final do evento. Fontes/rules nas [notas de cripto e esportes](Expansao_Mercados_Cripto_Esportes_2026-10-09.md).

## Como comparar sem inventar rentabilidade

1. **Gate de dados:** instrumento, fonte, granulação, histórico, cobertura e atraso conhecidos; snapshots limitados não sustentam estratégia que exige tape integral. Calcular VAP apenas de negócios válidos da janela. Odds históricas de resultado final não reproduzem book ao vivo.
2. **Gate de produto/acesso:** entidade e modalidade acessíveis no Brasil, termos e licenças aceitos; mercado apenas tecnicamente consultável pode ficar fora da avaliação operacional. Autorização de uma marca não prova que todo produto/API seja oferecido.
3. **Payoff e execução:** contratos locais por família, horários, mínimos, moeda/câmbio e taxas datadas. Backtest deve usar spread, profundidade, execução parcial, atraso, suspensões, funding/comissões e regras de settlement aplicáveis. Dados insuficientes resultam em não avaliável.
4. **Validação estatística:** treinar/selecionar em blocos passados e avaliar em período posterior separado; purgar sobreposição de labels quando relevante; reportar calibração/Brier ou log loss para probabilidades, cobertura e desempenho líquido. Não selecionar mercado/estratégia no mesmo período chamado de teste. Registrar todas as alternativas e correção da seleção múltipla.
5. **Simulação de banca:** comparar aguardar e quantidades/stakes admissíveis, reinvestimento e perdas cumulativas com política fixa. Estimar, se houver dados suficientes, distribuição do capital final, probabilidade de alcançar R$4.000 antes do prazo, perda integral ou limite, drawdown, perda de cauda e utilidade/crescimento log. Reamostragem em blocos respeita dependência temporal; mudanças de regime/execução não desaparecem com mais simulações.
6. **Piloto prospectivo de observação:** congelar estratégia e protocolo, registrar oportunidades e preços disponíveis em tempo real sem execução. Resultado em replay e em observação são diferentes de lucro realizado. Só depois é possível propor estudo operacional em escopo próprio.

O orçamento de perda tolerável, despesas autorizadas e mandato operacional pertencem ao usuário e não foram definidos. Isso não impede pesquisa/coleta; impede afirmar que uma alternativa econômica é aceitável para a pessoa. Hoje `P(meta)`, taxa de acerto real, capital operacional admissível e rentabilidade esperada permanecem **desconhecidos** para todos os mercados investigados. O estudo da CVM/FGV sobre day trade é referência empírica externa e não prova resultados de um futuro sistema: [material educativo CVM](https://www.gov.br/cvm/pt-br/assuntos/noticias/2020/educacao-financeira-em-pauta--cvm-lanca-materiais-educativos-sobre-day-trade-e-funcionamento-da-bolsa-de-valores-5221f3b6650040a084fd7e3554ad9807), consulta 2026-10-09.

## Reprodutibilidade

As fórmulas e números acima são verificáveis sem dados privados ou chamadas JEV. Precisão financeira na implementação futura deve ser Decimal; potências/logaritmos deste cenário são aproximações numéricas de planejamento. A evidência local registra código de verificação, resultados e plataforma; não confundir precisão aritmética com validade das hipóteses econômicas.
