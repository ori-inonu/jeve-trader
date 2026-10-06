# Verificação da versão 0.3.0

Data: 06/10/2026. A entrega contém o aplicativo desktop JEV WIN, instalador por usuário para Windows x64, pacote portátil, código, modelos de exportação e documentação.

## Resultado e alcance

**166 testes automatizados passaram.** O autoteste do aplicativo também passou, incluindo quatro cenários sintéticos de fluxo, oito cenários técnicos, oito alternativas na Central e recálculo de capital. A conclusão do exemplo sem JEV é `AGUARDAR`. Os testes foram executados com Python no ambiente Linux de desenvolvimento. Nenhuma chamada autenticada à API JEV, conexão à Toro, conexão ao Profit do usuário ou ordem real foi realizada.

**A abertura da interface no Windows não foi validada.** O ambiente disponível não permite executar Wine e o servidor de display necessários a esse teste. Testes de lógica e inspeção do formato executável não substituem abrir a janela, verificar a instalação e testar Excel/RTD no computador do usuário. A mensagem exata da falha com o pacote anterior não foi recebida; não há diagnóstico confirmado da causa naquela máquina.

## Correções desta versão

- Instalador real com atalhos de abertura, diagnóstico e desinstalação, em lugar da dependência de abrir um executável portátil isolado.
- Inicialização pelo interpretador Windows oficial incluído no pacote. A inicialização principal deixa de depender do bootstrap CArchive personalizado usado na versão anterior.
- Pré-verificação de recursos, captura de falhas de início e callbacks, arquivos de diagnóstico e logs persistentes. Não são coletadas chaves, configurações completas, variáveis de ambiente ou payloads da API.
- Central de decisão como primeira aba, com conclusão, evidências, impedimentos, alternativas e histórico. A mesma projeção de dados produz um relatório HTML estático.
- Leitura combinada de cotações e negócios no mesmo arquivo Excel. Falha em uma tabela invalida o ciclo; a captura continua identificada como parcial.
- Verificação determinística de risco e correspondência da resposta JEV à fonte, geometria e prazo de validade antes de usar seu apoio contextual.

## Cobertura automatizada

- Cálculo monetário com Decimal: ponto, stop/alvo, custos, slippage, margem e lote inteiro.
- Limites por operação, perda diária, pico, reserva de margem/perda, sequência e pausa.
- Redimensionamento com capital variável, sem recuperação obrigatória ou aumento motivado pelo prejuízo.
- Projeção de stops e comparação de dez combinações de fração/base, sem ranking de lucro esperado.
- Eventos duplicados, horários, integridade, retenção e cobertura parcial de fluxo.
- Progressão, absorção e exaustão em exemplos sintéticos; exigência de informação de livro quando necessária.
- Extração de níveis observados, exclusão de informação futura, geometria e até oito pares por comparação.
- CSV/Excel: separador brasileiro, datas, serial Excel, ID estável e agressor desconhecido preservado.
- COM simulado: Excel existente, leitura Value2, liberação de recursos e ausência de contorno após erro de permissão.
- Fonte combinada: as duas tabelas, falha parcial, deduplicação, ordem temporal e percurso até os cenários técnicos com cotação amostrada.
- Contrato HTTP JEV, tipos, distribuição das respostas, sanitização de erros e rejeição de respostas inesperadas.
- Separação dos valores financeiros e do contexto de mercado enviado ao JEV.
- Motor de conclusão: veto financeiro, recálculo de lote, cobertura parcial, resposta antiga ou de outra fonte, geometria divergente e ausência de suporte inventado.
- HTML: valores escapados, ausência de scripts/requisições e exclusão de campos arbitrários e credenciais.
- Controlador da Central: persistência de transições imediatas, deduplicação e mudança de geração da fonte.
- Pausa real após perda registrada, hipótese explícita quando falta horário e preservação de patrimônio negativo no diário.

