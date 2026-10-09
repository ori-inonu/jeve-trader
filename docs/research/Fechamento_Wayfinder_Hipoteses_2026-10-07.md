# Pesquisa de fechamento — hipóteses JEV

Date: 2026-10-07
Researcher: agente fechar_contexto; consolidação documental pela sessão principal
Scope: leitura do checkout e fontes oficiais; sem API paga, código ou prova financeira

## Fatos observados

[candidate_engine.py](../../app/candidate_engine.py) gera continuação buy/sell, até oito geometrias, com continuation-v2 e absorção oposta auxiliar. [context_requests.py](../../app/context_requests.py) possui S/C/I para continuação e apenas apoio para absorção. [flow_engine.py](../../app/flow_engine.py) contém progressão, absorção e exaustão de ambos os lados e redução exibida de bids/asks, como descrições sem geração de novas geometrias. Redução de liquidez não tem pergunta JEV específica no arquivo atual.

[flow_rules.json](../../app/flow_rules.json) declara regras experimentais não calibradas WIN. Mínimo quatro negócios nas regras e cinco em can_classify são estágios diferentes. [app_core.py](../../app/app_core.py) congela premissa do usuário depois de normalizar espaços/limitar300caracteres; premise_evaluable tem polaridade positiva. [jev_client.py](../../app/jev_client.py) não recebe citações/testemunhos selecionados pelo modelo e não integra Score. Choice aceita2–255opções e valida distribuição com tolerância1e−6; confidence tem checagem de intervalo, sem igualdade da fórmula demonstrada.

O serviço extrai dimensões de candidate_0; a UI já recupera alternativa por ID, mas ID reutilizado não garante semântica. O contrato causal foi revisado para incluir instrumento/sessão, batch/bindings e projeção calculada; a sessão principal incorporou esses pontos.

## Fontes e implicações

[Perguntas paralelas TypeSafe](https://docs.typesafe.ai/cookbooks/parallel_questions) avaliam cada pergunta independentemente do mesmo documento; composição dependente pertence ao código/consulta posterior. [Noul](https://docs.typesafe.ai/primitives/noul) mede sim da pergunta e [Choice](https://docs.typesafe.ai/primitives/choice) preserva categorias/probabilidades. [Confidence](https://docs.typesafe.ai/confidence/) depende de p_max e número de opções; não é chance de lucro.

[Limitações de jev-1.13](https://docs.typesafe.ai/model-jaggedness/jev-1.13), revisão consultada de02/10/2026, motivam filtrar dados irrelevantes, calcular aritmética/datas no motor e verificar ordem de opções/conteúdo adversarial. Não demonstram resistência garantida ou desempenho WIN.

Inferência: congelar catálogo, janela literal e projeção por pergunta. Apoio/contradição/insuficiência são independentes; ausência não vira contraevidência. Insuficiência determinística da fonte não é removida por Noul favorável. Absorção auxiliar recebe C/I próprios em nova versão; demais descrições não viram setups financeiros. Evidências enviadas e explicações calculadas devem ser identificadas; não atribuir seleção de testemunhos ao JEV sem retorno correspondente.

## Casos e limites

O [contrato de hipóteses](../../.scratch/wayfinder-evolucao-decisao/contracts/02-hipoteses.md) contém catálogo, campos, composição e fixtures de suporte/ausência/contraevidência/conflito. Fixtures são desenvolvimento sintético, sem respostas reais. Conflito segmentado exige trajetória referenciada; agregados atuais não autorizam explicação detalhada inventada. Reservados futuros não foram criados ou consultados; datas e orçamento pertencem ao protocolo.

Resolvido o desenho documental, permanecem implementação, robustez remota e eficácia empírica pendentes. Limiares existentes são comparadores experimentais, não escolhidos por esta pesquisa para conta real.
