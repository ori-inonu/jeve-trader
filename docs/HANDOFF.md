# Retomada — Jeve Trader

Data de consolidação: 06/10/2026, America/Sao_Paulo.

## Goal & Scope

Gabriel quer continuar este projeto no Codex e GitHub. O produto acompanha o mini índice WIN no Profit Pro/Windows, interpreta fluxo com JEV e pesquisa decisões e dimensionamento condicionados ao capital. O objetivo econômico exige avaliação fora da amostra após custos e limites explícitos; crescimento garantido não foi estabelecido.

## Current State

- Repositório privado confirmado: [ori-inonu/jeve-trader](https://github.com/ori-inonu/jeve-trader), branch `main`. A publicação tem história remota própria; o ambiente remoto no Codex ainda não foi confirmado como criado. Estado detalhado em `docs/TRANSFER_STATUS.json`.
- `app/` conserva a baseline JevWIN v0.3.0. A transferência organiza código/documentos e ferramentas de desenvolvimento; não aplica as melhorias da pesquisa.
- Interface Tk, COM Excel quote/tape/combined, importação CSV, fluxo, geometria, risco, diário e cliente JEV existem. Conta manual, cobertura parcial, nenhuma ordem.
- Empacotamento NSIS existe. Instalação/UI/Profit reais no Windows permanecem sem verificação. A causa da falha anterior do EXE não foi determinada.
- Os testes históricos de software são descritos em `app/VALIDATION.md`; a evidência da organização deste repositório fica em `docs/evidence/`.
- Pesquisa em `docs/research/Pesquisa_Decisao_JEV_WIN_2026-10-06.md`; plano E01–E10 em `docs/research/Plano_Experimentos_JEV.json`. Experimentos empíricos não executados.

## Decisions & Invariants

Mantenha separados contexto JEV, desfecho financeiro e risco. Preserve `full_tape=False`, validação temporal e execução desligada. Não transforme apoio/confiança em probabilidade de ganho nem perda passada em motivação para aumentar lote. Use `AGENTS.md` e `docs/decisions/README.md`.

Nome público: Jeve Trader. Nomes internos JevWIN permanecem para preservar compatibilidade. Não reformate/refatore toda a baseline antes de resolver os problemas de decisão identificados.

O histórico local pré-publicação está arquivado em `docs/archive/Jeve_Trader_Historico_2026-10-06.bundle`. Os ZIPs anteriores são snapshots dessa preparação. O clone GitHub é a base de continuidade; o bundle é histórico separado, sem instrução de empurrar sua branch sobre `main` remoto.

## Active Blockers

Continuam pendentes a criação/configuração confirmada do ambiente Codex e, para validação externa, instalação Windows, contrato real de exportação do Profit, acesso/licença de dados e conta, amostra de mercado reconciliável e chamadas JEV autorizadas com orçamento. Nenhum desses bloqueios impede a correção do payload e a instrumentação local sobre um clone do repositório.

## Suggested Skills

Use skills disponíveis no novo ambiente, sem presumir os caminhos desta sessão: implementação para executar o backlog; diagnóstico de bugs quando houver erro concreto; pesquisa para documentação primária; revisão de código para mudanças materiais. A skill oficial TypeSafe está referenciada no relatório de pesquisa e deve ser consultada ao alterar a integração. Não instale automaticamente um plugin ou substitua o modelo selecionado por Gabriel.

## Exact Next Action

Obtenha a base atual pelo repositório privado:

```bash
git clone https://github.com/ori-inonu/jeve-trader.git
cd jeve-trader
```

Na raiz, execute a preparação adequada ao sistema e `scripts/verify.py`. Depois use o texto de `docs/CODEX_NEXT_TASK.md`. Comece pelo problema da premissa em `app/desktop_app.py` e pela semântica das perguntas, conforme os IDs do backlog. Não reinicie a fase de definição do produto.

Para contexto adicional, consulte apenas a seção necessária de `PRD.md`, `ARCHITECTURE.md`, `IMPLEMENTATION_STATUS.md` e `BACKLOG.md`. Ao terminar, registre arquivos alterados, verificações, limitações e próximo item desbloqueado.