`test_inventory.json` contém o inventário por módulo. `desktop_self_test.json` registra o autoteste. Testes de API e COM usam respostas/objetos artificiais. Os testes do controlador usam a lógica real da atualização com componentes de tela substituídos; não executam uma janela Windows nem medem sua usabilidade.

## Empacotamento Windows

O novo instalador usa NSIS e inclui o runtime CPython 3.12.10 oficial para Windows x64, Tcl/Tk, SQLite, tzdata e comtypes. Instala em `%LOCALAPPDATA%\Programs\JevWIN`; diário e logs ficam separados em `%LOCALAPPDATA%\JevWIN` e são preservados na desinstalação. O portátil mantém o mesmo runtime e deve ser extraído inteiro antes de abrir `JevWIN.cmd`.

O processo de build registra formato PE, arquitetura, dependências privadas, recursos, extração e hashes dos arquivos distribuídos. O autoteste do código extraído pode ser executado com o Python Linux apenas para verificar lógica e recursos; isso não valida o interpretador Windows. Os relatórios de build descrevem o alcance exato das verificações. Instalador e lançadores não têm assinatura Authenticode.

O `JevWIN.exe` dentro da instalação é um lançador que depende da pasta completa. Não deve ser distribuído isoladamente. `WINDOWS_BUILD.md` descreve a reprodução do pacote; `GUIA_WINDOWS.md` explica instalação e diagnóstico. A confirmação da abertura nativa, da aparência, do comportamento do instalador e da integração real permanece pendente.

## Exemplos reproduzíveis, sem previsão de desempenho

| Caso de pesquisa | Resultado calculado |
|---|---|
| R$400; controle de 1%; stop 100 pontos; R$2 de custos hipotéticos | Nenhum contrato cabe no orçamento de R$4 |
| R$400; perfil de pesquisa de 15%; margem hipotética R$155; mesmo stop/custo | 2 contratos; perda planejada R$44; reserva de margem e perda R$354 |
| R$380 após perda de R$20; pausa transcorrida | 2 contratos nas mesmas hipóteses; orçamento por proposta cai para R$57 |
| Mesma perda registrada há menos de 60 segundos | Nova proposta de estudo bloqueada pela pausa |
| R$4.000; mesmas hipóteses | 22 contratos; perda planejada R$484; margem R$3.410 |
| Perda manual de R$401 sobre R$400 | Capital registrado em −R$1; novos cálculos bloqueados |
| Cotações RTD sem negócios individuais | Cotações observáveis; análise de fluxo indisponível |
| Cotação e tape combinados com cobertura parcial | Medidas e geometrias quando suficientes; confirmação permanece pendente |

Os valores de margem e custos são entradas dos exemplos, não cotação atual das condições da Toro/B3. As quantidades não são recomendações para a conta real. Stops projetados não garantem perda máxima.

## Revisão aplicada

A revisão desta versão encontrou dois problemas médios e verificou suas correções: pressuposto temporal de perda anterior não aparecia na Central/HTML; e uma limitação de frequência do diário podia perder transições rápidas. O pressuposto agora é exibido, cada alteração relevante é persistida e a geração da fonte fica registrada. Nove testes focados passaram no fechamento; fazem parte do total de 166. Não restaram pendências desses achados no escopo revisado.

Também permanecem cobertas as correções anteriores de expiração de cotação, alteração de capital, descarte de respostas de fonte anterior, distinção entre amostra RTD e livro, idade original do negócio e capital negativo.

## O que não foi demonstrado

Rentabilidade, lucro contínuo, recuperação de perdas, ganho de 900% em um dia, superioridade do JEV, probabilidade de alvo antes do stop, configuração ótima, tape completo, latência garantida ou sobrevivência da conta. Isso exige dados reais autorizados, conta conciliada e avaliação temporal fora da amostra com custos e execução plausíveis. A versão não contém simulador de fila, integração de notícias, gestão de posição aberta ou envio de ordens.
