# Jeve Trader — dados reais, movimento e atualização Windows

Label: wayfinder:map
Status: open
Created: 2026-10-07
Tracker: local-markdown

## Destination

Definir uma central dinâmica de decisão sustentada pelas fontes realmente disponíveis, com cadência, validade e alertas verificáveis, e deixar o aplicativo acessível no Windows com versionamento e aviso de novas versões.

## Notes

Incremento aprovado nesta conversa: [Mesa de fluxo](spec.md), especificação `ready` de 2026-10-07. Implementação local e evidência em [implementation-evidence.md](implementation-evidence.md), com revisão em [review-evidence.md](review-evidence.md). O estado de cada aceite é registrado separadamente do código; FW-06/FW-11/FW-12 não são encerrados por testes sintéticos ou por instalação.

Continuação 2026-10-08: instrumento local do piloto 0.5.1, com cobertura, interrupções, cenários declarados e latências separadas. Checkpoints visuais e recuperação após reinício foram revisados independentemente; 238 testes Python e 9 frontend passaram. A fronteira continua em `04-piloto-real.md`, sem certificação de fluxo completo, inferência JEV ou rentabilidade.

Em 2026-10-07 Gabriel autorizou “Implement the proposed plan”. [Implementação da central ao vivo](implementation.md) é o único incremento técnico em execução nesta sessão, com marcos internos A/B. A captura real continua pendente de arquivo, campos e contrato identificados; a licença DLL não está confirmada.

Pedido atual de Gabriel: investigar com Wayfinder; instalar no computador com ícone; controlar commits/GitHub e apresentar atualizações. A autorização de instalação e atualização permite executar este incremento, além da pesquisa documental. Os mapas anteriores de [contratos](../wayfinder-evolucao-decisao/map.md) e [oportunidades](../wayfinder-proximas-oportunidades/map.md) permanecem com seu escopo original; não representam funcionalidades entregues.

Wayfinder orienta o mapa, research os fatos, TDD o incremento especificado e code-review a revisão independente. Pesquisa realizada por dois agentes leitores; somente o principal escreve neste mapa e no incremento de instalação. Outro chat mantém a documentação geral; suas mudanças foram preservadas. O novo harness Desktop registrou o marco com revisão esperada, reconciliando o estado documental existente. Não depender de Mission Control para esta entrega.

Respostas humanas registradas: alertas experimentais identificados; horizonte de segundos a dois minutos; Profit e Excel disponíveis. Manter ordens manuais, identificadores JevWIN e dados existentes. Não confundir força contextual, confiança ou Noul com probabilidade de lucro. Não consultar API paga nos testes. Questões humanas pendentes permanecem abertas.

## Decisions so far

- [Fontes reais e capacidade do Excel](issues/01-fontes.md): RTD é parcial; velocidade de leitura não elimina limites da fonte; DLL exige SDK/licença próprios.
- [Cadência e termômetro contextual](issues/02-cadencia.md): dois ciclos separados; alvo inicial JEV de até 1 Hz por mudança relevante, condicionado a validade e orçamento; índice contextual tipado proposto.
- [Instalação e releases](issues/03-instalacao-updates.md): 0.4.1 instalada com ícone, release privada publicada e consulta de versão verificada. Download/instalação de versões futuras permanecem manuais.

## Next step

[Piloto com dados reais](issues/04-piloto-real.md) permanece aberto. A mesa, o controle OFF e os contratos de captura foram implementados e verificados localmente; confirmar arquivo Excel, planilhas/intervalos, campos exportados e contrato WIN para demonstrar atualização e cobertura reais. Medir 30 minutos, p95 após recebimento, atraso da fonte e latência JEV separadamente; colher reação humana lado a lado com Profit. Captura OCR textual é auxiliar e parcial, ainda sem validação de negócios/livro estruturados. Comparação contextual com inferências reais depende de casos autorizados e orçamento conhecido.

## Not yet specified

Modelo econômico aprovado, parâmetros pessoais de risco, retorno incremental medido em WIN, qualidade real da exportação e execução por liquidez/fila. Dependem da captura e anotação reais; não preencher essas ausências com mocks.

## Out of scope

Ordens automáticas, promessa de rentabilidade/alavancagem, contratação de feed, publicação do código privado, alteração global do Excel ou remoção de gates financeiros. Atualizador com instalação dentro do app depende de assinatura e publicação próprias.
