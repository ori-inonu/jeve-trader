# Instalação acessível e aviso de novas versões

Type: task
Status: claimed
Assignee: principal
Blocked by: none

## Question

O usuário consegue abrir a versão instalada pelo ícone e identificar uma versão publicada mais nova, preservando os dados e a privacidade do repositório?

## Spec

Instalar o pacote Windows no computador de Gabriel, com atalho e cópia acessível em Downloads. Preservar identificadores JevWIN e LOCALAPPDATA/JevWIN. Registrar versões e commits no Git existente e enviar a branch ao GitHub autorizado.

Neste primeiro incremento, consultar releases estáveis do repositório existente ao iniciar, em segundo plano, com timeout. Comparar versões numericamente e exigir o asset `JevWIN_<versão>_setup.exe`. Mostrar ícone/aviso, versão instalada/publicada e notas; botão abre a página confiável da release para baixar o instalador. Instalação ocorre pelo instalador, fora do app. Não declarar atualizado em erro de rede/autenticação, nem vazar credencial à UI/logs. Reutilizar credencial Git existente sem prompt; em outro computador sem acesso, informar necessidade de autenticação. Não tornar o repositório público por inferência.

Versionar app/frontend/Tauri/Cargo e empacotar a versão consistente com hashes SHA-256. Testes sem chamadas pagas: disponibilidade de release, numericamente maior, erro/ausência/acesso privado e serviço responsivo durante consulta. Verificar instalador isolado, preservação de dados e janela/processo Windows. A interação visual e o feed real têm evidências separadas.

## Comments

Pacote 0.4.0 instalado nesta sessão, saída 0; atalho verificado e installer copiado a Downloads. Baseline anterior capturada em `13b8ec2`; remoto incorporado em `66d9aee`. Incremento 0.4.1 em implementação. Questão opcional de distribuição privada/separada/pública apresentada ao usuário; preservar privado enquanto não houver resposta.
