# Dados B3 sem dependência do Profit: acesso, cobertura e licenciamento

Type: research
Label: wayfinder:research
Status: resolved
Assignee: b3-research
Blocked by:

## Question

Quais caminhos oficiais permitem obter WIN/WDO em tempo real sem Profit, quais dados/continuidade entregam, e quais dependências comerciais e técnicas impedem recomendar um provedor agora? Distinguir REST, cotações atrasadas, histórico e tape/livro streaming. Não contratar ou autenticar.

## Comments

2026-10-09: pesquisa autorizada na rodada de charting; escritor em workspace isolado, relatório primário a integrar pelo coordenador.

## Answer

A B3 oferece UMDF direto com infraestrutura institucional, contrato e mecanismos específicos de snapshot/replay. Cedro Socket e CQG têm streaming documentado e constam como distribuidores de futuros; o SKU, vencimentos WIN/WDO, entitlement, continuidade e direitos de processamento externo pelo JEV ainda precisam de confirmação. Enfoque é uma alternativa de diligência; a evidência pública dxFeed consultada cobre ações L1, sem comprovar mini futuros. CQG pode aplicar collapsing inclusive de negócios. Conexão ativa, snapshot recente e timestamps ordenados não provam tape completo.

As políticas B3 mudam em 01/11/2026. A licença de terminal não demonstra permissão para ingestão própria, retenção, derivados/features ou envio ao JEV. Não houve contratação nem exercício de stream. O [relatório com fontes primárias e limites](../../../docs/research/B3_Dados_Independentes_2026-10-09.md) fornece o checklist para [qualificação do feed B3](10-qualificacao-b3.md), que permanece aberto.
