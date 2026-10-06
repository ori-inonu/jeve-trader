# Jeve Trader — implementação e evidências

Baseline documental em 06/10/2026: aplicação **JevWIN v0.3.0** preservada em `app/`; Jeve Trader é o nome de apresentação do projeto. Este documento distingue código existente, verificações de software e validação no ambiente real. A organização do repositório não implica nova versão do aplicativo, correção do executável ou execução de experimentos financeiros.

## Resultado conhecido

O desktop Python/Tkinter, a Central de decisão, estudos de capital e a ponte Excel/CSV estão implementados. [VALIDATION.md](../app/VALIDATION.md) registra **166 testes automatizados aprovados em Linux** e autoteste aprovado. COM e HTTP foram simulados; os testes de controlador substituem componentes de tela. A evidência não comprova abertura nativa no Windows, conexão real ao Profit/Excel ou acesso autenticado JEV.

A transferência também reproduziu a suíte em **venv Linux novo, com Python 3.12.14 e tzdata 2025.2**: 166 testes e autoteste aprovados, sem abrir a interface ou consultar serviços reais. A [verificação da transferência](evidence/transfer-verification.json) registra essa evidência nova, separada dos relatórios históricos. Instalação, runtime e interface nativos Windows continuam pendentes.

O histórico registra falha ao abrir um executável anterior. **A causa permanece desconhecida:** a mensagem exata/diagnóstico da máquina não foi recebida. A v0.3.0 mudou o empacotamento para instalador NSIS e runtime Windows convencional, com diagnósticos. Isso é uma alteração verificável de distribuição, não uma confirmação de que a falha específica foi resolvida. [Limites de build](../app/WINDOWS_BUILD.md).

## Matriz de estado

“Testado” abaixo descreve verificações de software: a cobertura histórica foi reproduzida na transferência pelo ambiente Linux indicado acima. Nenhuma dessas execuções valida os comportamentos reais/empíricos da última coluna.

| Capacidade | Implementado | Evidência de software | Verificação real/empírica pendente |
|---|---|---|---|
| Desktop Tkinter e Central | Sim; oito abas, conclusões, impedimentos e alternativas | Autoteste e controlador com componentes substituídos | Abertura, aparência e uso em Windows. |
| Painel HTML | Sim; exportação estática | Escape, exclusão de credenciais e equivalência da conclusão | Não é painel conectado ou prova da janela nativa. |
| CSV e parsing temporal | Sim; schema de negócios, validação e deduplicação | Casos sintéticos e formatos nos testes | Integralidade e qualidade de dados reais. |
| Excel `quote`/`tape` | Sim; leitura COM somente de valores | COM simulado, parsing e recursos | Anexação ao Excel/Profit do usuário, frescor e layout autorizado. |
| Excel `combined` | Sim; duas tabelas, falha conjunta e deduplicação | Testes de falha parcial e percurso até cenários | Exportação real de negócios e perdas entre leituras; cobertura continua parcial. |
| Fluxo e referências | Sim; medidas e até oito geometrias observadas | Eventos sintéticos, retenção, geometria e integridade | Valor preditivo no WIN e limiares por regime. |
| Risco/capital dinâmico | Sim; `Decimal`, pisos, pausa e recálculo após P&L manual | Testes monetários, sequências e capital negativo | Conta real, margem/custos atuais e adequação da política escolhida. |
| Diário SQLite | Sim; histórico, configurações e JSON | Testes de persistência e transições | Conciliação com corretora; dataset experimental completo não implementado. |
| Cliente JEV | Sim; `jev-1.13.0`, `Choice`/`Noul`, validação e limites | HTTP/respostas artificiais e descarte de avaliação antiga | Credenciais, acesso e latência reais; benefício incremental do modelo. |
| NSIS/runtime Windows | Scripts e distribuição histórica existentes | Inspeção PE, conteúdo, extração e hashes em relatórios | Instalar/desinstalar e executar nativamente em Windows. |
| Conta Toro, ordens e posição | Não | Sem integração ou ordem real | Contrato autorizado, reconciliação e gestão de execução. |
| Feed integral/ProfitDLL | Não | Não foi inventada integração | Licença, contrato, sequenciamento, correções e captura adequada. |
| Notícias/calendário e simulador de fila | Não | Propostas | Implementação e validação própria. |
| Rentabilidade/calibração/lote ótimo | Não | Contas ilustrativas não medem desempenho | Resultados fora da amostra, custos, execução, incerteza e drawdown. |

