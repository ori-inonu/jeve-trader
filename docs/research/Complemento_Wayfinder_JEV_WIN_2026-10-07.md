# Complemento Wayfinder — inteligência e interface do Jeve Trader

**Data:** 07/10/2026, America/Sao_Paulo.  
**Entrega:** Scratch e especificações para a próxima etapa de planejamento.  
**Escopo:** leitura do checkout, atualização de fontes primárias e sonda aritmética sintética local, sem modificar código do aplicativo.  
**Estado empírico:** nenhuma nova amostra real do WIN, chamada autenticada JEV, ordem ou validação de rentabilidade.

Continua o plano “Jeve Trader — painel de decisão para alavancagem progressiva”, discutido no chat “Investigar UI, JEV e risco”, e complementa a [pesquisa de 06/10](Pesquisa_Decisao_JEV_WIN_2026-10-06.md). A pesquisa anterior conserva sua baseline v0.3.0; seus achados não serão silenciosamente atribuídos ao checkout novo.

O ponto de entrada é o [mapa Wayfinder](../../.scratch/wayfinder-evolucao-decisao/map.md). Os contratos e parâmetros estão na [especificação transversal](../../.scratch/wayfinder-evolucao-decisao/spec.md). Os seis tickets permanecem abertos para resolução no próximo planejamento.

## 1. Método e referência auditada

A leitura foi feita enquanto o outro chat concluía implementação; a gravação documental aguardou seu término para respeitar o AGENTS.md. O GET inicial do Mission Control não respondeu; uma nova consulta em 07/10/2026 às 14:55 UTC retornou disponível, sem tarefas registradas para este projeto. O status do chat identificou a implementação concorrente, sem autorização adicional.

Os achados abaixo distinguem **observado no código**, **inferência de engenharia** e **hipótese experimental**. Leitura de código não certifica a janela Windows, execução financeira ou comportamento remoto do JEV.

**Referência recapturada após a conclusão do outro chat:** 2026-10-07T11:59:31.110358-03:00 (America/Sao_Paulo), correspondente a 2026-10-07T14:59:31.110358+00:00. HEAD-base `4080f0f730fba89868a750677d4749526286cecd`. O checkout contém alterações locais e arquivos novos da entrega 0.4; o HEAD isolado não reproduz este estado. Os hashes abaixo identificam os arquivos efetivamente lidos.

| Arquivo | SHA-256 do conteúdo observado |
|---|---|
| [app/app_core.py](../../app/app_core.py) | `d1952d84ba282306f8d0db01959dd3d97d5cfad5ad221986a3afc4e64f0a8127` |
| [app/context_requests.py](../../app/context_requests.py) | `ec1749a33381e47433bb74aa0c6e6bb47cfd9e29ff4b63ae91ed2dbf1458e275` |
| [app/decision_engine.py](../../app/decision_engine.py) | `809a3010b398a9fb685fe32fb8c4ec6cf1d78af564a144e0fa62e389cbfde450` |
| [app/decision_lab.py](../../app/decision_lab.py) | `6cfd1358d2ece67b1cde4bcbed6c9f0aae77e4201efe3cf20c8db55f46220bab` |
| [app/decision_store.py](../../app/decision_store.py) | `5f1d418f8020bc168eed5f6ea6b9f74ffc01352d7642d3c14c8a3edf588c7cf1` |
| [app/desktop_service.py](../../app/desktop_service.py) | `1f210f59276ea9a1797846ce33d6728e103b2825647397d2e77f0ba5fe303a75` |
| [desktop/src/App.tsx](../../desktop/src/App.tsx) | `815f78923a5f7357f037fdcfb5e8bdb51107f3be627fe431a691b56d6481073c` |
| [scripts/run_decision_lab.py](../../scripts/run_decision_lab.py) | `d30768ea76a83cac4f0411f290c5129955f48befe2bc96033d44c519bca5b525` |

A conclusão do outro chat foi observada com status `completed` antes de qualquer gravação deste Scratch. A fronteira de alterações desta entrega é documental.

