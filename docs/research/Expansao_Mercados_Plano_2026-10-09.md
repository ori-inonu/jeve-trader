# Expansão — plano de tarefas e filtro de candidatos

Data: 2026-10-09. Estado da entrega: pesquisa/plano documental. Baseline: `da96c6a`. Critérios atuais: [AM-01–06](Expansao_Mercados_Aceites_2026-10-09.md). Requisitos futuros: [CM-01–12 / AC-01–07](../specs/Coleta_Multimercado_2026-10-09.md). Nenhuma linha abaixo significa implementação, lucro demonstrado ou autorização operacional.

## Fronteira escolhida

Objetivo financeiro confirmado: investigar crescimento 10× em prazo inferior a sete dias. **Shortlist para estudo econômico:** futuros B3 e derivativos cripto. **Base técnica:** cripto spot público para testar tape/L2/continuidade/replay. **Pendentes:** trading esportivo, pela API direta no Brasil, e binárias, pela observabilidade e admissibilidade. Filtro revisável quando houver evidência nova, sem apagar os motivos atuais.

Essa ordem combina mecanismo de exposição com dados observáveis; não é ranking demonstrado de rentabilidade. Recibo Jev Workflows `62035197-461c-4c76-8051-864eb7bd2632` recomendou essa shortlist de pesquisa. Recibo `d12f2d93-df47-4524-98e6-b501f259d412` recomendou piloto spot e envelope tipado. Probabilidades de preferência do Choice não são probabilidades de sucesso financeiro. [Recibos sanitizados](../evidence/expansao-mercados-decisoes-2026-10-09.json).

## Backlog proposto

| ID | Entrega e responsabilidade exclusiva sugerida | Requisitos / aceite | Dependências | Estado e condição para concluir |
|---|---|---|---|---|
| EM-00 | Pesquisa de quatro famílias, contratos atuais, economia e plano; integrador em docs/research e docs/specs desta frente | AM-01–06 | Pedido do usuário | Entrega atual; concluída apenas após verificação e parecer independente |
| EM-01 | Perfil de um feed público e instrumento: endpoint/versionamento, snapshot/delta, trade IDs, limites, termos/retensão, gaps e relógios; pesquisador em spec própria | CM-01–08; AC-02–04 definidos antes de código | EM-00; decisão provedor/par | Próxima etapa documental elegível; fixar contrato e limites do piloto para obter spec ready |
| EM-02 | Catálogo e envelopes neutros, compatibilidade WIN sem alterar cálculo existente; escritor futuro em app/market_data_contract.py e testes próprios | CM-02–03, CM-12; AC-01 | EM-01; baseline atualizado | Proposto, sem código; TDD de decimais/unidades e compatibilidade com WIN |
| EM-03 | Adapter público de um provedor spot, REST/WS/reconciliação e saúde; escritor em app/public_crypto_feed.py e testes de fixtures próprias | CM-04–06, CM-08; AC-02–04 | EM-02; autorização de implementação | Proposto; prova de gaps/dup/resync/checksum e observação real local delimitada |
| EM-04 | Retenção e replay conforme termos, VAP/agressor com cobertura; escritor em app/market_replay.py e fixtures próprias | CM-05–07; AC-03–04 | EM-03 | Proposto; replay exato e lacunas explícitas, sem redistribuição de dados restritos |
| EM-05 | Integração de snapshot contextual à ponte/UI, com missing e comentários rastreáveis; integrador sozinho nos arquivos compartilhados | CM-09, CM-12; AC-05 | EM-04; contrato público estável | Proposto; desligado por padrão, sem ordens; testes/CI sem API paga e verificação Windows própria |
| EM-06 | Viabilidade do feed B3 WIN/WDO: SDK oficial/licença/custos, exemplos callback/seq/histórico, contrato e cobertura; pesquisador em spec de fonte B3 | CM-01, CM-03–08 | EM-00; acesso/documentação comercial quando necessário | Parte documental elegível; implementação/validação real bloqueadas por SDK/licença e dados reais. Não baixar DLL de wrapper como licença |
| EM-07 | Viabilidade de dados derivativos cripto e produto brasileiro: trades/L2/mark/index/funding, catálogo/payoff/margem/liquidação, histórico e jurisdição | CM-01, CM-03, CM-10 | EM-00; entidade/modalidade e regras vigentes | Pesquisa pública elegível; acesso operacional não validado. Spot não satisfaz este aceite |
| EM-08 | Payoffs/custos/câmbio e comparação determinística de quantidades/stakes admissíveis com aguardar; escritor em módulo econômico separado | CM-10, CM-12; AC-06 | EM-06/07 com fonte suficiente; risco/mandato humanos | Draft; não usar .20/BRL e tarifas WIN em outros instrumentos; falta autorização para extensão financeira |
| EM-09 | Dataset e protocolo de avaliação da meta: cronologia, seleção, calibração, execução, custos, banca e cauda | CM-11; AC-07 | EM-04; EM-08; histórico representativo | Draft; P(meta)/ruína só estimada com incerteza; tamanho de amostra e custos precisam ser fixados |
| EM-10 | Estudo prospectivo em observação, um candidato congelado, comparação com aguardar e relatório de oportunidades/perdas | CM-06, CM-11; AC-07 | EM-09; qualidade mínima documentada | Proposto; observação sem ordens não prova lucro real nem garante 10× |
| EM-11 | Revisitar sports exchange se surgir rota oficial acessível no Brasil, ou integração de odds/estatísticas limitada e devidamente rotulada | CM-01, CM-03, CM-10 | Mudança documentada de acesso/termos; eventual custo autorizado | Pendente; scraping não contorna geo/auth/licença, odds polling não satisfaz book/tape |
| EM-12 | Revisitar binárias apenas com entidade/produto admissíveis e payoff/settlement verificáveis; nenhuma API não oficial de ordens | CM-01, CM-03, CM-10 | Evidência jurídica e de dados nova | Pendente; cotação pública não revela negócios/agressor/volume; alertas e termos atuais permanecem gates |

