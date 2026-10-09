# Laboratório de dados multimercado

O observador adicional usa BTCUSDT spot público. O fluxo WIN/Excel e o capital manual permanecem separados. O laboratório não envia ordens; a meta R$400 → R$4.000 continua uma hipótese sem probabilidade estimada.

## Uso local

O ambiente base e a CLI offline não precisam de conta, API key ou biblioteca WebSocket.

```powershell
.\.venv\Scripts\python.exe .\scripts\observe_multimarket.py
```

Esse comando usa três execuções sintéticas, com origem explícita, e imprime saúde e pendências. Nenhum negócio real é capturado.

Para transporte público opcional, instale a dependência no ambiente utilizado pelo motor:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\app\requirements-market-data.txt
.\.venv\Scripts\python.exe .\scripts\observe_multimarket.py --live --duration-seconds 60
```

Live exige a flag, dura no máximo 1800 segundos e não grava payloads. O diagnóstico imprime contadores e saúde; preços e quantidades não entram no log. Resposta bloqueada ou erro permanente encerra a sessão sem trocar host, conta ou localização. O diagnóstico `shutdown` deve confirmar o encerramento. Se uma requisição ainda estiver terminando, o painel indica esse estado e bloqueia nova coleta até o transporte encerrar.

No desktop, a seção **Mercados** oferece iniciar, encerrar e carregar a fixture sintética. Toda abertura começa com captura desligada. Livro inválido ou vencido fica indisponível; volume por preço usa somente execuções únicas recebidas, em quantidade base e valor cotado. Cobertura permanece parcial.

A dependência é opcional e não foi acrescentada automaticamente ao instalador empacotado. Validar um ambiente de desenvolvimento não certifica o instalador Tauri ou a integração Profit Pro.

## Interfaces para a próxima etapa

- `market_data_contract.py`: instrumentos, envelopes, negócio individual, livro e saúde.
- `public_crypto_feed.py`: catálogo, sincronização do livro e worker público com transportes injetáveis.
- `market_replay.py`: journal/replay com hashes, retenção desativada por padrão e volume por preço.
- `multimarket_context.py`: contexto puro e limitado, sem chamada JEV por tick.
- `multimarket_economics.py`: cenários de payoff, gates e protocolo de avaliação; custos ou risco ausentes mantêm aguardar com quantidade zero.

O gate de retenção não equivale a autorização de armazenamento. A interface desta entrega não habilita gravação real. Direitos, jurisdição, acesso a derivativos, API esportiva, binárias, custos vigentes e dados fora da amostra continuam dependências documentadas no plano.

O próximo avanço econômico depende de dados representativos e protocolo temporal. `confidence` contextual do JEV não fornece chance de lucro, de atingir a meta ou de ruína.
