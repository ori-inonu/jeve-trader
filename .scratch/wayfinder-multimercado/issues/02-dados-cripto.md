# Dados cripto públicos: trades, livro, sincronização e limites

Type: research
Label: wayfinder:research
Status: resolved
Assignee: crypto-research
Blocked by:

## Question

Quais APIs oficiais públicas de cripto oferecem trades e livro ao vivo, e como reconstruir continuidade com snapshots, sequência, reconexão e rate limits? Quais diferenças impedem tratar spot e derivativos como WIN? Não cadastrar conta, usar credenciais ou enviar ordens.

## Answer

Binance Spot e Coinbase Advanced Trade documentam negócios e livro públicos, separados de conta/execução. O contrato precisa preservar negócios individuais versus agregados, significado maker/taker, quantidades absolutas, aliases, base/quote, filtros decimais e limites por canal. Snapshot/livro sincronizado não certifica tape completo. Há divergências documentais sobre sequência Coinbase por produto/conexão e a fronteira inicial Binance `U=L+1`; o piloto deve resolvê-las antes de afirmar continuidade.

O [relatório primário](../../../docs/research/Cripto_Streaming_Contratos_2026-10-09.md) reúne fontes fixadas/URLs, hashes e aceites candidatos. Streaming e disponibilidade regional no Brasil não foram exercitados. Custos de conta não foram consultados; desconhecido não é zero. Derivativos permanecem fora do piloto proposto e exigem contrato próprio. As lacunas seguem na [prontidão dos contratos](11-prontidao-contratos.md).

## Comments

2026-10-09: pesquisa autorizada na rodada de charting, saída isolada.
