# Jeve Trader — arquitetura da baseline

Referência: `app/` herdado do **JevWIN v0.3.0**, em 06/10/2026. Esta documentação usa Jeve Trader como nome de projeto; os identificadores JevWIN continuam preservados. Não foi feita migração de dados, empacotamento ou nomes internos nesta organização.

## Sistema e limites

O aplicativo principal é [`desktop_app.py`](../app/desktop_app.py), em Python/Tkinter. O controlador coordena aquisição, estudos, consulta opcional ao JEV e atualização da interface. Cálculos de mercado e risco ficam em módulos separados da tela. A Central de decisão e o HTML recebem uma representação comum produzida por `build_decision_bundle` em [`app_core.py`](../app/app_core.py). O aplicativo observa e calcula; não controla Profit, ordens ou posições.

| Camada | Arquivos principais | Responsabilidade |
|---|---|---|
| Interface e controle | `desktop_app.py`, `decision_view.py` | Oito abas, formulários, workers, geração da fonte e histórico exibido. |
| Aquisição | `profit_bridge.py`, `helpers/read_excel.ps1` | Parsing CSV/Excel, saúde da fonte, IDs vistos, anexação COM e leitura combinada. |
| Estado e fluxo | `app_core.py`, `flow_engine.py`, `flow_rules.json` | Sessão de observação, retenção e medidas de fluxo, validade temporal. |
| Geometria | `candidate_engine.py`, `candidate_research.py` | Referências extraídas dos preços observados e combinações finitas de entrada/stop/alvo. |
| Finanças | `risk.py`, `capital_planner.py`, `risk_research.py`, `config.json` | Risco com `Decimal`, margem, pisos, dimensionamento, projeções e comparação de políticas. |
| Interpretação | `jev_client.py`, `observer_questions.json`, `questions.json` | Payload estruturado, versão fixada e validação estrita da resposta TypeSafe/JEV. |
| Conclusão e saída | `recommendation_engine.py`, `panel_report.py` | Vetos, correspondência da análise, estados de conclusão e HTML estático. |
| Persistência | `app_store.py` | Configurações permitidas, diário SQLite e exportação JSON. |
| Distribuição | `build_windows.ps1`, `packaging/` | Runtime Windows convencional, lançador, instalador NSIS e diagnóstico. |

`copilot.py`, `dashboard.py`, `stress_lab.py`, `demo_panel.py` e ferramentas relacionadas continuam como caminhos de pesquisa/compatibilidade. Não substituem a interface desktop principal.

## Aquisição e cobertura

O caminho implementado para observação externa é **Profit → exportação autorizada RTD/DDE → Excel aberto → leitura de valores**. A licença ProfitDLL não foi confirmada como disponível no ambiente do usuário; não há adaptador dessa DLL ou callbacks presumidos. [Contrato e limites da ponte](../app/PROFIT_BRIDGE.md).

| Fonte | Conteúdo utilizável | Limitação decisiva |
|---|---|---|
| Demonstração | Eventos sintéticos identificados como `WIN_SIM` | Verifica lógica, não representa pregão. |
| CSV | Negócios com ID, símbolo, timestamp, preço, quantidade e agressor | Replay e integralidade não comprovada. |
| Excel `quote` | Cotação e ofertas selecionadas | Não reconstrói negócios ou agressão. |
| Excel `tape` | Linhas individuais de negócios em intervalo configurado | Pode perder eventos entre leituras. |
| Excel `combined` | Cotação e negócios do mesmo arquivo, em um ciclo | Leitura sequencial; timestamps distintos; cobertura parcial. |

O backend preferencial usa `comtypes==1.4.17`, anexa `Excel.Application` já ativo e lê `Range.Value2` com dispatch dinâmico. Inicialização e liberação COM ocorrem na thread da leitura. Não abre Excel, escreve células, recalcula ou modifica políticas. O helper PowerShell é alternativa apenas na ausência de `comtypes`, sem contorno de erro de permissão. COM não oferece timeout rígido interrompível neste caminho; Excel ocupado pode atrasar a leitura.

No modo combinado, qualquer falha, tabela vazia ou dado inválido invalida o ciclo inteiro; confirmação da deduplicação ocorre após validar ambas as fontes. Não se mistura uma metade nova com outra antiga. O modelo [`Profit_RTD_Modelo.xlsx`](../app/templates/Profit_RTD_Modelo.xlsx) contém cotações e aba `Negocios` inicialmente vazia. Não há coletor automático de Times & Trades. Uma exportação real compatível precisa ser identificada na instalação do usuário. As fontes Excel/CSV mantêm `full_tape=False`.

## Estado, medidas e geometria

