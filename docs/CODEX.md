# Abrir e continuar no Codex

Este repositório contém as instruções e os scripts necessários para retomar o desenvolvimento. A publicação no GitHub e a criação de um ambiente remoto são estados externos separados; confira `TRANSFER_STATUS.json` antes de presumir que foram concluídos.

## Projeto local no computador

Abra a pasta raiz `jeve-trader` no Codex disponível no seu computador ou na extensão do editor. Após clonar o repositório, conserve `AGENTS.md` na raiz. O Codex lê instruções de projeto a partir desses arquivos; a documentação oficial descreve o encadeamento de instruções globais e locais [1].

Use Python 3.12 x64 com Tcl/Tk no Windows. Execute os comandos de `DEVELOPMENT.md` e forneça ao Codex o conteúdo de `CODEX_NEXT_TASK.md` como primeira tarefa. Para usar a aplicação, configure Profit/Excel e a chave TypeSafe localmente quando chegar à etapa correspondente.

## Ambiente Codex Cloud

Na interface da sua conta, selecione o repositório Jeve Trader e a branch de trabalho. Nome sugerido do ambiente: **Jeve Trader**. Se o repositório não aparecer, a conexão GitHub pode precisar incluir especificamente esse repositório. Revise o alcance antes de conceder acesso; não é necessário conceder acesso a todos os seus repositórios.

Configuração preparada:

| Campo | Valor/procedimento |
|---|---|
| Runtime | Python 3.12. |
| Setup | `bash scripts/setup-codex.sh` |
| Verificação | `.venv/bin/python scripts/verify.py` |
| Instruções do projeto | `AGENTS.md` e ponto de retomada em `docs/HANDOFF.md`. |
| Primeira tarefa | `docs/CODEX_NEXT_TASK.md`. |
| Credenciais para testes | Nenhuma. |
| Consultas JEV durante testes | Nenhuma. |

O setup instala dependências em `.venv`. As tarefas devem chamar o Python desse ambiente explicitamente. Não dependem de um `export` executado numa sessão anterior de setup. A documentação de cloud explica a clonagem, os scripts de preparação/manutenção, o cache e a separação da configuração de internet [2].

O acesso de rede necessário para instalar dependências deve ser separado de chamadas autenticadas ao modelo. Não adicione `TYPESAFE_API_KEY` para executar a suíte offline. O workflow GitHub Actions incluso é manual, e nenhuma tarefa de desenvolvimento precisa ser iniciada antes de Gabriel desejar usar sua cota.

Um arquivo local com estes valores **não cria automaticamente um ambiente na conta**. A criação só está concluída quando aparece na interface e há um identificador/URL confirmado no status da transferência.

## O que continua dependente do Windows

Codex/Linux consegue implementar e testar componentes do motor e reproduzir exemplos. A validação de instalação, inicialização gráfica, anexação COM ao Excel, atualização real do Profit e diagnóstico Windows precisa ocorrer no computador/runner correspondente. Testes sem janela não comprovam esses comportamentos.

## Fontes oficiais consultadas em 06/10/2026

[1] OpenAI — [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

[2] OpenAI — [Codex Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environment). A página consultada está marcada como legado; confirme os nomes atuais dos controles na interface da conta.
