# JEV WIN v0.3.0 — guia de uso no Windows

O aplicativo reúne observação de fluxo, comparação técnica e capital manual. **Não envia ordens nem conecta automaticamente sua conta Toro.** A tela inicial é a **Central de decisão**, com conclusão, motivos e impedimentos. Demonstração e replay continuam identificados; nenhum gráfico comprova conexão ao pregão.

## 1. Instalar ou abrir o portátil

Use Windows 10/11 x64. Abra **JevWIN_Instalador.exe** para instalar para seu usuário, em `%LOCALAPPDATA%\Programs\JevWIN`, e iniciar pelo atalho **JevWIN**. Esta versão oferece instalador e atalhos; o pacote anterior era portátil. O runtime necessário acompanha o programa: não é preciso instalar Python. O instalador não configura Profit, Excel, corretora ou chave JEV.

A alternativa é `JevWIN_Portatil.zip`: use **Extrair tudo**, preserve a estrutura inteira e execute `JevWIN.cmd`. Não abra de dentro do ZIP nem mova apenas o lançador. `Diagnosticar_JevWIN.cmd` executa o diagnóstico local e ajuda a conservar mensagens de erro; isso não comprova conexão ao Profit. `JevWIN.exe` também depende da pasta inteira. Os atalhos **Diagnosticar JevWIN** e **Desinstalar JevWIN** ficam no menu Iniciar; a desinstalação preserva o diário/dados. Excel e Profit são instalações externas do usuário.

Instalador/executáveis não possuem assinatura digital comercial. Confira a procedência e as regras do computador se o Windows exibir aviso. O ambiente de desenvolvimento não permitiu validar sua instalação Windows/Excel/Profit. Consulte `VALIDATION.md` e os relatórios para saber quais verificações foram realizadas; testes da lógica não substituem abrir e conferir localmente.

## 2. Usar a Central de decisão

As oito abas são **Central de decisão**, **Monitor**, **Cenários técnicos**, **Capital e risco**, **Conexões**, **JEV**, **Diário** e **Guia**.

Na Central, **Atualizar avaliação** reúne a situação atual. **Consultar JEV** solicita interpretação quando houver evidência utilizável. **Demonstrar cenários** carrega um exemplo sintético. As páginas internas são:

- **Evidências e impedimentos**: por que o programa chegou à conclusão e o que falta confirmar.
- **Cenários calculados**: entrada, stop, alvo, contratos, perda planejada, apoio e contradição, quando disponíveis.
- **Histórico de estados**: mudanças de conclusão nesta execução.

Os estados incluem **SEM DADOS SUFICIENTES**, **AGUARDAR CONFIRMAÇÃO**, **BLOQUEADO PELO RISCO** e **HIPÓTESE PARA REVISÃO**. Excel/CSV fornecem amostra parcial: isso mantém um impedimento de confirmação. Apoio favorável do JEV não comprova tape completo ou lucro futuro; veto financeiro prevalece. Nenhum número de apoio/confiança é chance de ganhar.

**Exportar painel HTML** salva um registro visual estático. Pode ser aberto no navegador para revisão, mas não continua recebendo dados, não consulta JEV e não é uma conexão ao mercado.

## 3. Explorar e informar o capital

Em **Monitor**, selecione `progression`, `absorption`, `exhaustion` ou `choppy`, lado `buy`/`sell`, e **Carregar demonstração**. São dados gerados localmente. O painel mostra preços, delta/contratos capturados, hipóteses, idade e cobertura. Absorção/exaustão descrevem a amostra, sem provar intenção, liquidez oculta ou reversão.

Em **Capital e risco**, confira patrimônio inicial/atual/pico, percentuais, stop/alvo estudados, perdas consecutivas, taxas, slippage, margem e teto técnico. Use **Recalcular e comparar políticas**. Os valores iniciais são parâmetros de laboratório. Maior lote permitido não significa maior retorno esperado; margem/stop não garantem perda máxima. A conta é um cenário manual, sem reconciliação de posição aberta.

Em **Diário**, preencha **Resultado líquido manual (R$)** e use **Registrar e atualizar capital**. Após perda registrada, o estudo aplica pausa de **60 segundos**; não bloqueia operações no Profit. Configurações e histórico ficam em `%LOCALAPPDATA%\JevWIN`, arquivo `journal.sqlite3`. O diagnóstico grava `diagnostico.json`, `self-test.json`, `startup.log`, `python-errors.log` e `diagnostic-console.log` na subpasta `%LOCALAPPDATA%\JevWIN\logs`. **Exportar diário JSON** gera cópia; não substitui extrato da corretora.

## 4. Preparar cotações no Excel

