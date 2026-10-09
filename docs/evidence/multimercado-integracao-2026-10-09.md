# Integração multimercado — evidência em andamento

Baseline independente: `da96c6ad4187030a98c4daa86a6b96e1e5b809a9`.
SPEC congelada: `7e8d20347360bfa6423b00208f8acdb03565b8d0f3a69118dfadbd3b41200612`.
Plataforma: Windows, Python 3.14.7 no ambiente isolado criado para a integração; Node e Vite locais. A versão foi confirmada pelo executável, não inferida do nome do ambiente.

## Ciclo público red/green do integrador

- Antes da integração, `python -m unittest test_multimarket_service -v` executou três testes e falhou com `TypeError: DecisionService.__init__() got an unexpected keyword argument 'multimarket_factory'`.
- Antes da CLI, `python -m unittest test_multimarket_cli -v` falhou no caso offline com `[Errno 2] No such file or directory` para `scripts/observe_multimarket.py`. A checagem de duração isolada ainda não certificava comportamento, pois o script não existia.
- Candidato integrado `907beb3365c8760b7214fd3af22f2f41d5269e9a`: `python scripts/verify.py` passou 337 testes em 12,586 s e self-test do serviço em 0,708 s; auditoria de sockets bloqueou conexão, DNS e sendto. Relatório original está em `.artifacts/verification.json` (ignorado), sem rede JEV/Profit/ordens ou certificação de GUI.
- Uma regressão adicional demonstrou `off` em vez de `stopping` ao encerrar com REST ainda ativo. Após a correção, os três testes do observador passaram: a referência ao transporte continua própria, livro/contexto são removidos e novo start/fixture permanece bloqueado até a requisição terminar. CLI expõe diagnóstico de shutdown sem payload financeiro.
- Ensaio das seams com módulos das frentes em andamento revelou filtro de catálogo `status=TRADING` ausente na fixture e codificação CP1252 na saída CLI Windows. Ambos foram corrigidos. A quantidade agregada é comparada como Decimal exato; zeros finais não alteram o valor. Este ensaio não substitui a verificação do candidato integrado e fixo.

## Interface

`npm run check`, `npm test` e `npm run build` passaram no checkout isolado. Suíte Node: 15 testes, zero falhas. Build Vite: 2167 módulos, concluído; aviso de bundle maior que 500 kB preservado. Os dois novos testes verificam que livro inválido/vencido não aparece como atual e que probabilidade ausente permanece desconhecida.

Dependências Node foram reutilizadas por junction local somente leitura para a pasta de dependências existente. Nenhum pacote, lockfile ou configuração do checkout principal foi alterado.

Verificação visual: navegador Codex no Windows, prévia Vite própria na porta 16422 e sidecar Python real com diretório de dados privado fora do repo. Painel começou desligado; fixture produziu 3 execuções, book synthetic 99/101, VAP 0,05 a 99 e 0,3 a 100, cobertura parcial e probabilidade não estimada. Screenshot privado SHA256 `13d26949f6ceb626b6017b055bcb20685dfe470a3fa3d34f2b65bbf079dfdc3d`; prévia/tab encerrados após inspeção. Porta inicial 1422 já ocupada; nenhum processo alheio foi encerrado. Build e teste em navegador não certificam janela/instalador Tauri.

## Ensaio público curto

No candidato `907beb3`, a CLI explícita com `--live --duration-seconds 20` recebeu 7 execuções e retornou 1. Livro permaneceu inválido e os canais desconectados/vencidos; razão `websocket_close_timeout`. Shutdown terminou `off`, sem worker, reader ou REST ativos. O [diagnóstico sanitizado](multimercado-smoke-publico-2026-10-09.json) conserva contadores e saúde sem preços/quantidades/payloads. A falha está em investigação pelo proprietário do coletor; não foi ocultada nem promovida a integração saudável. Nenhum piloto prolongado ou recuperação real ficou certificado.

## Limites de conclusão

Coleta real, duração prolongada, reconexão real, direitos de retenção, produto/jurisdição, custos atuais e avaliação financeira fora da amostra permanecem pendentes. AC-07 global não será marcado concluído a partir de fixtures. Nenhum preço ou payload real entra no repositório.
