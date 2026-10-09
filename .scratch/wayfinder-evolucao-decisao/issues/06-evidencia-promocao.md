# Evidência incremental e promoção

ID: WF-06
Type: research
Label: wayfinder:research
Status: resolved
Parent: [Mapa](../map.md)
Created: 2026-10-07
Blocked by: 01, 02, 03, 04

## Question

Como demonstrar separadamente se o JEV melhora previsão, seleção ou dimensionamento, sem escolher os parâmetros no mesmo período que será usado para confirmar o resultado?

## Alternativas

| Alternativa | Consequência |
|---|---|
| Comparar um sistema novo completo com o anterior | Mede a diferença total, mas não identifica sua origem e mistura versões. |
| Ajustar perguntas e políticas no teste final até melhorar | Facilita encontrar um resultado favorável; invalida sua interpretação confirmatória. |
| Protocolo temporal congelado com braços pareados e ablações | Permite atribuir ganhos e perdas; exige dados, registro de tentativas e confirmação independente. |

## Evidência

O laboratório já oferece baseline logística, features contextuais, divisões temporais, trajetórias e comparação entre políticas. Sua existência não comprova execução real, edge ou generalização. O gate do motor já exige metadados além de `validated=true`; a suficiência desses metadados permanece uma questão documental e empírica.

O cookbook de [descoberta de atributos TypeSafe](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery) demonstra um fluxo para propor e testar atributos semânticos. Seus resultados em outro dataset não provam benefício no WIN.

