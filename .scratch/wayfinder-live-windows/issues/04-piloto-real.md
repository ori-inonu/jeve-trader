# Contrato da captura real e reação ao painel

Type: grilling
Status: open
Assigned to: conversation 01a11717-73b1-7070-8d20-ad6d6e61188a
Blocked by: 01-fontes, 02-cadencia

## Question

Quais campos/intervalos reais estão disponíveis e o que Gabriel consegue interpretar no painel lado a lado com Profit em uma sessão de segundos a dois minutos?

## Comments

Marco 2026-10-08 — [OCR local nativo 0.5.2 entregue e auditado](../ocr-implementation-evidence-2026-10-08.md), com [duas revisões independentes](../ocr-review-evidence-2026-10-08.md) e [registro da release](../release-evidence-0.5.2.json). O helper compilado e Tesseract local substituem a rota bloqueada, sem alterar políticas. Runtime disponível e reconhecimento de texto gerado PASS; OCR e JEV OFF no smoke instalado, zero chamadas. 244 testes Python e 9 frontend passaram. Atualização 0.5.1 → 0.5.2 preservou bancos/atalho; release privada e aviso de versão foram verificados. Não há comprovação de captura real, extração estruturada, continuidade ou p95 visual. A consulta posterior de processos não encontrou Profit nem Excel; pergunta de arquivo/abas/intervalos/contrato continua pendente.

Próximo passo elegível do plano aprovado: observar os campos exportados e a janela Profit autorizada; validar perfil/filtros/modalidade/contrato antes do piloto de ≥30 minutos no instrumento instalado. Comparar o feed observado com o painel e registrar interrupções e cenários; separar atraso da fonte, latência visual e latência JEV. OCR continua auxiliar/parcial; não deduplicar negócios por preço/quantidade/horário nem declarar fluxo completo sem identidade e continuidade. Só após evidência real especificar a extração estruturada e o tratamento de perdas. FW-06/FW-11/FW-12 e este ticket permanecem abertos; nenhuma resposta humana foi substituída por suposição.

Marco 2026-10-08 — registro local do piloto 0.5.1 implementado e revisado: [evidência](../implementation-evidence.md), [pareceres independentes](../review-evidence.md). Checkpoints do frontend a cada 5 segundos, recuperação durável como interrompido, métricas cumulativas por renderer e baseline após recarga. 238 testes Python e 9 testes frontend passaram, sem feed/COM real ou API paga. Esse instrumento permite preparar evidências; mantém `PENDING_REAL_REVIEW`. Arquivo/abas/intervalos/contrato e sessão real de 30 minutos continuam pendentes, assim como OCR estruturado e comparação de inferências.

Retomada 2026-10-08 — Profit, Excel e JevWIN não estavam abertos na consulta de processos. A pergunta de arquivo/abas/intervalos/contrato permanece pendente. Sob FW-11, preparar registro local do piloto via `DecisionService.command/snapshot`: iniciar somente com captura Excel; duração por relógio monotônico, cobertura e interrupções, idade da cotação e transporte de captura separados da medição visual após dois frames. Cenários de rajada/rolagem/filtro/aba oculta/fechamento/reconexão serão marcas declaradas pelo operador, sem certificar continuidade. Relatório não conterá conta, credenciais, fórmulas, preços, negócios nem texto OCR. Reinício não retomará um piloto ativo. Este preparo não fecha o aceite real nem substitui a reação humana.

Marco 2026-10-07 — plano mesa de fluxo aprovado: [especificação ready](../spec.md), [evidência do incremento](../implementation-evidence.md), [revisão independente](../review-evidence.md). WIN, mesa integrada e JEV desligável mantendo cálculos locais foram confirmados pelo plano. O incremento inclui perfis Excel de cotação/negócios/livro/VAP, auditoria e throttle opt-in restaurável; testes locais não demonstram o feed disponível no Profit.

Na verificação desta conversa, não havia Profit/Excel abertos para piloto autorizado de 30 minutos. A rota OCR selecionada publica somente snapshot textual parcial; o helper nativo encontrou `UnauthorizedAccess` (scripts bloqueados), sem contornar a política. A extração estruturada real e a calibração de legibilidade/perdas permanecem pendentes. A latência de frontend observada em preview sintético não encerra FW-11. Casos anotados offline verificam contratos e significado dos fenômenos; não substituem a comparação de inferência do JEV nem demonstram rentabilidade.

Profit e Excel declarados disponíveis. Ainda faltam nome do arquivo aberto, planilhas/intervalos e contrato; pergunta enviada no chat. Validar quantidade/ID/agressor/timezone, qualidade de bid/ask, correções e refresh real antes de habilitar alertas experimentais. Chave do aplicativo deve ser inserida pelo campo local protegido; não solicitá-la no chat. Custos e capital reais continuam manuais e pendentes de conferência.

Após capturar um exemplo autorizado, criar protótipo do termômetro e medidores com estados indisponível/vencido e pedir reação humana. Não fechar este ticket com preferências supostas nem alegar que instalação validou operação.
