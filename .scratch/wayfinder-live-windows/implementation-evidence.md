# Mesa de fluxo — evidência de implementação

2026-10-07, Windows 11 x64 (10.0.26200), Python 3.14.7. Especificação [ready](spec.md), fronteira [04 — piloto real](issues/04-piloto-real.md), [revisão independente](review-evidence.md). Código local entregue em Jeve Trader 0.5.0; isso não comprova feed completo, qualidade financeira ou rentabilidade.

## Aceites e alcance

| Requisito | Evidência desta sessão | Estado do aceite |
|---|---|---|
| FW-01 | JEV inicia OFF; comando tipado, revisão de controle, singleflight; OFF durante chamada, resposta tardia, retry e reinício testados. Resposta antiga liquida consumo sem alterar contexto/alerta/recuo vigente. | Verificado localmente, HTTP substituído por cliente controlado. |
| FW-02 | Mínimo inicial 1 s, validade máxima 2 s, coalescimento por conteúdo material e orçamento SQLite US$1/dia, US$5 total. Livro/corretoras fazem parte da projeção; mudança isolada de relógio não dispara inferência. | Verificado localmente, sem consumo pago. |
| FW-03 | Perfis COM separados de cotação, negócios, livro e VAP; auditoria limitada de Value2/Formula; identidade fornecida pela fonte, correções e negócios coincidentes testados. Parser/engine aceitam até 256 níveis; contexto limitado a 20 por lado. | Contratos verificados com doubles; exportação real ainda não demonstrada. |
| FW-04 | Corretoras compradora/vendedora opcionais, saldo de contratos na janela; horários mercado/captura/recebimento separados e uma fonte principal. Snapshot/agregado não é convertido em execução individual. Livro rejeitado não substitui observação válida. | Verificado localmente; campos disponíveis dependem da fonte real. |
| FW-05 | COM 250 ms; throttle RTD opt-in 250 ms guarda/restaura valor anterior, preserva alteração externa e sinaliza restauração não confirmada. Publica polling efetivo e intervalo entre mudanças RTD. Teste: 250 ms de polling / 500 ms entre alterações. | Contrato verificado; intervalo efetivo em sessão Excel real pendente. |
| FW-06 | Seleção de HWND Profit/região Times & Trades ou livro, revalidação da janela, OCR WinRT local inicialmente OFF; snapshot textual parcial, perdas desconhecidas e legibilidade não calibrada explícitas. Não envia imagens/texto OCR ao JEV nem soma volume. | Parcial: ainda sem parser estruturado validado. Smoke nativo bloqueado por política de execução (`UnauthorizedAccess`); diagnóstico específico visível. Nenhuma política foi contornada. |
| FW-07 | Delta, contratos/s, progressão em ticks, resposta à agressão, comparação 5 s/5 s anteriores/30 s e mudanças observadas do livro. Agressor, cenário, fenômeno e premissa literal separados; Choice e Nouls independentes, sem soma ou chance de lucro. | Contratos/semântica verificados; qualidade de inferência ainda não aferida. |
| FW-08 | Mesa integrada, termômetro bipolar, gráfico com níveis, tape, delta, livro, corretoras e hipóteses dos dois lados; valores ausentes indisponíveis, transições curtas e movimento reduzido. Inspeção no IAB: viewport 640×800, scrollWidth 625; sem transbordamento horizontal, rolagem vertical. | Inspeção visual com demonstração explicitamente sintética, JEV OFF. |
| FW-09 | 80 / rearme abaixo de 60 / mínimo 15 s, episódio preservado entre avaliações da mesma direção. Cotação vencida impede alerta e não rearma; som opt-in. Cabeçalho usa validade vigente. | Verificado com relógio e avaliações controladas. |
| FW-10 | Build frontend, PyInstaller, Cargo release, NSIS e diagnóstico empacotado PASS. Upgrade instalado 0.4.1 → 0.5.0, exit 0; dois bancos locais idênticos por SHA256 imediatamente após instalação; backup local ignorado pelo Git. Binários/manifesto coincidem com este pacote, registro e atalho Desktop verificados. Aplicativo abriu com janela “Jeve Trader — painel de decisão”. | Entregue e testado no Windows desta máquina. Sem publicação de release remota nesta sessão. |
| FW-11 | Instrumentação após recebimento no frontend até dois frames, separada de fonte/JEV. Preview sintético visível: p95 219 ms / 4 amostras. | Aberto: amostra insuficiente para certificar meta; não houve piloto real ≥30 min. Profit/Excel não estavam abertos/disponíveis para a captura desta sessão. |
| FW-12 | Oito casos anotados offline de absorção, exaustão, progressão e insuficiência. Testes de interpretação, limites e projeção compartilhada, com Nouls independentes simulados. | Parcial: comparação das inferências JEV atuais/novas ainda não executada. Não comprova qualidade do modelo nem rentabilidade. |