A sonda local foi executada em Python no Windows, com `-B`, sem gravar script no aplicativo ou carregar credenciais. As verificações desta entrega são documentais e aritméticas; os testes realizados pelo outro chat têm seu próprio registro em [IMPLEMENTATION_STATUS](../IMPLEMENTATION_STATUS.md).

## 2. Achados reavaliados

| Tema | Observado na leitura atual | Implicação para o planejamento |
|---|---|---|
| Correspondência contextual | `DecisionService.accepts` compara ID, premissa, versão de hipótese e geometria, além de geração da fonte, revisão da conta e idade. O contexto apresentado ainda é extraído de `candidate_0_*`. | Houve uma correção parcial relevante. Falta contrato único por candidato/horizonte, evidências, custos e versões; o diagnóstico anterior não deve ser repetido como se a geometria continuasse sem conferência. |
| Hipóteses | `literal-hypotheses-v2` conserva premissa e perguntas independentes de apoio, contradição e insuficiência. | Formalizar a semântica, os requisitos de dados, os tempos e a composição. Não presumir robustez remota porque os campos estão presentes. |
| Aceitação financeira | `compare_plans` exige `validated`, holdout temporal, aprovação declarada de uso e indicação de dado não sintético. | O gate já excede um booleano isolado. Continua necessário definir o registro que sustenta essas declarações e seu escopo de validade. |
| Laboratório | Há junção contextual por `available_at_ms`, separação temporal, maturidade dos rótulos, comparação em oportunidades comuns e patrimônio próprio por política. | Estender esses mecanismos. O proxy de preços declara ausência de latência, fila e preenchimento parcial; isso não é avaliação completa da execução manual. |
| Interface | Tauri/React apresenta Decisão, Capital, Pesquisa e Configuração. A inspeção recupera a alternativa pelo ID do snapshot atual; a validade visual usa uma regra local de 2.000 ms. Falta vincular contexto e inspeção à avaliação imutável. | Especificar estados atuais/históricos, estabilidade durante atualização e uma verificação Windows própria. |
| Conta e custos | Conta conciliada manualmente; histórico inclui conciliação e registros manuais de preenchimento. Custos são identificados como experimentais não conferidos. | Preservar origem e fluxos externos; não substituir custo por uma referência educativa ou estimativa contextual. |

A correção de um achado estrutural pode ser demonstrada no código enquanto o ganho econômico permanece desconhecido. A etapa seguinte deve conferir novamente os arquivos ao converter um contrato em trabalho de implementação.

## 3. Sonda reproduzível de capacidade e arredondamento

**Entradas artificiais:** compra com entrada 100.000, stop 99.900 e alvo 100.200 pontos; valor R$0,20 por ponto/contrato; margem R$155 por contrato; R$0,50 de tarifa por lado, corretagem zero e cinco pontos de slippage por lado. O custo total assumido é R$3 por contrato, resultando em +R$37 ou −R$23 por contrato. Esses valores não foram conferidos para uma conta.

A capacidade usa as restrições existentes de margem disponível e margem mais perda planejada dentro do patrimônio. Não depende de uma probabilidade favorável inventada.

Para observar apenas a fórmula, cópias dos planos admissíveis em memória receberam crescimento logarítmico calculado com probabilidades **hipotéticas** 0,65 e 0,35. Nenhum registro de validação foi promovido. A política atual aplica teto `floor(q_melhor × 0,25 / (1 + drawdown / 0,30))`.

| Patrimônio | Pico | Drawdown | Capacidade | Escolha do motor com metadados antigos | Escolha da política aritmética isolada |
|---|---|---|---|---|---|
| R$400 | R$400 | 0% | 2 | 0 | 0 |
| R$800 | R$800 | 0% | 4 | 0 | 1 |
| R$600 | R$800 | 25% | 3 | 0 | 0 |

Os metadados antigos continham `validated=true` e `temporal_holdout=true`, sem os novos requisitos. A sonda confirmou sua rejeição: nenhum plano positivo recebeu estimativa financeira aceita. A cópia aritmética não é uma decisão do serviço, replay validado ou demonstração de edge.

