# Evidência atual do livro — revisão e entrega 0.5.4

Baseline: `6839d9c03e337bcb1d91f9b7e8eb53bddae68c42`. Fonte entregue: `88067db1ffa9cf2b9877415fc6191404859da834`. Aceites imutáveis LB-01..06: `35e31874203603c3f25ee560377e62331e8a39e3df584ee0bba74928f2189e1f`. FW-06/FW-11/FW-12 permanecem abertos; o piloto canônico continua em [04-piloto-real.md](issues/04-piloto-real.md).

Candidata: manifesto SHA-256 `ae33245f95182c5b0854282f688d14e6968a44a469ca424b229fb948c5403c40`; patch `c2d946b2f9e604f0e515e50e337167e23401f66eeeb79cf69020cb7af135c5b4`. Os dois revisores finais trabalharam em cópias isoladas, conferindo 19 hashes antes/depois. A normalização de um único CRLF para LF no teste novo recebeu adendos independentes, cada um repetindo 10 testes e confirmando ausência de outras alterações. Papel configurado harness_reviewer; modelo e tier efetivamente executados não comprovados. Os relatórios completos e logs ficam nas referências locais registradas em [release-evidence-0.5.4.json](release-evidence-0.5.4.json).

## Especificação

PASS_WITH_DOCUMENTED_LIMITS. O revisor independente executou 28 testes focados. O par vigente não pula um livro de topo; profundidade e grade são verificadas por lado e ambos os extremos têm validade. Metadados ausentes permanecem null; aumento de quantidade produz fração negativa e not_observed. Fonte desconectada, sequência e integridade mantêm a hipótese inconclusiva. A instrução contextual v6 compartilha os mesmos fatos, conservando Choice e Nouls independentes. Nenhum bloqueador ou regressão foi encontrado. Uma revisão anterior apontou lacunas de testes; três regressões adicionais as cobriram sem alteração posterior da produção. SHA-256 do relatório final: `1ec24c4213ca6d0c5a114b1e922fa48492b0532e6bfefcb1b5fe7fe8397bc926`.

## Padrões

PASS. A revisão independente verificou AGENTS.md, CONTEXT.md e a baseline de 12 heurísticas de Fowler; nenhuma violação documentada ou problema consequente foi encontrado. Seus 12 testes passaram. Redução exibida continua descritiva, sem causa inventada, posição de investidor, probabilidade de lucro ou autoridade de ordens. SHA-256 do relatório final: `c974247fb75af1e4e7f112acf74279bfef41d6bb617309dcbad459e27e97cd47`.

## Verificação e limites

TDD isolado reproduziu `AssertionError: 'potential' != 'inconclusive'` para o livro atual de um nível e para o primeiro extremo fora da janela curta; os mesmos comandos passaram após as respectivas correções. O teste público contextual também falhou antes da integração e passou depois. Regressões complementares exercitam saídas literais/arithmeticamente conhecidas. A verificação ampla passou com 260 testes Python, check desktop e 13 testes frontend no Windows 11/Python 3.14.7. Nenhuma chamada paga ou ordem foi executada.

O primeiro build falhou com WinError 5 na troca do runtime OCR gerado. A tentativa idêntica de preparação e o build completo seguinte passaram, sem mudança de código, permissões ou políticas; a causa transitória não foi comprovada. O pacote e a instalação tiveram 522 arquivos verificados por SHA-256. Atualização 0.5.3→0.5.4 preservou 2 arquivos de dados e o atalho; inicialização nativa com dados isolados observou janela, motor e banco, além da limpeza do motor após término do processo de teste. Os smokes iniciaram JEV/OCR desligados e temperatura indisponível. OCR reconheceu texto gerado, sem comprovar leitura real do Profit.

O instalador está em Downloads. Publicação binária pública aguarda a confirmação humana já solicitada; consulta de atualização 0.5.4 não foi certificada. Desconexão/restauração sem novo livro é uma limitação adjacente a investigar. Instalação, testes sintéticos e melhoria das instruções não comprovam aprendizagem, inferência real, rentabilidade ou fluxo completo.
