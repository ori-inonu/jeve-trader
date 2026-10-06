# Jeve Trader — instruções para agentes

## Objetivo e ponto de retomada

Construir um copiloto Windows para Profit Pro/B3 WIN com JEV contextual, evidência verificável e risco explícito. Retome tarefas concretas do backlog. Para uma sessão nova, use `docs/HANDOFF.md`; para o primeiro ciclo, `docs/CODEX_NEXT_TASK.md`. Leia os demais documentos conforme a tarefa, evitando carregar todo o arquivo histórico.

O nome do projeto é Jeve Trader. A baseline importada é JevWIN v0.3.0, em `app/`. Preserve identificadores de instalação e dados até uma migração deliberada e testada. O código inicial não foi reescrito nesta transferência.

## Comandos e mapa

- Linux/Codex: `bash scripts/setup-codex.sh`, depois `.venv/bin/python scripts/verify.py`.
- Windows: `powershell -File .\scripts\setup-windows.ps1`, depois `.\.venv\Scripts\python.exe .\scripts\verify.py`.
- UI local: `.\.venv\Scripts\python.exe .\app\desktop_app.py`.
- Build Windows: `app/build_windows.ps1`; veja `app/WINDOWS_BUILD.md`.
- Código, testes e fixtures ficam em `app/`; os testes usam `unittest`.
- Produto: `docs/PRD.md`; componentes: `docs/ARCHITECTURE.md`; estado: `docs/IMPLEMENTATION_STATUS.md`; prioridade: `docs/BACKLOG.md`.

## Invariantes de engenharia

- Diferencie observado, calculado, inferido pelo JEV e estimado por resultados financeiros. Não renomeie `confidence` ou Noul contextual como chance de lucro.
- Preserve aritmética monetária determinística e validação de schemas. JEV não escolhe regras financeiras por texto livre.
- Não amplie cobertura: `full_tape=False` continua parcial; ordem de timestamps não prova continuidade. Dados ausentes, vencidos ou inconsistentes devem ser visíveis.
- Não habilite ordens nem remova bloqueios para fazer uma demonstração parecer operacional. A baseline é um observador/laboratório; execução real exige escopo próprio e autorização correspondente.
- Nenhuma política aumenta lote apenas para recuperar uma perda. Compare `q=0` e quantidades admissíveis quando houver dados e avaliação econômica suficientes.
- Exemplos de R$400, custos, margens e perfis são contexto/fixtures; confirme os dados vigentes antes de uso operacional. O capital da conta ainda é manual.
- Use testes focados para riscos reais. Chaves, endpoints autenticados, feed pago e conta real não são necessários nos testes locais. Não faça chamadas pagas ao JEV durante setup ou CI.
- Não comite credenciais, diários privados, dados de mercado sem autorização de redistribuição, ambientes virtuais ou binários de runtime.
- Nunca desative Defender, validação TLS ou políticas de execução para contornar erro de instalação.

## Conclusão de uma tarefa

Implemente, execute as verificações relevantes e registre evidência com plataforma/escopo. Atualize status e backlog somente para o que foi demonstrado. Um teste Linux não valida a janela Windows; um teste sintético não valida rentabilidade. Se uma dependência externa bloquear uma etapa, conclua a parte independente e documente o bloqueio exato.

Respeite o modelo selecionado por Gabriel e seu orçamento. Preferência registrada: GPT-6.1 Sol; não troque automaticamente para Astra. As credenciais e o modelo do agente de desenvolvimento são separados da chave e do modelo JEV do aplicativo.
