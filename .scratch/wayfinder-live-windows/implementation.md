# Implementação autorizada da central ao vivo

Status: in-progress
Baseline: a887254
Autorização: Gabriel, “Implement the proposed plan”, 2026-10-07.

Um incremento de implementação, com marcos internos. Preservar as alterações documentais do outro chat. O piloto de captura e reação humana permanece aberto.

Entrega A (0.5.0): perfil Excel salvo, descoberta dos arquivos abertos, modo cotação sem tape, reconexão, protocolo v2, avaliação contextual independente automática por mudança (mínimo 1 s, uma chamada em voo), validade 2 s, credencial Windows, orçamento persistente US$1/dia e US$5 total, termômetro experimental, indicadores com ausência explícita, inspeção congelada e alertas com rearmamento. Ordens manuais e gate econômico preservados.

Entrega B (0.6.0): somente após SDK/licença e ABI autorizados, integração ProfitDLL com negócios V2 e PriceDepth em processo isolado. Não inventar driver nem declarar fluxo integral com dados incompletos. Preparar o limite de callbacks e diagnóstico sem declarar conexão entregue.

Limites de teste já aprovados no plano: interfaces públicas da coleta, avaliação/validade, orçamento persistente e alertas; protocolo do serviço e publicação; construção e instalação Windows. Testes locais não acessam API paga. Captura ao vivo, reação humana, latência real, DPI/Narrator e rentabilidade exigem evidência própria.

Revisão independente: regras e especificação a partir da baseline acima. Commitar apenas arquivos desta implementação. Preservar identifiers com.jevwin.desktop / JevWIN, banco local, ícone e consulta privada de releases com instalação manual.
