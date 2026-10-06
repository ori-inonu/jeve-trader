# JEV/TypeSafe — auditoria aprofundada da decisão contextual

Pesquisa em 2026-10-06. Projeto inspecionado: `jev_profit_copilot`, v0.3.0. Escopo: observação e revisão de hipóteses WIN/B3; nenhuma ordem, chave, chamada autenticada, instalação ou alteração de produção. Esta nota é um intermediário para incorporação ao relatório principal.

## Resultado principal

**Recomendação de pesquisa:** priorizar o contrato semântico das perguntas, a abstenção e a avaliação do valor incremental sobre o motor determinístico. O batching já existe. Trocar modelo, adicionar dezenas de perguntas ou converter confiança em chance de lucro não resolve a lacuna central: ainda não há evidência neste material de que os julgamentos acrescentem qualidade à interpretação do tape WIN, nem de que selecionem setups com retorno superior.

**Fato local:** a UI envia perguntas sobre uma hipótese técnica depois de descartar a premissa produzida pelo gerador. Também mistura falta de cobertura com contradição. Essas duas ambiguidades são oportunidades concretas de pesquisa, independentemente de qualquer benchmark do fornecedor. Ver `desktop_app.py:592–605`, `candidate_research.py:192–199` e `candidate_engine.py:62–68`.

**Limite epistemológico:** documentação técnica comprova interfaces e relata comportamento/benchmarks do fornecedor. Não comprova acurácia em tape WIN, capacidade causal de prever preço, qualidade de execução, rentabilidade, taxa de acerto ou calibração de retorno financeiro. Não fiz medição remota; as latências abaixo são relatadas pelo fornecedor ou configuradas no código.

## 1. Fontes oficiais e o que efetivamente estabelecem

