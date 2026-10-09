# Revisão independente e pacote — 0.5.3

Baseline: `7ab8e6ccfca4fce6e9ffdbf68bfc691bd602110f`. Contrato FD-01..06: SHA-256 `a2518a56c2d94a46c3c8da1eebb1fb1b62f2911fc94593ef377bfe2c496f9d2a`. Os aceites FW congelados permanecem inalterados.

Candidata final: manifesto `32606c8c3cc8f1074d04df298d50c3b1177f461363d6c59252571a3bd3982529`; patch `4945e4b59065ef951865d6acfb1ce088b8ca29e3dc21eb85e5a814214061e3d0`. Dois revisores, em cópias isoladas exclusivas, verificaram 22/22 hashes sem divergências e repetiram 4 testes Python focados e 13 testes frontend. Configuração de papel: harness_reviewer; modelo/tier efetivamente executados não comprovados.

Relatórios locais preservados em `.artifacts/flow-visual-research-20261008/`: `spec-review.md`, SHA-256 `9a3ae57cc28be0c70c14638ed8b8c6ef9431120d3961b8d6bd46edf5b3a26fb4`; `standards-review.md`, SHA-256 `a635f1e525083715184877131041619cd5b918d159687d0959ce28c7b0b2386a`. Os achados anteriores de OFF/validade e cobertura numérica foram corrigidos e o histórico não foi apagado. Não houve bloqueador restante no incremento. Um gap não bloqueante permanece: os testes não assertam diretamente os dois campos internos `context_by_candidate` e `jev.current`, embora o código os limpe.

Verificação ampla final: 248 testes Python, check desktop, 13 frontend e build Windows x64 passaram. O pacote foi gerado em 2026-10-08T19:15:29Z depois das correções; builds intermediários não foram instalados nem publicados. O smoke do motor empacotado observou versão 0.5.3, JEV OFF, zero chamadas, OCR OFF, ordens desabilitadas e dados isolados. O diagnóstico OCR usa texto gerado conhecido, não pixels reais do Profit.

Hashes de distribuição: instalador `5f5e31c3449855f9a095c2e229d0567d7a4232221b1d055e156b3befe4b280e5`; portable `3ffc9540123e3afaa80a78ce9f66c15a04451cf35bc519e0bddd708f4888f727`. Instalação/publicação e seus resultados serão registrados separadamente, sem usar animação ou instalação como prova de captura real.

FW-06, FW-11 e FW-12 permanecem abertos. Movimento reduzido do Windows foi testado por observador local, sem alteração global; o toggle real do sistema não foi exercitado. Inspeção e latência de desenvolvimento com poucas amostras não certificam piloto real nem ganho. A fronteira canônica segue [piloto real](issues/04-piloto-real.md).
