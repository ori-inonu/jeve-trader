# Próxima melhoria — evidência da jornada Windows

Status: draft; investigação elegível, implementação dependente da investigação.
Origem: auditoria do contrato I-07/I-10/I-11 e fronteira Wayfinder de 09/10/2026.

O incremento entregue possui testes offline e prévia React, mas não comprova a jornada da nova janela Windows, a atualização ponta a ponta nem redução de etapas manuais. A próxima melhoria proposta é um protocolo reproduzível para observar essa jornada e identificar onde a automação ainda exige intervenção. É uma proposta local fundamentada nos aceites existentes; não há autorização de ordens, contratação de feed ou acesso privado.

## Pesquisa anterior à decisão

RT-12 deve identificar quais capacidades nativas estão disponíveis, quais métricas podem ser colhidas sem dados privados e qual baseline permite comparar a mesma tarefa antes/depois. A investigação deve comparar essa entrega com a qualificação documental B3 e a importação read-only de conta. A [consulta JEV](../evidence/multimarket-next-cycle-jev.json) absteve-se por confiança insuficiente; sua distribuição não encerra a escolha. Não iniciar implementação dependente por essa recomendação.

## Contrato candidato

| ID | Comportamento e aceite propostos |
|---|---|
| N-01 | Identificar release, host, instrumentos/fontes e roteiro; preservar dados JevWIN em cópia autorizada. |
| N-02 | Observar boot desconectado, conexão explícita, atualização contínua, desconexão e retorno ao legado na janela real. Falhas e frescor devem ter causa visível. |
| N-03 | Medir a mesma jornada prospectiva antes/depois, com contagem de ações, intervenções, tempo e qualidade; ausência de comparador ou medição permanece null. |
| N-04 | Separar tempo pós-recebimento, transporte, renderização e idade da evidência; métricas/screenshot sanitizados, sem corpus de mercado ou conta privada. |
| N-05 | Relatar somente capacidades exercitadas. Build, instalação, execução nativa e ganho medido são aceites distintos. |

Esses critérios ainda não foram congelados. A investigação deve produzir fontes atuais, roteiro executável, limites de ferramenta e revisão independente de escopo antes de uma SPEC ready. A conclusão do incremento I-01–I-12 não inicia esse ciclo automaticamente.
