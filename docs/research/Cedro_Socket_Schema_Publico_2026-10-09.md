# Cedro — schema público de conexão, 2026-10-09

> Publication projection: personal checkout paths and the conversation UUID are omitted. Non-personal task and reviewer role labels are retained as provenance. Acceptance, findings, source hashes and measured results are unchanged. Raw source SHA-256: feb5c43cbaf00bd615d0f126f1bfba98a98f548923cf729aa4007f9e54f37d83

## Conclusão documental

**As quatro páginas públicas examinadas não fecham um schema Socket versionado para implementar um parser Cedro de WIN/WDO.** O portal documenta bibliotecas de conexão ao Crystal Difusor e uma API HTTP separada. A biblioteca .NET contém um token WIN em exemplos de comandos de cotação e livro, mas nenhuma das páginas examinadas contém exemplo literal WDO, gramática das respostas de mercado, escopo/reset de IDs ou protocolo de snapshot/recovery. A relação exata entre as bibliotecas Crystal Difusor e o SKU comercial API Socket também não está fixada neste corpus. [Índice público](https://docs.cedrotech.com/llms.txt), [conector Python](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-python.md), [conector .NET](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-dot-net.md), [introdução HTTP](https://docs.cedrotech.com/reference/market-data-introduction.md).

É admissível propor uma SPEC offline de lifecycle e degradação com stub próprio, restrita aos contratos locais já estabelecidos. Uma SPEC de parser/payload Cedro continua dependente de documentação aplicável. Este adendo não implementa nem certifica essa futura SPEC, escolhe licença, resolve o ticket contratual 10 ou habilita feed.

Objetivo observado: qualificar uma rota independente do Profit para WIN/WDO sem inventar continuidade ou permissões. Baseline `5f15ab73f4f5adfd3221b9bd5f785c24c9afc496`; checkout exclusivo `{research_checkout}`. Pesquisa `/root/rt12_research`, integrador `/root`, conversa `[local conversation id omitted]`. O ticket 13 delimita esta diligência; registra recomendação JEV `cedro_schema`, confidence 0.96, recibo `c6639729-9e7e-4aa0-b48f-5c4acecdbc34`. Esse conselho não concede acesso privado nem autorização comercial. Não houve chamada JEV pelo pesquisador.

## Corpus e rastreabilidade

Foram examinadas exatamente **quatro URLs primárias adicionais**, todas em `docs.cedrotech.com`, sem seguir outros links. As respostas HTTP 200 foram lidas como bytes públicos por `urllib.request`, com `Accept-Encoding: identity`; SHA256 refere-se a esses bytes completos. O leitor web não abriu as rotas Markdown; isso foi uma limitação do leitor, não evidência de indisponibilidade Cedro. As páginas são mutáveis: hash e horário fixam a captura; `updatedAt` é data editorial, não versão do SDK ou protocolo. Não foram baixados SDKs, templates, PCAPs ou amostras de mercado.

| ID / URL literal | Captura UTC | `updatedAt` declarado | Bytes / SHA256 |
|---|---|---|---|
| C01 — https://docs.cedrotech.com/llms.txt | 2026-10-09T12:50:41.568408+00:00 | Não declarado no índice | 49024 / `9ed332be8542aa7b276284b3b0c6756a38c4711884cb44368c0b49f8f5960af5` |
| C02 — https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-python.md | 2026-10-09T12:51:46.516880+00:00 | 2026-03-06T17:16:15.000Z | 8544 / `2ef09c4e3e733704f189f35d8cd19503b5b872b78e7558e54a832978f4226209` |
| C03 — https://docs.cedrotech.com/reference/market-data-introduction.md | 2026-10-09T12:51:46.518317+00:00 | 2025-02-19T21:51:18.000Z | 2189 / `b5183ad7a6ea4980f7da88a3195c6e7ef6ee12dee5e4ef4d5dbb3da8e1c109ca` |
| C04 — https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-dot-net.md | 2026-10-09T12:52:16.272817+00:00 | 2026-03-06T17:16:08.000Z | 8577 / `c47ecae58cce2669f2942a0b36ea078c6cb562374af246a5daf1d3588c050585` |

O índice distingue API Market Data e bibliotecas de conexão. A introdução de Market Data descreve autenticação HTTP e cookie de sessão; ela não fornece o framing de uma conexão Socket. Nenhum schema GraphQL foi examinado ou utilizado como substituto. O índice é um catálogo de links, não um schema normativo; a ausência de um título Socket nele não prova ausência de documentação em todo o fornecedor. [C01](https://docs.cedrotech.com/llms.txt), [C03](https://docs.cedrotech.com/reference/market-data-introduction.md).

Evidência literal curta, com menos de 25 palavras por página, sem reproduzir exemplos completos:

| Fonte | Evidência literal | O que estabelece |
|---|---|---|
| [C01](https://docs.cedrotech.com/llms.txt) | “LIB Conexão Market Data” | Categoria de documentação de conectores no portal. |
| [C02](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-python.md) | “SQT PETR4”; “BQT PETR4” | Exemplos Python de solicitação de cotação/livro de uma ação; não identificam futuros. |
| [C03](https://docs.cedrotech.com/reference/market-data-introduction.md) | “Cookie de sessão (JSESSIONID)” | Sessão HTTP; não estabelece sessão, IDs ou sequência de eventos Socket. |
| [C04](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-dot-net.md) | “sqt winm24”; “bqt winm24” | Token WIN em exemplos .NET de solicitação de cotação/livro. Não comprova vencimento vigente, entitlement ou catálogo operacional. |

## O que o corpus permite afirmar

Estados: **C** = confirmado no documento genérico; **A** = ausente nas páginas examinadas; **NP** = condição aplicável ao cliente/SKU não publicada nesse corpus. Nenhum estado C comprova funcionamento de uma conta real. Ausência delimitada não significa inexistência no fornecedor.

| Aspecto requerido | Resultado e limite | Fonte |
|---|---|---|
| Superfície de conexão | C: bibliotecas Python/.NET ao Crystal Difusor, início/parada, envio de comando e callbacks de conexão/desconexão/mensagem. A: framing, encoding de resposta, tamanho máximo, negociação e versão normativa do protocolo. | [C02](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-python.md), [C04](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-dot-net.md) |
| Versionamento | C: datas editoriais registradas acima. A: versão fixa do pacote e do wire protocol. A orientação .NET para atualização contém um placeholder de versão, não um artefato imutável aplicável. | [C02](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-python.md), [C04](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-dot-net.md) |
| WIN/WDO e vencimento | C: token WIN no exemplo .NET. A: WDO literal, enumeração/resolução por vencimento, validade operacional do token, roll, timezone/calendário e mapeamento de identidade. Não inferimos esses campos a partir de letras do símbolo. | [C02](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-python.md), [C04](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-dot-net.md) |
| Cotação/livro/negócios | C: comandos de cotação e livro em exemplos; callbacks recebem texto. A: gramática/campos das respostas, tipos/unidades, timestamps, precisão, multiplicador/tick, profundidade L1/L2, snapshot versus delta, lado/agressor e mensagem de negócio. | [C02](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-python.md), [C04](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-dot-net.md) |
| IDs, sequência e reset | A: trade ID, identidade/escopo de mensagem, sequência contígua, reinício de sequência, fronteira de sessão e política de duplicatas. O cookie HTTP não preenche nenhum desses contratos de mercado. | [C02](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-python.md), [C03](https://docs.cedrotech.com/reference/market-data-introduction.md), [C04](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-dot-net.md) |
| Gaps, snapshot e recovery | C: exemplos de reinício do conector após desconexão. A: detecção de perda, snapshot consistente, ponto de corte, replay/cursor, alcance/limites de recuperação e garantia de continuidade. Reconectar não demonstra recuperação de negócios perdidos. | [C02](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-python.md), [C04](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-dot-net.md) |
| Conflation e realtime | C: opções `active_conflated` e `active_realtime`, ambas false por padrão; a primeira reduz frequência e a segunda seleciona servidores realtime em vez do padrão delay. NP: entitlement e atraso efetivo do SKU. Selecionar realtime não comprova autorização; conflation exige avaliação antes de qualquer claim de tape. | [C02](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-python.md), [C04](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-dot-net.md) |
| Lifecycle e falhas | C: no Python, uma instância destruída não pode ser reutilizada; é necessário outro objeto. Há exemplos de erros de autenticação/permissão. A: taxonomia completa, retry/backoff normativo e indicação de reset dos dados. Recriar um objeto não define recovery de mercado. | [C02](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-python.md), [C04](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-dot-net.md) |
| Logs e amostras | C: conectores documentam pasta local padrão para logs; exemplos imprimem mensagens e usam filas. NP: licença dos exemplos/SDK, autorização de retenção de payload e amostras sintéticas no dialeto do fornecedor. O exemplo não define limite de fila nem concede licença de dados. | [C02](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-python.md), [C04](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-dot-net.md) |
| Uso analítico/JEV, retenção, redistribuição, sandbox, preço/SLA | NP: direitos específicos, prazo, destino, cobertura de ambiente de teste e preço completo aplicável. Resultado, custo, latência e entitlement permanecem `null`. | [C01](https://docs.cedrotech.com/llms.txt), [C02](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-python.md), [C03](https://docs.cedrotech.com/reference/market-data-introduction.md), [C04](https://docs.cedrotech.com/reference/biblioteca-de-conex%C3%A3o-dot-net.md) |

## Fronteira da futura SPEC e dependências

Inferência técnica: callbacks e controles de lifecycle permitem desenhar uma interface local de transporte; não fornecem dados suficientes para normalizar uma mensagem proprietária. O caminho mínimo preserva os requisitos I-02/I-07 da [SPEC vigente](../specs/Multimercado_Implementacao_2026-10-09.md) e os [contratos locais](../../app/multimarket/contracts.py), sem adicionar SDK, rede, chaves ou parser Cedro.

| Caminho | Prontidão documental | Dependência / condição de conclusão |
|---|---|---|
| SPEC local de lifecycle com stub próprio | Elegível para especificação e revisão independente; implementação não feita nesta pesquisa. | Reutilizar contratos locais, separar epoch e estado de transporte, limitar filas, invalidar continuidade em perda/desconexão; não gerar payload supostamente Cedro. |
| SPEC Socket específica e parser | Não ready. | Identificar SKU ↔ conector e obter versão imutável, framing/grammar, tipos/unidades, metadata WIN/WDO e regras de sequência/reset/snapshot/replay. Sem isso, não há oráculo independente para testar parser. |
| Piloto real WIN/WDO | Bloqueado por dependência externa. | Tudo acima mais documentação do entitlement, uso analítico/non-display/JEV, retenção/export, ambiente e custo aplicáveis. Ticket 10 permanece aberto; esta pesquisa não solicita esses documentos por contato. |

Aceites **propostos**, para congelamento pelo coordenador antes de uma nova implementação; não são resultados certificados:

- **CED-OFF-01 — isolamento:** fixture própria usa somente o contrato normalizado local; execução sem SDK Cedro, rede, credencial, conta, mercado ou JEV. Verificação independente confirma os limites e que nenhum evento é apresentado como feed licenciado.
- **CED-OFF-02 — continuidade:** desconexão, overflow, gap e regressão conhecidos pelo contrato local invalidam continuidade; cotação nova ou reconexão isolada não restauram tape completo. Verificar com sequências determinísticas próprias e clocks controlados, sem atribuir sequência ao protocolo Cedro.
- **CED-OFF-03 — lifecycle:** parada impede eventos posteriores de restaurar estado; reconexão inicia epoch local explícita. Filas e deduplicação ficam limitadas. Testar callbacks tardios/duplicados com stub; não afirmar que isso reproduz o SDK.
- **CED-DOC-01 — parser:** antes de especificar parser, fixar documento/versionamento aplicável e respostas exemplificadas para cada tipo, com metadados, IDs, resets e recovery. Registrar lacunas como desconhecidas; não inferir campos do comando de assinatura.
- **CED-CON-01 — dados reais:** contrato/entitlement e direitos de dados aplicáveis precedem captura, retenção/export e envio ao JEV. Confirmar por evidência apropriada do ticket 10, sem transformar orientação JEV em aprovação humana.

Dependência de tarefas: congelar/revisar CED-OFF-01–03 pode ocorrer sem CED-DOC-01; parser depende de CED-DOC-01; captura real depende de CED-DOC-01 e CED-CON-01. A futura telemetria offline pode registrar somente cenário, epoch local, causa de degradação, contador/tamanho de fila, eventos aceitos/descartados e duração monotônica. Sem tokens, mensagens brutas, usuários ou dados de mercado. Resultado executado = `null`: nenhum desses novos testes foi implementado ou executado aqui.

Os valores locais `full_tape=False`, retenção/export desconhecidos e B3 bloqueada permanecem impostos pela SPEC, não por uma suposta proibição universal Cedro. Não se devem copiar os exemplos de logging/retry como política operacional: o projeto exige limites e tratamento explícito de permissões. Não há autorização explícita de amostra de mercado neste corpus; fixtures próprias do contrato local não dependem de afirmar licença para payload proprietário.

## Fontes locais imutáveis e encerramento

| Fonte local | SHA256 |
|---|---|
| `{integration_checkout}/.scratch/wayfinder-multimercado/issues/13-schema-publico-cedro.md` — leitura somente | `e9d362738ddf546b2e3932666fb1875c6df32afa2790fe131e6e32346f9c89a8` |
| `{research_checkout}/docs/specs/Multimercado_Implementacao_2026-10-09.md` | `af174497bf764b1a7c67818cee6e3b925a40933d98c40c8e14f5b1b0f6bc01f4` |
| `{research_checkout}/app/multimarket/contracts.py` | `0341d03ebed624a83f4475d40daf1cf6776a44ff9d6430a5c6598dad0740c899` |
| `{research_checkout}/docs/research/B3_Qualificacao_Publica_2026-10-09.md` — preservado | `372c44b66d683fb7bd6aceb0208f81b3a1b35cfdbe0f36da70666f16a6e68255` |
| `{research_checkout}/docs/research/RT12_Proximo_Ciclo_2026-10-09.md` — preservado | `607acb62c3df7c05bbf93298814c2282f690de7dfcd367fef85ad6c991b1ef73` |

O limite de quatro páginas foi consumido; não foi reaberta busca geral. A pesquisa encerra a dúvida pública com lacunas identificadas, não com schema inventado. Nenhuma instalação, login, trial, download de amostras de mercado, contato comercial, feed, ordem, chamada paga, alteração de ticket, commit ou push foi feita. Cabe ao integrador revisar este adendo e escolher o próximo recorte elegível; o dossiê anterior conserva a comparação CQG/UMDF sem ser reescrito. A relação com o ticket 10 permanece documental e pendente.
