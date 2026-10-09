# EN-T1–T3 — implementação local

Objetivo autorizado: continuar as próximas etapas de Jeve Trader, com decisões técnicas delegadas ao JEV, a partir das especificações existentes. Entrega finita: implementar EN-01–EN-04 sem promover evidência local a instalação, janela nativa ou ganho humano.

Baseline: commit `385e79119b75bb8ea0277e3b0cfcb1656f443fba`, árvore `c9c06f1c99e7be9ccdee910affb5f0c795c2dae3`. SPEC imutável: `docs/specs/Instrumentacao_Protocolo_Multimercado_2026-10-09.md`, SHA-256 `9e6d06ed4ea275981bdcf8c0d4d26e568b3ff79d9f9be20482feb06e77565e26`. Prontidão independente: `docs/evidence/rt12-next-spec-readiness-final.md`; nova revisão de escopo será preservada em `docs/evidence/en-scope-review-2026-10-09.md`.

## Recuperação e decisões

O Git não reconhece mais os checkouts primário e de integração anterior: no primeiro falta `.git/HEAD`; no segundo falta metadata do worktree apontado. Causa desconhecida. Esses arquivos não foram alterados nem usados para reconstruir histórico. Esta tarefa usa clone novo fora do OneDrive, com estado SDD novo e identidade desta conversa. O JEV recomendou a recuperação isolada (`docs/evidence/en-stage-jev-2026-10-09.json`). A consulta de prioridade se absteve; a elegibilidade de T1–T3 vem da SPEC pronta e revisão independente, não dessa abstenção.

Decisões técnicas executadas: `docs/evidence/en-technical-jev-2026-10-09.json`, `approved_by=jev_delegated`. Interfaces públicas com arquivos temporários e relógios injetados; origem Git capturada uma vez antes do build e compartilhada com Vite; hashes de pacote no renderer permanecem null sem conferência real; manifest portátil fechado e recibo externo com hash do instalador quando presente. PR própria sobre `codex/multimarket-spec`; `main` recebeu arquitetura diferente via PR #1, commit observado `e64226ca76c622b08573c812efc433dc9b30beb2`. Não misturar automaticamente as linhas.

O pacote CPython/Tk gerado por `app/build_windows.ps1`/`app/packaging/build_installer.py` é legado, não contém o cockpit Tauri/sidecar separado e fica fora do conjunto de pacotes elegíveis EN. Seu manifesto existente não passa a ser certificado por este incremento. O contrato EN aplica-se ao builder `desktop/build-windows.ps1`.

## Grafo e propriedade

| Ticket | Dependência | Escritor isolado / arquivos exclusivos | Verificação |
|---|---|---|---|
| EN-T1 | SPEC ready | implementer pacote: `scripts/en_contracts.py`, `scripts/en_package.py`, `app/test_en_package.py`, `desktop/build-windows.ps1` | RED/GREEN CLI/API: ausência, adulteração, escape, links, duplicatas, dirty, origem e instalador externo; parser PowerShell |
| EN-T3 | contrato público T1 definido; integração após T1 | implementer protocolo: `scripts/en_protocol.py`, `app/test_en_protocol.py` | RED/GREEN arquivos hash-bound, run/task/events/stages/comparison fechados; ausência de evidência, origem, prospectividade e ganho null |
| EN-T2 | forma origin T1 fixa | implementer renderer: `desktop/src/enTelemetry.ts`, `desktop/src/EnTelemetryCommit.tsx`, `desktop/tests/en-telemetry.test.mjs`, componente cockpit | RED/GREEN receive/commit/export, sanitização, schema fechado, buffer, relógios, substituição e RAF |
| EN-INTEGRATE | T1/T2/T3 commits | merger exclusivo: raiz/transporte/Vite e demais seams compartilhados; root somente docs/estado/evidência | Python offline, frontend test/build, origem build única, comando sem dupla receipt |
| EN-REVIEW | candidato fixo e checks | reviewer independente em checkout isolado | cobertura EN-01–04 e riscos reais; correções em um implementer separado |

Interfaces acordadas: `en_contracts` fornece limites, `ValidationError`, validação fechada de origin e leitura JSON estrita; `en_package` gera/verifica manifest e devolve origin completa, com CLI. `en_protocol` aceita diretório/mapa explícito de evidência local e confere bytes SHA-256, sem resolução remota; ganho literal null. Collector T2 recebe snapshots, guarda receipt crescente, marca o commit da mesma receipt/identidade/época/sequence e exporta envelope validado; `useLayoutEffect` registra commit real. Nenhum teste chama API paga.

## Gates preservados

TTLs quote 5 s, trades 30 s, book 2 s, conta 60 s; contexto vencido continua rejeitado. Conexão explícita, JEV OFF inicial, ordens OFF, L1/parcial, WAIT/q=0 permanecem. Captura Git não infere hashes de binários nem certifica package origin no renderer. EN-T4 exige observação Windows e ponte J6 demonstrada; EN-T5 exige B finito e método prospectivo com cinco pares completos. Feed B3, entitlement, conta privada, calibração e promoção financeira seguem dependências próprias.

Conclusão: todos EN-01–04 com evidência local, revisão independente e PR revisável. Commit/push/PR são próprios da skill explicitamente solicitada implement-spec; merge, release, instalação e compras não estão autorizados por essa entrega.
