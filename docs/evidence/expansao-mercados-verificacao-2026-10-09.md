# Verificação da entrega documental

Conversa própria: `01a11ee0-293d-7a82-8719-5c41909aebcb`. Worktree: `C:/Users/gabri/.codex/worktrees/pesquisa-apis-mercados/jeve-trader`; baseline `da96c6ad4187030a98c4daa86a6b96e1e5b809a9`. Plataforma observada: Windows 11, Python 3.14.7. Estado: verificações locais aprovadas; revisão independente registrada em parecer separado quando concluída.

## Comando e alcance

Executado em 2026-10-09 no worktree:

```powershell
python docs/evidence/verify_expansao_mercados.py --output docs/evidence/expansao-mercados-verificacao-2026-10-09.json
```

Exit code 0; 18 links locais existentes, JSON de decisões válido, hashes dos dez artefatos e de três contratos do app. Cálculos Decimal confirmados: 10×/900%, composição 5/7 períodos, payout e equilíbrio binário, contagens ideais, WIN e responsabilidade lay. [Script](verify_expansao_mercados.py), [resultado completo](expansao-mercados-verificacao-2026-10-09.json).

`git diff --name-only HEAD` vazio; baseline confirmada. Nenhum arquivo rastreado do aplicativo foi alterado. Os artefatos novos estão sob docs desta frente, sem staging/commit. O checkout principal concorrente não recebeu edições desta investigação. Os 64 endereços externos do pacote são referências de pesquisa; o script não faz chamadas de rede nem verifica disponibilidade atual dessas páginas.

As notas de fonte distinguem documentação, GET público pontual, hashes de corpo, respostas 403 e campos desconhecidos. Foram observados quatro GETs REST sem conta; não houve teste de stream contínuo, feed B3, latência estatística, permissões de conta brasileira, execução, lucro ou probabilidade da meta. Não foi necessário executar a suite do aplicativo para esta entrega que não o modifica; a verificação exercita a matemática e a integridade afetadas.

## Preservação de erros e estado

- Claim na raiz recusado com `overlapping_lease`; foi usado worktree anexado, sem remover ownership de outra conversa.
- Primeira referência SDD absoluta recusada com `invalid_evidence_path`; transições dependentes encontraram conflito de revisão. A referência foi corrigida para caminho relativo e SHA-256, sem enfraquecer aceites.
- Um patch com delete/add do mesmo arquivo foi recusado; substituído por update, sem alteração parcial observada.
- Consulta Jev Workflows `607f7108-6d5f-4cc0-a3c3-0ba1123dbf1b` ficou indisponível por `invalid_response`; o fallback foi verificar contas e contratos locais já autorizados. Recibos sanitizados registram custo faturado desconhecido.

Esses eventos são falhas de coordenação/formato, sem evidência de desempenho econômico. A pesquisa mantém critérios AM-01–06 congelados e própria identidade; revisão usa cópia isolada e hashes. Próxima tarefa elegível: EM-01, especificar perfil de um feed público sem ordens; EM-06/07 são frentes documentais de alavancagem. SPEC futura não foi declarada ready nem implementada.
