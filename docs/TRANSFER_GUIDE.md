# Continuar o Jeve Trader no Codex

**Projeto preparado em 06/10/2026; publicação confirmada em 07/10/2026 (UTC).** O repositório privado é [ori-inonu/jeve-trader](https://github.com/ori-inonu/jeve-trader), branch `main`, com código, documentação, pesquisa e plano de implementação organizados. O **ambiente Jeve Trader está publicado na conta Codex** e disponível no seletor de ambientes de um novo chat. O status detalhado fica em [TRANSFER_STATUS.json](TRANSFER_STATUS.json).

## Caminho principal: clonar o GitHub

Com Git instalado e acesso ao repositório privado, execute:

```bash
git clone https://github.com/ori-inonu/jeve-trader.git
cd jeve-trader
```

Abra essa pasta no Codex disponível no computador ou no editor. A história remota é a base para novos commits; o aplicativo permanece na baseline JevWIN v0.3.0, sem as melhorias propostas pela pesquisa.

## ZIPs anteriores e distribuição Windows

Os pacotes entregues antes da publicação são **snapshots da preparação anterior**, não a fonte atual de desenvolvimento:

- **Jeve_Trader_Projeto.zip:** código e documentação daquele snapshot, sem a pasta interna `.git`.
- **Jeve_Trader_Entrega_Completa.zip:** o mesmo snapshot, histórico local em bundle e instalador/pacote portátil v0.3.0 já produzidos. Os binários não incorporam a pesquisa nova; sua execução Windows ainda precisa de validação.

O pacote completo conserva os formatos distintos de instalador e distribuição portátil. Os fontes de empacotamento, as licenças e os relatórios estão disponíveis para manutenção; clonar o repositório não instala o aplicativo nem inclui automaticamente os binários dos ZIPs anteriores.

## Abrir no computador

Com Python 3.12 x64 incluindo Tcl/Tk, abra um terminal na pasta `jeve-trader` e execute:

```powershell
powershell -File .\scripts\setup-windows.ps1
.\.venv\Scripts\python.exe .\scripts\verify.py
```

Se a política atual impedir o script, use os comandos individuais documentados em `docs/DEVELOPMENT.md`, sem desativar proteções do Windows.

Abra essa mesma pasta no Codex. As instruções estão em `AGENTS.md`; o ponto de retomada é `docs/HANDOFF.md`. Copie `docs/CODEX_NEXT_TASK.md` para iniciar o primeiro ciclo. A execução de novas tarefas fica para quando você desejar usar sua cota.

## Consultar o histórico local pré-publicação

O arquivo [archive/Jeve_Trader_Historico_2026-10-06.bundle](archive/Jeve_Trader_Historico_2026-10-06.bundle) preserva os commits locais anteriores à publicação. A publicação no GitHub foi preparada com história remota própria. O bundle é um arquivo histórico separado, não uma branch destinada a substituir `main` remoto.

Se precisar consultar essa fase, na raiz do clone atual recupere o bundle em outra pasta ainda inexistente:

```powershell
git clone .\docs\archive\Jeve_Trader_Historico_2026-10-06.bundle ..\jeve-trader-historico
```

Esse clone histórico tem o bundle local como origem. Continue a implementação na pasta clonada do GitHub; não envie a branch do histórico por cima de `main` remoto. Mudanças úteis identificadas no arquivo histórico devem ser portadas como alterações revisáveis sobre a história atual.

## Usar o ambiente Codex publicado

No Codex, abra um novo chat, use o seletor de ambientes e procure **Jeve Trader**. O ambiente foi publicado com `ori-inonu/jeve-trader` e `bash scripts/setup-codex.sh`. A preparação confirmou checkout `main`, Python 3.12.14 e `.venv/bin/python scripts/verify.py` aprovado. Nenhuma chave foi adicionada. A interface não exibiu campo de branch nem URL exclusiva do ambiente; o [chat de configuração](https://chatgpt.com/local/01a113f1-e024-75b3-9113-723a82fd30f9?hostId=local) permite consultar a preparação e seu painel. Veja [CODEX.md](CODEX.md).

O produto iniciou uma tarefa de configuração do ambiente, concluída apenas nesse escopo. Nenhuma tarefa de implementação do backlog foi iniciada. A interface não apresentou um valor de consumo de cota para registrar.

## Prompt curto de retomada

> Continue o projeto Jeve Trader existente. Leia AGENTS.md, docs/HANDOFF.md e docs/CODEX_NEXT_TASK.md. Execute a verificação inicial e implemente os primeiros itens viáveis de docs/BACKLOG.md: preservação da premissa, separação entre apoio/contradição/insuficiência e registro experimental versionado. Entregue código e testes, com atualização do estado e evidência. Preserve a execução de ordens desligada e a distinção entre testes sintéticos e validação financeira. Respeite o modelo selecionado; a preferência registrada é GPT-6.1 Sol.

## O que foi verificado nesta transferência

Preparação de ambiente Linux novo e reutilização desse ambiente; Python 3.12.14, `tzdata==2025.2`, 166 testes e autoteste aprovados; links canônicos e equivalência dos 71 arquivos do aplicativo importado. Windows, integração real com Profit/Excel, chamadas JEV autenticadas e vantagem financeira continuam pendentes. Consulte `docs/evidence/` e `docs/IMPLEMENTATION_STATUS.md` para o alcance exato.
