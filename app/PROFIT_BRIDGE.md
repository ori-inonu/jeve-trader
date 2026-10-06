# Profit Pro no Windows: leitura pelo Excel, sem ProfitDLL

Esta implementação usa o RTD/DDE que o Profit exporta para uma planilha do Microsoft Excel já aberta. O copiloto lê **valores**, em modo somente leitura, por COM nativo com `comtypes`, incluído na distribuição Windows. Não inicia Excel, não abre arquivos automaticamente, não escreve fórmulas, não modifica configurações de segurança, não consulta conta e não envia ordens. Não exige `pywin32` ou SDK/DLL da Nelogica. A disponibilidade efetiva do RTD depende da instalação, plano e permissões do usuário no Profit e no Excel.

O leitor preferencial usa `GetActiveObject('Excel.Application', dynamic=True)`, sem gerar wrappers de tipos do Excel. Cada leitura inicializa e encerra seu acesso COM na mesma thread; não compartilha ponteiros entre threads. A busca limita-se a 100 arquivos já abertos, e somente o intervalo da planilha escolhida tem seus valores lidos. O helper PowerShell anterior é usado **apenas se comtypes não estiver instalado**. Erro de acesso, sessão ou permissão no leitor nativo é apresentado ao usuário; não dispara uma tentativa alternativa nem alteração de política.

O caminho implementado não é uma conexão direta com a corretora Toro. Capital, posição, ordens e margem continuam sendo informados manualmente. Detectar Excel ou Profit aberto não comprova login, conexão com bolsa ou atualização dos dados.

## Preparar a planilha de cotações

1. No Profit, abra **Arquivo → Exportar em Tempo Real (RTD/DDE)**.
2. Em **Ativos**, adicione o contrato exato que deseja observar. Confira o vencimento no Profit; o copiloto não escolhe vencimento automaticamente.
3. Em **Atributos**, selecione último preço (`ULT`), oferta de compra (`OCP`), oferta de venda (`OVD`), volume da oferta de compra (`VOC`) e volume da oferta de venda (`VOV`). Se disponível, exporte também data (`DAT`) e hora (`HOR`).
4. Em **Configurações**, escolha o destino Excel/RTD, use **Copiar** e cole em uma planilha que você abriu no Excel. Confirme visualmente que os números se atualizam.
5. Prepare um intervalo retangular com uma linha de cabeçalho e pelo menos uma linha de dados. Use os nomes abaixo ou os aliases oficiais reconhecidos.
6. No copiloto, informe nome do arquivo aberto, nome da planilha e intervalo com cabeçalho, por exemplo `cotacoes.xlsx`, `Planilha1`, `A1:H20`. Deixe Excel e a ferramenta de origem no Profit abertos.

Cabeçalho recomendado:

```text
symbol;last;bid;ask;bidqty;askqty;date;time
```

Aliases aceitos neste modo:

| Campo do copiloto | Cabeçalho aceito do Profit | Significado |
|---|---|---|
| `symbol` | Ativo, Ticker, Contrato | Contrato explícito |
| `last` | ULT, Último, Preço | Último preço em pontos |
| `bid` | OCP | Oferta de compra |
| `ask` | OVD | Oferta de venda |
| `bidqty` | VOC | Quantidade/volume da oferta de compra |
| `askqty` | VOV | Quantidade/volume da oferta de venda |
| `date` | DAT, Data | Data da origem |
| `time` | HOR, Hora | Hora da origem |

`QUL` (quantidade do último trade) e `VOL` (volume agregado) **não são usados para fabricar eventos individuais**. Mudança de último preço entre leituras não identifica todos os negócios, agressão ou sequência do tape. As ofertas representam apenas os níveis presentes no intervalo, sem prova de profundidade ou continuidade do livro.

