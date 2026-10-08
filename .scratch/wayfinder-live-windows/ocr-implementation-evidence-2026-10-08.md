# Entrega parcial Windows 0.5.2 — OCR local nativo

Data: 2026-10-08. Plataforma: Windows 11 x64 10.0.26200, Python 3.14.7. Código: `52a0914b7e0fa630336aeda0d4f499e73509b1b9`, sobre baseline `3ee94e2af7dc71ffebf26479110dfe319b422d91`. Branch: `codex/windows-updates-and-live-roadmap`.

Incremento derivado do plano aprovado e do [contrato OCR nativo](ocr-native-contract.md), sem alteração dos aceites da [mesa de fluxo](spec.md). O PowerShell 5.1 bloqueado e o requisito de identidade de pacote da API WinRT impediam a rota anterior. O helper C# compilado usa captura Windows; Tesseract 5.5.3 local reconhece a região selecionada. A configuração expõe disponibilidade do runtime. Nenhuma política Windows foi alterada.

OCR inicia OFF, revalida janela/processo/região, limita a área e aplica timeouts separados de captura e reconhecimento. Temporários permanecem locais e são limpos. O resultado continua `ocr_text_snapshot`, parcial: não produz negócios, níveis de livro, IDs ou continuidade, nem soma volume ao Excel. Imagens e texto OCR não integram o estado enviado ao JEV. Coleta Excel e cálculos locais continuam independentes do controle JEV.

## Verificação e revisão

244 testes Python e checks desktop passaram; 9 testes frontend, build frontend/Windows e diagnóstico empacotado passaram. Os 522 arquivos do manifesto do pacote tiveram tamanho e hash conferidos. O diagnóstico Tesseract reconheceu texto gerado; `real_profit_tested=false` e `continuity_verified=false`. O motor instalado passou no teste isolado com runtime disponível, OCR OFF, JEV OFF, zero chamadas, fonte idle e ordens desabilitadas.

Duas [revisões independentes](ocr-review-evidence-2026-10-08.md) em cópias isoladas verificaram 21 hashes de fontes e 40 payloads do runtime; cada revisor executou 12 testes offline, sem bloqueio restante. Modelo/tier/sandbox efetivos não foram comprovados. Os achados de overlays e declaração de reutilização foram corrigidos antes do pacote final.

O log vcpkg inicial registra zero pacotes restaurados, 20 construções e submissões para cache. O pacote final reutilizou dependências já instaladas; não corresponde a uma segunda compilação independente e o log inicial não certifica uso do wrapper endurecido posteriormente. Hashes, baseline, ABI e notices acompanham o runtime. Não se afirma ausência de escrita a cache nem auditoria comercial de licenças.

## Instalação, publicação e atualização

A atualização 0.5.1 → 0.5.2 ocorreu após encerramento gracioso. Os dois bancos locais permaneceram byte a byte iguais antes da reabertura; backup ficou somente local. Três hashes do payload instalado, registro 0.5.2 e atalho foram conferidos. A rota 0.4.1 não foi exercitada porque não estava instalada; nenhum downgrade foi realizado. O aplicativo iniciou com janela nativa e motor filho observados. Uma consulta posterior não encontrou JevWIN, Profit ou Excel; a causa da saída do aplicativo não foi inferida. Esse registro de inicialização não comprova interação de UI ou permanência do processo.

A [release privada v0.5.2](https://github.com/ori-inonu/jeve-trader/releases/tag/v0.5.2) foi publicada no commit acima. Instalador, portátil e SHA256SUMS tiveram tamanho e digest confirmados. A cópia `Downloads/Jeve-Trader-0.5.2-setup.exe` confere com o asset publicado. Consulta real de atualizações: 0.5.1 → `available`/0.5.2; 0.5.2 → `current`/0.5.2. Download e instalação de novas versões continuam manuais. Evidência estruturada: [release 0.5.2](release-evidence-0.5.2.json).

## Auditoria e próxima fronteira

OCR-N01..06 foram verificados no escopo local exercitado; isso não encerra FW-06, FW-11 ou FW-12. FW-06 exige pixels reais do Profit, extração estruturada e legibilidade/perdas calibradas. FW-11 exige captura autorizada ≥30 minutos, com rajadas, rolagem, filtros, abas/janelas e continuidade demonstrada; p95 visual ≤250 ms após recebimento ainda não foi medido nessa sessão real. FW-12 exige comparação independente de inferências JEV reais em casos anotados, com orçamento conhecido. Nenhuma chamada JEV paga, ordem ou alegação de rentabilidade foi usada nesta entrega.

Retomar [Contrato da captura real e reação ao painel](issues/04-piloto-real.md). A pergunta já enviada sobre arquivo/abas/intervalos/contrato permanece pendente; não inventar campos nem solicitar chave no chat. Próximo incremento elegível: validar o perfil observado, executar o instrumento de piloto já instalado e conferir cobertura/identidade/continuidade e latências separadas. JEV pode permanecer OFF. O mapa não recebe nova solução de OCR estruturado sem evidência dos campos e pixels reais; a decisão será registrada no ticket canônico. Mudanças gerais mantidas por outro chat foram preservadas e ficaram fora do commit desta etapa.

Estado da captura: `PENDING_REAL_REVIEW`. Instalação e animação não comprovam fluxo completo ou qualidade de decisão.
