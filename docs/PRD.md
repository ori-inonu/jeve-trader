# Jeve Trader — requisitos de produto

Documento canônico para continuidade no Codex/GitHub. Referência inicial: código herdado **JevWIN v0.3.0**, em 06/10/2026. O nome público do projeto passa a ser **Jeve Trader**; nomes internos, versão, caminhos de dados, scripts e artefatos JevWIN permanecem preservados por compatibilidade até uma migração explícita.

## Objetivo e usuário

Gabriel quer um copiloto de decisão para **Windows, Profit Pro e minicontrato de índice WIN da B3**, usando interpretação contextual JEV, leitura de fluxo e dimensionamento que acompanhe a variação do capital. O ambiente declarado no histórico inclui Toro, acesso informado à API TypeSafe/JEV e ausência de licença ProfitDLL/DLL Feed. Essa declaração não substitui teste de credenciais, licença ou disponibilidade de exportação na instalação real. [Fonte: `app/config.json` e documentação histórica](../app/config.json).

A aspiração é pesquisar crescimento de capital, inclusive com exposição agressiva, sem congelar o lote em um saldo inicial ou impor recuperação obrigatória de perdas. **Lucro, superioridade do JEV e quantidade economicamente ótima ainda não foram demonstrados.** O produto atual é um observador e laboratório de decisão: não envia ordens, não conhece automaticamente a conta e não gerencia posições. O sucesso desta etapa significa funcionamento verificável e informação rastreável; desempenho financeiro exige uma avaliação própria. [Estado e alcance](IMPLEMENTATION_STATUS.md).

## Escopo atual que deve ser preservado

| Necessidade | Comportamento existente / requisito de continuidade |
|---|---|
| Entender a conclusão | Central de decisão com evidências, impedimentos, alternativas e histórico; motivos de abstenção visíveis. |
| Acompanhar o mercado | Demonstração sintética, replay CSV e leitura de Excel já aberto nos modos `quote`, `tape` e `combined`, com origem, idade e cobertura identificadas. |
| Estudar fluxo | Volume, delta capturado, intensidade, progressão, absorção/exaustão potenciais; agressor desconhecido não é inventado. |
| Comparar geometria | Até oito combinações de entrada/stop/alvo apoiadas em referências observadas; sem ranking por lucro esperado. |
| Recalcular exposição | Capital inicial, atual e pico, custos, slippage, margem e limites explícitos; lote inteiro recalculado após resultado líquido manual. |
| Interpretar contexto | Cliente opcional TypeSafe/JEV, modelo fixado `jev-1.13.0`; respostas válidas e atuais, separadas do veto determinístico de risco. |
| Revisar decisões | Diário SQLite, exportação JSON e painel HTML estático com a avaliação do instante. |
| Usar no Windows | Fontes Python/Tkinter, instalador NSIS por usuário, runtime incluído e diagnóstico; execução nativa ainda pendente. |

Detalhes operacionais estão no [README herdado](../app/README.md), [guia Windows](../app/GUIA_WINDOWS.md) e [arquitetura](ARCHITECTURE.md).

## Regras do produto

1. Toda avaliação mostra se usa demonstração, replay ou observação Excel. As fontes Excel/CSV continuam parciais; cotação isolada não é tape nem livro integral.
2. Sem dados suficientes ou atuais, a conclusão explica a limitação. Apoio contextual do JEV não remove impedimento de cobertura, falta de conta conciliada ou veto monetário.
3. `confidence`, apoio e contradição do modelo não são probabilidade de atingir alvo antes do stop. Nenhum lote é apresentado como o de maior lucro esperado.
4. Resultados registrados manualmente atualizam patrimônio e sequência; perda pode esgotar ou ultrapassar o capital. A pausa do estudo não bloqueia ações no Profit.
5. Parâmetros agressivos, margens e custos de exemplo são hipóteses de laboratório, não uma política aprovada para a conta real.
6. Chaves não são persistidas no diário; consultas são opcionais e limitadas. Não adicionar chamadas autenticadas ou integração de ordens apenas para verificar documentação.

## Próximas entregas e critérios de aceitação

| Etapa | Resultado revisável necessário |
|---|---|
| Baseline Windows | Instalação, abertura da janela, diagnóstico e persistência comprovados em Windows; falhas acompanhadas da mensagem e dos logs sanitizados. |
| Contrato da fonte | Exportação real autorizada identificada, símbolos/timestamps/IDs/agressor verificados e perda de informação documentada; `combined` não recebe rótulo de feed integral. |
| Experimento JEV | Premissa explícita, perguntas exatas/versionadas, relógios e resultados posteriores reproduzíveis; comparação entre regras, quantitativo e quantitativo+JEV. |
| Avaliação econômica | Divisões temporais e teste futuro separado, custos e execução plausíveis, incerteza, drawdown e abstenção avaliados. |
| Possível uso operacional | Conta e exposição conciliadas, dados e execução adequados e limites de risco escolhidos explicitamente antes de discutir recomendações acionáveis ou ordens. |

Feed integral licenciado, notícias/calendário, simulador de fila, gestão de posição, pirâmide, saídas parciais, Kelly e escolha de lote por vantagem **não estão implementados**. O [relatório de pesquisa](research/Pesquisa_Decisao_JEV_WIN_2026-10-06.md) e seu [plano de experimentos](research/Plano_Experimentos_JEV.json) são propostas para essas etapas, não funcionalidades entregues.

## Proveniência e autoridade

Este PRD descreve o objetivo e os requisitos de continuidade. [ARCHITECTURE.md](ARCHITECTURE.md) descreve a implementação; [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) registra evidência e pendências. O código em `app/` é a referência do comportamento executável. Os documentos em [archive](archive/Projeto_JEV_Profit.md) preservam o contexto histórico; documentos em `app/` podem manter nomes/versões anteriores. A pesquisa em `docs/research/` não altera o comportamento da v0.3.0. Divergências devem ser resolvidas com inspeção do código e evidência, atualizando estes documentos sem apagar a proveniência.
