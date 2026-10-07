# Jeve Trader — requisitos de produto

## Requisitos aceitos do painel 0.4 — 07/10/2026

O produto é um copiloto Windows para decisões sobre WIN, com execução manual no Profit Pro. O painel moderno centra a apresentação em uma recomendação principal; hipóteses, alternativas e fundamentos ficam nos detalhes. Gráficos representam evidência contextual, capital, drawdown e distribuições financeiras quando estas forem validadas. O gráfico de preço é secundário.

Cada avaliação usa a banca atual inteira e as posições informadas. R$400 → R$800 → R$600 muda a base financeira; não existe reinício obrigatório em um contrato. Lotes podem começar acima de um contrato quando o plano e a capacidade justificarem. Não há parada por lucro. Drawdown de 30% é referência de adaptação, sem pausa fixa. Perda anterior não obriga recuperação ou aumento de lote. Planos incluem aguardar e quantidades admissíveis dentro do limite computacional configurado.

Preços, custos, margem e regras financeiras são calculados no código com `Decimal`. JEV interpreta hipóteses e, após integração de um modelo aprovado, poderá selecionar IDs de planos admissíveis. Confiança, apoio e contradição permanecem contextuais. Sem validação financeira temporal, o painel mostra “não estimada” para probabilidade e aguardar como recomendação principal. Exemplos de R$300 para R$4.000 são cenários de pesquisa, não metas obrigatórias.

Excel/RTD é a fonte inicial, com coleta isolada e cobertura explicitamente parcial. Capital, posição, custos e execuções são informados manualmente e registrados com revisão e idempotência. ProfitDLL real depende do SDK autorizado e começa por Market Data. Ordens automáticas, contratação de dados e licenciamento comercial seguem escopos posteriores.

O [ADR 0010](decisions/0010-painel-e-capital-progressivo.md), o [guia do painel](DECISION_PANEL.md) e o [status](IMPLEMENTATION_STATUS.md) registram implementação e pendências. A ausência de modelo aprovado não impede calcular hipóteses, custos e capacidade; impede apresentá-los como uma recomendação financeira validada.

## Requisitos históricos da baseline 0.3.0

As seções abaixo descrevem a entrega anterior. As políticas de pausa dessa baseline não governam o novo serviço. A afirmação histórica de ausência de laboratório estatístico foi superada pelo código offline 0.4, sem que isso demonstre desempenho empírico.

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
