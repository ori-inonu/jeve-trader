# Integração implementada — Profit Pro Windows, Excel e JEV

A versão 0.2.0 implementa o aplicativo desktop `desktop_app.py`, leitura somente de valores de uma planilha Excel RTD já aberta, replay CSV, motor de eventos/medidas, referências estruturais, estudos de capital, diário local e cliente TypeSafe/JEV. Os fontes e os pacotes Windows tornam essa implementação revisável. **A leitura COM/RTD ainda precisa ser validada no Windows do usuário**; não foi observada neste ambiente.

O ambiente confirmado é Profit Pro no Windows, Toro e acesso à API JEV. A licença ProfitDLL/DLL Feed está ausente. A solução atual não usa essa DLL, não presume que Profit Pro a inclui e não contorna licença ou permissão. Usa a exportação RTD/DDE que o próprio Profit disponibiliza dentro da instalação/plano do usuário.

## Caminho de dados atual

| Origem | Implementação | Limite |
|---|---|---|
| Demonstração | Eventos sintéticos locais `WIN_SIM` | Não são dados da bolsa |
| Excel `quote` | Último preço e ofertas selecionadas, com horário quando disponível | Não fornece tape completo/agressão |
| Excel `tape` | Negócios individuais de intervalo explicitamente configurado | Pode perder linhas entre leituras |
| Excel combinado | Cotação + negócios em dois intervalos do mesmo arquivo, no mesmo ciclo COM | Depende de exportação real de negócios; leitura sequencial e cobertura parcial |
| CSV | Replay limitado de negócios com schema explícito | Arquivo não prova integralidade da sessão |
| Conta Toro | Entrada manual de capital, margem, custos e resultado | Sem saldo/posição/ordens reconciliados |
| JEV | Classificação do contexto com perguntas estruturadas | Não estima lucro nem executa operações |

Para configurar o template, use `Profit_RTD_Modelo.xlsx`, `Dados!A2` para contrato exato, planilha `Dados`, intervalo `A1:I2`, modo `quote`. O arquivo contém fórmulas RTD, sem macros ou contrato real pré-selecionado. As instruções completas estão em [GUIA_WINDOWS.md](GUIA_WINDOWS.md).

A integração combinada `CombinedExcelBridge` lê simultaneamente, em um ciclo do aplicativo, o intervalo de cotações e um intervalo de negócios do mesmo arquivo. Essa agregação permite conservar ofertas e referências calculadas por trades na mesma sessão; anteriormente, alternar `quote` e `tape` reiniciava a fonte sem unir essas informações. O consumidor ainda deve verificar horário/contrato/integridade individual antes de produzir cenários.

O template agora possui **Negocios!A1:F501**, com cabeçalhos e dados inicialmente vazios. É necessário configurar ou colar uma exportação real autorizada de negócios compatível. **Não há fórmula RTD de Times & Trades presumida nem descoberta automática da janela.** A disponibilidade de ID/agressor/timestamp na exportação concreta continua precisando ser conferida. Cotação isolada nunca preenche essa tabela automaticamente.

## Leitor Excel somente de valores

O backend preferencial usa `comtypes==1.4.17` e `GetActiveObject('Excel.Application', dynamic=True)`. Anexa uma instância Excel já registrada no COM da sessão do usuário, identifica o arquivo escolhido por nome/caminho e lê apenas `Range.Value2` da planilha/intervalo informado. Dispatch dinâmico evita gerar wrappers Excel. Cada worker inicializa/encerra COM na mesma thread e não conserva ponteiros entre leituras.

Não cria Excel, abre/salva arquivos, escreve/recalcula fórmulas, altera segurança ou encerra Excel. A busca limita-se a 100 arquivos abertos, e o intervalo a 64 colunas/5001 linhas. Múltiplas instâncias, sessões diferentes, elevação distinta ou Excel ocupado podem impedir/atrasar acesso. O backend nativo não possui timeout rígido interrompível; a interface executa a leitura em background e não acumula leituras concorrentes.

No modo combinado, uma única anexação/apartment lê dois intervalos sequenciais. Se qualquer fonte estiver vazia, inválida ou inacessível, não retorna uma meia leitura misturada com valores anteriores. O cache de IDs é atualizado somente depois de ambas as fontes validarem. A operação não é atômica na bolsa; os horários originais das duas tabelas são preservados e podem divergir. O status mantém feed desconhecido e tape incompleto.

O helper PowerShell é utilizado **apenas se comtypes estiver ausente**, não como alternativa após falha de acesso ou permissão. O script respeita a política de execução existente; nenhuma alteração ou bypass foi implementado. O pacote Windows inclui a biblioteca para priorizar leitura nativa.

O fato de Excel estar acessível não comprova login/feed da bolsa. RTD pode pausar quando a aba vinculada fica inativa ou a janela de origem fecha. O aplicativo não ativa janelas. DAT/HOR exportados não são tratados como garantia de timestamp independente para cada atualização do livro. Sem horário válido da origem, idade real desconhecida permanece explícita.

## Eventos, cobertura e tempo

