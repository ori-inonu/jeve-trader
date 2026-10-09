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

## Revisão e segundo ensaio

As duas revisões independentes de `907beb3` reprovaram o candidato: clocks eram registrados ao processar a fila, duplicatas renovavam freshness e faltava regressão explícita Book → VAP. Um único implementador corrigiu esses achados com testes que falharam antes da alteração. O candidato `91df26b623c6262fa5f62a94588d249ca0ea74e6` passou 341 testes em 11,681 s e self-test offline em 0,483 s, novamente com sockets bloqueados. Isso ainda não constitui aprovação independente das correções.

O segundo ensaio público de 20 s nesse candidato recebeu 772 execuções e registrou duas ressincronizações, mas terminou com livro inválido e shutdown `stopping/stop_timeout_close_alive`. O [diagnóstico sanitizado 02](multimercado-smoke-publico-02-2026-10-09.json) preserva o resultado reprovado. A fonte instalada `websocket-client 1.9.2` mostra `close(timeout=3)`; o wrapper não fornecia timeout, enquanto o stop esperava 1,8 s. Fechamento e sincronização estão sendo reproduzidos pelo mesmo implementador. Não há nova certificação live.

## Correções e terceiro ensaio

Em `f761644a7f19dccf40dfa6ed277ba6fb117651b3`, o implementador demonstrou dois novos testes RED: wrapper esperava timeout 3 em vez de 0; delta `[2,3]` recebido durante REST com snapshot `S=2` causava uma segunda consulta indevida. Após correção, ambos passaram, sem alterar `U <= S <= u`. O wrapper real da dependência foi exercitado com socket falso e sem rede.

Integração fixa `09e7b3090106cd1cabccef4327f541fca55f0354`: `python -E -s -B scripts/verify.py` passou 343 testes em 11,211 s e self-test em 0,503 s com sockets bloqueados. Terceiro ensaio público de 20 s recebeu 147 execuções, uma ressincronização e terminou com `websocket_transport_error`, livro inválido. Shutdown chegou a `off/stopped`, com todos os helpers encerrados. O [diagnóstico 03](multimercado-smoke-publico-03-2026-10-09.json) preserva a reprovação da coleta e a confirmação limitada do fechamento.

A hipótese genérica de comprovar coleta saudável com esses ensaios curtos falhou em três candidatos distintos e não será repetida sem causa nova demonstrada. O erro de transporte requer diagnóstico separado; disponibilidade, livro sincronizado e operação sustentada continuam pendentes.

## Correção do motivo de fechamento

Revisões isoladas do candidato `52464af` passaram 343 testes e self-test, mas reprovaram dois P2: status canônico desatualizado e `recv()` após fechamento intencional substituindo o motivo por `websocket_transport_error`. O revisor Spec reproduziu `stopped` com todos os helpers encerrados e uma razão falsa; o implementador reproduziu também o mesmo mascaramento de `sequence_gap` durante recuperação. Ambos usaram somente fakes, sem rede.

No commit `280580fa975c88d5d99cc5999fbee1396dddccf5`, duas novas regressões falharam antes e passaram após a correção: a recuperação preserva `sequence_gap` e a parada solicitada preserva `stopped`. O teste de falha remota genuína continua expondo `websocket_transport_error`. O fechamento local marca a conexão como encerrada antes de chamar o transporte e o reader não cria erro para uma conexão que já está sendo fechada. Invalidação do livro, limites de helpers e a política `U <= S <= u` permanecem exigidos.

Integração `41230ae81b434e30b197f78ea715b0c7cdd5c6df`: o integrador executou `python -E -s -B scripts/verify.py` no Windows e passou 345 testes em 12,654 s e self-test em 0,866 s, com sockets Python bloqueados. Nenhum quarto ensaio público foi realizado. A correção de diagnóstico não comprova a causa do livro inválido no terceiro ensaio nem a estabilidade live; nova revisão independente está pendente.

## Limites atuais

Coleta real, duração prolongada, reconexão real, direitos de retenção, produto/jurisdição, custos atuais e avaliação financeira fora da amostra permanecem pendentes. AC-07 global não será marcado concluído a partir de fixtures. Nenhum preço ou payload real entra no repositório.
