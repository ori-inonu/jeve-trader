# Percurso observado e profundidade da mesa

Status: ready (2026-10-08). Incremento reversível derivado de FW-07/FW-08 e do pedido humano de aprofundar a leitura de fluxo e o visual 2.5D/3D. Os aceites congelados do plano original permanecem intactos.

## Escopo e origem

O código atual conserva progressão líquida e amplitude, mas não diferencia avanço retido de devolução na janela. A mesa usa React/ECharts e já tem transições de 180 ms; o livro e algumas séries ainda escapam do bloqueio visual de frescor. A implementação usa os dados existentes e CSS/SVG, sem novo feed, biblioteca WebGL, treinamento automático, Scores, ordens ou chamadas pagas de teste. O piloto real continua aberto.

## Aceites imutáveis desta fatia

- FD-01: `FlowEngine.snapshot` acrescenta `price_path` às janelas atuais de 5 s, anteriores de 5 s e de 30 s. Excursões para cima/baixo partem do primeiro negócio observado; devoluções compradora/vendedora são máximo menos último e último menos mínimo, divididos pelo tick. Menos de dois negócios deixa métricas nulas; quantidade de observações e escopo parcial são explícitos. Empates de horário com IDs diferentes preservam a ordem aceita, sem inferir percurso entre negócios.
- FD-02: `build_context` transporta essa evidência no estado comum do JEV e explica seu significado literal. Permanecem Choice e Nouls independentes, regras financeiras determinísticas e distinções entre absorção, exaustão e progressão. Não há novos thresholds nem alegação de aprendizado, intenção ou rentabilidade.
- FD-03: casos anotados independentes distinguem subida 4 ticks/devolução 3 de subida direta 1 tick; espelho vendedor, preço constante, vazio, observação única e cobertura parcial. Verificar o transporte pelo seam público sem consultar API.
- FD-04: mesa apresenta termômetro com profundidade e barras do livro em relevo, mantendo preços, quantidades, direção e indisponibilidade legíveis. O comprimento continua proporcional à quantidade observada; nenhuma rotação/pulsação contínua simula dados. Transições no máximo 180 ms; sem novos timers de animação.
- FD-05: tape, delta, corretoras, livro e hipóteses deixam de parecer atuais quando suas capacidades vencem. JEV OFF retira contexto mas mantém observações locais frescas. Livro usa seu próprio horário de mercado, não o relógio da última cotação. Sem horário verificável continua indisponível como livro atual. Fonte ausente/expirada não produz movimento de dados fictícios.
- FD-06: movimento reduzido manual e preferência do sistema desativam transições; alteração da preferência do sistema é acompanhada. Inspecionar 640 × 800 e viewport amplo, com ausência de dados e demonstração explicitamente ativada. Medição local/sintética não encerra p95 de piloto real.

## Responsabilidades e verificação

Implementador isolado: `app/flow_engine.py`, `app/context_cycle.py` e novo teste de percurso. Integrador: `desktop/src/LivePanel.tsx`, `liveView.ts`, novo componente de profundidade, CSS e testes frontend. Nenhum escritor altera os arquivos do outro. Revisão independente usa cópia isolada e confere critérios e invariantes separadamente. Artefatos de pesquisa e hashes são anexados antes da integração final.

Dependências humanas: Profit/Excel abertos e perfil/contrato observados para FW-11; casos autorizados e comparação de inferências reais para FW-12. Nenhuma melhoria local encerra essas fronteiras.