[Cawley e Talbot](https://www.jmlr.org/papers/v11/cawley10a.html) mostram que a seleção de modelos pode sobreajustar o próprio critério de avaliação. Isso justifica separar desenvolvimento e confirmação também para perguntas, features, cadência e política.

## Direção recomendada

Fechar e versionar o protocolo antes de consumir o período confirmatório. Registrar todas as tentativas, inclusive as descartadas.

### Braços e atribuição do efeito

| Comparação | Manter igual | Efeito investigado |
|---|---|---|
| A: quantitativo sem JEV versus B: quantitativo com atributos JEV congelados | Oportunidades, dados disponíveis, família logística, rótulo, método de calibração e orçamento de ajuste comparável | Ganho ou perda de previsão. |
| Seleção determinística versus C: seleção tipada JEV entre os mesmos candidatos admissíveis | Estimativas financeiras de B, conjunto candidato, restrições, custos, horizonte e quantidade fixa de estudo | Ganho ou perda de seleção. |
| Políticas de quantidade sobre as mesmas oportunidades e seleção | Modelo, selecionador, cadência e hipóteses de execução | Ganho ou perda de dimensionamento, com patrimônio próprio de cada política. |

O “igual” se refere ao desenho e às regras; coeficientes das regressões podem diferir porque B tem atributos adicionais. A seleção tipada não altera regras financeiras nem cria candidatos fora do conjunto admissível. A quantidade fixa é exclusivamente um controle do estudo, sujeito à admissibilidade; não é um mínimo imposto no produto.

Preservar a baseline logística. Regras existentes podem ser um braço diagnóstico. Consultar JEV somente em ambiguidades e comparar gatilhos de consulta são fatores adicionais a testar separadamente, evitando atribuir à previsão o efeito de custo ou latência.

Fixar o gerador de oportunidades e candidatos antes da comparação. Registrar seus limites e cobertura: um selecionador não recupera cenários que o gerador não ofereceu. Candidatos simultâneos, respostas repetidas e horizontes sobrepostos pertencem a episódios identificados, não a amostras independentes artificiais.

### Separação temporal e parâmetros

Definir desenvolvimento, seleção/calibração e confirmação futura intocada por datas e sessões. Aplicar maturidade dos rótulos e exclusão de sobreposição de horizontes. Ajustes sucessivos usam divisões internas ao desenvolvimento; o teste final não escolhe perguntas, fração de Kelly, limiares ou features.

Congelar dataset e regras de correção, cobertura, catálogo, perguntas/opções, modelo JEV, gerador, features, baseline, calibrador, horizonte, cadência, regra de execução, custos e políticas. Modelo retornado diferente do solicitado deve seguir regra prévia de incompatibilidade.

Definir número de sessões e precisão desejada a partir da unidade efetiva de comparação, dependência temporal e frequência de oportunidades. Não adotar cinco sessões ou qualquer número mecânico do código como tamanho suficiente para provar edge. Dados e orçamento seguem pendentes; ausência não é autorização de chamada paga.

### Métricas e critérios

- Previsão: Brier, log loss e calibração para um evento financeiro definido, com contagens, maturidade e cobertura. Não avaliar apoio contextual como probabilidade de lucro.
- Seleção: resultado líquido pareado por oportunidade e por período, incluindo espera, ausência de entrada, descarte e desconhecido.
- Dimensionamento: crescimento líquido cronológico, drawdown a partir do pico, recuperação, perdas de cauda, saldo não positivo e incapacidade de admitir o lote mínimo.
- Utilidade: preenchimento, cobertura, latência, respostas vencidas, oportunidades perdidas, despesas de API e custo total conforme o contrato temporal.

Usar as mesmas oportunidades e diferenças pareadas. Intervalos devem preservar dependência entre episódios/sessões, com método e limitações predefinidos. Não excluir períodos adversos, desconexões ou casos desconhecidos por tornarem o resultado menos favorável.

Apresentar benefício junto de risco, custos e cobertura. Critérios de resultado favorável, desfavorável ou inconclusivo serão declarados antes da confirmação, incluindo quando o intervalo e a cobertura não permitem concluir. Uma melhoria estrutural pode estar demonstrada enquanto o benefício financeiro permanece inconclusivo.

### Registro de validação e promoção

Substituir a interpretação de um booleano isolado por um registro verificável: identidade/hash dos dados, direito de uso e cobertura; datas/divisões; versões congeladas; regras de disponibilidade, custos e execução; tentativas; comparadores; métricas e incerteza; limitações; cenário validado; vigência e condições de invalidação.

Separar estado de evidência, aprovação de uso no escopo e autorização operacional. Metadados como `deployment_approved` não concedem permissão para ordens. Um registro sintético jamais é promovido por alterar uma flag.

A evidência aplica-se ao conjunto validado de fonte, conta/custos, modelo, política, horizonte e execução. Alteração material exige revisão, conforme uma matriz previamente definida. Implementação correta, prognóstico melhor e crescimento líquido melhor são conclusões diferentes.

## Dependências e escopo

Depende da definição da [identidade causal](01-identidade-causal.md), dos [contratos JEV](02-contratos-hipoteses.md), do [replay de execução](03-latencia-execucao.md) e dos [comparadores de dimensionamento](04-dimensionamento-incerto.md).

Essas dependências são documentais: o protocolo deve estar resolvido antes de rodar a confirmação econômica dos tickets anteriores. Assim não há exigência circular de resultado econômico para definir o protocolo.

Estende E02–E10, com requisitos de fonte E01; os IDs e os status dos experimentos existentes são preservados.

## Critérios de aceite — próxima etapa

Entregar protocolo datado com braços, unidade de análise, divisões temporais, parâmetros congelados, métricas, método de incerteza, critérios de resultado, registro de tentativas e gates de promoção. Campos ainda sem dados ou orçamento devem estar explicitamente pendentes; não marcar o protocolo como pronto para confirmação enquanto forem indispensáveis.

### Cenários de verificação futura

| Caso | Resultado exigido |
|---|---|
| Respostas repetidas do mesmo episódio | Sem aumento da amostra financeira. |
| Modelo B melhora Brier, mas perde após custos | Resultado de previsão e resultado econômico registrados separadamente. |
| Seleção C altera quantidade ou candidato elegível | Violação do desenho identificada, sem atribuição artificial de ganho de seleção. |
| Política A ganha cedo e política B perde | Patrimônios próprios preservados até o fim. |
| Prompt alterado depois de consultar confirmação | Nova tentativa e contaminação do teste registradas; sem confirmação válida no mesmo holdout. |
| Casos desconhecidos ou cobertura perdida | Denominador e massa desconhecida visíveis, sem remoção favorável. |
| Flag de validação verdadeira sem registro suficiente | Evidência insuficiente no escopo, sem promoção automática. |
| Resultado desfavorável ou intervalo inconclusivo | Resultado preservado; não renomear como melhoria comprovada. |
| Modelo, fonte ou custo muda após o estudo | Revisão de validade pelo contrato, com histórico preservado. |

## Comments

2026-10-07 — Reivindicado com WF-01–04 resolvidos; braços, incerteza, critérios e gates em fechamento documental, antes de qualquer confirmação.

2026-10-07 — Desenho proposto e pendências explicitados. Nenhum experimento confirmatório foi executado e nenhum modelo financeiro foi promovido por esta entrega.

2026-10-07 — Resolvido após revisão somente leitura de WF-04/05/06. Acrescentadas regras de término sem resposta em H3, classificação exaustiva dos resultados e tratamento de réplicas com saldo não positivo. Ver [auditoria de aceite](../acceptance-audit.md).

## Answer

Adotado o [protocolo incremental-evidence-v1](../contracts/06-protocolo.md), com H1 previsão, H2 utilidade líquida dos atributos, H3 seleção no mesmo instante causal e H4 S1 versus S0 com patrimônios próprios. O alvo financeiro futuro tem versão/modelo próprios; o diagnóstico stop/alvo/horizonte existente permanece separado. O manifesto, divisões temporais, métricas, bootstrap pareado, multiplicidade, ledger e gates estão especificados.

O contrato trata espera sem resposta, custo de tentativas, massa desconhecida, saldo não positivo e resultados inválidos, desfavoráveis, favoráveis ou inconclusivos sem promover sobreviventes selecionados. Datas, direitos dos dados, custos da conta, orçamento, precisão/efeito e limites de risco são pendências indispensáveis de G1: o desenho está resolvido, mas não está pronto para confirmação. Nenhum experimento ou chamada paga foi executado; nenhuma rentabilidade ou autorização operacional foi demonstrada.
