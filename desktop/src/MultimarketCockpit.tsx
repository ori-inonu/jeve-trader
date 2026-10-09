import { useEffect, useMemo, useState, type FormEvent } from 'react';
import {
  Activity, ArrowDownUp, BookOpen, CheckCircle2, ChevronDown, CircleDollarSign,
  Database, FileText, Gauge, LockKeyhole, Radio, RefreshCw, Shield, Wallet, WifiOff,
} from 'lucide-react';
import {
  createMultimarketProjector,
  type MultimarketRun,
  type MultimarketSnapshot,
  type MultimarketWorkspace,
  type UnknownRecord,
} from './multimarketModel';
import './multimarket.css';

const PUBLIC_SOURCE = 'binance_public_spot';
const PILOT_SYMBOL = 'BTCUSDT';
const DECIMAL_TEXT = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;

function text(value: unknown, fallback = '—'): string {
  return typeof value === 'string' && value.trim() ? value : fallback;
}

function decimal(value: unknown, fallback = '—'): string {
  return typeof value === 'string' && DECIMAL_TEXT.test(value) ? value : fallback;
}

function ageLabel(value: unknown): string {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) return 'idade desconhecida';
  if (value < 1_000) return `${Math.floor(value)} ms`;
  return `${(value / 1_000).toFixed(1)} s`;
}

function statusLabel(value: unknown): string {
  const labels: Record<string, string> = {
    connecting: 'conectando', live: 'ao vivo', retrying: 'reconectando', error: 'erro',
    stale: 'desatualizado', unavailable: 'indisponível', disabled: 'desabilitado',
    blocked: 'bloqueado', healthy: 'saudável', gap: 'lacuna', invalid: 'inválido',
    disconnected: 'desconectado', replay: 'replay', pending: 'pendente', unknown: 'desconhecido',
  };
  return labels[String(value)] ?? text(value, 'desconhecido');
}

function statusTone(value: unknown): 'live' | 'warn' | 'bad' | 'quiet' {
  if (['live', 'healthy', 'reconciled', 'allowed'].includes(String(value))) return 'live';
  if (['retrying', 'connecting', 'stale', 'pending'].includes(String(value))) return 'warn';
  if (['error', 'gap', 'invalid', 'blocked', 'denied'].includes(String(value))) return 'bad';
  return 'quiet';
}

function record(value: unknown): UnknownRecord | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value) ? value as UnknownRecord : null;
}

function shortTime(value: unknown): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
  try { return new Date(value).toLocaleString('pt-BR'); } catch { return '—'; }
}

function parseObject(value: string, label: string): UnknownRecord {
  let parsed: unknown;
  try { parsed = JSON.parse(value); } catch { throw new Error(`${label}: JSON inválido.`); }
  const object = record(parsed);
  if (!object) throw new Error(`${label}: informe um objeto JSON.`);
  return object;
}

function workspaceLabel(workspace: MultimarketWorkspace): string {
  return `${workspace.symbol} · ${workspace.venue} · ${workspace.segment}`;
}

function HealthCard({ label, domain }: { label: string; domain: unknown }) {
  const value = record(domain);
  const status = value?.status;
  return <div className="mm-health-row">
    <span className={`mm-health-icon mm-tone-${statusTone(status)}`}><Activity size={15} aria-hidden="true"/></span>
    <div className="mm-health-copy"><strong>{label}</strong><small>{text(value?.reason, 'Sem observações adicionais.')}</small></div>
    <div className="mm-health-state"><b className={`mm-tone-text-${statusTone(status)}`}>{statusLabel(status)}</b><small>{ageLabel(value?.age_ms)}</small></div>
  </div>;
}

function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return <div className="mm-stat"><span>{label}</span><strong>{value}</strong>{note && <small>{note}</small>}</div>;
}

function Gate({ label, state, detail }: { label: string; state: unknown; detail: string }) {
  const tone = statusTone(state);
  return <div className="mm-gate-row"><span className={`mm-gate-dot mm-tone-${tone}`} aria-hidden="true"/><div><strong>{label}</strong><small>{detail}</small></div><b className={`mm-tone-text-${tone}`}>{statusLabel(state)}</b></div>;
}

export interface MultimarketCockpitProps {
  snapshot: MultimarketSnapshot;
  run: MultimarketRun;
}