A Nelogica documenta a sintaxe `=RTD("RTDTrading.RTDServer";;"CÓDIGO_SUFIXO";"ATRIBUTO")`, com sufixo `F_0` para ativos BMF. Use preferencialmente a fórmula copiada pelo próprio Profit para seu contrato. Esta implementação não insere fórmulas no Excel.

### Pausa e atualização

A documentação da Nelogica descreve situações como RTD desativado, RTD pausado quando a aba vinculada não está ativa e janela de origem fechada. Confira o estado no Profit e as células do Excel. O leitor não ativa abas nem muda a janela do Profit.

A leitura bem-sucedida identifica **acesso à planilha**, não conexão comprovada com a bolsa. Sem timestamp da origem, a idade da cotação permanece desconhecida. `observed_at_ms` é o instante de leitura local; nunca substitui o horário de mercado. Excel é lido por amostragem: pode combinar células atualizadas em momentos diferentes e perder negócios entre leituras.

O leitor anexa uma instância Excel registrada no COM da sessão Windows atual. Com múltiplas instâncias, ele pode encontrar apenas uma delas; abra a planilha na mesma instância acessível. Diferenças de usuário ou elevação entre Excel e copiloto podem impedir a anexação. O programa apresenta erro sanitizado e não tenta elevar privilégios nem alterar políticas.

## Leitura combinada: cotações e negócios juntos

`CombinedExcelBridge` resolve a separação anterior entre `quote` e `tape`: lê dois intervalos do **mesmo arquivo já aberto** em uma única anexação COM/apartment. A fonte de cotações permanece no modo de cotação; a fonte de negócios precisa conter registros individuais reais. Os timestamps originais de cada fonte permanecem separados. O instante local de leitura não substitui nenhum horário da origem.

```python
from profit_bridge import CombinedExcelBridge

reader = CombinedExcelBridge(
    "Profit_RTD_Modelo.xlsx", "Dados", "A1:I2",
    "Negocios", "A1:F501", symbol="SEU_CONTRATO")
batch = reader.read()  # batch.quotes e batch.events no mesmo ciclo
```

O arquivo fornecido agora inclui a aba **Negocios**, com cabeçalho `id,symbol,ts_ms,price_points,quantity,aggressor` e linha de dados vazia. Ela **não contém fórmulas inventadas de Times & Trades**. Configure uma exportação real autorizada que sua instalação disponibilize, ou cole registros reais compatíveis, preservando IDs como texto. Não troque QUL/VOL por eventos nem crie ID pelo número da linha. Negócios devem estar em ordem do mais antigo ao mais recente. Timestamp pode ser epoch UTC em `ts_ms`, ou cabeçalho `timestamp` com data/hora e offset. A disponibilidade e o layout dessa exportação precisam ser conferidos na sua instalação; o modelo não implementa um coletor específico da janela Times & Trades.

Ambos os intervalos precisam ter registros válidos do contrato escolhido. Se qualquer leitura ou parser falhar, o ciclo combinado gera erro sem devolver apenas uma tabela ou consumir IDs da outra. Uma aba Negocios vazia não é um negócio nem libera análise. Valores velhos não são reutilizados pelo bridge como substitutos de uma leitura que falhou. IDs só são confirmados no cache depois de ambas as tabelas passarem pela validação. Negócios sem ID continuam sem ID e serão excluídos do acumulador da interface.

O status é `EXCEL_COMBINED_SNAPSHOT`, com `feed_connected=None` e `full_tape=False`: acesso ao Excel não confirma feed, cobertura integral ou conta. As duas leituras são sequenciais e podem refletir atualizações em instantes distintos; não há transação atômica de mercado. Dado sem timestamp mantém idade desconhecida. O consumidor deve verificar frescor individual de cotação e tape antes de comparar cenários.

O modo combinado exige `comtypes` nativo, incluído no pacote. Não utiliza o fallback PowerShell. Limites por intervalo continuam 64 colunas/5001 linhas, e COM continua sem timeout rígido interrompível. O tratamento de falha deve invalidar a avaliação atual no aplicativo; reconectar não comprova continuidade dos negócios perdidos.

