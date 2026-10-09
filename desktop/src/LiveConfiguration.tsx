import {useState, type FormEvent} from 'react';
import {Radio} from 'lucide-react';
import {type Snapshot} from './transport';

type Run = (method:string, params?:Record<string,unknown>)=>Promise<void>;
function values(e:FormEvent<HTMLFormElement>) {e.preventDefault();return Object.fromEntries(new FormData(e.currentTarget)) as Record<string,string>;}
function Input({label,name,value,required=false,type='text',min,max}:{label:string;name:string;value?:string;required?:boolean;type?:string;min?:number;max?:number}) {
  return <label className="field"><span>{label}</span><input name={name} defaultValue={value} required={required} type={type} min={min} max={max} autoComplete="off"/></label>;
}
export function LiveConfiguration({data,run}:{data:Snapshot;run:Run}) {
  const [workbook,setWorkbook]=useState(data.source.config.workbook||'');
  const [windowHandle,setWindowHandle]=useState('');
  const cfg=data.source.config, s=data.context_settings, b=data.budget;
  const ocr=data.source.ocr, rtd=data.source.rtd, audit=data.source.audit;
  const discovery=data.source.discovery;
  const sheets=discovery.workbooks.find(w=>w.workbook===workbook)?.sheets||[];
  return <>
    <div className="analytics"><section className="panel"><h3>Excel aberto · complemento da captura</h3><p className="muted">Informe o contrato e os intervalos reais. Somente cotação não oferece leitura de agressão, absorção ou exaustão.</p>
      <button className="button secondary" disabled={discovery.status==='checking'} onClick={()=>void run('source.discover')}>Localizar arquivos abertos</button>
      <p className="muted">{discovery.status==='ready'?`${discovery.workbooks.length} arquivo(s) na instância acessível do Excel; nenhuma célula lida.`:discovery.status==='checking'?'Consultando nomes de arquivos e planilhas…':discovery.error||'A descoberta consulta somente nomes. O arquivo precisa estar aberto no Excel.'}</p>
      <form onSubmit={e=>void run('source.excel',values(e))}>
        <Input label="Contrato WIN vigente (ex.: WINV26)" name="symbol" value={cfg.symbol} required/>
        <label className="field"><span>Nome exato do arquivo aberto</span><input name="workbook" value={workbook} onChange={e=>setWorkbook(e.target.value)} list="open-workbooks" required autoComplete="off"/></label>
        <datalist id="open-workbooks">{discovery.workbooks.map(w=><option key={w.workbook} value={w.workbook}/>)}</datalist>
        <datalist id="open-sheets">{sheets.map(sheet=><option key={sheet} value={sheet}/>)}</datalist>
        <div className="form-grid">
          <label className="field"><span>Planilha de cotações</span><input name="quote_sheet" defaultValue={cfg.quote_sheet||cfg.sheet} list="open-sheets" required/></label>
          <Input label="Intervalo de cotação com cabeçalhos" name="quote_range" value={cfg.quote_range||cfg.cell_range} required/>
          <label className="field"><span>Planilha de negócios (opcional)</span><input name="tape_sheet" defaultValue={cfg.tape_sheet} list="open-sheets"/></label>
          <Input label="Intervalo de negócios (opcional)" name="tape_range" value={cfg.tape_range}/>
          <label className="field"><span>Planilha do livro (opcional)</span><input name="book_sheet" defaultValue={cfg.book_sheet} list="open-sheets"/></label>
          <Input label="Intervalo do livro (opcional)" name="book_range" value={cfg.book_range}/>
          <label className="field"><span>Planilha Volume At Price (opcional)</span><input name="vap_sheet" defaultValue={cfg.vap_sheet} list="open-sheets"/></label>
          <Input label="Intervalo Volume At Price (opcional)" name="vap_range" value={cfg.vap_range}/>
          <Input label="Modalidade da janela (individual / agregada)" name="window_mode" value={cfg.window_mode}/>
          <Input label="Filtros ativos na exportação" name="filters" value={cfg.filters}/>
        </div>
        <button className="button"><Radio size={16}/>Salvar perfil e conectar</button><button className="button secondary" type="button" onClick={()=>void run('source.disconnect')}>Desconectar</button>
      </form>
      <p className="muted">Reconexão automática: {data.source.reconnect_enabled?'habilitada para este perfil':'desabilitada'}. {data.source.retry_in_ms!=null?`Nova tentativa em ${Math.ceil(data.source.retry_in_ms/1000)}s.`:''}</p>
      <small>Negócios exigem ID estável, contrato, horário de origem, preço, quantidade e agressor. Corretoras compradora/vendedora são opcionais. Livro exige bid, ask, bidqty e askqty; VAP exige price e quantity. Selecione planilha e intervalo juntos. Esses dados não comprovam tape integral nem profundidade completa.</small>
      <hr/><h3>Auditoria local e frequência RTD</h3>
      <p className="muted">A coleta consulta o Excel a cada 250 ms; isso não força a origem a publicar nesse intervalo. O throttle do RTD é global para a instância do Excel.</p>
      <div className="capture-actions"><button className="button secondary" disabled={!data.source.excel_running||audit.status==='checking'} onClick={()=>void run('source.audit')}>Ler fórmulas selecionadas e throttle</button>
        <button className="button secondary" disabled={!data.source.excel_running||rtd.enabled} onClick={()=>void run('source.rtd',{enabled:true})}>Aplicar RTD 250 ms</button>
        <button className="button secondary" disabled={!data.source.excel_running||!rtd.enabled} onClick={()=>void run('source.rtd',{enabled:false})}>Restaurar RTD anterior</button></div>
      <p className="muted">RTD: {rtd.current_ms==null?'ainda não observado':`${rtd.current_ms} ms`}; anterior: {rtd.previous_ms==null?'desconhecido':`${rtd.previous_ms} ms`}. {rtd.status==='restore_unconfirmed'?'Restauração não confirmada após interrupção. Confira o valor no Excel.':rtd.enabled?'250 ms aplicado nesta sessão; será restaurado ao desconectar, se não houver alteração externa.':''}</p>
      {!!audit.tables.length&&<details className="capture-audit"><summary>Fórmulas e campos fornecidos · somente local</summary><pre>{JSON.stringify(audit.tables,null,2)}</pre><small>{audit.note}</small></details>}
    </section><section className="panel"><h3>JEV · credencial protegida</h3><p className="muted">{data.jev.model} · {data.jev.configured?'chave salva no Gerenciador de Credenciais do Windows':'chave não configurada'} · {data.jev.calls}/{data.jev.limit} chamadas nesta execução</p>
      <button className="button secondary" onClick={()=>void run('jev.set_enabled',{enabled:!data.jev.enabled})}>JEV {data.jev.enabled?'ON · desligar':'OFF · ligar'}</button><p className="muted">Inicia desligado. OFF mantém coleta e cálculos locais. Uma solicitação já recebida pelo servidor pode concluir e consumir API; o retorno não atualiza o painel vigente.</p>
      <form onSubmit={e=>{const v=values(e);void run('jev.configure',{api_key:v.api_key,limit:Number(v.limit)});e.currentTarget.reset();}}>
        <Input label="Nova chave TypeSafe" name="api_key" type="password" required/>
        <Input label="Limite adicional de chamadas por execução" name="limit" value={String(data.jev.limit)} type="number" min={1} max={10000} required/>
        <button className="button">Salvar chave protegida</button><button type="button" className="button secondary" onClick={()=>void run('jev.configure',{api_key:'',limit:data.jev.limit})}>Remover chave</button>
      </form>
      {data.jev_error&&<p role="status" className="notice error">{data.jev_error}</p>}
      <div className="budget-readout"><span>Estimativa liquidada <b>US$ {b.estimated_usd}</b></span><span>Reserva não liquidada <b>US$ {b.reserved_usd}</b></span><span>Comprometido hoje <b>US$ {b.today_usd}</b></span><span>Total comprometido <b>US$ {b.committed_usd}</b></span></div>
      <p className="muted">Faturamento real desconhecido. Tentativas sem uso confirmado: {b.unknown_attempts}. Reservas persistem após reiniciar. O piloto não se renova automaticamente.</p>
      <hr/><h3>ProfitDLL · etapa dependente de licença</h3><p className="muted">Negócios V2 e PriceDepth exigem o SDK autorizado e sua licença. A instalação do Profit Pro não confirma esse acesso. Nenhum driver foi inventado.</p>
      <a href="https://ajuda.nelogica.com.br/hc/pt-br/articles/51583791325211-Como-obter-acesso-%C3%A0-ProfitDLL" target="_blank" rel="noreferrer">Requisitos oficiais da Nelogica</a>
    </section></div>
    <section className="panel"><h3>Profit · OCR local auxiliar</h3><p className="muted">Selecione uma janela Profit visível e a região de Times & Trades ou livro. Coordenadas em pixels a partir do canto superior esquerdo da janela inteira. OCR começa desligado; imagens e texto ficam locais. Não soma volumes ao Excel nem demonstra continuidade.</p>
      <p className="muted">{ocr?.runtime?.available?`Reconhecimento local disponível · Tesseract ${ocr.runtime.version}`:ocr?.runtime?.error||'Verificando disponibilidade do OCR local…'}</p>
      <button className="button secondary" onClick={()=>void run('source.ocr_windows')}>Localizar janelas Profit</button>
      <form onSubmit={e=>{const v=values(e),selected=ocr?.windows.find(w=>String(w.handle)===windowHandle);if(selected)void run('source.ocr',{enabled:true,selection:{handle:selected.handle,title:selected.title,region_kind:v.region_kind,x:Number(v.x),y:Number(v.y),width:Number(v.width),height:Number(v.height)}});}}>
        <label className="field"><span>Janela selecionada</span><select value={windowHandle} onChange={e=>setWindowHandle(e.target.value)} required><option value="">Selecione uma janela</option>{ocr?.windows.map(w=><option key={w.handle} value={w.handle}>{w.title}</option>)}</select></label>
        <label className="field"><span>Tipo da região textual (parcial)</span><select name="region_kind" required><option value="times_trades">Times &amp; Trades individual</option><option value="book">Livro de ofertas</option></select></label>
        <div className="form-grid"><Input label="X (px)" name="x" value="0" type="number" min={0} max={10000} required/><Input label="Y (px)" name="y" value="0" type="number" min={0} max={10000} required/><Input label="Largura (px)" name="width" value="640" type="number" min={32} max={4096} required/><Input label="Altura (px)" name="height" value="480" type="number" min={32} max={4096} required/></div>
        <button className="button" disabled={!windowHandle||!ocr?.runtime?.available}>Ativar região OCR</button><button type="button" className="button secondary" disabled={!ocr?.enabled} onClick={()=>void run('source.ocr',{enabled:false})}>Desligar OCR</button>
      </form><p className="muted">{ocr?.enabled?`OCR ativo · ${ocr.status}`:'OCR desligado'}. Snapshot textual auxiliar; ainda não extrai negócios ou níveis estruturados. Legibilidade não calibrada; perdas de negócios desconhecidas. Janelas minimizadas, rolagem e renderização podem invalidar a leitura.</p>{ocr?.error&&<p role="status" className="notice error">{ocr.error}</p>}
    </section>
    <section className="panel"><h3>Ciclo contextual e alertas experimentais</h3><p className="muted">Avalia mudanças relevantes, com uma chamada em voo. A coleta e a interface continuam atualizando enquanto o JEV responde. Respostas vencidas são descartadas.</p>
      <form key={s.revision} onSubmit={e=>{const v=values(e);void run('context.configure',{automatic:v.automatic==='on',alerts_enabled:v.alerts_enabled==='on',sound_enabled:v.sound_enabled==='on',cadence_ms:Number(v.cadence_ms),validity_ms:Number(v.validity_ms),horizon_seconds:Number(v.horizon_seconds),alert_threshold:Number(v.alert_threshold),alert_rearm:Number(v.alert_rearm),alert_cooldown_ms:Number(v.alert_cooldown_ms),daily_limit_usd:v.daily_limit_usd,total_limit_usd:v.total_limit_usd});}}>
        <div className="live-toggles">{[['automatic','Avaliação automática',s.automatic],['alerts_enabled','Alertas no painel',s.alerts_enabled],['sound_enabled','Som experimental (habilite áudio no painel)',s.sound_enabled]].map(([name,label,checked])=><label key={String(name)} className="toggle"><input type="checkbox" name={String(name)} defaultChecked={Boolean(checked)}/>{String(label)}</label>)}</div>
        <div className="cost-form">
          <Input label="Intervalo mínimo entre chamadas (ms)" name="cadence_ms" value={String(s.cadence_ms)} type="number" min={1000} max={60000} required/>
          <Input label="Validade máxima desde o dado (ms)" name="validity_ms" value={String(s.validity_ms)} type="number" min={500} max={2000} required/>
          <Input label="Horizonte contextual (s)" name="horizon_seconds" value={String(s.horizon_seconds)} type="number" min={5} max={120} required/>
          <Input label="Limiar absoluto do termômetro" name="alert_threshold" value={String(s.alert_threshold)} type="number" min={1} max={100} required/>
          <Input label="Rearmar abaixo de" name="alert_rearm" value={String(s.alert_rearm)} type="number" min={0} max={99} required/>
          <Input label="Intervalo mínimo entre episódios (ms)" name="alert_cooldown_ms" value={String(s.alert_cooldown_ms)} type="number" min={15000} max={300000} required/>
          <Input label="Teto diário do piloto (US$, máximo 1)" name="daily_limit_usd" value={s.daily_limit_usd} required/>
          <Input label="Teto total do piloto (US$, máximo 5)" name="total_limit_usd" value={s.total_limit_usd} required/>
          <button className="button">Salvar parâmetros · revisão {s.revision}</button>
        </div>
      </form><small>Alerta exige cotação atual, geometria válida e dimensões contextuais suficientes. O indicador não autoriza ordens nem aumenta lote após perdas.</small>
    </section>
  </>;
}
