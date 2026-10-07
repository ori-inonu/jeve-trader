# Contrato da captura real e reação ao painel

Type: grilling
Status: open
Blocked by: 01-fontes, 02-cadencia

## Question

Quais campos/intervalos reais estão disponíveis e o que Gabriel consegue interpretar no painel lado a lado com Profit em uma sessão de segundos a dois minutos?

## Comments

Marco 2026-10-07 — plano mesa de fluxo aprovado: [especificação ready](../spec.md), [evidência do incremento](../implementation-evidence.md), [revisão independente](../review-evidence.md). WIN, mesa integrada e JEV desligável mantendo cálculos locais foram confirmados pelo plano. O incremento inclui perfis Excel de cotação/negócios/livro/VAP, auditoria e throttle opt-in restaurável; testes locais não demonstram o feed disponível no Profit.

Na verificação desta conversa, não havia Profit/Excel abertos para piloto autorizado de 30 minutos. A rota OCR selecionada publica somente snapshot textual parcial; o helper nativo encontrou `UnauthorizedAccess` (scripts bloqueados), sem contornar a política. A extração estruturada real e a calibração de legibilidade/perdas permanecem pendentes. A latência de frontend observada em preview sintético não encerra FW-11. Casos anotados offline verificam contratos e significado dos fenômenos; não substituem a comparação de inferência do JEV nem demonstram rentabilidade.

Profit e Excel declarados disponíveis. Ainda faltam nome do arquivo aberto, planilhas/intervalos e contrato; pergunta enviada no chat. Validar quantidade/ID/agressor/timezone, qualidade de bid/ask, correções e refresh real antes de habilitar alertas experimentais. Chave do aplicativo deve ser inserida pelo campo local protegido; não solicitá-la no chat. Custos e capital reais continuam manuais e pendentes de conferência.

Após capturar um exemplo autorizado, criar protótipo do termômetro e medidores com estados indisponível/vencido e pedir reação humana. Não fechar este ticket com preferências supostas nem alegar que instalação validou operação.
