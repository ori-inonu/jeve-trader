# Fontes reais e capacidade do Excel

Type: research
Status: resolved
Blocked by: none

## Question

Quais informações Profit/Excel podem fornecer e o que falta para avaliar fluxo e executar um piloto verificável?

## Answer

RTD/DDE oferece cotações e, conforme a exportação, indicadores e janelas relacionadas a negócios/livro. Isso não prova tape completo, continuidade ou IDs estáveis. Quantidade do último negócio e volume agregado não permitem reconstruir todos os negócios nem o agressor. Indicadores exportados têm limitações de periodicidade documentadas pela Nelogica. O Excel tem `RTD.ThrottleInterval` padrão de 2000 ms; ler COM a cada 100 ms pode apenas reler valores antigos. Não alterar esse parâmetro global sem acordo.

ProfitDLL Market Data é uma rota apropriada quando o usuário dispõe de licença/SDK autorizados. Assinatura Profit Pro não comprova acesso à DLL. Inicialização assíncrona não comprova conexão, e callbacks devem alimentar fila própria. Depth agregado e OfferBook têm capacidades distintas; verificar ABI instalada antes de adaptar.

Fontes primárias: [configuração RTD](https://ajuda.nelogica.com.br/hc/pt-br/articles/360044293432-Como-configurar-RTD-DDE-no-Profit), [campos RTD](https://ajuda.nelogica.com.br/hc/pt-br/articles/7834206674075-Significados-e-sintaxe-do-RTD), [Microsoft ThrottleInterval](https://learn.microsoft.com/en-us/office/vba/api/excel.rtd.throttleinterval), [acesso ProfitDLL](https://ajuda.nelogica.com.br/hc/pt-br/articles/51583791325211-Como-obter-acesso-%C3%A0-ProfitDLL), [funções Real Time](https://ajuda.nelogica.com.br/hc/pt-br/articles/11168755650459-Fun%C3%A7%C3%B5es-Real-Time-DLL).

## Comments

Pesquisa primária concluída por agente leitor nesta sessão. Inferências sobre reconstrução de tape e filas são conclusões de engenharia. Nenhuma exportação real nem licença foi validada. Solicitar arquivo/intervalos e contrato em pergunta humana; não criar dados para preencher ausência.