O motor normaliza eventos, preserva agressor desconhecido e trata duplicatas, regressões temporais e retenção limitada. Usa janelas de 5 segundos, comparação com os 5 anteriores e contexto de 30 segundos, com retenção de até 60 segundos. Delta e volume referem-se ao material capturado. Progressão, absorção e exaustão são descrições/hipóteses da amostra, sem prova de intenção ou previsão de preço. [Desenho herdado](../app/DECISION_DESIGN.md).

Referências técnicas são extremos e preços com toques repetidos na janela observada, preservando evidência. O comparador gera até oito geometrias; dados antigos, referências ausentes ou geometria inválida podem produzir conjunto vazio. Não há modelo de desfecho nem seleção por valor esperado.

O polling Excel é aproximadamente de dois segundos e não sobrepõe leituras. Trocar/parar a fonte invalida a avaliação; cada fonte possui geração. Respostas de workers anteriores são descartadas. Cenários expiram após dois segundos da referência de cotação e são invalidados ao alterar os dados financeiros. Receber resposta JEV não renova a idade do evento original.

## Risco e capital

O risco é determinístico e usa `Decimal`. Dimensionamento combina stop, custos, slippage, orçamento, margem, reserva e teto de contratos; pisos diário/do pico, sequência e pausa podem bloquear novas propostas. O capital é manual: resultados líquidos informados atualizam patrimônio, pico e sequência, inclusive saldo negativo. O perfil de pesquisa usa capital atual; o perfil de controle limita a base ao menor entre patrimônio inicial e atual. [Políticas e pressupostos](../app/RISK_MANAGEMENT.md).

O núcleo pode rejeitar estados de conta ausentes, antigos ou não conciliados quando esses campos são fornecidos. A interface atual trabalha com pressupostos de estudo; esse mecanismo não cria conexão com a Toro nem garante que posições abertas no Profit sejam conhecidas. Lote admissível representa um limite contábil do cenário, não exposição ótima. Custos e margens armazenados são exemplos datados.

## JEV e conclusão

[`jev_client.py`](../app/jev_client.py) fixa `jev-1.13.0` e o endereço configurado `https://api.typesafe.ai/v1/systemone`. Aceita perguntas `Choice` e `Noul`, valida estrutura, identidade do modelo, respostas e probabilidades, limita tamanho da resposta e não faz retries automáticos nem redirecionamentos. Estes são fatos do código herdado; nenhuma chamada autenticada foi realizada nesta organização ou na validação histórica citada.

A chave vem da interface ou `TYPESAFE_API_KEY`, permanece em memória e não é persistida. Consultas automáticas começam desligadas; quando habilitadas, exigem fonte Excel ativa/evidência suficiente, intervalo mínimo de dez segundos e orçamento de chamadas. O padrão documentado é 120 por abertura. O payload separa contexto de mercado dos valores financeiros e da pressão por recuperação.

`recommendation_engine.py` valida fonte, idade, geometria e risco recalculado; apoio do modelo só é usado quando corresponde à avaliação. Estados internos:

| Estado | Interpretação na Central |
|---|---|
| `SEM_DADOS` | Sem dados suficientes. |
| `AGUARDAR` | Aguardar confirmação; inclui impedimento de cobertura parcial. |
| `BLOQUEADO_RISCO` | Limite financeiro/contábil impede a proposta. |
| `HIPOTESE_PARA_REVISAO` | Evidência compatível para revisão, sem ordem ou validação operacional. |

O veto financeiro prevalece. `confidence`, apoio e contradição são medidas contextuais; não existe probabilidade calibrada de lucro. O painel HTML exportado é estático, sem feed ou consultas.

## Persistência e Windows

`app_store.py` mantém `journal.sqlite3`, configurações em lista permitida e até 10 mil eventos. A interface mostra até 50 mudanças recentes de conclusão. Sanitização exclui campos com nomes de credenciais; o diário não é extrato de corretora nem dataset experimental completo.

No Windows, dados ficam em `%LOCALAPPDATA%\JevWIN`; a instalação NSIS usa `%LOCALAPPDATA%\Programs\JevWIN` e preserva dados na desinstalação. O runtime de distribuição inclui CPython Windows x64, Tcl/Tk, SQLite, tzdata e comtypes. `JevWIN.exe` é lançador dependente da pasta inteira. `build_offline_windows.py` e `JevWIN.spec` são referências do empacotamento anterior, não o fluxo principal atual. [Build e diagnóstico](../app/WINDOWS_BUILD.md).

## Proveniência e evolução

Esta arquitetura deriva da inspeção dos módulos citados e dos documentos em `app/`. O [projeto histórico](archive/Projeto_JEV_Profit.md) é preservado; [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) separa implementação de verificação. A [pesquisa de 06/10/2026](research/Pesquisa_Decisao_JEV_WIN_2026-10-06.md) aponta melhorias como transportar a premissa do candidato e criar registro experimental versionado. Essas mudanças **não foram incorporadas** à baseline. Uma evolução deve alterar código, testes relevantes e documentação, sem promover proposta ou relatório matemático a resultado empírico.
