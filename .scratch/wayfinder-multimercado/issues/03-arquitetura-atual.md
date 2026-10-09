# Limites reais da arquitetura atual e pontos de extensão

Type: research
Label: wayfinder:research
Status: resolved
Assignee: architecture-research
Blocked by:

## Question

Quais acoplamentos WIN/Profit/Excel/manual existem no motor, transporte e frontend atual, e quais contratos precisam mudar para múltiplos mercados sem invalidar risco e dados existentes? Inspecionar cópia isolada; separar comportamento executável de intenção documental.

## Answer

O snapshot confirma uma base reutilizável Tauri/React/Python, porém com tick/multiplicador WIN, quantidades inteiras, conta BRL e identificador `excel_observation` espalhados. ObservationSession trata toda fonte não replay como Excel; serviço/JEV/frontend repetem esse gate. Conta, ledger e agendamento são globais; fronteiras novas precisam isolar instrumento, fonte/epoch, conta e sessão. Ordenação de timestamps não comprova continuidade; livro incremental multimercado não foi demonstrado.

O [relatório estático com referências e 25 hashes](../../../docs/research/Arquitetura_Multimercado_Lacunas_2026-10-09.md) identifica contratos reutilizáveis e cenários de migração. Não houve execução de produto. O orçamento do piloto JEV do aplicativo é separado dos limites delegados ao plugin de desenvolvimento. A pesquisa está resolvida; código e decisões de migração permanecem pendentes nos tickets técnicos.

## Comments

2026-10-09: snapshot isolado do checkout com alterações preexistentes; nenhum código será alterado por este agente.