## Verificações executadas

- `.venv\Scripts\python.exe scripts\verify.py`: PASS, **229 testes**, verificação desktop PASS. Log local `.artifacts/mesa-verify.log`.
- `npm test` em `desktop/`: **5/5** testes de validade frontend/latência/visibilidade passaram; `npm run check` passou.
- `desktop/build-windows.ps1 -SkipInstallDependencies`, com PowerShell 7: passou, sem relaxar política de execução. Diagnóstico sidecar `PASS`, schema 2, ordens desabilitadas e probabilidade financeira ausente.
- Smoke do motor **instalado**, com diretório temporário: `PASS`, fonte `idle`, JEV OFF, 0 chamadas, termômetro indisponível, ordens desabilitadas. Não leu credenciais nem alterou diário real.
- Revisão independente em baseline fixa: dois leitores, quatro P2 corrigidos e reverificados, sem achado duro remanescente. Follow-up do diagnóstico OCR e demonstração passou em dois testes adicionais.

Instalação preserva identificadores JevWIN, dados e ícone existentes. Os artefatos, screenshot e backup privado ficam em `.artifacts/`, fora do commit. Instalação/animação não encerram os aceites de dados reais.

## Pacote 0.5.0

| Artefato | SHA256 |
|---|---|
| `JevWIN_0.5.0_setup.exe` | `bf18314d536dc85364a1842b1f76146ba18c5ae3d691e3e3e0faed5eef075af7` |
| `JevWIN_0.5.0_portable.zip` | `f953d11dab815a2e526d97c790d5fde2236e25808330f1f49685cd81c0da182e` |
| `JevWIN.exe` instalado | `4510659022fc295fc64d8eda07e23d71bbc8532211f50bbb226158d0e79a1b6f` |
| `jeve-engine.exe` instalado | `17cd501f1575ed9d535cc69ecac10f05d73909179679210dd29c1e028d171df5` |
| `package-manifest.json` instalado | `6a55d6305904338230db5fb7ac2a136ddf07337e9a3f4dbec25951a07c8dcd5d` |

## Continuação 2026-10-08 — instrumento do piloto (0.5.1)

Sob FW-11, a interface passa a iniciar/encerrar um piloto apenas com vínculo Excel ativo. Essa condição permite registrar falhas e ausência de leituras; não prova captura bem-sucedida. Registra duração monotônica, amostras de cobertura, interrupções, mudança de contrato, cenários declarados pelo operador e histogramas limitados de idade da cotação, transporte ao motor, resposta JEV e atualização após dois frames no frontend. Medição visual do piloto inclui somente novas capturas Excel em primeiro plano; perdas de renderização e períodos ocultos ficam excluídos e contados. Snapshots repetidos não contam como exclusões. Uma resposta após OFF pode entrar na medição, sem reativar contexto ou alertas. O piloto não habilita JEV nem solicita chamadas.

Relatórios locais não contêm preços, negócios, fórmulas, texto OCR, credenciais ou estado da conta. Checkpoint do motor a cada 30 segundos e envio visual a cada 5 segundos, também ao ocultar a janela; o envio visual salva o relatório completo. Interrupções preservam somente o último checkpoint recebido: recibos ainda não enviados são desconhecidos, portanto o relatório interrompido não comprova contagem integral de exclusões ou desempenho. Reinício grava o estado interrompido nos dois arquivos locais, sem retomar o piloto. Histogramas cumulativos são vinculados à sessão do renderer, com até oito sessões por piloto; reload não substitui as medições anteriores e regressões são rejeitadas. O primeiro snapshot de cada renderer estabelece a referência de captura, sem gerar amostra do piloto; snapshots retidos após reload não são medidos novamente. Frames pendentes só são excluídos no encerramento final. Checkpoint inválido ou ID adulterado não bloqueia o aplicativo nem autoriza gravação fora do diretório. Falha de gravação fica visível e permite tentar novamente. O relatório conserva `PENDING_REAL_REVIEW`, inclusive após 30 minutos e p95 abaixo da meta: marcas de cenário não certificam continuidade do feed.