Fontes de evidência: [`app/test_inventory.json`](../app/test_inventory.json), [`app/desktop_self_test.json`](../app/desktop_self_test.json), [validação histórica](../app/VALIDATION.md) e [relatórios preservados](evidence/JevWIN_distribution_report.json). Os relatórios em `docs/evidence/` podem abranger métodos anteriores; sua existência não atesta que binários correspondentes estejam incluídos neste repositório ou tenham sido executados no Windows.

## Limites que não podem desaparecer na continuidade

- Não há envio de ordens, consulta de saldo/posição ou proteção efetiva de operações feitas diretamente no Profit. Conta e resultados são manuais.
- Excel/CSV são amostras parciais. `combined` não produz tape integral; a aba `Negocios` do template começa vazia e depende de exportação real compatível.
- Não houve chamada autenticada à API JEV nem conexão real ao ambiente do usuário na validação descrita. Acesso informado pelo usuário é contexto histórico, não teste de disponibilidade.
- Software correto, empacotamento inspecionado e contas reproduzíveis não são backtest, operações observadas ou prova de lucro.
- Frações agressivas, custos e margens de exemplo não foram selecionados/validados para operação real. Stops planejados não garantem limite absoluto de perda.
- A mudança de nome para Jeve Trader ainda não migra dados `%LOCALAPPDATA%\JevWIN`, atalhos, scripts, versão ou recursos internos.

## Pesquisa aprofundada: entregue como proposta

O [relatório de pesquisa](research/Pesquisa_Decisao_JEV_WIN_2026-10-06.md), [plano JSON](research/Plano_Experimentos_JEV.json) e [snapshot auditado](research/study-2026-10-06/manifest.json) documentam auditoria, fontes e propostas. A reprodução local do estudo examina projeção de payload e exemplos matemáticos; não consulta modelo/mercado e não mede rentabilidade. **Nenhum experimento empírico E01–E10 foi executado, e nenhuma proposta foi incorporada à v0.3.0.**

Achados relevantes para o próximo trabalho: a premissa criada no candidato não é transportada na projeção enviada ao JEV; o diário não preserva todos os prompts, versões e hashes necessários para reconstituir um experimento; apoio, contradição e insuficiência precisam ser avaliados como dimensões distintas. Corrigir esses pontos exige mudanças explícitas e verificação, não apenas atualizar este documento.

## Ordem recomendada para continuidade

1. **Reproduzir a baseline offline e implementar o ciclo local JT-001–JT-005:** registrar ambiente/resultados, corrigir a perda de premissa, separar apoio/contradição/insuficiência e acrescentar registro experimental versionado e relógios. Esse trabalho usa fixtures e transporte simulado; não depende de Windows, feed real ou chamadas autenticadas. Consulte o [backlog](BACKLOG.md) e a [primeira tarefa no Codex](CODEX_NEXT_TASK.md).
2. **Conduzir as verificações externas como trilhas independentes:** JT-006 valida instalação/abertura/diagnóstico em Windows e exige logs sanitizados caso falhe; JT-007 formaliza exportação autorizada, IDs, símbolo, relógios, agressor, correções e perda de eventos. A indisponibilidade desses ambientes não bloqueia o ciclo local. Windows é gate para anunciar distribuição validada; o contrato da fonte é gate para experimentos que exigem dados reais. Nenhuma trilha confirma por si só a correção da falha anterior ou tape integral.
3. **Preparar e executar os experimentos próprios:** com dados/acesso/orçamento apropriados, congelar o protocolo, apurar desfechos causalmente e comparar regras, quantitativo e quantitativo+JEV com divisões temporais, custos/execução e teste futuro separado; incluir abstenções e falhas. Instrumentação local não conclui E01–E10.
4. **Estudar exposição por vantagem após os fundamentos:** com distribuição de resultados e conta conciliada, comparar quantidades menores que o teto e incerteza. Execução de ordens é uma etapa adicional, ainda sem implementação.

## Proveniência e manutenção

Este é o registro canônico de status; o [PRD](PRD.md) define intenção e a [arquitetura](ARCHITECTURE.md) descreve o código. [`archive/Projeto_JEV_Profit.md`](archive/Projeto_JEV_Profit.md) e documentos herdados preservam afirmações e nomes da entrega anterior. Atualizações devem registrar data, alteração, evidência e alcance da execução. Uma capacidade só passa de “pendente” a “verificada” com evidência no ambiente correspondente; aprovação de testes locais não promove o projeto a ferramenta operacional ou lucrativa.
