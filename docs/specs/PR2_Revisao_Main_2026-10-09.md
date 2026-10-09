# PR #2 — correções da revisão contra main

Status: ready para regressões offline; os aceites anteriores permanecem imutáveis.
Origem: revisão independente de `0171aed6c4a25adf26d349bfe2c3140805a35e97` a `5f15ab73f4f5adfd3221b9bd5f785c24c9afc496`, solicitada por Gabriel em 09/10/2026.

| ID | Fonte e comportamento | Verificação |
|---|---|---|
| R-01 | FW-01 em `.scratch/wayfinder-live-windows/spec.md`: OFF concluído antes do despacho não permite novo HTTP. A mudança de enabled/revision e a última validação mais tentativa de cliente compartilham uma exclusão mútua. | Cliente externo offline pausa no intervalo anterior à invocação; OFF e despacho concorrentes nunca registram envio com enabled=false. |
| R-02 | FW-01/02/09: chamada já iniciada continua contabilizada; OFF revoga seu contexto/alerta/recuo, reinício continua OFF. | Regressões existentes de sucesso/erro em voo e restart passam; nenhuma API paga. |
| R-03 | I-02/I-11 em `Multimercado_Implementacao_2026-10-09.md`: reter no máximo 100.000 identidades por workspace/epoch, sem esquecer silenciosamente IDs e reaplicar duplicatas. No próximo evento único, invalidar todos os domínios com `dedup_capacity_exceeded`, avançar epoch e liberar identidades; qualquer invalidação libera IDs do epoch antigo. | Capacidade pequena injetada para testar saturação, duplicata no limite, rejeição de epoch antigo e recuperação com nova evidência. Estatística de ocupação em snapshot; teste prolongado por vários epochs confirma limite. |
| R-04 | I-02/I-06: saturação remove contexto dependente e usa o resync existente do adaptador; full_tape permanece false. | Teste da integração do serviço observa motivo, contexto removido e recuperação; suíte offline, frontend e build permanecem compatíveis. |

Seams existentes: `DecisionService.command/request_jev/snapshot`, cliente JEV externo, `MarketState.ingest/invalidate/snapshot`, clock injetável e serviço multimercado. A extensão opcional `dedup_capacity` é um limite de recursos positivo, máximo 100.000; não cria garantia de continuidade. Não altera preços, quantidades, taxas, orçamento JEV do produto, autorização de dados ou ordens.

Decisão JEV consultiva: recibo `3c2e92b0-5b34-4505-aee9-5571ab6116a9` recomenda sincronizar gate de despacho (0,98), abstém no tamanho do dedup (0,19). Limite local 100.000 preserva margem de dez vezes sobre a carga congelada de 10.000 eventos em 10 s, sem afirmar adequação a todo tráfego real. Saturação causa resync visível, nunca cobertura integral. Recibo de estratégia `5de57ca7-0014-4197-8683-43eefffd4b4d` recomenda corrigir e revisar novamente.

Risco explícito: a confirmação de OFF pode aguardar uma tentativa já iniciada. `timeout_seconds=3` é configuração de transporte, não prova de deadline total nem de latência nativa. Redesenho assíncrono/medição da jornada deve manter FW-01 e precisa de critérios próprios. Nenhum ganho de responsividade, rentabilidade, instalação ou janela nativa é certificado aqui.

Exclusões: merge, instalação/publicação de release, contratação B3, conta privada, ordens, fusão de outro PR e alteração de aceites anteriores. Nova revisão independente deve fixar o candidato final e reler ambos os achados; preparação do PR não executa merge.
