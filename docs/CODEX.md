# Abrir e continuar no Codex

Este repositório contém as instruções e os scripts necessários para retomar o desenvolvimento. O repositório privado e o ambiente **Jeve Trader** no Codex foram publicados e verificados. O estado detalhado está em `TRANSFER_STATUS.json`.

## Ambiente publicado — acesso confirmado

No Codex, abra um novo chat, abra o seletor de ambientes e procure **Jeve Trader**. O ambiente aparece entre os publicados e foi selecionado com o campo de tarefa vazio. Use `docs/CODEX_NEXT_TASK.md` quando desejar iniciar a implementação.

O registro privado da preparação (identidade omitida) registra a preparação e permite abrir o painel do ambiente. A interface consultada não forneceu URL canônica exclusiva do ambiente nem campo para configurar a branch; a tarefa de preparação confirmou checkout/origin `main`.

A configuração publicada contém o nome **Jeve Trader**, repositório `ori-inonu/jeve-trader`, acesso **Somente eu**, instalação `bash scripts/setup-codex.sh` e instruções de inicialização com Python 3.12 e `.venv/bin/python scripts/verify.py`. O acesso à internet permaneceu no perfil **Gerenciadores de pacotes**, sem domínios extras, variáveis ou segredos adicionados.

O onboarding executou somente a preparação autorizada, usando **GPT-6.1 Sol Leve**. O resultado mostrado no Codex registrou Python 3.12.14, setup executado e repetido com sucesso, 166 testes e autoteste aprovados, 71 arquivos de `app/` idênticos e Git limpo. A implementação do backlog não foi iniciada. O consumo de cota dessa tarefa de preparação não foi informado na interface.

As capturas e o registro do alcance estão em [evidence/codex-publication-2026-10-07.json](evidence/codex-publication-2026-10-07.json). A validação continua restrita ao ambiente Linux; Windows e integrações reais mantêm os critérios próprios do backlog.

## Projeto local no computador

Abra a pasta raiz `jeve-trader` no Codex disponível no seu computador ou na extensão do editor. Após clonar o repositório, conserve `AGENTS.md` na raiz. O Codex lê instruções de projeto a partir desses arquivos; a documentação oficial descreve o encadeamento de instruções globais e locais [1].

Use Python 3.12 x64 com Tcl/Tk no Windows. Execute os comandos de `DEVELOPMENT.md` e forneça ao Codex o conteúdo de `CODEX_NEXT_TASK.md` como primeira tarefa. Para usar a aplicação, configure Profit/Excel e a chave TypeSafe localmente quando chegar à etapa correspondente.

## Ambiente Codex Cloud

Para recriar o ambiente futuramente, selecione o repositório `ori-inonu/jeve-trader` e a branch de trabalho quando esse campo estiver disponível. Nome usado: **Jeve Trader**. Se o repositório não aparecer, a conexão GitHub pode precisar incluir especificamente esse repositório. Revise o alcance antes de conceder acesso; não é necessário conceder acesso a todos os seus repositórios.

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

Um arquivo local com estes valores **não cria automaticamente um ambiente na conta**. Nesta transferência, a criação foi confirmada pelo estado **Publicado** no painel e pela presença de **Jeve Trader** no seletor de ambientes de um novo chat. O chat de configuração e as evidências foram registrados no status da transferência.

## O que continua dependente do Windows

Codex/Linux consegue implementar e testar componentes do motor e reproduzir exemplos. A validação de instalação, inicialização gráfica, anexação COM ao Excel, atualização real do Profit e diagnóstico Windows precisa ocorrer no computador/runner correspondente. Testes sem janela não comprovam esses comportamentos.

## Fontes oficiais consultadas em 06/10/2026

[1] OpenAI — [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

[2] OpenAI — [Codex Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environment). A página consultada está marcada como legado; confirme os nomes atuais dos controles na interface da conta.
