# Revisão independente do PR contra main — 2026-10-09

PR: [#1](https://github.com/ori-inonu/jeve-trader/pull/1). Base fixa `0171aed6c4a25adf26d349bfe2c3140805a35e97`; candidato de código `3e2bfec012512582859bee69e9edae76fb70aabf`. A comparação inclui as entregas Windows anteriores: 48 commits, 210 arquivos, +25.022/−157. Os revisores usaram arquivos ZIP fixos em cópias privadas isoladas, sem editar a implementação.

## Standards

O primeiro parecer encontrou um bloqueio P2: documentos rastreados continham caminhos pessoais e identificadores privados. A correção documental `824cce9d0deae4ceaff714e7e48798614e7a83b6` passou por nova revisão independente: 21 documentos, +29/−29, quatro JSONs válidos, links relativos válidos e 129 hashes técnicos preservados. Não houve alteração de código ou critérios de aceitação. O parecer final não encontrou novo bloqueio Standards. A correção não reescreve o histórico Git.

O eixo examinou atualização/instalação Windows, OCR, credenciais e migração de estado; 24 testes offline focados passaram. O parecer inicial tem SHA-256 `528318abb0d7890c6704b513d3eded31e44f7180ee7de76259dd0180650614d8`; a revisão da correção tem SHA-256 `3cee992740451a3fb474944274eaa00107127ce2df5bc37e70c79338247dce93`.

## Spec

PASS limitado ao software exercitado e ao observador/calculadoras sem ordens. A revisão mapeou CM-01–12, AC-01–07, IM-01–09, FW-01–12 e WF-01–06, além de PRD e contratos Wayfinder. Nenhum requisito Spec ausente, desvio ou comportamento incorreto bloqueia esse recorte. O candidato de código coincide com a versão anterior revisada, que passou independentemente 345 testes e self-test offline; a suíte não foi repetida para o delta documental.

Parecer Spec SHA-256 `22397c3f3d883f12c4c399f33ec6d95e1c393ea67b04fd0f71d2a011a5702af0`. Archive do candidato SHA-256 `3f94e1734f8e1f533a71d32751064451db1f1bb476b94668a23352826416b24a`; diff congelado SHA-256 `6eb82ec3153166b4eb09ce5ff8574df915d6e7d0e141f4d6c30ea6e644035146`.

## Alcance e continuação

Os três ensaios públicos anteriores continuam reprovados. Coleta sustentada, janela Tauri, Profit/Excel, direitos/licenças, seleção econômica real e AC-07 permanecem pendentes; amostra financeira 0 e probabilidades desconhecidas. O parecer não certifica rentabilidade nem a meta R$400 → R$4.000. Não há checks/statuses remotos do candidato que comprovem CI. Nenhum merge foi executado.

A próxima entrega é [DI-01–07](../specs/Diagnostico_Coleta_Publica_2026-10-09.md): instrumentação opt-in de sequência/lifecycle, limitada e sanitizada, com testes offline antes de um único ensaio causal público de até 20 segundos. Essa investigação preserva a política de sequência e não repete o ensaio genérico de saúde em quarentena.

O código desse incremento ainda não começou: a transição do harness foi bloqueada pela referência de proveniência anterior à sanitização. O [checkpoint de continuação](multimercado-proximo-incremento-2026-10-09.md) registra a comparação independente, a rejeição da restauração dos bytes privados e os passos pendentes sem alterar os aceites.
