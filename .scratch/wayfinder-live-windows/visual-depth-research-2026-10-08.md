# Profundidade visual orientada pelo fluxo — pesquisa de 2026-10-08

Pesquisa delegada para o ticket `issues/05-profundidade-visual.md`. Código do produto somente lido; nenhum pacote instalado, chamada paga ou alteração de implementação. Esta nota propõe um incremento para especificação e revisão independente. Não certifica implementação, latência, ergonomia humana ou operação real.

## Recomendação

Começar por uma mesa **2.5D em DOM/CSS/SVG**, preservando React/Vite/Tauri e ECharts existentes. Transformar o termômetro em um instrumento com tubo, preenchimento bipolar, marcador de nível e faces de profundidade; representar delta, intensidade e quantidades do livro por barras com faces superior/lateral. Números, horários, sinais e legendas ficam frontais. Mudanças de nível e largura acompanham os dados recebidos, com transições curtas; a profundidade decorativa é fixa e não significa confiança, força do mercado ou probabilidade de lucro.

É uma inferência de engenharia: o produto já dispõe de todos esses valores e de invalidação temporal, e as tecnologias CSS permitem profundidade sem adicionar um segundo renderer. A pesquisa **não** demonstra que CSS seja sempre mais rápido que WebGL, nem que um visual com profundidade melhore a decisão humana. O primeiro resultado verificável é uma mudança visual expressiva e fiel aos mesmos valores; compreensão e latência real exigem avaliação.

WebGL com Three.js/React Three Fiber é uma alternativa válida para uma futura superfície de profundidade preço × tempo × quantidade, caso essa terceira dimensão tenha uma pergunta analítica concreta. Não é necessário migrar para Next.js para desenhar 3D. Introduzir uma câmera móvel e modelos 3D apenas para ornamentação acrescentaria mecanismos que o uso em meia tela ainda não justifica.

## Contratos e código observados

Baseline lida: Git `7ab8e6ccfca4fce6e9ffdbf68bfc691bd602110f`. Os seis arquivos de produto abaixo estavam sem alterações locais na inspeção. Hashes SHA-256 dos bytes locais:

| Fonte | SHA-256 |
|---|---|
| `.scratch/wayfinder-live-windows/spec.md` | `0183310d90dcfffd921ac551df12e7d2590db55fdfb7c1e1604a7c2b22f1ced6` |
| `.scratch/wayfinder-live-windows/issues/05-profundidade-visual.md` | `5c64830a7d7632a9a950505e7d24708b9a6a8ccfc964646bbe57d8568164426f` |
| `desktop/src/LivePanel.tsx` | `5c6de69171b2ca90dbdaed452efec0044ddf2c0c072bd46f2b91e6c0f534dfcd` |
| `desktop/src/style.css` | `c7595969ada41d6526cacb809fb3653c8bb9d71c94cb60defe81410f2e02f9f9` |
| `desktop/src/Chart.tsx` | `dba8bb82ef6b04d0812bace7523da5f11ddbcca8aa66ce41189f6c2805bc8e78` |
| `desktop/src/liveView.ts` | `60950757c00bda48419028423c978f599091c3a482d8debabe6e418737b1c0d8` |
| `desktop/src/visualLatency.ts` | `c9c50904b7a08c5e66a20de39e64c37c84057f572d53ac3564152d4ee9833867` |
| `desktop/package.json` | `cae475411afc6517b5b6ce1982f7db826a1b940cd812d6783bebc9a0d04d74fe` |

Evidência literal do contrato aprovado:

- FW-08: `dados ausentes indisponíveis, transições curtas, movimento reduzido; inspeção em 640×800`.
- FW-11: `piloto Windows ≥30 min com rajadas/rolagem/filtros/abas/janelas e p95 visual ≤250 ms após recebimento; depende de Profit/Excel e dados autorizados disponíveis`.

Evidência literal do código e interpretação:

