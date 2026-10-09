# ADR-0010 — painel e capital progressivo

**Status:** aceito para engenharia em 07/10/2026, conforme plano solicitado por Gabriel. A aceitação não promove uma política financeira. Implementação local ainda não commitada; [evidência](../evidence/decision-panel-2026-10-07.json).

## Problema e decisão

A coordenação Tkinter dificultava evolução do painel, supervisão de COM e separação entre interpretação contextual e resultado financeiro. Adotamos Tauri 2 + React + TypeScript + Vite, Tailwind CSS 4 e Apache ECharts, mantendo cálculos/persistência em Python. Qt/QML e Electron foram alternativas consideradas no plano; a escolha preserva o motor e oferece o ecossistema React em um aplicativo Windows.

`desktop_service.py` coordena o novo painel sem importar Tkinter. Tauri supervisiona o processo Python por JSON lines schema 1, com correlação de respostas e descarte de estados antigos. Dinheiro trafega como texto decimal; o código valida valores, geometria, custos e quantidade. Um Job Object Windows encerra os processos próprios quando o aplicativo termina. COM fica em processo separado; nenhum encerramento atinge o Excel.

`MarketSnapshot`, `AccountState`, `OutcomeEstimate` e `DecisionPlan` distinguem observação, conta manual, estimativa financeira e ação calculada. Conta usa patrimônio atual inteiro e pico persistente. Não existe parada por lucro ou pausa automática em 30% de drawdown. Nova oportunidade precisa justificar exposição; prejuízo não é regra de recuperação. Quantidades incluem aguardar e capacidade calculada, atualmente limitada a 100 por geometria no serviço.

Premissa literal, referências e receitas acompanham candidatos no payload. Apoio, contradição e insuficiência são Nouls separados. Choice recebe IDs de planos calculados e admissíveis; não cria preços ou valores por texto. Modelo financeiro requer validação temporal e aprovação explícita de integração. O serviço desta versão ainda não possui modelo/Choice econômico conectado; a recomendação principal fica em aguardar. Nenhuma barra contextual é renomeada como chance de lucro.

## Consequências e gates

- Dados JevWIN anteriores permanecem; novo SQLite separado, bootstrap compatível, sem migração destrutiva. Interface antiga é mantida.
- Rust/MSVC/WebView2 entram na manutenção; NSIS distribui payload x64 com stub Unicode x86 compatível, exigindo Windows x64. Python e licenças disponíveis são incluídos; ProfitDLL/dados proprietários não são redistribuídos.
- Primeira entrega apresenta hipóteses, finanças condicionais e registro manual. Não recomenda entradas financeiras nem saídas automáticas para posições abertas sem estimativas aprovadas.
- Logística calibrada, replay causal e políticas são implementações offline de pesquisa. CatBoost, simulador de fila, stops adaptativos/trailing e piramidagem intraposição permanecem experimentos posteriores.
- Instalação isolada, janela/processos e preservação foram verificados em Windows. Formulários React foram verificados no navegador. Excel/Profit real, interação nativa completa, JEV autenticado e modelo financeiro WIN são gates externos ainda pendentes.

Vínculos: JT-002–JT-007, JT-010–JT-015, E02–E10. [Guia](../DECISION_PANEL.md), [estado](../IMPLEMENTATION_STATUS.md). Os ADR-0001–0009 do índice original permanecem propostas com escopos maiores; este registro não os encerra automaticamente.