Os nomes de módulos são propostas de responsabilidade; a implementação deve verificar a organização atual antes de fixá-los. Não criar duas frentes de escrita no mesmo checkout. Subagentes futuros recebem cópia isolada e arquivos exclusivos; integrador mantém contratos compartilhados. Novos incrementos precisam de SPEC ready e critérios congelados, seguidos de teste de regressão, implementação, verificação e revisão independente.

## Gates de seleção para o JEV

Pipeline proposto: **descobrir fonte → validar acesso/cobertura → validar produto/payoff/custos → estimar alternativas → comparar com aguardar → comentário/Choice contextual → gate determinístico final**. JEV organiza o contexto e compara opções admissíveis; não reescreve fórmulas monetárias, acesso ou limite de risco.

Cada candidato conserva uma ficha: exposição/mecanismo, dados necessários/obtidos, motivos de pendência, custos/margem/minimos datados, qualidade fora da amostra, capital final/cauda e próxima evidência capaz de mudar o status. Sem dados econômicos válidos, a melhor decisão pode ser não selecionar nenhuma oportunidade. Isso não muda a meta; evita tratar desconhecido como vantagem.

As informações manuais dividem-se entre dados que uma fonte pode automatizar (preços, quantidade, book, funding, eventos) e dependências específicas de conta/produto (saldo, margem da corretora, taxas, permissões). Automatizar somente o que o endpoint realmente fornece, com procedência. A conta atual em BRL continua manual até uma reconciliação explicitamente autorizada e testada.

## Critério de passagem da próxima etapa

EM-01 é a primeira entrega pequena a especificar: um feed spot público, um par, leitura sem chave, sem ordens, prova de continuidade e plano de replay. EM-06 e EM-07 podem avançar em pesquisa documental independente porque são as hipóteses de alavancagem. Nenhum candidato passa ao estágio de operação real com base nesta pesquisa. A escolha financeira final depende dos resultados de EM-08–10 e do escopo operacional, não apenas da existência de uma API.