- `LivePanel.tsx`: `const data=liveSnapshot(raw,now)`; `const temperature=d.temperature`; `const tape=!!caps.tape`. A direção e delta/intensidade já passam por invalidação temporal.
- `LivePanel.tsx`: `const book=flow?.book` e `(flow?.recent_trades||[]).slice(-8).reverse().map(...)`. Livro, histórico, negócios e corretoras são desenhados diretamente a partir do snapshot retido. **Inferência:** a nova animação precisa consultar disponibilidade/frescor por domínio; a existência de arrays antigos não comprova fluxo atual. O histórico pode continuar visível se identificado como anterior, sem efeitos de chegada.
- `style.css`: `transition:bottom 180ms ease`, `transition:width 180ms ease`, `animation:received-trade 180ms ease-out`. A mesa já possui transições discretas, mas não tem faces de profundidade ou uma cena 3D.
- `Chart.tsx`: `CanvasRenderer`; `animationDurationUpdate:180`. Os gráficos atuais utilizam Canvas 2D de ECharts, não Three.js.
- `liveView.ts`: `if(data.market.application_mode !== 'excel_observation') return data`; `now-stamp<=data.context_settings.validity_ms`. Replay/sintético são modalidades históricas explícitas; contexto live tem TTL configurado.
- `visualLatency.ts`: `const ms=Math.max(0,performance.now()-received.at)`; `paintLatency` é chamado após dois `requestAnimationFrame` no painel. Mede uma aproximação de atualização após recebimento, **não** término da interpolação CSS nem latência da B3. Não trocar essa definição silenciosamente.
- `LivePanel.tsx`: preferência do SO é consultada na inicialização de `useState`; `Chart.tsx` consulta `matchMedia` no efeito de atualização. **Inferência:** uma assinatura do evento `change` do media query é necessária para garantir resposta imediata quando a preferência do SO mudar com o aplicativo aberto; o toggle persistente já existe.
- `package.json`: React `^19.3.0`, Vite `^8.3.3`, ECharts `^6.0.0`; não há Three.js/R3F. A compatibilidade de versões de uma futura inclusão precisa ser validada antes de instalar; esta nota não escolhe versões.

## Fontes primárias consultadas

URLs foram abertas com a ferramenta web. As páginas também foram recuperadas por HTTP para registrar o hash **do corpo de resposta**, antes de parsing, entre `2026-10-08T14:15:55Z` e `14:15:59Z`. Hashes não significam que a página permanecerá imutável nem são prova de implementação. O material bruto não foi gravado em outro arquivo. As citações literais abaixo foram verificadas no conteúdo consultado; o restante é paráfrase/inferência identificada.

