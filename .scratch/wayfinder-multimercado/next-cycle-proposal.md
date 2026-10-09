# Proposta de ciclo: evidência e fronteira multimercado

Origem: solicitação humana de 09/10/2026 para revisar o PR e prosseguir o plano de especificações, usando Wayfinder e JEV. O ciclo finito anterior permanece concluído; seus aceites I-01–I-12 não mudam.

O próximo ciclo corrige os dois defeitos reproduzidos pela revisão independente contra main, preservando os contratos existentes: FW-01 (OFF antes do despacho não inicia chamada JEV) e I-02/I-11 (deduplicação idempotente com memória limitada e recuperação conservadora por epoch). A correção terá SPEC própria, regressões offline red/green, verificação e nova revisão independente. Não amplia os aceites antigos nem declara pronta a execução financeira.

Em seguida investiga RT-12 e transforma a evidência em uma especificação verificável para a próxima melhoria elegível do mesmo copiloto multimercado. Compara a jornada Windows, a qualificação documental de B3 independente do Profit e a importação somente leitura de conta, usando fontes primárias, capacidades locais observadas e consultas JEV sanitizadas. Inclui revisão de escopo independente e registro de dependências; não pressupõe melhoria medida nem funcionamento nativo.

Não inclui merge, publicação de release, instalação, ordens, contratação de dados, acesso privado, envio de segredos, migração destrutiva ou alteração do objetivo. Ausência de comparador ou capacidade permanece explícita. A revisão do PR contra `main` é evidência adicional de prontidão, com baseline fixo `0171aed6c4a25adf26d349bfe2c3140805a35e97` e candidato `5f15ab73f4f5adfd3221b9bd5f785c24c9afc496`.

Saídas: correções revisadas no PR próprio; evidência da revisão contra main; pesquisa RT-12 com citações; mapa e tickets de decisões atualizados; recibos JEV; SPEC da próxima entrega com aceites, tarefas, limites e verificação independente. Uma SPEC pronta não certifica build, instalação, execução nativa ou ganhos. Tarefas posteriores só avançam quando seus contratos e dependências permitirem.
