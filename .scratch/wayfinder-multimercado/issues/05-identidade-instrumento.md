# Identidade e capacidades de instrumentos entre B3 e cripto

Type: grilling
Label: wayfinder:grilling
Status: open
Assignee:
Blocked by: 01, 02, 03

## Question

❓ **Q2** - **Identidade e capacidades de instrumentos entre B3 e cripto**: Qual identidade impede misturar livro, moeda, quantidade e vencimento de mercados diferentes?

Alternativas reais: Ticker global e defaults WIN; cores totalmente separados; contrato comum tipado com semântica por família.

➡️ Recomendação JEV proposta: Instrumento versionado por venue/mercado/produto, com precisão monetária e famílias financeiras explícitas.

## Stress cases

WIN vencido e contínuo não são intercambiáveis; BTC/USDT de venues diferentes não compartilha livro. Deve ser possível invalidar avaliação após alteração de metadata.

## Dependencies and unresolved evidence

Definir conversão cambial e instrumentos derivados somente após fontes/regras próprias; não generalizar fórmula WIN.

## Comments

2026-10-09: consulta independente da primeira fronteira, receipt `9cfb6ee1-26a5-4f2f-a44a-6b6b81bda599`, modelo `jev-1.13.0`, rubric `batch-2026-09-26.2`, pergunta `instrument_identity`, disposition `recommendation`, recommendation `typed_instrument_venue`. Confiança contextual do conselho: 0.99; não é probabilidade de ganho nem autorização. [Entrada/saída sanitizadas](../jev-receipt.json).

Charting não encerra tickets grilling. Ainda não há Answer aceita ou ADR accepted; confrontar a recomendação com os relatórios finais, completar o contrato deste ticket e registrar a resolução em rodada própria.