1. Em **Conexões**, use **Salvar modelos de exportação**.
2. No Profit, configure **Arquivo → Exportar em Tempo Real (RTD/DDE)** e habilite a transferência para Excel dentro das permissões da instalação.
3. Abra `Profit_RTD_Modelo.xlsx`. Digite o contrato exato em **Dados!A2**, sem `_F_0`; o programa não escolhe vencimento.
4. Confirme visualmente atualização das células e deixe Profit/Excel abertos na mesma sessão.
5. Informe **Contrato exato**, **Arquivo já aberto no Excel**, **Planilha principal / cotações** = `Dados`, **Intervalo principal com cabeçalho** = `A1:I2`.
6. Para apenas cotações, escolha `quote` e use **Conectar leitura Excel**. **Parar leitura** interrompe o acompanhamento.

O leitor preferencial usa COM nativo incluído no pacote. Não inicia Excel, abre arquivos, escreve células ou altera segurança. Acesso ao Excel não comprova feed da bolsa. DAT/HOR ausentes ou inválidos deixam a idade desconhecida. `ULT`, `QUL` e `VOL` não viram uma sequência fabricada de negócios: **quote não libera leitura de fluxo**.

## 5. Combinar cotações com negócios reais

Em **Modo: quote / tape / combined**, selecione `combined` para ler as duas tabelas do mesmo arquivo. Mantenha `Dados`/`A1:I2` e informe:

| Campo | Conteúdo |
|---|---|
| **Planilha de negócios (combined)** | `Negocios` |
| **Intervalo de negócios (combined)** | `A1:F501` |

A aba **Negocios começa vazia**. Precisa receber uma exportação real compatível e autorizada, com:

```text
id;symbol;ts_ms;price_points;quantity;aggressor
```

Preserve ID estável como texto; quantidade inteira e positiva; agressor reportado pela fonte. `ts_ms` é epoch UTC em milissegundos. Alternativas: `timestamp` com data/hora e offset, ou colunas data/hora. Hora isolada não recebe o dia atual. Organize negócios do mais antigo ao mais recente. Registros sem ID não alimentam o acumulador; agressor desconhecido não é inferido do preço/corretora.

**O modelo não exporta Times & Trades automaticamente.** É preciso conferir na sua instalação se a exportação oferece esses campos; faltar ID/agressor/horário pode exigir um adaptador ainda não disponível. Colagem estática não permanece recente sozinha.

Falha/tabela vazia/registro inválido em qualquer fonte invalida o ciclo combinado. Ambas são lidas sequencialmente, sem atomicidade de bolsa. A combinação permite referências e geometria quando os dados forem utilizáveis, mas continua parcial e não retira automaticamente **AGUARDAR CONFIRMAÇÃO**.

**Carregar negócios CSV** é replay. O exemplo `negocios_modelo.csv` usa `WIN_SIM` e IDs `SYNTHETIC-*`; informe `WIN_SIM` para carregá-lo. O relógio acompanha o arquivo, sem fingir pregão ao vivo.

## 6. JEV e cenários

Em **JEV**, informe **Chave da API** e **Limite de consultas nesta execução**: padrão **120**, ajustável de 1 a **10.000**. A chave fica em memória, sem persistência no diário/configuração. **Analisar agora** usa sua conta TypeSafe; medidas e limites de cobertura são enviados, sem patrimônio/pressão por recuperação nas perguntas de mercado.

Consulta automática começa desligada e requer fonte Excel ativa/evidência suficiente, com mínimo de **10 segundos**. Resposta atrasada, fonte alterada ou dados antigos vencem a avaliação. Notícias, conta e gestão de posições não estão conectadas.

**Cenários técnicos** usa referências observadas, sem inventar níveis futuros ou ranking de retorno esperado. Dados insuficientes podem produzir nenhuma combinação. Uma linha financeiramente viável continua sendo estudo, sem ordem ou promessa de lucro.

## 7. Falhas comuns e referências

Excel não encontrado: confira arquivo, planilhas, intervalos e sessão. COM ocupado: feche diálogos; a chamada nativa não tem timeout rígido. RTD imóvel: confira transferência, aba vinculada e janela de origem. Fontes sem `comtypes` podem usar PowerShell alternativo, respeitando a política local; combined exige COM nativo. Nenhuma política é contornada.

Consulte [PROFIT_BRIDGE.md](PROFIT_BRIDGE.md), [Nelogica: RTD/DDE](https://ajuda.nelogica.com.br/hc/pt-br/articles/360044293432-Como-configurar-RTD-DDE-no-Profit), [sintaxe RTD](https://ajuda.nelogica.com.br/hc/pt-br/articles/7834206674075-Significados-e-sintaxe-do-RTD) e [TypeSafe: API](https://docs.typesafe.ai/api).
