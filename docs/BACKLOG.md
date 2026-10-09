# Backlog acionável do Jeve Trader

## Revisão contra main e próximo ciclo — 09/10/2026

O [PR #2](https://github.com/ori-inonu/jeve-trader/pull/2) foi revisado contra `main` (`0171aed6c4a25adf26d349bfe2c3140805a35e97`). O candidato de código corrigido é `e52172de0c127a8f1d3768cc072964501eb8ff69`, árvore `3e2e3ceb4856ea71ec1b903efda4fc6fd729098e`. As revisões independentes [Standards](evidence/pr2-main-standards-final.md) e [Spec](evidence/pr2-main-spec-final.md) terminaram com zero achados restantes. A [evidência Windows offline](evidence/pr2-main-verification-public.json) registra 326 testes Python, autoteste legado, 36 testes frontend e build TypeScript/Vite aprovados. Rust offline foi reaproveitado porque seus arquivos não mudaram. O merge local com a baseline não tem conflitos; checks e base remotos são conferidos separadamente antes da entrega.

Corrigidos os dois achados reproduzidos: concorrência entre OFF e despacho JEV e retenção ilimitada de identidades. Os [aceites R-01–R-04](specs/PR2_Revisao_Main_2026-10-09.md) e o [RED/GREEN](evidence/pr2-repair-tests.md) preservam FW-01 e I-01–I-12. OFF pode aguardar uma tentativa já iniciada; timeout de transporte não comprova latência da janela.

A [SPEC de instrumentação e protocolo](specs/Instrumentacao_Protocolo_Multimercado_2026-10-09.md) está **ready_local para EN-T1–EN-T3**, conforme [revisão independente](evidence/rt12-next-spec-readiness-final.md), SHA-256 `9e6d06ed4ea275981bdcf8c0d4d26e568b3ff79d9f9be20482feb06e77565e26`. O cabeçalho draft conserva o snapshot exato revisado; este registro e o relatório fixam sua prontidão. Isso é planejamento concluído, sem implementação dessas três tarefas nesta rodada.

| Próxima entrega | Dependência e aceite |
|---|---|
| EN-T1 — origem e manifest de pacote | Hashes de código/artefatos, validação fechada e regressões offline; primeiro incremento local elegível |
| EN-T2 — correlação de telemetria | Origem EN-T1; relógio único do renderer, allowlist, buffer limitado e sanitização |
| EN-T3 — protocolo verificável | Schemas de run/tarefa/evento/pares; estados e falhas preservados; ganho null |
| EN-T4 — jornada Windows J1–J6 | Pacote identificado, observação nativa e ponte J6 comprovada; não executada |
| EN-T5 — comparação humana prospectiva | Tratamento B congelado, ambiente equivalente ou diferenças qualificadas e cinco pares completos; não executada |

O JEV recomendou [fechar schemas locais](evidence/rt12-schema-jev.json) e [aprofundar o schema público Cedro](evidence/b3-next-diligence-jev.json). A consulta anterior de prioridade foi inválida e não virou recomendação. O [dossiê B3](research/B3_Qualificacao_Publica_2026-10-09.md) delimita Cedro/CQG/UMDF; SKU WIN/WDO, entitlement, licença e direitos de retenção/envio ao JEV continuam sem confirmação. O [adendo Cedro](research/Cedro_Socket_Schema_Publico_2026-10-09.md) encerrou quatro páginas de pesquisa: parser real não ready; faltam payload versionado, identidade WDO e recuperação aplicável. Conta real depende de fonte/formato/autorização; calibração financeira depende de corpus e aprovação por escopo. Ordens permanecem desabilitadas. O piloto FW-11 de 30 minutos e seus critérios originais continuam abertos; a prontidão local do código não certifica release operacional.

## Incremento multimercado — 09/10/2026

IMP-01–IMP-05 estão concluídos no escopo local e revisados independentemente na branch `codex/multimarket-spec`. IMP-05 registra a verificação e a revisão independente no [contrato finito](specs/Multimercado_Implementacao_2026-10-09.md), com [evidência por aceite](evidence/multimarket-acceptance.md). A conclusão local desses tickets conserva as dependências externas abaixo e o histórico JT.

| Próxima fronteira | Evidência necessária antes de habilitar |
|---|---|
| B3 sem Profit | Fornecedor/SKU WIN/WDO, entitlement, schema/captura autorizada e licença de uso/retention/export |
| Conta automática | Escopos read-only, fixture autorizada, reconciliação com posição/saldo reais |
| Modelo financeiro por mercado | Corpus licenciado, comparação temporal sem leakage, custos e aprovação por instrumento/venue/horizonte/metadata |
| Nova distribuição Windows | Build instalável, jornada nativa e comparação prospectiva pareada; métricas sintéticas não comprovam benefício |

Nenhum desses gates é encerrado pela presença de contratos ou botões no cockpit. O planejamento histórico de 07/10 abaixo mantém seus próprios critérios.

**Atualizado em 07/10/2026.** Critérios abaixo preservam o escopo do estudo de 06/10; o quadro atual identifica o que já foi demonstrado. Protocolo e gates: [ROADMAP.md](ROADMAP.md). Decisão aceita: [ADR 0010](decisions/0010-painel-e-capital-progressivo.md). Evidência: [status](IMPLEMENTATION_STATUS.md).

## Planejamento Wayfinder — 07/10/2026

Resolvidos documentalmente WF-01–06 no [Scratch de inteligência e interface](../.scratch/wayfinder-evolucao-decisao/map.md), com [contratos/parâmetros](../.scratch/wayfinder-evolucao-decisao/spec.md), [sequência de implementação](../.scratch/wayfinder-evolucao-decisao/implementation-plan.md) e [auditoria de aceite](../.scratch/wayfinder-evolucao-decisao/acceptance-audit.md). Quando a implementação for retomada, a sequência começa pela identidade causal no código, após recapturar o checkout e reivindicar o incremento. Os tickets estendem E01–E10 e os itens JT existentes; o fechamento documental não altera os estados empíricos abaixo. Dados, custos, orçamento e limites de confirmação permanecem pendentes no protocolo. Evidências e limites no [complemento datado](research/Complemento_Wayfinder_JEV_WIN_2026-10-07.md).

Gabriel solicitou continuar em planejamento após esse fechamento. A nova rodada está no [mapa de oportunidades com valor verificável](../.scratch/wayfinder-proximas-oportunidades/map.md): investigar composições JEV, aquisição/anotação de evidência e compreensão da interface; depois escolher uma direção para especificar. Esta descoberta não promove experimentos nem substitui os seis contratos anteriores.

## Estado atual por item

| Item | Estado em 07/10/2026 | Continuação concreta |
|---|---|---|
| JT-001 | Concluído no escopo offline Windows: 188 testes/autoteste, regressões e preservação da revisão local. | Manter regressões ao alterar contratos. |
| JT-002 | Parcial: premissa literal/versionada e continuidade/absorção separadas no payload/registro. | Projetar família de exaustão e verificar todas as dependências de dados por família. |
| JT-003 | Composição local implementada/testada; dimensões independentes e ausência explícita. | Validação empírica dos seletores pertence a JT-008/016. |
| JT-004 | Parcial: registro reproduzível de pedidos/respostas/falhas, clocks, conta/custos e hashes. | Protocolo experimental final, retenção e associação completa aos desfechos reais. |
| JT-005 | Parcial: timeout, geração/revisão e contexto vencido verificados offline. | Medir clocks, cobertura e latência reais; sem percentis simulados como medidos. |
| JT-006 | Parcial: novo pacote instalado/reinstalado/desinstalado em Windows; janela e processos verificados; formulários na prévia React. | Exercitar formulários na janela nativa e RTD real em uso prolongado. |
| JT-007 | Pendente externo: não há contrato real reconciliado do feed. | Obter amostra autorizada, mapa de campos/IDs, símbolos, relógios e correções. |
| JT-008/009/016 | Protocolos empíricos pendentes. | Congelar hipóteses/perguntas, orçamento e avaliação remota sem usar teste futuro na seleção. |
| JT-010 | Parcial: replay causal de preço, censura por cobertura/hash/contrato e custos implementados. | Validar captura WIN e acrescentar fila, liquidez/executabilidade e execução parcial. |
| JT-011 | Parcial: comparação pareada com/sem JEV e bootstrap por sessão implementados; smoke sintético. | Avaliar utilidade incremental em dados WIN futuros e custo real da API. |
| JT-012 | Pendente empírico. | Ablacionar features e episódios após integridade/apuração. |
| JT-013 | Parcial: logística multiclasse, calibração temporal, Brier/log-loss/ECE e intervalos offline. | Aprovação em WIN, monitoramento de regime, artefato versionado e integração online. |
| JT-014 | Parcial: livro manual com entrada/saída parcial, margem, custos e revisão. | Conciliação externa autorizada e observação de exposição real. |
| JT-015 | Parcial: comparação finita de quantidades/aguardar e Choice tipado no motor; políticas no laboratório. | Integrar estimativas aprovadas e Choice ao serviço, selecionar parâmetros temporalmente e avaliar live sem ordens. |

**Painel e distribuição 0.4 entregues:** Tauri/React/Python, quatro áreas, COM isolado, capital progressivo e instalador/portátil Windows. **ProfitDLL real pendente:** contrato de Market Data preparado; SDK/licença/ABI ainda necessários. **Pesquisa de risco:** 17 variantes executáveis offline, com progressões após perdas restritas ao laboratório; piramidagem é protótipo sem trajetória intratrade, e trailing/stops alternativos permanecem pesquisa. [Guia](DECISION_PANEL.md) e [estudo atualizado](research/Pesquisa_Decisao_JEV_WIN_2026-10-06.md#13-implementação-experimental-em-07102026).

## Critérios históricos e entregas restantes

Os estados “proposto” nos detalhes abaixo representam a redação original; use o quadro acima para o status atual. Nenhum item empírico passa a concluído apenas porque há código ou dados sintéticos.

## Como usar

Cada item especifica dependências de engenharia, fonte da necessidade, entrega e critérios de conclusão. Concluir software não conclui um experimento empírico. Para atualizar status, anexar commit, comandos/ambiente, artefatos e alcance exato da evidência. Falta de dados, acesso ou Windows significa **bloqueado/inconclusivo**, não aprovado. Não executar rede, mercado ou ordens por efeito deste documento.

**Fontes locais:** [R: pesquisa](research/Pesquisa_Decisao_JEV_WIN_2026-10-06.md); [P: plano E01–E10](research/Plano_Experimentos_JEV.json); [D: desenho atual](../app/DECISION_DESIGN.md); [V: validação v0.3](../app/VALIDATION.md). A suíte documentada de 166 testes é evidência histórica de software em Linux; deve ser reproduzida, sem exigir o mesmo número após mudanças. O script de pesquisa não consulta JEV nem mercado.

## Ciclo v0.4

### JT-001 — Reproduzir a linha de base e congelar regressões

- **Prioridade / status:** P0 / proposto. **Dependências:** nenhuma. **Experimentos:** suporte a E02–E05; não execução empírica.
- **Evidência:** R §§2 e 12; V, alcance dos testes; `research/study-2026-10-06/reproduce_examples.py` e resultados auditados.
- **Trabalho:** localizar comandos da suíte/autoteste e executar a revisão atual; reproduzir os exemplos a partir da cópia auditada e confrontar o caminho atual; criar fixtures rotuladas para premissa omitida, contradição direta, informação ausente, estado misto, resposta insuficiente, resposta inválida, mudança de fonte/geração, geometria alterada, expiração e veto financeiro.
- **Concluído quando:** ambiente, revisão, comandos e resultados da linha de base estiverem registrados; os defeitos relevantes estiverem reproduzidos e as fixtures de regressão demonstrarem a falha anterior à correção; cobertura testar comportamento observável na Central/HTML e não apenas repetir expressões da implementação; diferenças entre cópia auditada e app atual estiverem explicadas. Este gate inicial não exige corrigir os defeitos. A passagem das regressões pertence aos tickets de correção correspondentes e ao fechamento do ciclo. Nenhum resultado chamado de acurácia JEV ou edge WIN.
- **Estado em 07/10/2026:** regressões locais implementadas e suíte reproduzida com 188 testes/autoteste em Windows. JT-001 concluído no escopo offline. Evidência no status atual.

### JT-002 — Preservar premissa e separar famílias de hipótese

- **Prioridade / status:** P0 / proposto. **Dependências:** JT-001. **Experimento:** E02, parte de software.
- **Evidência:** R §2.1; P/E02; D §§3–4. Pontos iniciais: `candidate_engine.py`, `candidate_research.py`, projeção de cenário em `desktop_app.py`.
- **Trabalho:** transportar premissa literal em todo o caminho candidato → estado enviado → pergunta → resposta → decisão/histórico; substituir a disjunção continuidade-ou-absorção por hipóteses identificadas de progressão, absorção e exaustão, cada uma com confirmação, invalidação, alternativa relevante, capacidades de dados exigidas e horizonte. Manter geometria separada da proposição contextual.
- **Concluído quando:** payload e registro preservarem a proposição exata e sua versão; IDs/descrições distinguirem famílias e lado; testes impedirem reconstrução silenciosa só pelo nome/lado; falta de livro tornar a hipótese dependente de livro indisponível; absorção observada não promover automaticamente cenário de reversão; resposta incompatível com hipótese/versão for rejeitada; regressões de premissa/família preparadas em JT-001 passarem após a correção. Comparação remota entre braços permanece JT-016.

### JT-003 — Separar e consumir apoio, contradição e insuficiência

- **Prioridade / status:** P0 / proposto. **Dependências:** JT-001, JT-002. **Experimentos:** E02/E03, contrato e composição local.
- **Evidência:** R §§2.2–2.3; P/E02–E03. Caminho auditado carrega `observer_questions.json`, acrescenta perguntas dinâmicas e ignora `evidence_insufficient` na revisão.
- **Trabalho:** revisar o conjunto realmente carregado pela UI; formular julgamentos independentes de apoio observado, contradição direta e suficiência para distinguir uma explicação alternativa. Implementar uma política versionada que consuma explicitamente insuficiência, resposta ausente/inválida e inconsistência; expor motivo e estado na Central/HTML. Registrar a interpretação escolhida antes dos testes, com tabela de casos, sem alegar calibração econômica.
- **Concluído quando:** ausência não contar como contradição; apoio/contradição não forem forçados a somar um nem virarem probabilidade financeira; mudar a dimensão de insuficiência alterar a decisão ou seu veto conforme a tabela declarada; ausência/invalidade não promover revisão silenciosamente; estados mistos forem visíveis; qualidade/risco determinísticos prevalecerem; regressões de composição preparadas em JT-001 passarem após a correção. Não escolher um limiar de entrada ou lucro neste ticket. Qualquer seletor numérico de pesquisa será avaliado em JT-008, fora do teste final.

### JT-004 — Criar registro experimental completo, separado e versionado

- **Prioridade / status:** P0 / proposto. **Dependências:** JT-001; contrato final depende de JT-002/JT-003. **Experimentos:** infraestrutura de E02–E10.
- **Evidência:** R §2.5; diário atual limita retenção e não conserva todas as perguntas dinâmicas exatas.
- **Trabalho:** definir schema com IDs de sessão/oportunidade/candidato/chamada, estado efetivamente disponível, origem/capacidades/geração, hipótese e geometria, perguntas e ordem exatas, versões/hashes de código/config/features/política, modelo solicitado e versão resolvida quando informada, resposta validada, motivos/vetos, latência e custo conhecido ou desconhecido. Associar outcomes futuros por evento separado com horário de disponibilidade e método, preservando a decisão original.
- **Concluído quando:** uma avaliação puder ser reconstituída do registro sem pedir a configuração atual; replay não incorporar outcomes futuros; feed/API/interpretação/decisão tiverem categorias distintas; segredos e credenciais estiverem excluídos; retenção/exportação não dependerem do limite de 10 mil eventos visuais; schema tiver versão, compatibilidade documentada e validação de leitura/gravação, incluindo registro parcial/falha. Modelo não informado pela API é desconhecido, não inventado.

### JT-005 — Instrumentar qualidade, relógios e orçamento de tempo

- **Prioridade / status:** P0 / proposto. **Dependências:** JT-001, JT-004. **Experimento:** E05, instrumentação; medição real depende de E01/JT-007.
- **Evidência:** R §6; P/E05; D §9. Intervalos atuais e exemplo 1.900+300 ms são configuração/demonstração, não medição remota.
- **Trabalho:** registrar fonte, recebimento, processamento, submissão, resposta e exibição, com fuso/unidade e clock skew conhecido/desconhecido; usar duração monotônica onde aplicável. Separar idade do evento, idade da cotação, latência HTTP, fila e heartbeat; declarar capacidades, ordem temporal e continuidade verificada/desconhecida. Preparar relatório p50/p95/p99, vencimento e custo por avaliação utilizável.
- **Concluído quando:** fixtures de atraso, relógio incoerente, timeout e resposta pós-troca de geração produzirem razões corretas; resposta/cache não renovarem idade da evidência; sem heartbeat idade do último negócio não afirmar conexão saudável; relatório diferenciar números sintéticos e medidos; inexistência de amostra produzir desconhecido, sem percentis inventados. Não aumentar TTL para fazer a latência caber. Horizonte útil será verificado junto ao replay causal JT-010.

### JT-006 — Validar instalador e integração em Windows real

- **Prioridade / status:** P0 de distribuição / proposto; ambiente Windows necessário. **Dependências:** JT-001; repetir sobre o pacote final após JT-002–JT-005. **Experimentos:** validação de produto, sem substituição de E01.
- **Evidência:** V, abertura Windows não validada; `app/WINDOWS_BUILD.md`, `app/GUIA_WINDOWS.md` e relatórios em `docs/evidence/`.
- **Trabalho:** reproduzir build e identificar hashes; instalar por usuário em Windows x64, abrir Central nativa, testar atalhos/diagnóstico, validar runtime e persistência de diário/logs, desinstalar e verificar preservação documentada de dados. Testar COM com Excel existente e depois perfil RTD real identificado; guardar logs e imagens sanitizados, versões e passos.
- **Concluído quando:** relatório separar instalação/janela, lógica, COM real e RTD real; falha observada tiver diagnóstico e reteste; pacote portátil tiver extração integral e abertura verificadas; teste de erro de permissão não abrir contorno indevido; ausência de assinatura e dependência da pasta inteira documentadas. Sem ambiente real, registrar pendência: PE, mocks COM, HTML e autoteste Linux não aprovam este gate.

## Fundamentos empíricos e robustez

### JT-007 — Formalizar fonte e integridade de eventos

- **Prioridade / status:** P0 / proposto. **Dependências:** JT-004, JT-005; acesso/dados reais necessários. **Experimento:** E01; pré-requisito empírico de E05/E06.
- **Evidência:** R §4; P/E01; D, captura Excel amostrada/parcial.
- **Trabalho:** documentar contrato/aba/filtros, execuções versus Ordem Original, campos/unidades, IDs e escopo, tipos, agressor, sessões, horário, sobrescrita/overflow e recuperação. Preservar duplicata idêntica versus edição com mesmo ID, referência de correção e eventos especiais. Conciliar contra referência do mesmo contrato/período/unidade; testar reconexão, empate de horário, lacuna, leilão, RLP e reset de sessão.
- **Concluído quando:** manifesto e relatório de reconciliação mostrarem perda, eventos não resolvidos e divergência por sessão; capacidades de cotação, tape, profundidade/ofertas forem explícitas; ordem de timestamps não provar continuidade; não presumir sequência +1 por ativo; sem denominador confiável cobertura permanecer desconhecida. Não declarar tape completo sem prova.

### JT-008 — Avaliar abstenção e inconsistência

- **Prioridade / status:** P1 / proposto. **Dependências:** JT-003, JT-004, JT-016. **Experimento:** E03; dependência original E02.
- **Evidência:** R §§2.3 e 8.3; P/E03.
- **Trabalho:** congelar rótulos de interpretação e cobertura; comparar composição atual, suficiência explícita e seletor ajustado apenas em validação. Separar cobertura do feed de oportunidades aceitas; relatar erro/cobertura, desacordo e cobertura por hora. Registrar rejeições e, após JT-010, resultados contrafactuais em replay sob a mesma execução.
- **Concluído quando:** protocolo, curvas e incerteza estiverem publicados com todos os casos/rejeições; limiar/seleção não usar teste externo; quase-abstenção total não for descrita como melhora suficiente; avaliação interpretar custo/inatividade e concluir passou/falhou/inconclusivo. Resultado contextual não afirmar utilidade financeira antes de JT-011.

### JT-009 — Medir sensibilidade à ordem, nomes e simetria

- **Prioridade / status:** P1 / proposto. **Dependências:** JT-002, JT-004, JT-016. **Experimento:** E04; dependência original E02.
- **Evidência:** R §2.4; P/E04. Primeira opção `buy_progression` é achado de contrato, não viés comprador empiricamente demonstrado.
- **Trabalho:** preparar transformações reversíveis de ordem Choice/candidatos, nomes neutros e espelhamento sintético compra/venda; congelar casos e balanceamento; repetir chamadas segundo orçamento e registrar distribuição completa.
- **Concluído quando:** transformações preservarem significado e geometria válida; mapeamento recuperar a classe original; relatório medir taxa de troca, variação da distribuição e sensibilidade ao conjunto candidato com incerteza; repetições correlacionadas não inflarem amostra; resultado permitir manter, corrigir ou remover perguntas sensíveis. Fixtures locais não comprovam robustez remota.

### JT-016 — Congelar protocolo e executar validação remota de E02

- **Prioridade / status:** P0 para E02 remoto / proposto. **Dependências:** JT-002, JT-003, JT-004, JT-005; para casos reais, JT-007. **Experimento:** E02; fornece protocolo a E03/E04.
- **Evidência:** P/E02 e orçamento API nulo; R §§2 e 12.
- **Trabalho:** congelar casos sintéticos rotulados por proposição, braços payload atual/premissa explícita/famílias separadas, modelo e perguntas versionadas; definir repetição, precisão desejada, unidade efetiva, critérios de passagem e orçamento antes de chamadas autenticadas. Separar amostra sintética de fonte real; registrar todas as tentativas, inclusive descartadas.
- **Concluído quando:** fidelidade à premissa, desacordo por família e erro na falta de dados tiverem resultados reproduzíveis com incerteza e alcance; custos/latências conhecidos ou explicitamente indisponíveis; conclusão referir o gate pré-definido. Sem acesso/orçamento, entregar protocolo pronto e manter execução pendente. Não há tamanho universal de amostra ou promessa de resultado positivo.

## Replay, avaliação e refinamento

### JT-010 — Implementar replay causal e apuração de execução/desfechos

- **Prioridade / status:** P0 / proposto. **Dependências:** JT-004, JT-005, JT-007. **Experimentos:** E06 e fechamento causal de E05; dependências originais E01/E05.
- **Evidência:** R §§6–7; P/E05–E06.
- **Trabalho:** congelar candidato, regras de entrada/saída/roteamento, validade, horizonte e estado disponível. Modelar toque ideal, execução plausível e adversa pré-definida; respeitar chegada/latência, não entrada, preenchimento parcial quando observável, alvo/stop, timeout, sessão forçada e dados irresolúveis. Custos por saída/quantidade e pressupostos de fila explícitos.
- **Concluído quando:** replay reproduzir outcomes e custos; nada preencher cotação anterior à chegada; empate/ordem desconhecida não escolher caminho favorável; timeout econômico diferir de perda de feed; cenários evidenciarem limites sem fila inventada; custos líquidos não descontarem spread/slippage duas vezes; horizonte útil e fração de respostas vencidas forem medidos no percurso causal. Dados amostrados insuficientes levam a irresolução/limites, não preenchimentos fabricados.

### JT-011 — Comparar baseline e JEV em oportunidades pareadas

- **Prioridade / status:** P1 / proposto. **Dependências:** JT-008, JT-009, JT-010, JT-016. **Experimento:** E07; dependências originais E02/E03/E04/E06.
- **Evidência:** R §§3 e 8; P/E07; D §7.
- **Trabalho:** avaliar A regras atuais, B modelo quantitativo básico, C B+JEV e D JEV só em ambiguidades pré-definidas. Mesmas oportunidades/estado, custos e limites; separar treino, escolha/calibração e blocos futuros intocados. Purgar outcomes ainda não disponíveis; agrupar candidatos simultâneos e sobreposição de capital; registrar toda busca de ajuste.
- **Concluído quando:** comparação principal C versus B incluir resultado líquido pareado por oportunidade/tempo, custo API, cobertura, não entrada/timeout/ambiguidade, drawdown e incerteza por sessão; Brier/log loss somente para evento probabilístico definido; relatório incluir execução adversa e períodos negativos/inativos. Promover somente frente a gate pré-especificado em blocos futuros; falhou/inconclusivo não virar alegação de superioridade.

### JT-012 — Ablacionar features e episódios de fluxo

- **Prioridade / status:** P2 / proposto. **Dependências:** JT-007, JT-011. **Experimento:** E08; dependência original E07.
- **Evidência:** R §5; P/E08; D §§2–3.
- **Trabalho:** comparar preço/spread, delta normalizado, desequilíbrio de topo, OFI, níveis fixos e episódios por preço, acrescentando um componente por vez. Localizar progressão/aceitação, possível absorção com reposição e possível exaustão; explicitar explicações alternativas e requisitos da fonte. Normalizar apenas com passado disponível; identificar contratos/rolagens/reset de sessão.
- **Concluído quando:** ganho incremental futuro, estabilidade por regime e custo computacional forem relatados; falta de eventos adequados desabilitar OFI; profundidade/faixa de níveis permanecer comparável; medidas do mesmo fluxo não aparecerem como confirmações independentes; ajuste contemporâneo não for chamado de previsão. Remover componentes sem contribuição demonstrada.

### JT-013 — Calibrar desfechos fora da amostra e monitorar regime

- **Prioridade / status:** P2 / proposto. **Dependências:** JT-004, JT-010, JT-011. **Experimento:** E09; dependência original E07.
- **Evidência:** R §§3 e 8.1/8.5; P/E09.
- **Trabalho:** modelar evento definido por geometria/horizonte/execução com base temporal e calibrador simples; versionar estado, perguntas, modelo e momento de disponibilidade dos outcomes. Avaliar confiabilidade com contagens/intervalos, erro por estrato, cobertura de incerteza e sequências de falha. Adaptação/recuperação de episódios só depois de comparar contra versão estável.
- **Concluído quando:** treino/calibração/teste forem separados temporalmente; nenhuma atualização usar outcome ainda imaturo; reexecução recuperar versão conhecida e permitir rollback; Noul contextual mantiver nome/semântica distintos da estimativa financeira; mudança de regime e falhas concentradas forem visíveis. Calibração ou cobertura agregada não garantir lucro/proteção da conta.

## Conta e quantidade: somente depois dos fundamentos

### JT-014 — Conciliar conta, exposição e custos

- **Prioridade / status:** P2, pré-requisito de sizing / proposto. **Dependências:** JT-004, JT-007; adaptador e acesso de conta apropriados. **Experimento:** requisito adicional de E10.
- **Evidência:** R §§4.4 e 9; P/E10; D §§2 e 8, conta manual não conhece alterações externas.
- **Trabalho:** definir contrato de patrimônio/saldo, margem livre, posições, ordens pendentes, risco reservado e custos; conciliar snapshot/referência e mudanças externas. Preservar perdas e saldo negativo; distinguir origem manual de conta reconciliada; detectar desatualização e conflito sem enviar ordens.
- **Concluído quando:** divergência, duplicata, posição externa, ordem pendente e snapshot antigo produzirem bloqueio/motivo determinístico; relatório permitir explicar exposição e capacidade residual; dado manual não for rotulado conciliado; falha de conta não for compensada pelo JEV. Validar em fonte autorizada de teste antes de alegar integração real.

### JT-015 — Comparar quantidade e utilidade sustentável com `q=0`

- **Prioridade / status:** P3 / proposto. **Dependências:** JT-010, JT-011, JT-013, JT-014. **Experimento:** E10; dependências originais E06/E07/E09.
- **Evidência:** R §9; P/E10; D §§5–6.
- **Trabalho:** pré-definir tolerância de perda e limites de trajetória; comparar esperar, quantidades inteiras abaixo do teto, fração fixa e sizing robusto. Incorporar incerteza da vantagem, custos/impacto condicionais à quantidade, exposição comprometida, perda além do stop, drawdown e incapacidade de operar tamanho mínimo. Objetivo: utilidade líquida sustentável, não maximizar margem usada ou recuperar prejuízo.
- **Concluído quando:** estudo incluir crescimento composto, expected shortfall, drawdown, saldo negativo e `q=0`; teto por margem aparecer como restrição; cenários adversos/inconclusivos permitirem esperar; teste impedir aumento motivado apenas por perda/meta de recuperação; pressupostos e limitações publicados. Nenhuma fração ou lote deste estudo constitui recomendação real, nem autoriza sinal ou ordem.
