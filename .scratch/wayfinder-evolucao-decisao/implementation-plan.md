# Sequência de implementação dos contratos resolvidos

Date: 2026-10-07
State: planned; application_code_unchanged
Parent: [Mapa Wayfinder](map.md)

## Ponto de partida

Esta rodada resolve as seis decisões documentais. A sequência abaixo transforma os contratos em incrementos revisáveis de software, sem executar esses incrementos agora. Conferir novamente o checkout e Mission Control antes de reivindicar o primeiro: o painel atual já contém correções de identidade parcial, replay causal, dimensões independentes e comparação por sessão. Preservar esses avanços e os identificadores/dados JevWIN.

O serviço atual continua em espera financeira sem modelo aprovado integrado. Nenhum incremento habilita ordens ou promove resultados sintéticos. Os trabalhos reutilizam JT/E existentes, sem mudar seu status por planejamento.

## Incrementos e evidência exigida

| Ordem | Entrega concreta | Pontos atuais a conferir | Verificação necessária e limite |
|---|---|---|---|
| 1 — identidade | Projetar os registros imutáveis e projeções atuais do [contrato causal](contracts/01-identidade.md), com versão explícita de protocolo e migração deliberada dos registros antigos para histórico sem inventar campos | `app/decision_engine.py`, `app/desktop_service.py`, `app/context_requests.py`, armazenamento de pesquisa e types React | Vetor canônico; troca de geometria/horizonte/evidências; reorder; custos em consulta; cache; restart e revisão tardia. Falhas deixam contexto indisponível. Sem API remota. JT-004/005/009/013; E01/02/04/05/09. |
| 2 — semântica | Materializar catálogo e projeções por pergunta do [contrato JEV](contracts/02-hipoteses.md); bindings do batch; estados brutos S/C/I e avaliação por candidato | `app/candidate_engine.py`, `app/flow_engine.py`, `app/context_requests.py`, `app/recommendation_engine.py`, `app/jev_client.py` | Casos anotados de ausência/conflito e compatibilidade; contrato contra campos irrelevantes; mocks tipados. Teste remoto/permutação só com protocolo e orçamento próprios. JT-002/003/008/009/012/016; E02/03/04/08/09. |
| 3 — tempo e execução | Acrescentar ledger causal de oportunidade, clocks, parcelas e custos do [contrato temporal](contracts/03-tempo-execucao.md); replay preserva a informação conhecida no instante | `app/decision_lab.py`, `app/desktop_service.py`, adapters de fonte e livro manual | Relógios controlados, correção tardia, não entrada, parcial, desconhecido, gaps e duas cadências pareadas. Excel parcial não passa a fita completa. JT-005/007/010/014; E01/05/06. |
| 4 — economia offline | Distribuições conjuntas por quantidade, comparadores discreto/fracionário/robusto e patrimônio próprio do [contrato econômico](contracts/04-dimensionamento.md) | `app/decision_engine.py`, `app/decision_lab.py`, modelos e artefatos financeiros | Reproduzir trajetória com fluxos externos, zero admissível, ruína, custo não linear e incapacidade de lote mínimo. Fração atual é comparador; nenhum modelo é aprovado por smoke. JT-010/013/014/015; E06/09/10. |
| 5 — interface | Projetar estados do [contrato visual](contracts/05-interface.md) nas quatro áreas; contexto por chave; histórico congelado e avisos atuais; preservação de foco/formulário | `desktop/src/App.tsx`, tipos, componentes e ECharts | Primeiro checks de estado offline; depois tarefas na janela Tauri Windows nativa a 125/150/200%, teclado e leitor de tela. Uma prévia React não substitui esses checks. JT-005/006/014/015. |
| 6 — registro de evidência | Manifesto imutável, ledger de tentativas e gates do [protocolo](contracts/06-protocolo.md); separar evidência, revisão de uso e autorização operacional | `app/decision_lab.py`, persistência de pesquisa, carregamento de estimativa no serviço e `docs/research/Plano_Experimentos_JEV.json` | Recusar promoção sem registro, mistura de holdout, mudança de modelo/escopo e flag sintética. Não alterar catálogo E até evidência do experimento. JT-004/011/012/013/015/016; E02–E10. |

Incrementos 2 e 3 dependem do 1; o 4 depende do 3; o 5 depende de 1–3. O protocolo documental está definido antes dos experimentos. A instrumentação do incremento 6 pode ser construída junto do laboratório, mas sua confirmação financeira depende de 1–4 e dos dados necessários.

## Gates para trabalho externo e confirmação

Antes de qualquer confirmação: preencher datas/sessões e direito de uso do dataset, tarifas e margem aplicáveis, observabilidade de execução/latência, orçamento autorizado, precisão/tamanho e tolerâncias de risco. O [protocolo](contracts/06-protocolo.md) registra esses campos como pendentes; seu estado é `not_ready_for_confirmation`.

Antes de ProfitDLL real: SDK autorizado, versão/ABI, licença e vigência das regras de dados. Nenhum contrato aqui presume que uma assinatura Profit Pro concede esse acesso. Antes de recomendação financeira no serviço: registro verificável favorável no escopo e revisão explícita; ordens permanecem manuais e sem envio pelo aplicativo.

Não há pergunta humana necessária para concluir os documentos. Valores pessoais de risco, dados privados, contratação e orçamento pago serão solicitados quando houver uma proposta concreta dependente deles. Expiração, cobertura desconhecida ou falta de evidência continuam motivos de espera.

## Retomada verificável

Ler [auditoria de aceite](acceptance-audit.md) e o contrato do incremento; recapturar arquivos atuais e dependências; reivindicar o trabalho no tracker antes de editar. Usar TDD para os riscos de associação, dinheiro e causalidade; executar checks focados e depois a verificação requerida pelo projeto. Atualizar backlog/status com plataforma, comandos e alcance do resultado efetivamente demonstrado. Revisão Windows e confirmação empírica têm registros separados.