export function MultimarketCockpit({ snapshot, run }: MultimarketCockpitProps) {
  const projector = useMemo(() => createMultimarketProjector(), []);
  const [localSnapshot, setLocalSnapshot] = useState<MultimarketSnapshot>(snapshot);
  const [clockMs, setClockMs] = useState(() => typeof performance === 'undefined' ? 0 : performance.now());
  const [pending, setPending] = useState<string | null>(null);
  const [commandError, setCommandError] = useState<string | null>(null);
  const [commandNotice, setCommandNotice] = useState<string | null>(null);
  const [accountId, setAccountId] = useState('');
  const [accountRevision, setAccountRevision] = useState('');
  const [balancesJson, setBalancesJson] = useState('');
  const [positionsJson, setPositionsJson] = useState('');
  const [costCurrency, setCostCurrency] = useState('');
  const [feeRate, setFeeRate] = useState('');
  const [slippage, setSlippage] = useState('');
  const [costsConfirmed, setCostsConfirmed] = useState(false);

  useEffect(() => setLocalSnapshot(snapshot), [snapshot]);
  useEffect(() => {
    const timer = window.setInterval(() => setClockMs(performance.now()), 250);
    return () => window.clearInterval(timer);
  }, []);

  const projection = projector.project(localSnapshot, clockMs);
  const selected = projection.selected;
  const instrument = record(selected?.instrument);
  const source = record(selected?.source);
  const market = record(selected?.market);
  const quote = record(market?.quote);
  const health = record(market?.health);
  const features = record(market?.features);
  const account = record(selected?.account);
  const costs = record(selected?.costs);
  const scheduler = projection.scheduler;
  const workspaces = projection.workspaces;
  const selectedWorkspace = workspaces.find(item => item.workspace_id === selected?.workspace_id) ?? null;
  const connectionState = selected?.status ?? selectedWorkspace?.status ?? 'disconnected';
  const currency = text(instrument?.quote_currency, text(costs?.currency, 'moeda da cotação não informada'));
  const tradeRows = Array.isArray(market?.recent_trades) ? market.recent_trades.slice(-8).reverse().map(record) : [];
  const warnings = Array.isArray(market?.warnings) ? market.warnings.filter((item): item is string => typeof item === 'string') : [];
  const selectedId = typeof selected?.workspace_id === 'string' ? selected.workspace_id : undefined;

  async function execute(method: string, params: UnknownRecord): Promise<MultimarketSnapshot | null> {
    if (pending) return null;
    setPending(method);
    setCommandError(null);
    setCommandNotice(null);
    try {
      const next = await run(method, params);
      setLocalSnapshot(next);
      setCommandNotice(`Comando enviado: ${method}`);
      return next;
    } catch (error) {
      setCommandError(error instanceof Error ? error.message : `Não foi possível executar ${method}.`);
      return null;
    } finally {
      setPending(null);
    }
  }

  async function connectPublicSpot() {
    const params = { symbol: PILOT_SYMBOL, source_id: PUBLIC_SOURCE };
    const discovered = await execute('multimarket.discover', params);
    if (discovered) await execute('multimarket.connect', params);
  }

  async function disconnectSelected() {
    if (selectedId) await execute('multimarket.disconnect', { workspace_id: selectedId });
  }

  async function selectWorkspace(workspaceId: string) {
    if (workspaceId && workspaceId !== selectedId) await execute('multimarket.select', { workspace_id: workspaceId });
  }

  async function reconcileAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId) return;
    try {
      const revision = Number(accountRevision);
      if (!accountId.trim() || !Number.isSafeInteger(revision) || revision < 1) throw new Error('Informe o identificador da conta e uma revisão inteira positiva.');
      const balances = parseObject(balancesJson, 'Saldos');
      const positions = positionsJson.trim() ? parseObject(positionsJson, 'Posições') : {};
      await execute('account.reconcile', {
        workspace_id: selectedId,
        account: { account_id: accountId.trim(), revision, mode: 'manual', status: 'reconciled', asof_ms: Date.now(), balances, positions },
      });
    } catch (error) {
      setCommandError(error instanceof Error ? error.message : 'Não foi possível validar a reconciliação.');
    }
  }

  async function updateCosts(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId) return;
    if (!costsConfirmed) { setCommandError('Confirme que os custos foram informados e estão atualizados.'); return; }
    if (!costCurrency.trim() || !DECIMAL_TEXT.test(feeRate) || !DECIMAL_TEXT.test(slippage)) {
      setCommandError('Informe moeda, taxa e slippage como valores decimais explícitos.');
      return;
    }
    await execute('costs.update', {
      workspace_id: selectedId,
      costs: { currency: costCurrency.trim().toUpperCase(), verified: true, fee_rate: feeRate, slippage },
    });
  }

  async function setJevEnabled(enabled: boolean) {
    await execute('jev.set_enabled', { enabled });
  }

  async function setRecording(enabled: boolean) {
    await execute('recording.set', { enabled });
  }

  async function replayWorkspace() {
    if (selectedId) await execute('replay', { namespace: selectedId });
  }

  async function refreshMetrics() {
    if (selectedId) await execute('metrics', { workspace_id: selectedId });
  }

  const healthComplete = !!health && !!health.quote && !!health.trades && !!health.book;
  const fullTape = source?.full_tape === true && market?.full_tape === true;
  const schedulerEnabled = scheduler?.enabled === true;
  const accountStatus = account ? text(account.status) : 'not_configured';
  const recordingEnabled = text(projection.recording?.status) === 'enabled' || text(projection.recording?.status) === 'recording';

  return <div className="mm-shell">
    <aside className="mm-sidebar" aria-label="Navegação do Jeve Trader">
      <a className="mm-brand" href="#multimarket" aria-label="Jeve Trader — multimercado">
        <span className="mm-brand-mark" aria-hidden="true"><ArrowDownUp size={18}/></span>
        <span><b>JEVE</b><small>MARKETS</small></span>
      </a>
      <div className="mm-nav-caption">AMBIENTE</div>
      <nav className="mm-nav">
        <a className="selected" href="#multimarket" aria-current="page"><Gauge size={16} aria-hidden="true"/>Cockpit</a>
        <a href="#legacy"><FileText size={16} aria-hidden="true"/>Excel · OCR · JevWIN</a>
      </nav>
      <div className="mm-side-section">
        <span className="mm-nav-caption">WORKSPACE ATIVO</span>
        {selectedWorkspace ? <div className="mm-workspace-chip"><span className="mm-live-dot"/><b>{workspaceLabel(selectedWorkspace)}</b><small>{selectedWorkspace.workspace_id}</small></div> : <div className="mm-workspace-empty"><WifiOff size={15} aria-hidden="true"/><span>Nenhum workspace conectado</span></div>}
      </div>
      <div className="mm-side-foot"><Shield size={15} aria-hidden="true"/><span>Observador local<br/><b>ordens desabilitadas</b></span></div>
    </aside>

    <main className="mm-main" id="multimarket">
      <header className="mm-topbar">
        <div className="mm-breadcrumb"><span>JEVE TRADER</span><b>/</b><strong>Multimercado</strong></div>
        <div className="mm-top-status"><span className={`mm-status-pill mm-tone-${statusTone(connectionState)}`}><i aria-hidden="true"/>{statusLabel(connectionState)}</span><span className="mm-environment-label">PILOTO PÚBLICO · SPOT</span></div>
      </header>

      <div className="mm-content">
        <section className="mm-page-head">
          <div><span className="mm-eyebrow"><Radio size={13} aria-hidden="true"/>COCKPIT MULTIMERCADO</span><h1>Mercado com contexto e limites claros.</h1><p>Leitura pública de BTCUSDT. Sem ordens, sem conta conectada e sem probabilidade financeira não aprovada.</p></div>
          <div className="mm-head-actions">
            {workspaces.length > 0 && <label className="mm-select-wrap"><span>WORKSPACE</span><select aria-label="Selecionar workspace" value={selectedId ?? ''} onChange={event => void selectWorkspace(event.target.value)} disabled={!!pending}>
              {!selectedId && <option value="">Selecionar workspace</option>}
              {workspaces.map(item => <option key={item.workspace_id} value={item.workspace_id}>{workspaceLabel(item)} · {item.source_id}</option>)}
            </select><ChevronDown size={14} aria-hidden="true"/></label>}
            <button className="mm-button mm-button-primary" onClick={() => void connectPublicSpot()} disabled={!!pending}>
              <Radio size={15} aria-hidden="true"/>{pending === 'multimarket.discover' || pending === 'multimarket.connect' ? 'Conectando…' : 'Conectar BTCUSDT'}
            </button>
          </div>
        </section>

        {projection.diagnostic && <div className="mm-banner mm-banner-error" role="alert"><Shield size={17} aria-hidden="true"/><div><b>Diagnóstico de compatibilidade</b><p>{projection.diagnostic} O contexto foi removido da projeção.</p></div></div>}
        {commandError && <div className="mm-banner mm-banner-error" role="alert"><Shield size={17} aria-hidden="true"/><div><b>Ação não concluída</b><p>{commandError}</p></div></div>}
        {commandNotice && !commandError && <div className="mm-banner mm-banner-notice" role="status"><CheckCircle2 size={16} aria-hidden="true"/><span>{commandNotice}</span><button onClick={() => setCommandNotice(null)} aria-label="Fechar aviso">×</button></div>}

        <section className="mm-market-bar" aria-label="Fonte de mercado e seleção">
          <div className="mm-market-identity"><span className="mm-coin-mark" aria-hidden="true">₿</span><div><strong>{text(instrument?.symbol, PILOT_SYMBOL)}<span>/ {currency}</span></strong><small>{text(instrument?.venue, 'BINANCE')} · {text(instrument?.segment, 'SPOT')} · fonte pública</small></div></div>
          <div className="mm-market-meta"><span><small>METADATA</small><b className={instrument?.constraints_verified === true ? 'mm-text-live' : 'mm-text-warn'}>{instrument?.constraints_verified === true ? 'Verificada' : 'Aguardando descoberta'}</b></span><span><small>FONTE</small><b>{text(source?.source_id, PUBLIC_SOURCE)}</b></span><span><small>WORKSPACE</small><b>{text(selectedId, 'Ainda não conectado')}</b></span></div>
          {selectedId && <button className="mm-icon-button" onClick={() => void disconnectSelected()} disabled={!!pending} aria-label="Desconectar workspace" title="Desconectar"><WifiOff size={16} aria-hidden="true"/></button>}
        </section>

        {selected?.market && !projection.diagnostic ? <>
          {typeof market?.application_mode === 'string' && market.application_mode === 'replay' && <div className="mm-replay-banner"><RefreshCw size={15} aria-hidden="true"/><b>REPLAY IDENTIFICADO</b><span>Esta visão histórica não representa um feed ao vivo.</span></div>}
          <section className="mm-grid-top">
            <article className="mm-card mm-decision-card">
              <div className="mm-card-head"><div><span className="mm-eyebrow">DECISÃO DO SISTEMA</span><h2>AGUARDAR</h2></div><span className="mm-wait-mark"><Activity size={20} aria-hidden="true"/></span></div>
              <p className="mm-decision-reason">{text(selected.decision.reason, 'Sem avaliação compatível; aguardar nova evidência.')}</p>
              <div className="mm-decision-tags"><span><LockKeyhole size={12} aria-hidden="true"/>Ordens desabilitadas</span><span>Probabilidade de lucro: não estimada</span></div>
              <div className="mm-decision-bottom"><span>QUANTIDADE</span><b>0</b><span className="mm-decision-hint">Nenhum modelo financeiro aprovado para esta metadata.</span></div>
            </article>

            <article className="mm-card mm-quote-card">
              <div className="mm-card-head"><div><span className="mm-eyebrow">MELHOR OFERTA · L1</span><h3>Bid / Ask</h3></div><span className="mm-partial-tag">L1 PÚBLICO</span></div>
              {quote ? <>
                <div className="mm-quote-values"><div><small>BID · COMPRA</small><strong>{decimal(quote.bid)}</strong><span>{currency}</span></div><div><small>ASK · VENDA</small><strong>{decimal(quote.ask)}</strong><span>{currency}</span></div></div>
                <div className="mm-spread-line"><span>Spread</span><b>{decimal(features?.spread)} {currency}</b><span className="mm-age">cotação {ageLabel(quote.age_ms)}</span></div>
              </> : <div className="mm-empty-data"><WifiOff size={18} aria-hidden="true"/><span>Aguardando uma cotação válida.</span></div>}
              <small className="mm-card-foot">Book L2 indisponível nesta fonte. Identificadores não certificam continuidade.</small>
            </article>
          </section>

          {warnings.length > 0 && <div className="mm-warnings" role="status">{warnings.slice(0, 4).map((warning, index) => <p key={`${index}-${warning}`}>{warning}</p>)}</div>}

          <section className="mm-grid-data">
            <article className="mm-card">
              <div className="mm-card-head"><div><span className="mm-eyebrow">ATIVIDADE OBSERVADA</span><h3>Negócios individuais</h3></div><ArrowDownUp size={16} aria-hidden="true"/></div>
              <div className="mm-trade-stats"><Stat label="NEGÓCIOS" value={String(features?.trade_count ?? 0)} note="janela recente"/><Stat label="COMPRA AGRESSORA" value={decimal(features?.buy_quantity)} note="quantidade observada"/><Stat label="VENDA AGRESSORA" value={decimal(features?.sell_quantity)} note="quantidade observada"/><Stat label="DELTA" value={decimal(features?.delta_quantity)} note={`em ${text(instrument?.base_asset, 'ativo base')}`}/></div>
              <div className="mm-coverage"><span className="mm-coverage-icon"><Activity size={14} aria-hidden="true"/></span><div><b>Cobertura parcial</b><small>Fluxo de trades individuais. A fonte não certifica tape completo nem sequência contínua.</small></div><span className="mm-partial-tag">{fullTape ? 'COMPLETO' : 'PARCIAL'}</span></div>
              <div className="mm-trade-list" aria-label="Últimos negócios recebidos">
                {tradeRows.length ? tradeRows.map((trade, index) => {
                  const side = text(trade?.aggressor, 'unknown');
                  return <div className="mm-trade-row" key={String(trade?.event_id ?? trade?.id ?? index)}><span className={side === 'buy' ? 'mm-text-live' : side === 'sell' ? 'mm-text-bad' : ''}>{statusLabel(side)}</span><b>{decimal(trade?.price)}</b><span>{decimal(trade?.quantity)}</span><small>{ageLabel(trade?.age_ms)}</small></div>;
                }) : <small className="mm-no-trades">Nenhum negócio recente no snapshot.</small>}
              </div>
            </article>

            <article className="mm-card">
              <div className="mm-card-head"><div><span className="mm-eyebrow">SAÚDE POR DOMÍNIO</span><h3>Estado das evidências</h3></div><span className="mm-health-legend">Idade pela recepção local</span></div>
              {healthComplete ? <div className="mm-health-list"><HealthCard label="Cotação L1" domain={health?.quote}/><HealthCard label="Trades" domain={health?.trades}/><HealthCard label="Book" domain={health?.book}/></div> : <div className="mm-empty-data">Saúde por domínio indisponível.</div>}
              <div className="mm-source-notes"><span><b>Venue</b>{text(instrument?.venue)}</span><span><b>Segmento</b>{text(instrument?.segment)}</span><span><b>Metadata</b>{text(instrument?.metadata_version)}</span><span><b>Epoch</b>{String(market?.epoch ?? '—')}</span></div>
            </article>
          </section>

          <section className="mm-grid-accounts">
            <article className="mm-card mm-account-card">
              <div className="mm-card-head"><div><span className="mm-eyebrow">LEDGER LOCAL</span><h3>Conta e reconciliação</h3></div><Wallet size={17} aria-hidden="true"/></div>
              {!account ? <div className="mm-unknown"><span className="mm-unknown-mark"><Wallet size={16} aria-hidden="true"/></span><div><b>Sem conta conectada</b><p>Informe um snapshot manual para reconciliar o ledger deste workspace. A UI não solicita credencial nem escopo de negociação.</p></div></div> : <>
                <div className="mm-account-meta"><span><small>STATUS</small><b className={`mm-tone-text-${statusTone(accountStatus)}`}>{statusLabel(accountStatus)}</b></span><span><small>CONTA</small><b>{text(account.account_id)}</b></span><span><small>REVISÃO</small><b>{String(account.revision ?? '—')}</b></span><span><small>REFERÊNCIA</small><b>{shortTime(account.asof_ms)}</b></span></div>
                {typeof account.age_ms === 'number' && <p className="mm-age-note">Recebido há {ageLabel(account.age_ms)}. Conta e cotação têm frescor independente.</p>}
                {record(account.balances) && <div className="mm-balance-list"><span>Saldos por moeda</span>{Object.entries(account.balances as UnknownRecord).map(([asset, amount]) => <b key={asset}>{asset} <i>{decimal(amount)}</i></b>)}</div>}
                {record(account.positions) && <small className="mm-positions-count">Posições por instrumento: {Object.keys(account.positions as UnknownRecord).length}</small>}
              </>}
              <details className="mm-details"><summary><span>Reconciliação manual</span><ChevronDown size={14} aria-hidden="true"/></summary>
                <form className="mm-form" onSubmit={event => void reconcileAccount(event)}>
                  <div className="mm-form-grid"><label>ID da conta<input value={accountId} onChange={event => setAccountId(event.target.value)} autoComplete="off" required placeholder="Identificador local"/></label><label>Revisão<input type="number" min="1" step="1" value={accountRevision} onChange={event => setAccountRevision(event.target.value)} required placeholder="Revisão recebida"/></label></div>
                  <label>Saldos por moeda · objeto JSON<textarea value={balancesJson} onChange={event => setBalancesJson(event.target.value)} required rows={3} spellCheck={false} placeholder='Informe saldos decimais por moeda'/></label>
                  <label>Posições por instrumento · objeto JSON<textarea value={positionsJson} onChange={event => setPositionsJson(event.target.value)} rows={3} spellCheck={false} placeholder='Opcional: posições explícitas por instrument_id'/></label>
                  <button className="mm-button mm-button-subtle" type="submit" disabled={!!pending || !selectedId}>Reconciliar snapshot manual</button>
                  <small>A revisão, saldos e posições são enviados somente ao comando local escopado neste workspace.</small>
                </form>
              </details>
            </article>

            <article className="mm-card mm-cost-card">
              <div className="mm-card-head"><div><span className="mm-eyebrow">CUSTOS EXPLÍCITOS</span><h3>Taxa e slippage</h3></div><CircleDollarSign size={17} aria-hidden="true"/></div>
              {costs ? <div className="mm-cost-summary"><span className={`mm-status-pill mm-tone-${statusTone(costs.verified ? 'healthy' : 'unknown')}`}><i aria-hidden="true"/>{costs.verified ? 'informado e verificado' : 'não verificado'}</span><div><b>{text(costs.currency, 'Moeda não informada')}</b><span>taxa {decimal(costs.fee_rate, 'não informada')} · slippage {decimal(costs.slippage, 'não informado')}</span></div></div> : <div className="mm-unknown mm-unknown-cost"><span className="mm-unknown-mark"><CircleDollarSign size={16} aria-hidden="true"/></span><div><b>Custos não informados</b><p>Valores ausentes permanecem desconhecidos; não são tratados como zero.</p></div></div>}
              <form className="mm-form mm-cost-form" onSubmit={event => void updateCosts(event)}>
                <div className="mm-form-grid"><label>Moeda<input value={costCurrency} onChange={event => setCostCurrency(event.target.value)} autoComplete="off" placeholder="Código da moeda" required/></label><label>Taxa<input inputMode="decimal" value={feeRate} onChange={event => setFeeRate(event.target.value)} placeholder="Decimal explícito" required/></label></div>
                <label>Slippage<input inputMode="decimal" value={slippage} onChange={event => setSlippage(event.target.value)} placeholder="Decimal explícito" required/></label>
                <label className="mm-check"><input type="checkbox" checked={costsConfirmed} onChange={event => setCostsConfirmed(event.target.checked)}/><span>Confirmo que estes custos estão atualizados.</span></label>
                <button className="mm-button mm-button-subtle" type="submit" disabled={!!pending || !selectedId}>Salvar custos do workspace</button>
              </form>
              <div className="mm-cost-block"><LockKeyhole size={14} aria-hidden="true"/><span>Sem conta conciliada, metadata válida e custos verificados, a saída permanece AGUARDAR.</span></div>
            </article>
          </section>

          <section className="mm-context-row">
            <article className="mm-card mm-context-card">
              <div className="mm-card-head"><div><span className="mm-eyebrow">CAMADA CONTEXTUAL</span><h3>JEV contextual</h3></div><span className={`mm-status-pill mm-tone-${schedulerEnabled ? 'live' : 'quiet'}`}><i aria-hidden="true"/>{schedulerEnabled ? 'habilitado' : 'desabilitado'}</span></div>
              <div className="mm-context-body"><div className="mm-context-icon"><BookOpen size={18} aria-hidden="true"/></div><div><b>{text(selected.contextStatus, 'Sem resposta contextual')}</b><p>Respostas tipadas servem como apoio contextual. Não são probabilidade de lucro, decisão financeira nem autorização para operar.</p></div></div>
              {projection.context ? <div className="mm-context-answer"><span>RESPOSTAS · {text(projection.context.questions_version)}</span><b>{ageLabel(projection.context.age_ms)}</b><ul>{Array.isArray(projection.context.answers) ? projection.context.answers.map((answer, index) => <li key={index}>{JSON.stringify(answer)}</li>) : <li>Sem resposta compatível.</li>}</ul></div> : <div className="mm-context-empty">Nenhuma resposta contextual válida para esta identidade de workspace.</div>}
              <div className="mm-context-controls"><button className="mm-button mm-button-subtle" onClick={() => void setJevEnabled(!schedulerEnabled)} disabled={!!pending || (!schedulerEnabled && !selectedId)}>{schedulerEnabled ? 'Desabilitar JEV' : 'Habilitar JEV'}</button><span>Modelo: {text(scheduler?.model)} · versão de perguntas: {text(scheduler?.question_version)}</span></div>
              <small className="mm-context-note">Se o JEV ainda não estiver configurado, use a tela de configuração do modo legado. Nenhuma chave é coletada aqui; chamadas seguem o budget do produto.</small>
            </article>
          </section>

          <details className="mm-card mm-progressive">
            <summary><span><Database size={16} aria-hidden="true"/><b>Detalhes, gates e diagnóstico</b><small>Metadata, cobertura, retenção e métricas sanitizadas</small></span><ChevronDown size={16} aria-hidden="true"/></summary>
            <div className="mm-progressive-grid">
              <section><h4>Identidade e capacidades</h4><div className="mm-kv"><span>Workspace</span><b>{text(selected.identity.workspace_id)}</b><span>Instrumento</span><b>{text(selected.identity.instrument_id)}</b><span>Fonte</span><b>{text(selected.identity.source_id)}</b><span>Metadata</span><b>{text(selected.identity.metadata_version)}</b><span>Vencimento</span><b>{shortTime(selected.identity.expiry_at_ms)}</b><span>Tick de preço</span><b>{decimal(instrument?.price_tick)}</b><span>Passo de quantidade</span><b>{decimal(instrument?.quantity_step)}</b><span>Quantidade mínima</span><b>{decimal(instrument?.quantity_min)}</b><span>Multiplicador</span><b>{decimal(instrument?.contract_multiplier)}</b><span>Tape completo</span><b>{fullTape ? 'sim' : 'não certificado'}</b><span>Modo de livro</span><b>{text(source?.book_mode, 'não informado')}</b></div></section>
              <section><h4>Gates não promovidos</h4><div className="mm-gates"><Gate label="Feed B3 independente" state={projection.gates?.b3} detail="Aguardando fornecedor, entitlement e licença."/><Gate label="Conta privada" state={projection.gates?.private_account} detail="Somente reconciliação manual read-only nesta tarefa."/><Gate label="Modelo financeiro" state={projection.gates?.financial_model} detail="Probabilidade de lucro permanece não estimada."/><Gate label="Evidência nativa" state={projection.gates?.native_evidence} detail="Janela Windows e jornada humana não medidas."/></div></section>
              <section><h4>Persistência e replay</h4><div className="mm-retention"><Database size={15} aria-hidden="true"/><div><b>Gravação: {statusLabel(projection.recording?.status)}</b><small>{text(projection.recording?.reason, 'Política de retenção/exportação não informada.')}</small></div></div><p>Sem política afirmativa por fonte, payload de mercado não deve ser persistido. O estado e a contagem de eventos são diagnósticos sanitizados.</p><div className="mm-inline-actions"><button className="mm-button mm-button-subtle" onClick={() => void setRecording(!recordingEnabled)} disabled={!!pending}>{recordingEnabled ? 'Solicitar parada da gravação' : 'Solicitar gravação'}</button><button className="mm-button mm-button-subtle" onClick={() => void replayWorkspace()} disabled={!!pending || !selectedId}><RefreshCw size={14} aria-hidden="true"/>Reproduzir namespace</button></div></section>
              <section><h4>Métricas sem payload</h4><div className="mm-metrics-grid"><Stat label="EVENTOS" value={String(projection.metrics?.events ?? '—')}/><Stat label="DUPLICATAS" value={String(projection.metrics?.duplicates ?? '—')}/><Stat label="REJEITADOS" value={String(projection.metrics?.rejected ?? '—')}/><Stat label="OVERFLOW" value={String(projection.metrics?.overflow ?? '—')}/><Stat label="P95 · ms" value={projection.metrics?.process_p95_ms == null ? '—' : String(projection.metrics.process_p95_ms)}/><Stat label="ATRASO · ms" value={projection.metrics?.market_lag_ms == null ? '—' : String(projection.metrics.market_lag_ms)}/><Stat label="RSS · bytes" value={projection.metrics?.rss_bytes == null ? '—' : String(projection.metrics.rss_bytes)}/><Stat label="GPU · bytes" value={projection.metrics?.gpu_bytes == null ? '—' : String(projection.metrics.gpu_bytes)}/></div><button className="mm-button mm-button-subtle" onClick={() => void refreshMetrics()} disabled={!!pending || !selectedId}><RefreshCw size={14} aria-hidden="true"/>Atualizar métricas</button></section>
            </div>
          </details>

          <footer className="mm-footer"><span><Shield size={13} aria-hidden="true"/> Observador local · Binance Spot público · sem ordens</span><span>Último snapshot local · {shortTime(localSnapshot.generated_at_ms)}</span><button onClick={() => void refreshMetrics()} disabled={!!pending || !selectedId}><RefreshCw size={13} aria-hidden="true"/> Atualizar estado</button></footer>
        </> : <>
          <section className="mm-connect-empty">
            <div className="mm-connect-illustration"><Radio size={23} aria-hidden="true"/><span/></div>
            <span className="mm-eyebrow">SEM FONTE CONECTADA</span>
            <h2>Conecte uma fonte pública quando estiver pronto.</h2>
            <p>A conexão começa somente após sua ação. O piloto consulta metadata atual de BTCUSDT e abre streams públicos read-only. Nenhuma conta ou ordem é conectada.</p>
            <button className="mm-button mm-button-primary" onClick={() => void connectPublicSpot()} disabled={!!pending}><Radio size={15} aria-hidden="true"/>{pending ? 'Preparando conexão…' : 'Descobrir metadata e conectar BTCUSDT'}</button>
            <div className="mm-empty-gates"><span><CheckCircle2 size={14} aria-hidden="true"/>TLS validado pelo transporte</span><span><LockKeyhole size={14} aria-hidden="true"/>Ordens sempre desabilitadas</span><span><Activity size={14} aria-hidden="true"/>Sem livro L2 no piloto</span></div>
          </section>
          <section className="mm-grid-locked">
            <article className="mm-card mm-locked-card"><span className="mm-lock-icon"><LockKeyhole size={17} aria-hidden="true"/></span><div><span className="mm-eyebrow">B3 · WIN / WDO</span><h3>Feed independente bloqueado</h3><p>Ative somente após qualificação documental do fornecedor, SKU, entitlement e política de uso/retenção. Este piloto não conecta placeholder como feed live.</p></div><span className="mm-status-pill mm-tone-bad"><i aria-hidden="true"/>bloqueado</span></article>
            <article className="mm-card mm-locked-card"><span className="mm-lock-icon"><Wallet size={17} aria-hidden="true"/></span><div><span className="mm-eyebrow">CONTA PRIVADA</span><h3>Sem credenciais ou trading scopes</h3><p>O ledger permanece local e manual até existir integração read-only qualificada e fixture autorizada.</p></div><span className="mm-status-pill mm-tone-quiet"><i aria-hidden="true"/>não conectada</span></article>
          </section>
          <section className="mm-card mm-gate-preview"><div className="mm-card-head"><div><span className="mm-eyebrow">ESTADO DO SISTEMA</span><h3>Gates e métricas</h3></div><Gauge size={16} aria-hidden="true"/></div><div className="mm-gates mm-gates-compact"><Gate label="Feed B3 independente" state={projection.gates?.b3} detail="Licença e entitlement pendentes."/><Gate label="Conta privada" state={projection.gates?.private_account} detail="Nenhuma conta conectada."/><Gate label="Modelo financeiro" state={projection.gates?.financial_model} detail="Lucro líquido e chance não estimados."/><Gate label="Evidência nativa" state={projection.gates?.native_evidence} detail="Não medida nesta superfície."/></div></section>
          <footer className="mm-footer"><span><Shield size={13} aria-hidden="true"/> Observador local · nenhuma conexão automática</span><a href="#legacy">Abrir modo legado Excel/OCR/JeVWIN</a></footer>
        </>}
      </div>
    </main>
  </div>;
}