| ID | Fonte, evidência literal curta e alcance | SHA-256 / bytes |
|---|---|---|
| P1 | [MDN — perspective](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/perspective): “Large values of perspective cause a small transformation”. Perspectiva projeta elementos com profundidade; também cria stacking context e afeta descendentes fixed. | `0393185579115356f26c7c2f548516b571ba0eaa453cbeeb36b364cbcbaedd04` / 329651 |
| P2 | [MDN — transform-style](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/transform-style): “Indicates that the children of the element should be positioned in the 3D-space.” `preserve-3d` não é herdado; overflow/opacity/filter e outras propriedades podem achatar descendentes. | `11d7146eecf50084e1c5cba06a841db0600198f5388e1fefa465d1a2fdf4e764` / 333265 |
| P3 | [MDN — prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion): “Animations such as scaling or panning large objects can be vestibular motion triggers.” A preferência sinaliza reduzir, remover ou substituir movimento não essencial. | `e39188b0c8c7214715e3d8328b7b35e209713c88c1a72c645ae5f208adeb1a9a` / 329728 |
| P4 | [MDN — CSS/JavaScript animation performance](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/CSS_JavaScript_animation_performance): “If an element is promoted as a layer, animating transform properties can be done in the GPU”. A promoção e o navegador condicionam esse caminho; não garantem desempenho nesta máquina. | `4890a3bf45ddaee5049c1a307f9085f0426aeb52b12e0389dbe7f98d6fcdb99c` / 159814 |
| P5 | [W3C — SC 2.3.3, Animation from Interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html): “Motion animation triggered by interaction can be disabled”. O critério AAA permite exceção para movimento essencial; o documento distingue animação iniciada automaticamente. Não é uma certificação WCAG do app. | `14af35e29c3c990a8de49207a26b260c1812eb09b2c70b25f3750a9f114c12f2` / 36817 |
| P6 | [React Three Fiber — Scaling performance](https://r3f.docs.pmnd.rs/advanced/scaling-performance): “Running WebGL can be quite expensive depending on how powerful your devices are.” Render sob demanda (`frameloop="demand"`) descansa quando nada muda; `invalidate` agenda um frame, sem render imediato. | `e9ac90e90eb06fee6773285aa63a77e8536fac9dc212b0fe9a805705140db3a3` / 1872127 |
| P7 | [React Three Fiber — Canvas](https://r3f.docs.pmnd.rs/api/canvas): “optional DOM JSX elements or regular components in case GL is not supported”. Documenta fallback, modo demand, câmera ortográfica, DPR e proteção contra falhas de contexto. | `e289d8c7f859dfd0c4fcf6e2c63a545be651874cce2ea97cdd28714e3133b824` / 1819862 |
| P8 | [Three.js — WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer.html): “This renderer uses WebGL 2 to display scenes.” WebGL 1 deixou de ser suportado desde r163; recursos GPU precisam de descarte quando o renderer deixa de ser usado. | `0d6f74e9590ca30c45945fc9c3dbb315e64d8b0c8f662bbe7aaf39f46c119dc4` / 72800 |

## Alternativas reais

| Caminho | O que permite | Custos/riscos neste produto | Decisão proposta |
|---|---|---|---|
| DOM/CSS com faces e SVG para escala | Relevo, tubo, barras extrudadas e movimento curto baseado em valores; texto/controlos permanecem DOM. P1/P2 documentam profundidade. | Perspectiva exagerada distorce leitura; overflow atual pode achatar preserve-3d; sombras/filtros precisam de medição. Não há garantia de aceleração. | Primeiro incremento. Usar profundidade pequena, labels frontais, `transform`/`opacity` onde fizer sentido e layers limitadas. |
| SVG 2D com polígonos isométricos + CSS | Projeção fixa das faces, eixos precisos, sem contexto WebGL. Integra componente React; posição numérica continua em tela. | Não há cena volumétrica/câmera livre. Eixos isométricos podem ocultar barras; exige contraste e equivalência textual. | Também elegível; preferir projeção fixa nas barras do livro e tubo central. |
| Three.js/R3F com câmera ortográfica | Cena 3D real, meshes/iluminação, exploração de preço × tempo × quantidade. P6/P7/P8. | Novas dependências, WebGL 2, perda de contexto, ciclo/disposal, GPU e acessibilidade paralela; interoperabilidade Tauri precisa ser exercitada. | Experimento posterior separado, render demand, fallback DOM e dados idênticos. Não antecipar ganho de decisão. |
| ECharts existente, 2D com transições e gradientes | Evolução incremental dos gráficos já usados, sem nova biblioteca. | Sozinho pode manter a percepção de painel plano que motivou o pedido; Canvas requer equivalência textual para valores críticos. | Preservar para séries/tempo; combinar com instrumentos 2.5D da primeira opção. |

## Incremento delimitado para especificação

Requisitos propostos (exigem congelamento pelo coordenador e revisão independente antes da implementação):

1. **Termômetro:** continuar a usar `directional.temperature`, em −100…+100 e fórmula já aprovada, com zero fixo, número assinado, texto compra/venda/equilíbrio/indisponível e marca visual −80/+80. Faces e luz estáticas produzem profundidade; o marcador e o preenchimento respondem ao dado. Sem giro contínuo, câmera orbital ou vibração decorativa. Avaliação e validade são exibidas por timestamps disponíveis, separadas da idade da cotação.
2. **Volume/intensidade/livro:** delta assinado, contratos/s e quantidade por nível mantêm escala e número explícitos. As faces 2.5D refletem exatamente a largura/altura do mesmo valor; saturação da escala é indicada. Não usar iluminação, dimensão Z ou velocidade de animação como novo indicador quantitativo sem uma definição aprovada. A escala atual de 100 contratos/s é visual, não limiar de negociação.
3. **Movimento:** transições de até 180ms entre estados recebidos; chegada de negócio dispara no máximo um realce curto para um ID novo verificável. Heartbeat/renderização/reordenamento não representam um negócio novo. Sem timer que simule mercado ativo, randomização, onda permanente ou pulso que aparente atividade da fonte. Não bloquear o valor textual durante a interpolação.
4. **Disponibilidade por domínio:** cotação, tape, livro e contexto consultam seus timestamps/capacidades atuais. Desconexão, vencimento ou timestamp ausente remove os efeitos de fluxo ao vivo imediatamente no estado renderizado. Histórico retido continua identificado como histórico, ou apresenta indisponível; não retorna visualmente a zero como se zero fosse dado observado. OFF do JEV elimina o instrumento contextual vigente, preservando instrumentos locais quando a fonte permanece válida. Sintético/replay mantêm aviso permanente.
5. **Acessibilidade:** toggle persistente e preferência do SO reduzem movimento durante a sessão, incluindo quando o SO muda sem reload. Ambos desligam transições/realces; os valores continuam atualizando. Números/labels frontais, signos e estados textuais acompanham cor. Faces decorativas ficam fora da árvore de acessibilidade, sem capturar foco/pointer. Não anunciar cada tick por aria-live.
6. **Meia tela:** em viewport 640×800, direção, estado da fonte, idade e ON/OFF ficam legíveis, sem horizontal scroll e sem sobreposição. Conteúdo detalhado pode usar rolagem vertical; meia tela não significa colocar todas as evidências simultaneamente em 800px. O instrumento não invade os níveis de preço ou esconde alertas.
7. **Medida:** preservar receipt→dois frames e exclusões da instrumentação existente. Uma comparação local baseline/candidato com a mesma sequência identifica regressões, mas não comprova FW-11; p95 ≤250ms só se fecha no piloto real Windows aprovado. Registrar separadamente eventuais medidas de término de transição, fonte e JEV. Nenhum número de desempenho é inferido da tecnologia escolhida.

Não objetivos: trocar framework; adicionar feed/API/ordens; alterar Choice/Noul, cálculo financeiro, política de alertas ou lote; vender movimento como cobertura real ou probabilidade de lucro; prometer rentabilidade ou ganho cognitivo; certificar o próprio contrato.

## Aceite independente proposto e riscos a resolver

O revisor deve executar casos com sinal +90/−90/0/null, fonte parcial, timestamps ausentes, contexto vencido com cotação nova, cotação vencida com heartbeat novo, JEV OFF, fonte desconectada, replay/sintético, repetição/reordenação de IDs e preferência reduzida inicial/alterada durante uso. Conferir a equivalência dos valores entre texto, escala e geometria. Uma avaliação sem feed não pode fechar continuidade nem legibilidade da coleta.

Inspecionar manualmente 640×800 no renderer usado para entrega, teclado/foco e cores neutras; conferir que a animação cessa em repouso, indisponível e movimento reduzido. Comparar a mesma sequência antes/depois em ambiente local isolado, registrando máquina, renderer, exclusões e escopo. O piloto de 30 minutos e a reação de Gabriel permanecem dependências abertas do ticket canônico; uma aprovação técnica local não substitui nenhuma delas.

Riscos concretos: `overflow:hidden` presente nas barras achata preserve-3d (P2), então pode ser necessário separar wrapper de clipping e faces; `perspective` muda containing/stacking context (P1), então não aplicar ao contêiner global de modais/alertas; sombra/filter em várias linhas exige medição (P4); o timer `now` pode rerenderizar históricos sem nova captura, então os efeitos de chegada devem usar identidade/geração; a métrica de dois frames não inclui o fim de uma transição de 180ms; preferência reduzida baseada apenas em inicialização pode ficar desatualizada; dados ausentes hoje ainda atravessam arrays retidos do livro/tape/brokers, exigindo semântica temporal explícita antes de adicionar movimento.

Conclusão da pesquisa: há um caminho implementável e reversível para profundidade visível e resposta ao fluxo dentro do stack existente. A escolha CSS/SVG é fundamentada em integração e leitura; ganhos de latência, ergonomia e decisão continuam não demonstrados.