Verificação Windows local após o incremento: `scripts/verify.py` PASS, **238 testes** e desktop PASS; `npm test` **9/9**; `npm run build` PASS. Nove testes Python cobrem fonte desconectada/sintética, relógio monotônico, cobertura, interrupção/reinício durável, relatório privado, histograma inválido/latência acima da meta, respostas tardias/falhas JEV, recuperação de gravação, reload visual e checkpoint local inválido. Quatro testes frontend adicionais cobrem sessão do piloto, captura elegível, snapshots repetidos, cancelamentos, frames pendentes, períodos ocultos e recarga do renderer. São testes isolados sem COM/feed real e sem chamadas pagas.

Profit e Excel continuam ausentes na consulta de processos. FW-06 (OCR estruturado), FW-11 (piloto real/latência) e FW-12 (comparação da inferência JEV) seguem abertos. Este instrumento prepara a coleta de evidências e não certifica operação completa ou rentabilidade.

### Pacote e instalação 0.5.1

PowerShell 7, PyInstaller, Cargo release e NSIS passaram; diagnóstico empacotado `PASS`. Atualização instalada **0.5.0 → 0.5.1**, saída 0: dois bancos locais byte-idênticos por SHA256, backup local ignorado pelo Git, atalho Desktop e registro 0.5.1 conferidos. Executável, motor e manifesto instalados coincidem com o pacote. Smoke do motor instalado, em diretório temporário, passou: fonte `idle`, piloto `idle`, JEV OFF, 0 chamadas, termômetro indisponível e ordens desabilitadas. Nenhum diário/credencial real foi usado no smoke. O build conserva o aviso conhecido de chunk frontend acima de 500 kB; isso não demonstra latência de renderização.

| Artefato | SHA256 |
|---|---|
| `JevWIN_0.5.1_setup.exe` | `8c925c4a51055063e011d64486b1f3178b0740fe5c2cabcfcbc05a12c148c476` |
| `JevWIN_0.5.1_portable.zip` | `26e8a62492be98aeae411c84e8b4ea465adf8897a8c9842bef721fef6dd810e6` |
| `JevWIN.exe` instalado | `cce9c0c7ef4a419a89b94c59ee0935ec85cdac28bcbed75bcb4710727910c476` |
| `jeve-engine.exe` instalado | `d76aa76da567ba53594ca58f56d3aee0c6cd92d774189e1450282c00c8479c79` |
| `package-manifest.json` instalado | `6e0fc1629aa712b1978bfd8922438acf4977cfb5e019af8fb9f6c417d6043daa` |

### Publicação e aviso de atualização 0.5.1

Release privada [v0.5.1](https://github.com/ori-inonu/jeve-trader/releases/tag/v0.5.1) publicada no commit `ee54938aaacf1f02ae2c4679e803e0a0aebe7ce7`. Instalador, portable e `SHA256SUMS-0.5.1.txt` tiveram tamanho e digest remoto conferidos contra os arquivos locais antes da publicação. A branch `codex/windows-updates-and-live-roadmap` foi enviada ao origin; alterações de outra conversa foram preservadas fora dos commits desta etapa. O repositório continua privado.

Consulta real pelo mesmo código usado no aplicativo confirmou `available` para a versão 0.5.0 e `current` para 0.5.1, ambas apontando para a release publicada. A consulta reutilizou a credencial Git existente sem prompt ou exposição à interface; nenhuma chamada JEV foi feita. A atualização continua manual pelo instalador após abrir a release. Evidência sanitizada: [entrega 0.5.1](release-evidence-0.5.1.json).

## Próximo aceite externo

Identificar contrato WIN, arquivo/intervalos Excel e ferramentas/filtros do Profit; auditar campos realmente exportados e identidade/continuidade dos negócios. Executar o piloto de 30 minutos com rajadas, rolagem, filtros, abas ocultas e fechamento/reconexão; medir fonte, frontend e JEV separadamente. Captura estruturada OCR exige contrato observado e validação local sob a política vigente. Comparação contextual exige casos anotados autorizados e orçamento conhecido. Feed gratuito completo, ProfitDLL/MT5 e posição real de investidores não foram demonstrados por este incremento. Ordens permanecem fora do escopo.
