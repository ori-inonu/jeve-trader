# Percurso de fluxo e mesa com profundidade — 0.5.3

Incremento delimitado pelo [contrato FD-01..06](flow-depth-contract.md), dentro do plano humano aprovado. Baseline `7ab8e6ccfca4fce6e9ffdbf68bfc691bd602110f`. Os aceites FW originais não foram alterados.

## Inteligência contextual

As três janelas do motor expõem quantidade de observações, escopo e quatro distâncias em ticks, calculadas com Decimal a partir dos negócios aceitos. Com menos de dois negócios, as distâncias ficam nulas. Negócios distintos com horário igual conservam a ordem aceita. Nenhum percurso entre negócios é inventado.

O estado comum do JEV transporta essas observações com explicação literal. Uma subida de quatro ticks seguida de devolução de três se distingue de uma subida direta de um tick, embora ambas tenham o mesmo saldo final. Choice e Nouls independentes continuam avaliando apoio, contradição e insuficiência. Não foram acrescentados pesos, thresholds, aprendizado automático, regras financeiras ou promessas de resultado.

## Interface e frescor

CSS/SVG representam profundidade fixa no termômetro e relevo proporcional às quantidades do livro. Movimento permanece ligado a mudanças de dados, com transições de até 180 ms e sem novos timers. Preferência do sistema é acompanhada e o controle manual também desativa transições.

Tape, delta, corretoras, hipóteses e livro respeitam frescor. O livro depende de seu próprio horário de mercado; cotação fresca não rejuvenesce livro antigo. OFF retira contexto e níveis do JEV, preservando observações locais válidas. A ausência de dados não produz métricas sintéticas.

## Evidência local

Windows 11 x64; Python 3.14.7. `scripts/verify.py`: 248 testes Python e check desktop passaram. Frontend: 13 testes passaram; build de produção web e pacote Windows passaram. Os testes de percurso incluem resultados numéricos e limites de todas as três janelas, espelho vendedor, constância, vazio, observação única, cobertura parcial e transporte pelo seam público, sem API paga.

Inspeção no navegador local: ausência de fonte e demonstração explicitamente ativada em 640 × 800 e viewport amplo, sem overflow horizontal. Termômetro isolado verificado em −90, 0, +90 e indisponível; os três valores usam ARIA meter e a ausência usa imagem sem valor numérico. Movimento reduzido manual observou transição 0 s; normal 0,18 s. A mudança e limpeza do observador da preferência do sistema foram testadas em unidade; não foi alterada a configuração global do Windows.

Medições locais de desenvolvimento tiveram p95 de 1.422,6 ms (3 amostras) na ativação inicial da demonstração e 75,9 ms (2 amostras) após HMR. São amostras pequenas de sessões diferentes; não demonstram ganho ou cumprimento do aceite de latência real. A inspeção posterior sem fonte mostrou 45,2 ms (2 amostras), igualmente sem valor de certificação do piloto.

## Correções da revisão independente

A revisão SPEC encontrou `wait` contextual ainda visível com OFF ou contexto vencido. O teste reproduziu a falha (11 passaram, 2 falharam); a correção limpa também seleção, candidato, geometria e tempos da avaliação, preservando o snapshot original. Os 13 testes frontend passaram depois. A lacuna de oráculos numéricos nas janelas anterior e de 30 s foi fechada com teste independente de limites e distâncias. VAP declara ausência de horário próprio e frescor não verificado.

As duas revisões independentes verificaram 22/22 hashes da candidata final e repetiram 4 testes Python focados e 13 frontend, sem bloqueadores pendentes. A evidência e os limites estão em [revisão e pacote](flow-depth-review-evidence-2026-10-08.md).

## Fronteira preservada

FW-06, FW-11 e FW-12 continuam abertos. OCR estruturado exige pixels/campos reais; o piloto exige Profit/Excel e contrato/perfil identificados; a comparação contextual exige casos anotados autorizados e orçamento conhecido. Instalação, pesquisa e animação não comprovam completude do feed ou rentabilidade. O ticket canônico continua [captura real](issues/04-piloto-real.md).
