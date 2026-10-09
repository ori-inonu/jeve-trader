# Profundidade visual orientada pelos dados

Type: research
Status: closed
Assigned to: conversation 01a11717-73b1-7070-8d20-ad6d6e61188a
Blocked by: none

## Question

Qual caminho 2.5D/3D melhora a mesa React existente, com movimento vinculado ao fluxo recebido, sem prejudicar leitura em meia tela, estados indisponíveis, acessibilidade ou latência?

## Comments

Pedido humano de 2026-10-08: investigar recursos 2.5D/3D para tornar a mesa mais viva e continuar sua evolução. Derivado de FW-08; não muda os gates de dados reais. Pesquisar CSS/SVG com profundidade e WebGL/React Three Fiber usando fontes primárias. Escrita da pesquisa isolada; coordenador integra o resultado. O piloto e a reação humana continuam em [Contrato da captura real e reação ao painel](04-piloto-real.md).

## Resolution — 2026-10-08

Pesquisa independente recomenda projeção fixa CSS/SVG nesta fatia: profundidade decorativa, etiquetas frontais, comprimento proporcional à quantidade recebida e transições de até 180 ms. Não introduzir rotação contínua, novo timer nem migração para Next/WebGL. React Three Fiber permanece alternativa posterior se houver uma terceira dimensão analítica demonstrada, com renderização sob demanda e fallback. Nenhum ganho de ergonomia ou desempenho foi comprovado pela pesquisa.

Fontes primárias e limites estão em [Pesquisa visual](../visual-depth-research-2026-10-08.md). A decisão originou [Percurso observado e profundidade da mesa](../flow-depth-contract.md); encerramento desta pesquisa não prova sua implementação ou o piloto real.