**Inferência de engenharia:** a ordem de otimização, aplicação da fração e arredondamento merece comparação discreta. **Hipótese experimental:** uma alternativa discreta ou robusta pode melhorar a relação crescimento/risco. Ela também pode produzir resultado desfavorável ou inconclusivo; o zero não será corrigido impondo um contrato.

## 4. Oportunidades de pesquisa e fonte de verdade

| Pergunta | Ticket responsável |
|---|---|
| Como impedir associação entre evidência e cenário incompatíveis? | [Identidade causal da decisão](../../.scratch/wayfinder-evolucao-decisao/issues/01-identidade-causal.md) |
| Como distinguir apoio, contraevidência, insuficiência e horizonte? | [Contratos das hipóteses JEV](../../.scratch/wayfinder-evolucao-decisao/issues/02-contratos-hipoteses.md) |
| Como medir utilidade depois de disponibilidade, latência e execução? | [Utilidade após latência e execução](../../.scratch/wayfinder-evolucao-decisao/issues/03-latencia-execucao.md) |
| Como comparar inteiros e distribuições incertas em trajetórias próprias? | [Dimensionamento sobre distribuições incertas](../../.scratch/wayfinder-evolucao-decisao/issues/04-dimensionamento-incerto.md) |
| Como manter decisão verificável e inspeção estável durante atualizações? | [Interface verificável e estável](../../.scratch/wayfinder-evolucao-decisao/issues/05-interface-verificavel.md) |
| Como separar ganhos de previsão, seleção e dimensionamento? | [Evidência incremental e promoção](../../.scratch/wayfinder-evolucao-decisao/issues/06-evidencia-promocao.md) |

O catálogo [E01–E10](Plano_Experimentos_JEV.json) permanece a referência dos experimentos. Os tickets acrescentam contratos e critérios, sem novas pesquisas duplicadas ou mudanças de status empírico.

## 5. Fontes primárias e limites de inferência

