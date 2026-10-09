# Expansão de mercados — contrato da investigação

Data: 2026-10-09, America/Sao_Paulo. Origem: pedido observado de Gabriel nesta conversa. Baseline de código: `da96c6ad4187030a98c4daa86a6b96e1e5b809a9`. Entrega autorizada: pesquisa e planejamento das próximas etapas.

## Objetivo e limites

Investigar coleta de dados de B3 (WIN/WDO e futuros candidatos), cripto, trading esportivo e opções binárias; reduzir a dependência manual de Profit/Excel; identificar rotas de acesso e planejar normalização, estudo e integração contextual ao JEV. Avaliar a meta R$400 → R$4.000 em menos de uma semana como cenário experimental e seus riscos, sem prometer resultado ou escolher operação real.

Não estão incluídos alterações do aplicativo, ordens, depósitos, criação de contas, compras/assinaturas, instalações, publicação, push ou recomendação de lote operacional. Consultas delegadas ao Jev Workflows usam contexto mínimo sanitizado, com recibo, sem confundir conselho e autorização. A chave/modelo do aplicativo são independentes do agente de desenvolvimento.

## Critérios imutáveis da entrega documental

- **AM-01 — fontes:** cada mercado terá evidência primária, URL e data de consulta; documentado, observado em acesso público e desconhecido serão distinguíveis. Não alegar inexistência universal a partir de buscas sem resultado.
- **AM-02 — granularidade e acesso:** comparar trades, livro, volume por preço, agressor, histórico, cadência/latência, limites, autenticação, custos, termos/redistribuição e disponibilidade brasileira. Biblioteca open source não equivale a feed gratuito. Candle, cotação e odds não viram tape integral ou book de ordens.
- **AM-03 — economia:** separar alavancagem/exposição de vantagem estatística; apresentar contas reproduzíveis da meta 10×, payout, responsabilidade lay, custos e risco de ruína. Nenhuma taxa de acerto, rentabilidade, capital admissível ou probabilidade de atingir a meta será inventada.
- **AM-04 — arquitetura:** localizar dependências atuais de WIN e propor contratos por mercado com precisão decimal, unidade, moeda, timestamps, origem, sequência, cobertura, saúde e replay; evitar reutilização silenciosa de multiplicador, lotes inteiros ou semântica WIN em outros mercados. JEV recebe evidência contextual; finanças e gates permanecem determinísticos, incluindo aguardar/q=0.
- **AM-05 — plano:** organizar tarefas finitas com IDs, requisitos, dependências, arquivos/responsabilidade, aceites e estados. Separar pesquisa pronta, especificação pronta, implementação e validação econômica. Declarar bloqueios reais e primeira entrega elegível.
- **AM-06 — preservação e revisão:** preservar mudanças preexistentes e aplicativo; verificar links locais, matemática e integridade dos artefatos; obter revisão independente em cópia isolada. Registrar hashes, plataforma, comandos, limites e checkpoint da própria conversa.

## Estado inicial e responsabilidade

Checkout principal já contém mudanças de outras frentes. O harness recusou ownership da raiz com `overlapping_lease`; a investigação foi isolada no worktree anexado `C:/Users/gabri/.codex/worktrees/pesquisa-apis-mercados/jeve-trader`. O integrador escreve os artefatos desta frente; cada pesquisador escreve apenas sua nota em pasta privada exclusiva; revisor recebe uma cópia hash-verificada e escreve somente parecer. Nenhum auxiliar altera índices compartilhados.

Fontes locais inspecionadas: `app/profit_bridge.py` (`SourceBatch`, `MarketEvent.quantity: int`, livro/agregados/capacidades); `app/profitdll_contract.py` (SDK autorizado ausente, valida símbolo WIN); `app/decision_engine.py` (`POINT_VALUE=.20`, conta BRL manual, quantidade inteira, tarifas exemplares). A inspeção não valida Profit/Excel real, feed integral ou rentabilidade.

O termo “CPI” mencionado no pedido não teve contrato identificado nas fontes locais consultadas. A arquitetura usa provisoriamente “camada de contexto/interpretação JEV”, sem inventar um módulo ou confundir com indicador macroeconômico.
