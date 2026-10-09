# Captura OCR local sem PowerShell

Status: ready (2026-10-08). Incremento reversível derivado de FW-06/FW-10 do plano aprovado; não altera os aceites congelados.

Baseline do código: `3ee94e2af7dc71ffebf26479110dfe319b422d91`. Responsável pela integração: conversa `[identidade privada omitida]`; arquivos de outras conversas preservados.

## Problema observado e caminho

O Windows PowerShell 5.1 bloqueia `app/profit_ocr.ps1` com `UnauthorizedAccess` antes de capturar pixels. A documentação da [Microsoft](https://learn.microsoft.com/en-us/uwp/api/windows.media.ocr?view=winrt-26100) exige identidade de pacote para suporte desktop de Windows.Media.Ocr; o NSIS/portable atual não tem essa identidade. Nenhuma política de execução, TLS ou Defender será alterada.

Usar um helper C# compilado para a captura GDI delimitada da janela Profit selecionada e o [Tesseract](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html) local para reconhecer a imagem. Compilar Tesseract pelo [port vcpkg](https://github.com/microsoft/vcpkg/tree/2750401336fb7c95f6619657a46a7e798661341c/ports/tesseract), baseline fixada, triplet `x64-windows-static`, sem ferramentas de treinamento; preservar os avisos de todas as dependências e fixar modelo `eng` de tessdata_fast. Testes e diagnóstico não enviam imagens, textos, transcrições ou chamadas ao JEV.

## Aceites do incremento

- OCR-N01: `capture_profit` revalida handle/título/processo visível e não minimizado, região interna e área limitada. Helper compilado revalida a seleção antes e após PrintWindow; seleção inválida não deixa imagem. Nenhum script PowerShell é executado pelo runtime.
- OCR-N02: captura e reconhecimento têm timeouts separados, processos próprios sem filhos e pasta temporária própria removida em sucesso, erro e timeout. Erro público distingue runtime ausente de janela indisponível, sem publicar pixels ou texto de stderr.
- OCR-N03: saída continua `ocr_text_snapshot`, parcial, sem IDs/negócios/níveis estruturados/continuidade ou confiança financeira. Datas de captura e recebimento, duração e engine são explícitas. OCR nunca é somado ao tape Excel nem enviado ao contexto JEV.
- OCR-N04: `DecisionService.command/snapshot` inicia OCR OFF, mostra disponibilidade do runtime; falha e OFF descartam a observação vigente; resultado tardio de outra revisão é ignorado. JEV permanece OFF durante testes.
- OCR-N05: preparar runtime verificável com baseline, modelo e hashes, notices das dependências; falhar o build se faltarem helper/engine/modelo/manifesto. Diagnóstico local com texto conhecido verifica reconhecimento; isso não certifica pixels reais do Profit, estrutura do fluxo, perdas ou latência do feed.
- OCR-N06: revisão independente em cópia isolada, checks afetados, build Windows e atualização preservando os dados locais antes de distribuir o incremento.

## Limites que continuam abertos

FW-06 exige validar leitura real e calibração; o snapshot textual continua sem extração estruturada. FW-11 exige Profit/Excel reais por 30 minutos, continuidade e p95 visual. FW-12 exige casos anotados e comparação contextual. A nova engine não fecha nenhum desses aceites por si só.

Se a compilação/fechamento de dependências falhar, registrar o erro exato e manter o runtime indisponível; não distribuir a API WinRT sem suporte nem substituir o feed por dados sintéticos.