| Fonte | O que sustenta | Limite para este projeto |
|---|---|---|
| [TypeSafe — perguntas paralelas](https://docs.typesafe.ai/cookbooks/parallel_questions) | Perguntas do batch são avaliadas independentemente contra o documento. | Dependências entre respostas exigem composição explícita; benchmark externo não valida as hipóteses WIN. |
| [TypeSafe — confidence](https://docs.typesafe.ai/confidence/) | Para Choice, medida baseada na probabilidade máxima e no número de opções. | Não resume a distribuição nem representa chance de lucro. A fórmula foi conferida novamente na documentação oficial. |
| [Feast — point-in-time joins](https://docs.feast.dev/getting-started/concepts/point-in-time-joins) | Diferencia tempo do evento e criação; filtro adicional evita incorporar backfills posteriores. | Timestamp do negócio sozinho não comprova disponibilidade histórica. Não implica adoção de Feast. |
| [Sun e Boyd — Kelly robusto](https://stanford.edu/~boyd/papers/robust_kelly.html) | Formula otimização no pior caso de um conjunto de distribuições. | Conjunto, custos, execução e restrições do WIN precisam de desenvolvimento e avaliação próprios. |
| [Microsoft HAX — explicações](https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-why-the-system-did-what-it-did/) | Acesso à explicação do comportamento da IA. | Direção de desenho; compreensão do painel exige verificação com usuários e dados identificados. |
| [WCAG — atualização automática](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html) | Controle de atualização para permitir leitura, com exceções para atividade essencial. | Inspiração para inspeção histórica e alertas atuais; não comprova conformidade Windows. |
| [TypeSafe — descoberta de atributos](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery) | Fluxo experimental de atributos semânticos. | Resultado em outro dataset/modelo não é edge WIN e não dispensa confirmação intocada. |
| [Cawley e Talbot — seleção e sobreajuste](https://www.jmlr.org/papers/v11/cawley10a.html) | A seleção pode sobreajustar o critério de avaliação. | Perguntas, catálogo, cadência, features e políticas também devem ser congelados antes da confirmação. |

Estas fontes fundamentam métodos e contratos. As direções dos tickets são inferências de engenharia; nenhuma fonte externa determina os parâmetros financeiros da conta.

## 6. Custos, licença e vigência

A tabela educativa [B3 Educação](https://edu.b3.com.br/pt/day-trade) apresenta R$0,50 para entrada e saída do WIN. O default experimental examinado usa R$0,50 em cada lado. A especificação pede a tarifa aplicável por conta, fonte e vigência, mantendo separado esse exemplo da configuração operacional. A referência de margem R$155 também não substitui a margem contratada com a corretora.

A [Nelogica](https://ajuda.nelogica.com.br/hc/pt-br/articles/51583791325211-Como-obter-acesso-%C3%A0-ProfitDLL) exige contratação específica para ProfitDLL. O planejamento da integração deve registrar SDK autorizado, versão, licença, capacidades e direito de uso dos dados; acesso ao Profit Pro não será presumido suficiente.

A página de [políticas de market data B3](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/distribuidores/politica-comercial-e-contratos/) distingue vigência até 31/10/2026 e a partir de 01/11/2026. A referência posterior não substitui a política vigente nesta data nem determina, sozinha, o enquadramento contratual do projeto. Essa conferência depende do contrato e do uso efetivo; não foi obtida licença nova nesta entrega.

## 7. Entrega inicial — registro histórico

Foram documentados mapa, seis tickets, contratos internos, parâmetros em seleção, dependências e cenários de aceite. Permanecem Tauri/React, motor Python, conta manual, comparação com zero, JEV fixado, baseline logística e Excel parcial. A adaptação de 30% é referência, sem pausa automática; não existe progressão para recuperar perda.

Na entrega inicial, a fronteira era a identidade causal. Os contratos deveriam ser resolvidos progressivamente; o protocolo de evidência precisava estar fechado antes dos experimentos confirmatórios. O fechamento posterior está registrado na seção 8; dados, custos aplicáveis, orçamento e critérios ainda ausentes permanecem pendências explícitas.

**Verificação local desta entrega: PASS.** Nove novos arquivos Markdown em UTF-8, 64 vínculos locais existentes, seis tickets abertos com campos obrigatórios, dependências sem ciclos e fronteira WF-01. `git diff --check` passou para os documentos afetados. Os hashes dos 118 arquivos encontrados em `app/`, `desktop/` e `scripts/` por `rg --files --hidden`, respeitando os ignores, permaneceram idênticos; HEAD e catálogo E01–E10 também permaneceram iguais. Esses checks não validam interface Windows, execução financeira ou rentabilidade.

## 8. Fechamento das decisões — 07/10/2026

WF-01–06 e o [mapa](../../.scratch/wayfinder-evolucao-decisao/map.md) estão resolvidos documentalmente. A fonte de verdade agora são seis contratos: identidade, hipóteses, tempo/execução, dimensionamento, interface e evidência incremental, vinculados pela [especificação transversal](../../.scratch/wayfinder-evolucao-decisao/spec.md). A [sequência de implementação](../../.scratch/wayfinder-evolucao-decisao/implementation-plan.md) converte essas decisões em incrementos futuros e a [auditoria de aceite](../../.scratch/wayfinder-evolucao-decisao/acceptance-audit.md) registra cada requisito e as verificações executadas.

Os complementos de [hipóteses](Fechamento_Wayfinder_Hipoteses_2026-10-07.md), [tempo/economia](Fechamento_Wayfinder_Tempo_Economia_2026-10-07.md) e [interface/protocolo](Fechamento_Wayfinder_Interface_Protocolo_2026-10-07.md) preservam fontes, inferências e propostas. Revisão final corrigiu término de Choice sem resposta, classificação de benefício abaixo do efeito mínimo e réplicas com saldo não positivo, sem descartar oportunidades ou sobreviventes desfavoráveis.

O vetor de identidade e a fixture de patrimônio/drawdown foram conferidos por cálculo isolado em memória. A comparação final de fontes, links e tracker está na auditoria. Nenhum novo contrato foi implementado no aplicativo, experimento confirmatório executado ou interface Windows validada nesta rodada. E01–E10 e os estados empíricos JT não foram promovidos. O desenho não está pronto para confirmação: dados/direitos, custos/margem da conta, clocks/execução, orçamento, datas/N, precisão/efeito e tolerância de risco continuam indispensáveis e pendentes.
