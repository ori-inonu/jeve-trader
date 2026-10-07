# Primeira tarefa no Codex — ciclo de decisão v0.4

**Retomada em 07/10/2026:** o painel 0.4 e boa parte deste primeiro ciclo estão implementados. Leia [HANDOFF.md](HANDOFF.md), [status](IMPLEMENTATION_STATUS.md) e o quadro atual do [backlog](BACKLOG.md). Não repita a transferência, o scaffold ou a implementação das premissas já corrigidas. O texto abaixo preserva a tarefa original e seus critérios; os itens ainda parciais têm continuação explícita no backlog.

Você está no repositório **Jeve Trader**, continuação de um projeto existente. Leia `AGENTS.md`, `docs/HANDOFF.md` e os itens iniciais do `docs/BACKLOG.md`. Trabalhe sobre `app/`, que contém a baseline JevWIN v0.3.0. Respeite o modelo selecionado por Gabriel; a preferência registrada é GPT-6.1 Sol.

**Objetivo desta sessão:** implementar o primeiro conjunto verificável de melhorias na avaliação contextual do JEV. Conclua código e testes dos itens viáveis; não entregue apenas uma nova especificação.

1. Execute a preparação e a verificação existentes; registre o estado inicial.
2. Reproduza a perda de `premise` no payload produzido pela interface. Preserve a premissa e os campos necessários à interpretação sem enviar patrimônio ou pressão por recuperação como evidência de mercado.
3. Separe hipóteses de continuidade e absorção quando sua disjunção torna a avaliação ambígua. Preserve IDs/versões rastreáveis e invalidações explícitas.
4. Separe apoio, contradição e insuficiência de evidência nas perguntas efetivamente usadas pela interface. Consuma insuficiência explicitamente na composição do estado de revisão, sem inventar um limiar financeiro ou uma probabilidade de lucro.
5. Adicione os testes relevantes para ausência de dados, contradição real, hipóteses mistas, payload e resposta inválida. Use fixtures e transporte simulado; não faça chamadas pagas ao JEV.
6. Inicie o registro experimental versionado: perguntas exatas, estado disponível, ordem, versão do modelo, regras, horários e resposta validada. Mantenha credenciais fora dos registros e distinga falha de captura de falha de API.
7. Rode as verificações afetadas e a verificação do projeto ao concluir o conjunto. Atualize `docs/IMPLEMENTATION_STATUS.md` e os itens concluídos do backlog com evidência e plataforma.

Continue autonomamente nos itens independentes se um teste Windows ou uma integração externa bloquear parte do ciclo. Preserve o acompanhamento sem ordens e os bloqueios de dados/frescor. Não afirme que os experimentos E01–E10 foram executados apenas por existirem fixtures.

**Entrega esperada:** diff implementado e revisável, testes e seus resultados, mudanças no painel explicadas, limitações restantes e próximo item. O arquivo `docs/research/Plano_Experimentos_JEV.json` orienta a pesquisa futura; não é uma configuração pronta para operação ao vivo.
