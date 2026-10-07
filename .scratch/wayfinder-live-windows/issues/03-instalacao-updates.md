# Instalação acessível e aviso de novas versões

Type: task
Status: resolved
Assignee: principal
Blocked by: none

## Question

O usuário consegue abrir a versão instalada pelo ícone e identificar uma versão publicada mais nova, preservando os dados e a privacidade do repositório?

## Spec

Instalar o pacote Windows no computador de Gabriel, com atalho e cópia acessível em Downloads. Preservar identificadores JevWIN e LOCALAPPDATA/JevWIN. Registrar versões e commits no Git existente e enviar a branch ao GitHub autorizado.

Neste primeiro incremento, consultar releases estáveis do repositório existente ao iniciar, em segundo plano, com timeout. Comparar versões numericamente e exigir o asset `JevWIN_<versão>_setup.exe`. Mostrar ícone/aviso, versão instalada/publicada e notas; botão abre a página confiável da release para baixar o instalador. Instalação ocorre pelo instalador, fora do app. Não declarar atualizado em erro de rede/autenticação, nem vazar credencial à UI/logs. Reutilizar credencial Git existente sem prompt; em outro computador sem acesso, informar necessidade de autenticação. Não tornar o repositório público por inferência.

Versionar app/frontend/Tauri/Cargo e empacotar a versão consistente com hashes SHA-256. Testes sem chamadas pagas: disponibilidade de release, numericamente maior, erro/ausência/acesso privado e serviço responsivo durante consulta. Verificar instalador isolado, preservação de dados e janela/processo Windows. A interação visual e o feed real têm evidências separadas.

## Comments

0.4.1 instalada no Windows 11 x64, saída 0. Atalho `C:/Users/gabri/OneDrive/Área de Trabalho/JevWIN.lnk` aponta para o executável instalado. Instalador acessível em `C:/Users/gabri/Downloads/Jeve-Trader-0.4.1-setup.exe`. Atualização preservou os arquivos existentes em LOCALAPPDATA/JevWIN.

Release privada publicada: https://github.com/ori-inonu/jeve-trader/releases/tag/v0.4.1, código `2e55df3bffd7239bbfe63fac4ef99d8cbb6ab651`. Instalador, portable e SHA256SUMS enviados com tamanho/digest conferidos. Não houve mudança de visibilidade do repositório. Baseline anterior capturada em `13b8ec2`; remoto incorporado em `66d9aee`; branch `codex/windows-updates-and-live-roadmap` enviada ao origin.

203 testes Python e diagnóstico desktop passaram; build TypeScript/Vite, PyInstaller, Cargo e NSIS concluídos. Verificação isolada confirmou janela/sidecar, encerramento do sidecar, preservação dos dados em reinstalação/desinstalação e instalação principal intacta. Computer Use confirmou o ícone, o painel e “Instalada: 0.4.1 · Publicada: 0.4.1” na janela principal. Consulta real detectou `available` para 0.4.0 e `current` para 0.4.1. A revisão independente de padrões e a de especificação encontraram a mesma falha P2 de credencial revogada; corrigida e coberta por teste em `2e55df3`.

Evidência detalhada: [Windows release 0.4.1](../../../docs/evidence/windows-release-0.4.1.json). Não são evidências de feed Excel/Profit, rentabilidade, termômetro, alertas ou cadência JEV nova. A instalação de uma atualização continua manual após abrir a release.
