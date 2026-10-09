# Vocabulário multimercado proposto

Status: proposed
Date: 2026-10-09

Complemento candidato ao CONTEXT.md existente, que foi preservado. Termos não contêm decisões de implementação. Resolver no [ticket de instrumento](issues/05-identidade-instrumento.md) e incorporar ao glossário somente após resolução; WIN atual não foi renomeado nem migrado.

## Language

**Instrumento negociável**:
Produto identificável de um mercado e local de negociação, com unidade, moeda e condições próprias. Dois instrumentos com ticker semelhante podem ter livros e riscos distintos.
_Avoid_: ticker global, ativo genérico.

**Local de negociação**:
Bolsa ou exchange onde o instrumento e os eventos correspondentes existem. Um agregado entre locais não representa o livro de nenhum deles.
_Avoid_: fonte, corretora como sinônimo universal.

**Fonte de evidência**:
Origem identificada dos fatos disponíveis para uma avaliação, incluindo suas limitações e permissões de uso. A fonte pode entregar somente parte do mercado.
_Avoid_: mercado completo, prova de integralidade.

**Continuidade observada**:
Condição de uma captura no intervalo e canal para os quais perdas puderam ser detectadas e tratadas. Não prova histórico integral nem ausência universal de perdas.
_Avoid_: full tape por conexão, timestamps ordenados como prova.

**Conta conciliada**:
Conta cujos saldos, posições e registros correspondem às fontes e ao instante exigidos pela avaliação. Ser conectada não torna a conta conciliada.
_Avoid_: conta inferida, saldo presumido.

**Escopo de validade financeira**:
Conjunto de condições de mercado, instrumento, horizonte, execução e custos para os quais uma estimativa recebeu evidência e avaliação próprias.
_Avoid_: confiança contextual, modelo aprovado para qualquer ativo.