Negócios normalizados possuem ID, contrato, timestamp UTC em milissegundos, preço em pontos, quantidade inteira e agressor reportado. Há aliases explícitos, números brasileiros e suporte a ISO com offset ou data/hora São Paulo. Hora sem data não recebe o dia atual. Observação local e timestamp de mercado são campos distintos.

IDs explícitos são deduplicados em cache limitado. Negócios idênticos sem ID não recebem identificador artificial; a interface os exclui do acumulador. Agressor ausente/desconhecido não é deduzido de preço ou corretora. Eventos inválidos e ordem temporal regressiva tornam os limites de integridade visíveis.

**Excel e CSV mantêm `full_tape=False`.** Intervalo visível e arquivo válido não provam todos os negócios da sessão. A cotação `ULT`, a quantidade `QUL` e o volume agregado `VOL` não viram tape fabricado. Cotações podem ser exibidas separadamente, sem autoridade de sequência do book.

O motor mantém janelas e buffers limitados, calcula delta/volume capturados e distingue hipóteses inconclusivas de observações sintéticas completas. Referências técnicas são extraídas de preços presentes na amostra, preservando evidência. Comparações de entrada/stop/alvo são pesquisa, sem ranking de retorno esperado ou probabilidade financeira calibrada.

Detalhes de schema, parsing, limites de arquivo e saúde estão em [PROFIT_BRIDGE.md](PROFIT_BRIDGE.md).

## JEV e validade da avaliação

O cliente oficial TypeSafe usa perguntas independentes numa requisição, versão fixada e resposta validada. O estado enviado contém medidas, referências e limites da amostra; patrimônio e pressão por recuperação permanecem fora das perguntas de mercado. Apoio contextual e confiança não representam chance de lucro.

Consultas automáticas começam desativadas. Quando habilitadas, exigem leitura Excel ativa/evidência suficiente e respeitam intervalo mínimo de 10 segundos. Orçamento padrão: 120 consultas por execução, configurável entre 1 e 10.000. A chave permanece em memória, sem persistência no diário/configuração. Chamadas consomem a conta TypeSafe do usuário.

Troca de fonte, atraso, erro ou evidência antiga invalidam o uso atual de uma resposta. O diário pode conservar a leitura histórica identificada. O aplicativo não envia ordens nem promove automaticamente o estudo para modo real.

## O que ainda requer integração própria

Saldo, patrimônio, pico, posição, ordens, execução parcial, margem efetiva e resultado líquido Toro não são consultados. O diário é manual. Uma origem de conta autorizada deverá reconciliar operações inclusive feitas fora do aplicativo; acesso a market data não equivale a acesso à conta.

Não há monitoramento de notícias/calendário, serviço Windows instalado, atualização automática, mensagens externas, gestão de posição aberta ou validação de vantagem estatística. Fechar/parar o copiloto não zera posição nem confirma que existe stop na corretora. A pausa local após perda registrada afeta o estudo, sem impedir ações no Profit.

Para pesquisar uma futura coleta integral licenciada:

1. Contratar/confirmar licença e direito de armazenamento/processamento da fonte adequada.
2. Utilizar exclusivamente SDK oficial da versão concreta; não adivinhar layouts, callbacks ou códigos de agressão.
3. Implementar status, sequência, correções/cancelamentos, book consistente, reconnect e lacunas de fila.
4. Registrar amostras e comparar cada evento com a origem; medir atrasos de ponta a ponta.
5. Integrar conta e verificar reconciliação, inclusive durante falha/reconexão.
6. Comparar baselines e JEV com teste temporal, custos e execução plausíveis antes de propor uso operacional.

A implantação desse coletor continua futura e separada do COM/RTD já implementado. Nenhum teste de software ou lucro isolado substitui essas etapas.

## Referências oficiais

- Nelogica: [configuração RTD/DDE](https://ajuda.nelogica.com.br/hc/pt-br/articles/360044293432-Como-configurar-RTD-DDE-no-Profit) e [sintaxe/atributos](https://ajuda.nelogica.com.br/hc/pt-br/articles/7834206674075-Significados-e-sintaxe-do-RTD).
- Nelogica: [acesso à ProfitDLL](https://ajuda.nelogica.com.br/hc/pt-br/articles/51583791325211-Como-obter-acesso-%C3%A0-ProfitDLL), [SDK/ecossistema](https://ajuda.nelogica.com.br/hc/pt-br/articles/22396517026203-Ecossistema-ProfitDLL-e-primeiros-passos) e [funções de dados em tempo real](https://ajuda.nelogica.com.br/hc/pt-br/articles/11168755650459-Fun%C3%A7%C3%B5es-Real-Time-DLL).
- [comtypes: cliente COM](https://comtypes.readthedocs.io/en/stable/client.html) e [distribuição oficial](https://pypi.org/project/comtypes/).
- [TypeSafe: API](https://docs.typesafe.ai/api) e [confiança](https://docs.typesafe.ai/confidence).

`VALIDATION.md` registra a validação final disponível; os guias acima registram o que precisa ser preparado e observado localmente no Windows.
