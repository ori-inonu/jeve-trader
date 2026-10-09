# Continuação EM-03 — checkpoint de implementação

Data: 2026-10-09. Escopo: diagnóstico da coleta pública, conforme [DI-01–07](../specs/Diagnostico_Coleta_Publica_2026-10-09.md). A [revisão contra main](multimercado-revisao-main-2026-10-09.md) passou no recorte de software existente. Nenhum código diagnóstico ou novo ensaio público foi executado.

## Preparação concluída

- SPEC candidata atual: SHA-256 `83898c30b721e6e3d803b38704e16f705630bbe3eed4a049b2a85039adc2fbaa`. A revisão documental pediu os domínios exatos do schema; o apêndice define chaves, enums, faixas e contagem/serialização sem alterar DI-01–07. O status HTTP numérico sugerido foi removido após revisão Spec para conservar as categorias previstas.
- Proposta estruturada da versão anterior da candidata (`bdeccdacfdcae19299f902aee9423030619e6f8b5fb99a880deadc3fefc562ec`): digest semântico `85d06ff83946c0653ce14bd7c8cbe91ffc4bca5dde0ee6a6813d16b0bee66163`; SHA-256 dos bytes do JSON `4f1e6ee0deff928f2081909c717252a4b806a495a58150d4a541f79819fb511b`. São verificações distintas e vínculos históricos, não aprovação da versão atual.
- Revisão independente de escopo favorável à proposta anterior: SHA-256 `b1f948a7d5d673266941cff8c19168c672d2949f66de848aa5a70765f34d7386`. Esse parecer não aprova código, execução ou merge. Antes de congelar a candidata atual, regenerar a proposta e obter parecer tipado vinculado ao novo hash.
- Workspace isolado preparado; nenhum implementador foi iniciado. Ownership e testes RED/GREEN estão descritos na SPEC.

## Dependência que impede iniciar o código

A transição `begin_cycle` falhou atomicamente com `stale_evidence`; o estado observado após a falha foi `revision=27`, `phase=audit`, `status=completed`, sem lease e sem novo ciclo. A auditoria anterior referencia os bytes exatos da SPEC original, SHA-256 `7e8d20347360bfa6423b00208f8acdb03565b8d0f3a69118dfadbd3b41200612`. A correção documental de privacidade alterou somente a linha de proveniência desse documento; seu SHA-256 atual é `926530d39ff6119a26a39ef817ef79e423833b3fd400b337971e701e22c5044c`. Objetivo e aceites permanecem idênticos, conforme comparação independente.

O runtime valida a referência congelada antes de arquivar o ciclo. `supersede_evidence` exige tarefa ativa e lease, e só aceita evidência ou falha; não revalida a SPEC de uma auditoria concluída. Não há operação exposta para essa migração documental. Alterar o ledger ou enfraquecer a validação não foi realizado.

A alternativa de restaurar temporariamente os bytes originais foi rejeitada em revisão independente porque reintroduziria o identificador privado redigido e deixaria a referência histórica stale após a restauração da versão sanitizada. Nenhuma restauração ou cópia dessa versão foi feita. Parecer da recuperação: dependência de revalidação que preserve os critérios, a privacidade e o histórico. A recomendação consultiva anterior não substituiu esse parecer.

## Próxima execução, após resolver a dependência

1. Revalidar a proveniência sanitizada por mecanismo suportado, preservando os aceites congelados e a evidência da revisão independente; conferir estado e hashes antes de `begin_cycle`.
2. Regenerar a proposta e o parecer tipado de escopo para o hash atual, registrar e congelar DI-01–07 e seu contrato fechado no novo ciclo. Um implementador isolado cuida de feed, observer, CLI e testes focados; o integrador cuida das evidências e documentos.
3. Executar RED/GREEN offline para sequência, primeira falha causal, fechamento local, sanitização, limites de 64 eventos/16384 bytes e desligamento dos helpers; verificar a suíte pertinente sem fonte pública nem JEV pago.
4. Após verificação, executar no máximo um diagnóstico público causal de 20 segundos, com metadados permitidos e classificação da causa ou insuficiência de evidência. Revisar o candidato independentemente nos eixos Standards e Spec.

A hipótese de repetir ensaios genéricos para obter coleta saudável permanece em quarentena. Ordem real, GUI Tauri/Profit/Excel, licença/acesso aos demais mercados e AC-07 empírico continuam dependências próprias. A meta R$400 → R$4.000 não possui probabilidade financeira estimada; dados/custos/risco insuficientes mantêm `wait` e q=0.

Escolha de continuidade: Jev Workflows abstém no recibo `b3ff4e0d-184a-4a66-b30d-1b6e62447e4a`; o fallback local fundamentado conclui a revisão do PR e adia somente o código dependente da transição. Custo faturado desconhecido: `null`.