## Times & Trades: dados reais de negócio, quando disponíveis

O modo `tape` aceita somente um intervalo com negócios efetivamente exportados do Times & Trades. Precisa conter preço, quantidade inteira, agressor e timestamp com data. Informe também ID estável do negócio, quando fornecido. Uma coluna com nome da corretora compradora/vendedora não é identidade do agressor e não deve ser renomeada para `aggressor`.

Cabeçalho recomendado:

```text
id;symbol;timestamp;price_points;quantity;aggressor
```

Exemplo de **replay ilustrativo**, sem representar mercado ao vivo:

```csv
id;symbol;timestamp;price_points;quantity;aggressor
exemplo-1;WIN_SIM;2026-10-06T10:30:00.125-03:00;130000,0;2;Compra
exemplo-2;WIN_SIM;2026-10-06T10:30:00.250-03:00;130005,0;1;Venda
```

Agressão aceita `Compra/Comprador/BUY/C/B` e `Venda/Vendedor/SELL/V/S`; demais valores preservam `UNKNOWN`. Códigos numéricos não são interpretados por adivinhação. Negócios idênticos sem ID continuam distintos e geram aviso de integridade; não recebem ID fabricado. IDs são deduplicados por símbolo/data/ID em cache limitado. Quando o cache expira, a possível repetição de registros antigos é informada.

Mesmo com todas as colunas, exportar um intervalo visível do Excel não comprova que todos os negócios foram recebidos. O status será `EXCEL_TAPE_SNAPSHOT` e `full_tape=False`. Cálculos podem descrever a janela observada; não devem ser apresentados como fluxo integral ou sequência garantida.

## CSV para replay e validação

`read_csv_events()` aceita CSV UTF-8/BOM ou CP1252, separado por vírgula, ponto e vírgula ou tabulação. CSV brasileiro com decimal vírgula deve usar ponto e vírgula ou aspas no campo. Preços como `130.000,5` são reconhecidos; valores numéricos com ponto sem vírgula tratam o ponto como decimal. Quantidades precisam ser inteiras e positivas; `1,5` contrato é rejeitado. Quantidade zero é aceita apenas nas ofertas.

Horários aceitos:

- `ts_ms`: epoch UTC em milissegundos inteiro positivo.
- `timestamp`: ISO com offset, como `2026-10-06T10:30:00.125-03:00`, ou data/hora juntas.
- `data` + `hora`: por exemplo `06/10/2026` e `10:30:00,125`.

Data/hora sem offset usam `America/Sao_Paulo`. No Windows, instale `tzdata` para regras históricas (`python -m pip install tzdata`). Se a base IANA estiver ausente, datas de 2020 em diante usam UTC−03; datas anteriores são rejeitadas para não errar o horário de verão histórico. Hora sem data é rejeitada. Não se atribui o dia atual a uma célula antiga.

O arquivo tem limite de 8 MiB e a janela retornada, 10.000 eventos. Exportação maior deve ser dividida. Arquivo modificado durante a leitura é rejeitado. Registro final com campos faltantes é ignorado com aviso; registros inválidos não geram dados substitutos. Prefira concluir a exportação ou substituir o CSV de forma atômica. A leitura não modifica o arquivo.

`CSV_REPLAY` também usa `full_tape=False`: o conteúdo do arquivo não comprova integralidade da sessão. O aplicativo pode usar o último timestamp do arquivo como relógio de replay, com esse modo explicitamente visível. Não compare dados históricos com o relógio atual para fingir que são ao vivo.

## Contrato Python