| Fonte primária | Trecho verificável | Relevância |
|---|---|---|
| [API](https://docs.typesafe.ai/api) | Linhas 31–82, 100–274, 294–370, 558–566 | REST, forma de perguntas/respostas, ids, limites por primitiva e erros |
| [Models](https://docs.typesafe.ai/models) | 30–40, 45–65, 70–86 | Modelo, orçamento de contexto, preço, limites dinâmicos, aliases, customização |
| [Confidence](https://docs.typesafe.ai/confidence) | 94–143 | Fórmulas exatas e distinção entre probabilidades e concentração |
| [Choice](https://docs.typesafe.ai/primitives/choice) | 42–46, 94–106, 280–302 | Nomes/descritivos de opções são vistos pelo modelo; ids de perguntas não |
| [Score](https://docs.typesafe.ai/primitives/score) | 30–43, 98–146 | Expectativa de níveis, ambiguidade e critérios concretos |
| [State](https://docs.typesafe.ai/concepts/state) | 24–43, 69–70 | Mesmo estado compartilhado; formatos e separação de fatos/perguntas |
| [Advanced structure](https://docs.typesafe.ai/primitives/advanced) | 31–54, 96–98 | Objetos e listas para limites, definições e critérios |
| [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13) | Revisão 2026-10-02; 47–56, 86–110, 115–139 | Falhas reconhecidas de literalidade, matemática, indireção, contexto e ordem |
| [Skill oficial](https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md) | 84–130 | Premissas explícitas, perguntas independentes, domínio próprio e investigação de falhas |
| [System One](https://docs.typesafe.ai/concepts/system-one) | 24–38 | Probabilidades treinadas para calibração; calibração é coletiva, não garantia individual |
| [Parallel questions](https://docs.typesafe.ai/cookbooks/parallel_questions) | 48–54, 234–303 | Exemplo de batching com jev-1.12 e cinco repetições |
| [Retries](https://docs.typesafe.ai/sdk/python/api/retries) | 46–48, 84–101, 122–124 | Política configurável, retry headers e orçamento total |
| [Autoresearch feature discovery](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery) | 24–40 | Jev como gerador de features para um modelo supervisionado downstream |


## 2. Contrato atual, limites e customização — fatos verificados

O endpoint documentado é `POST https://api.typesafe.ai/v1/systemone`, Bearer auth; o corpo contém `state`, `model`, `questions`. A resposta contém `model`, `answers`, `usage`, com resposta por id. Os ids das perguntas servem ao programa e não são usados na inferência. Choice aceita até 255 opções; Score tem 2–10 níveis; Noul pode ter critérios `true`/`false`. Erros documentados incluem 401, 422, 429 e 529. [API, linhas 31–82, 118–274, 294–370 e 558–566](https://docs.typesafe.ai/api).

A página de modelos lista `jev-1.13.0`; `jev-latest` e `jev-preview` apontam hoje a essa versão. Preço publicado: US$ 0,042/M tokens de entrada, saída grátis. Limites publicados: 100 mil tokens/s e 80 requests/s, explicitamente dinâmicos; contexto de 64k total e 32k para estado + maior pergunta. O fornecedor não oferece fine-tuning/LoRA por cliente: personalização ocorre por estado, instruções/critérios e composição, com possibilidade de modelo downstream. Inglês é a linguagem principal. [Models, linhas 30–72](https://docs.typesafe.ai/models).

**Fato local positivo:** `jev_client.py:17–19,67–85` fixa modelo e endpoint e exige que a resposta reporte a versão esperada. Isso segue a recomendação oficial de fixar uma versão ao calibrar comportamento. O adapter intencionalmente só permite Choice/Noul (`35–64`), embora a plataforma também suporte Score. Adicionar Score seria uma extensão de contrato, não uma capacidade já presente. Sua validação rejeita campos extras e respostas parcialmente preenchidas (`77–119`); isso favorece falha fechada, mas precisa de fixtures de compatibilidade quando o contrato evoluir.

**Proposta:** não substituir esse adapter durante a pesquisa. Comparar primeiro implementações isoladas com fixtures REST oficiais e erros simulados. Separar metadados de inferência, versão de perguntas e versão de regra de composição. Model pinning sozinho não fixa features, perguntas, fonte, janela ou interpretação.

## 3. Semântica correta — fatos e consequências

Noul devolve probabilidade de “sim” para a proposição escrita. Não é intensidade física. Um valor perto de 0,5 expressa incerteza entre sim/não. Choice devolve opção de maior probabilidade e distribuição sobre as opções. Seu `confidence` é `(p_max - 1/n)/(1 - 1/n)`: depende do número de opções e só usa a maior probabilidade; duas distribuições com runner-up distintos podem ter a mesma confiança. Noul não traz confidence separado; o fornecedor sugere, se necessário, `abs(2*p - 1)`. [Confidence, linhas 94–121](https://docs.typesafe.ai/confidence).

Score é a expectativa do índice de níveis descritos: `sum(i * p_i)`. Normalizar pelo maior índice coloca escalas no intervalo 0–1, mas não as torna uma frequência observada ou uma chance de sucesso. Distribuições muito diferentes podem ter a mesma expectativa. Níveis devem descrever situações completas e uma só dimensão. [Score, linhas 98–146](https://docs.typesafe.ai/primitives/score).

**Inferência:** `support - contradiction` não é probabilidade líquida, Bayes factor ou evidência independente. São duas perguntas ao mesmo modelo sobre o mesmo estado; independência computacional de avaliação não demonstra independência estatística. Tampouco se pode multiplicar Nouls para obter uma “confiança combinada” sem modelo validado de dependência.

**Proposta de apresentação:** manter “apoio à proposição X”, “contradição da proposição X”, cobertura e hipótese separados; preservar distribuições completas para análise. `classification_confidence` deve continuar identificado como concentração da distribuição. Rentabilidade só poderia ser pesquisada numa camada supervisionada distinta, com outcomes, horizonte, custos e execução definidos; nenhuma fonte aqui valida essa camada para WIN.

## 4. Lacunas concretas do código

### P0 de pesquisa — premissa e critérios da hipótese

`candidate_engine.py:62–68` cria uma premissa explícita; `candidate_research.py:196–199` a preserva na linha técnica. `desktop_app.py:603` exclui `premise`, `recipe` e a nota de interpretação, mandando apenas geometria, lado, id e níveis. A pergunta de `604` se refere à “technical hypothesis” e a de `605` à “directional hypothesis”, sem escrever qual é a proposição. A skill oficial exige premissa explícita para perguntas especulativas; perguntas estreitas podem carregar objetos estruturados com definições e limites. [Skill, linhas 92–114](https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md), [Structure, linhas 45–54 e 96–98](https://docs.typesafe.ai/primitives/advanced).

**Inferência:** a API pode responder sobre uma premissa inferida do nome `buy_stop0_target0` ou da geometria, em vez de uma premissa auditável. Além disso, as quatro alternativas de cada lado compartilham a mesma premissa genérica, ainda com uma disjunção “progressão OU absorção”. Isso não oferece discriminação explícita entre stop/target distintos.

**Experimento proposto:** ablação atual versus premissa explícita versus premissas separadas (progressão, absorção observada, contexto misto). Dividir famílias com gatilho, invalidação e horizonte observacional próprios; corrigir o payload sozinho ainda preservaria a premissa composta por OR. Uma pergunta deve avaliar o sentido da hipótese; outra a suficiência de evidência específica dos níveis. Não chamar essa última de “qualidade do stop” ou “probabilidade de atingir alvo”. Remover id descritivo do conteúdo do modelo no braço cego e restaurá-lo no envelope por mapeamento.

### P0 de pesquisa — ausência de evidência versus contradição

`desktop_app.py:605` pede que contradição avalie também “missing decisive coverage”. `questions.json` tem critérios opostos: sua pergunta de contradição diz que evidência ausente sozinha não é contradição. A UI usa `observer_questions.json` em `592`, portanto esse cuidado no arquivo antigo não corrige a pergunta dinâmica. `recommendation_engine.py:293–302` compara os Nouls diretamente.

**Experimento proposto:** três proposições distintas e rotuladas: apoio observado; contradição observada; suficiência de cobertura. Rotular casos “sem apoio, sem contradição, sem dados” separadamente de “apoio e contradição simultâneos”. A combinação em código deve admitir ambos altos e ambos baixos, sem forçar `contradiction = 1 - support`.

### P1 de pesquisa — abstenção e inconsistência entre respostas

`observer_questions.json:34–36` pergunta insuficiência, mas `recommendation_engine.py:85–118,279–304` não lê essa resposta nem as outras seis perguntas de apoio geral: só lê flow_context e os pares por candidato. `classification_confidence` é armazenada, não usada como gate; o teste em `test_recommendation_engine.py:27,38–51` deliberadamente aceita confidence 0,1. A desigualdade `support > contradiction` admite diferenças arbitrariamente pequenas.

**Qualificação:** isso é uma escolha explícita de motor descritivo, não prova automática de bug ou um motivo para inventar 0,65. A etiqueta é hipótese para revisão, `actionable_live_signal` continua falso e outros gates, incluindo cobertura, podem bloquear o caso. Não é acionamento de ordem. O risco de interpretação é uma etiqueta de revisão parecer conclusão suficientemente sustentada mesmo quando a distribuição do Choice é ambígua ou o Noul de insuficiência discorda.

**Experimento proposto:** replay de quatro quadrantes apoio/contradição, ambos perto de 0,5, flow inconclusivo, insuficiência alta e flow definido, múltiplos lados simultaneamente plausíveis. Produzir curvas de cobertura versus erro de interpretação, além de frequência de desacordo. Escolher política de abstenção depois de observar rotulagem e custos de erro; manter todos os thresholds atuais intactos.

### P1 de pesquisa — viés de ordem, denominação e fronteiras

`observer_questions.json:6–11` tem ordem fixa começando por `buy_progression`. Choice vê nomes e descrições das opções; ids das perguntas não. [Choice, linhas 42–46](https://docs.typesafe.ai/primitives/choice). O fornecedor reconhece preferência pela primeira opção, matemática fraca, leitura literal e piora com estado irrelevante; recomenda permutar alternativas, reduzir indireção e manter contas em código. [Jaggedness, linhas 47–56,86–110,115–139](https://docs.typesafe.ai/model-jaggedness/jev-1.13).

**Experimentos propostos:** permutar critérios mantendo significado; renomear rótulos de forma equivalente; permutar candidatos com remapeamento dos índices; inverter compra/venda e sinal das features num caso sintético simétrico; duplicar uma alternativa equivalente e verificar divisão artificial da massa; contrastar exemplos de fronteira (desaceleração sem janela anterior, negociação intensa sem deslocamento, tape parcial, agressor desconhecido). Reportar taxa de flips e distância das distribuições, não só coincidência do vencedor.

### P1 de pesquisa — baseline e redundância numérica

`flow_engine.py:298–334` já calcula progressão, absorção potencial e exaustão por regras, cobertura, volumes e deslocamentos. `app_core.py:181–191` envia as features numéricas, cobertura e definições, sem enviar essas hipóteses determinísticas.

**Inferência:** boa parte do que se pede ao JEV pode ser reconstrução de relações já calculadas, com ambiguidades numéricas desnecessárias. A comparação honesta deve ser contra o baseline completo, não contra uma tela sem interpretação.

**Experimento proposto:** braço A motor atual sem JEV; B JEV com estado atual; C JEV com relações semânticas pré-calculadas e dados essenciais; D baseline + JEV apenas nos casos onde regras têm ambiguidade legítima. Não enviar label esperado ao modelo no teste cego. Só promover perguntas que corrigirem classes de erro ou reduzirem tempo de revisão de maneira verificável.

### P1 de pesquisa — reproducibilidade e diário

`desktop_app.py:609–619` registra estado, resposta, timestamps, modo e latência, mas não o objeto exato de perguntas dinâmicas, hash de perguntas, versão de features ou política de composição. O caminho CLI antigo já registra `state_sha256` e `questions_sha256` (`copilot.py:251–253`), mas é outro fluxo. `app_store.py:75` limita o diário aos últimos 10 mil eventos de todos os tipos; não é arquivo de avaliação imutável.

**Proposta:** o dataset experimental deve persistir request exato sem segredo, resposta bruta validada, versão resolvida, hashes, code revision, ordem de opções/candidatos, relógios de fonte/request/receive/render, token usage, status de serviço e outcome/label posterior. Falhas de fonte, serviço, modelo e composição precisam de rótulos diferentes. Isso evita imputar ao JEV um erro que veio da observação ou do código.

## 5. Paralelismo, latência, freshness e custo de informação

**Fato oficial:** perguntas no mesmo request são avaliadas de forma independente e em paralelo contra o mesmo estado; não veem respostas umas das outras. Segundo request só é necessário quando o primeiro resultado determina busca de evidência ou novo estado/opções. Perguntas extras ainda usam tokens. [Skill, linhas 109–114](https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md).

**Fato local:** a UI já envia batch único em `desktop_app.py:592–613`: sete perguntas gerais, mais duas por candidato. O gerador produz até oito alternativas (`candidate_engine.py:19`), portanto até 23 perguntas nesse caminho. Uma thread evita bloquear a UI (`desktop_app.py:487–501`); não é paralelismo independente no servidor. Mínimo automático é 10s; timeout é 3s; validade contextual live é 2s de origem (`app_core.py:194–216`, `recommendation_engine.py:15,95–103`).

**Fato sobre benchmark:** o cookbook usa `jev-1.12`, cinco repetições e um artigo GDPR, com média batch 0,27s contra soma serial 2,71s. O ganho de 10x diminui se as chamadas individuais forem concorrentes. A tabela tem alguma variação: por exemplo mean 0,804 versus 0,814 numa Noul, apesar do título simplificar como respostas inalteradas. Não é SLA, benchmark do modelo pinado ou medição no computador de Gabriel. [Parallel questions, linhas 48–54,250–277,299–303](https://docs.typesafe.ai/cookbooks/parallel_questions).

**Inferência:** tempo útil é `freshness restante na origem - tempo até decisão/render`, não só duração HTTP. Uma resposta HTTP em 300ms pode chegar inútil se o trade já tinha 1,9s. O timeout de 3s não permite resposta útil de 3s para uma fonte com validade de 2s; a checagem posterior é essencial e já existe. Não alterar janelas para acomodar a API sem estudar o horizonte observado.

**Proposta de medição futura:** p50/p95/p99 de request, fila/UI, idade na submissão, idade no recebimento, idade na exibição; percentual de respostas válidas e úteis, 401/422/429/529/timeouts separados; estado pequeno/médio/grande, números de perguntas e cold/warm. O diário mede `latency_ms` da execução do job (`desktop_app.py:493–496,619`), sem decomposição desses componentes. Sem chave não existem medidas remotas desta pesquisa.

**Proposta de custo de informação:** a cada candidato/pergunta registrar quantas vezes a resposta muda a revisão correta e quantas vezes repete o baseline. Testar cache por hash de estado/perguntas/versão para replay e reprocessamento; em observação live, cache não autoriza estender freshness. Priorizar mudanças materiais de evidência, evitar chamadas sobre estados idênticos, perguntar detalhes de candidatos apenas quando o gate determinístico permitir. O contador atual limita número de calls (`desktop_app.py:576–590`), não tokens ou benefício por pergunta.

**Retries:** o adapter customizado faz uma tentativa sem retry (`jev_client.py:140–193`). A SDK oficial oferece RetryPolicy e orçamento de retry total; migrar para defaults pode aumentar latência/idade e calls sem intenção. [Retries, linhas 46–48,84–101,122–124](https://docs.typesafe.ai/sdk/python/api/retries). Pesquisa deve separar política offline de política live e jamais repetir automaticamente um estado vencido.

## 6. Desenho de perguntas experimentais, sem implementação de produção

Usar instruções estruturadas para separar `question`, `premise`, `evidence_scope`, `exclusions` e critérios `true`/`false`. Esses nomes internos seriam escolha do projeto, não novos campos reservados da API. Não incluir a resposta esperada; incluir exemplos de fronteira apenas no conjunto de desenvolvimento. [Structure, linhas 31–54,96–98](https://docs.typesafe.ai/primitives/advanced).

Conjunto candidato de julgamentos estreitos:

1. A progressão descrita está sustentada pelas observações da janela indicada?
2. Há um fato observado que contradiz especificamente essa progressão?
3. Faltam elementos necessários para avaliar a hipótese?
4. A premissa de absorção é compatível com os fatos observados, sem inferir ordens ocultas ou reversão?
5. O material distingue exaustão de mera baixa atividade, dado o segmento anterior já calculado?
6. Os níveis referenciados têm evidência observada suficiente para a interpretação declarada? Isso não valida suporte/resistência preditiva.

Uma Choice pode oferecer estados “sustentada”, “contradita”, “mista”, “não avaliável” para um diagnóstico exclusivo, ou Nouls separados podem permitir coexistência. Comparar formatos; não supor superioridade de um deles. Score só merece extensão experimental se houver dimensão ordinal concreta e rotulável, como suficiência semântica da evidência; não usar score para inventar quantidade, preço ou probabilidade de P&L.

**Contrafactuais:** remover a janela anterior deve reduzir conclusões de exaustão; retirar cobertura de agressor não pode produzir agressor conhecido; remover a premissa deve levar a não avaliável; alterar patrimônio não deve alterar interpretação (nem entrar no request); trocar id de setup não deve alterar julgamento; remover evidência favorável deve afetar apoio, e não transformar automaticamente ausência em contradição. São hipóteses de teste de invariância, não resultados medidos.

## 7. Evals, drift e valor incremental

**Proposta metodológica:** rotular interpretação contextual primeiro, resultados financeiros em estudo separado. Para contexto, dois revisores veem só passado disponível até cada snapshot; preservar desacordo e classe ambígua. Dataset deve incluir dias/regimes, janelas sobrepostas, tape parcial, falta de book, agressor desconhecido, alternância e fronteiras das regras. Split por pregão/tempo, não shuffle de snapshots vizinhos: desenvolvimento para perguntas, validação para política, teste final intocado, depois shadow prospectivo. Quantificar confusão, erro com abstenção, cobertura, Brier/log loss por proposição rotulada, confiabilidade por regime, invariância, inconsistência e tempo humano de revisão.

Comparar A/B/C/D descritos acima no mesmo conjunto, estratificado por qualidade da fonte. Ganho aparente concentrado em um único dia, redutor de cobertura excessivo ou confundido com regras pré-calculadas não estabelece valor robusto. Monitorar drift de features, cobertura, frequência de labels, distribuição de respostas, taxa de abstenção e erros em amostras auditadas; modelo pinado reduz uma fonte de mudança, não drift do mercado.

O cookbook de autoresearch demonstra geração de features Jev para regressor supervisionado em notas de vinho, com avaliação held-out. É um padrão arquitetural de pesquisa, sem validação de qualquer feature no WIN. [Autoresearch, linhas 24–40](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery). Uma camada downstream só merece exploração se uma pergunta agregar informação além das features já existentes, e precisa de separação temporal e controle de vazamento próprios.

## 8. Ordem de trabalho sugerida e perguntas ainda abertas

1. **Primeiro:** documentar exatamente a proposição de cada pergunta e tornar verificáveis as diferenças entre premissa, apoio, contradição e cobertura; preservar versão atual como controle.
2. **Segundo:** construir replay rotulado e invariâncias com baseline determinístico, sem chamar API inicialmente. Fixtures sintéticas verificam composição e contratos, mas não acurácia do modelo.
3. **Terceiro:** com execução experimental autorizada e chave fornecida ao ambiente pelo usuário, rodar comparação remota delimitada, budget de tokens/calls e medição de freshness útil. Não foi executada aqui.
4. **Depois:** estudar abstenção, variações de pergunta/ordem, estado semântico filtrado e custo de informação. Só discutir novos thresholds depois de evidência fora da amostra.

Aberto: disponibilidade/SLA sob carga real; p95/p99 desde a fonte de Gabriel; repetibilidade de distribuições com jev-1.13.0; quanto melhoram interpretação/revisão contextual; quais perguntas são redundantes; comportamento em Português de avisos/descrições locais; persistência de versão de prompts e features; se há ground truth confiável de hipóteses de absorção. Nenhuma documentação encontrada resolve essas questões do produto.

### Evidência que permite encerrar esta pesquisa

Foram lidos documentos oficiais de contrato/modelo/primitivas/estado/confiança/limitações/skill/padrões/cookbooks e os caminhos locais de request, armazenamento e composição. Há oportunidades específicas suficientes para um plano de pesquisa. Continuar enumerando todo o catálogo de cookbooks tem baixo valor frente ao próximo passo: dataset de replay e proposições explícitas.