```python
from profit_bridge import ExcelBridge, SeenTradeIds, read_csv_events

# Apenas leitura de arquivo fornecido pelo usuário.
seen = SeenTradeIds(capacity=50000)
batch = read_csv_events("negocios.csv", "WINV26", seen_ids=seen)
for event in batch.events:
    normalized = event.to_dict()  # id, symbol, ts_ms, price_points, quantity, aggressor

# Apenas anexação ao Excel existente; nenhum arquivo é aberto pelo código.
excel = ExcelBridge("cotacoes.xlsx", "Planilha1", "A1:H20",
                    mode="quote", symbol="WINV26")
batch = excel.read()
health = batch.health.to_dict()
```

`SourceBatch` contém `events`, `quotes`, `health` e `warnings`. Em cotações, `events` é vazio. `QuoteSnapshot.ts_ms` pode ser `None`. `SourceHealth.connected` informa que foi possível ler registros, e não autenticação/feed da bolsa. `complete`/`full_tape` ficam falsos para estas fontes. `sequence_ok` informa ordem temporal observada dos eventos retornados, sem verificar sequência numérica do provedor. O chamador deve tratar avisos, idade real e falhas; a última leitura bem-sucedida não autoriza reutilizar sinal indefinidamente.

## Instalação e empacotamento Windows

Python 3.10 ou superior; Excel instalado; Profit com exportação RTD/DDE disponível e configuração concluída pelo usuário. A distribuição Windows inclui `comtypes==1.4.17`, biblioteca Python de acesso COM; a leitura preferencial não executa script PowerShell e não depende da política de execução de scripts. Em instalação manual dos fontes, instale `comtypes` para habilitar esse caminho.

Se a biblioteca estiver ausente, o helper alternativo usa Windows PowerShell 5.1 e COM de Excel. Uma política local que bloqueie esse script deve ser respeitada; o copiloto não aplica `ExecutionPolicy Bypass`. O `timeout_seconds` limita o subprocesso PowerShell. Chamadas COM nativas rodam em worker do aplicativo, mas não possuem timeout rígido interrompível: um Excel ocupado pode atrasar a leitura. Feche diálogos e confirme que Excel responde; o aplicativo não inicia leituras concorrentes enquanto a anterior estiver em andamento.

Em uma pasta de distribuição, mantenha `helpers/read_excel.ps1` junto do módulo. Ao usar PyInstaller, inclua-o explicitamente (o ponto e vírgula abaixo é sintaxe Windows):

```powershell
python -m PyInstaller --add-data "helpers;helpers" <demais-opcoes> desktop_app.py
```

Não existe execução de ordens nem reconciliação de saldo/posição neste módulo. Validação real de COM, RTD, atualização e layout deve ser feita no Windows do usuário com planilha que ele escolheu. Os testes automatizados cobrem parsing, timestamps, limites, integridade, ID, seleção COM dinâmica com objetos simulados, balanceamento de inicialização/encerramento, erros sanitizados, ausência de fallback por permissão e restrições do helper. Não substituem essa validação.

## Fontes oficiais consultadas

- Nelogica, [Como configurar RTD/DDE no Profit](https://ajuda.nelogica.com.br/hc/pt-br/articles/360044293432-Como-configurar-RTD-DDE-no-Profit): fluxo de exportação, destino Excel, mensagens de pausa/falha e limitação de exportação simultânea.
- Nelogica, [Significados e sintaxe do RTD](https://ajuda.nelogica.com.br/hc/pt-br/articles/7834206674075-Significados-e-sintaxe-do-RTD): atributos, sintaxe do servidor e sufixos.
- comtypes, [documentação oficial de cliente COM](https://comtypes.readthedocs.io/en/stable/client.html): anexação a objetos já registrados, propriedades e dispatch dinâmico sem wrappers gerados.
- comtypes, [pacote oficial PyPI](https://pypi.org/project/comtypes/): distribuição 1.4.17, biblioteca Python para Windows.

Consultadas em 06/10/2026. Nenhuma afirmação de disponibilidade do seu plano, conexão testada no seu computador ou autorização para distribuição de dados é inferida dessas páginas.
