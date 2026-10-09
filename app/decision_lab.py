"""Offline experiments. Progressions after losses are never live policies.

Execution is a conservative trade-price proxy, not a Profit fill simulator.
Coverage proof is an input; chronological timestamps alone are not proof.
"""
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
import math
import random
import statistics

from decision_engine import decimal, money, CostSchedule

RISK_METHODS = ('fixed_lot', 'fixed_cash', 'initial_fraction', 'current_fraction', 'kelly',
                'fractional_kelly', 'drawdown_kelly', 'volatility', 'optimal_f', 'fixed_ratio',
                'paroli', 'partial_reinvest', 'pyramiding', 'martingale', 'dalembert', 'fibonacci', 'labouchere')
BASE_FEATURES = ('return_points', 'volatility_points', 'delta_ratio', 'trade_count', 'intensity', 'stop_distance', 'target_distance', 'side_sign')
JEV_FEATURES = ('jev_support', 'jev_contradiction', 'jev_insufficient')


def tape_digest(events):
    return hashlib.sha256(json.dumps(events, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def coverage_proof_matches(proof, *, symbol, digest, start_ms, end_ms):
    # A declaration binds to one captured tape and horizon; clocks alone do not
    # prove continuity. Its external reference must still be independently audited.
    return (proof.get('full_tape') is True and proof.get('continuity_verified') is True
            and isinstance(proof.get('reference'), str) and bool(proof['reference'].strip())
            and proof.get('symbol') == symbol and proof.get('events_sha256') == digest
            and type(proof.get('start_ms')) is int and type(proof.get('end_ms')) is int
            and proof['start_ms'] <= start_ms < end_ms <= proof['end_ms'])


def label_path(plan, events, *, coverage_verified=False):
    start = plan['entry_ts_ms']
    end = start + plan['horizon_ms']
    if type(start) is not int or type(plan['horizon_ms']) is not int or plan['horizon_ms'] <= 0:
        raise ValueError('Invalid decision horizon')
    stamps = [e['ts_ms'] for e in events]
    if any(type(t) is not int for t in stamps) or stamps != sorted(stamps):
        raise ValueError('Replay must preserve causal event order')
    entry, stop, target = [decimal(plan[k]) for k in ('entry_points', 'stop_points', 'target_points')]
    side = plan['side']
    if side not in ('buy', 'sell') or not (stop < entry < target if side == 'buy' else target < entry < stop):
        raise ValueError('Invalid label geometry')
    sign = 1 if side == 'buy' else -1
    result = dict(label='censored', gross_points=None, outcome_ts_ms=end, label_version='trade-proxy-gap-stop-v1',
                  coverage_verified=coverage_verified, horizon_end_ms=end, fill_assumption='trade_price_proxy_no_queue_or_partial_fill')
    if coverage_verified is not True or not stamps or stamps[-1] < end:
        return result
    last = None
    for event in events:
        if not start < event['ts_ms'] <= end:
            continue
        price = decimal(str(event['price_points']))
        last = event
        stop_hit = price <= stop if sign == 1 else price >= stop
        target_hit = price >= target if sign == 1 else price <= target
        if stop_hit or target_hit:
            # Stop gap is charged in full. Target never receives favorable gap credit.
            exit_price = price if stop_hit else target
            return {**result, 'label': 'stop' if stop_hit else 'target', 'gross_points': str((exit_price-entry)*sign), 'outcome_ts_ms': event['ts_ms']}
    if last:
        return {**result, 'label': 'time', 'gross_points': str((decimal(str(last['price_points']))-entry)*sign), 'outcome_ts_ms': end}
    return result


def replay_opportunities(events, *, coverage=None, contexts=None, horizon_ms=60000, stride_ms=60000):
    """Build features from the prefix only, then attach future outcomes separately."""
    if horizon_ms <= 0 or stride_ms <= 0:
        raise ValueError('Invalid sampling')
    data = [x.to_dict() if hasattr(x, 'to_dict') else dict(x) for x in events]
    if any(data[i]['ts_ms'] > data[i+1]['ts_ms'] for i in range(len(data)-1)):
        raise ValueError('Out-of-order input; reconcile corrections before replay')
    sessions = {}
    for event in data:
        session = datetime.fromtimestamp(event['ts_ms']/1000, timezone.utc).astimezone(__import__('zoneinfo').ZoneInfo('America/Sao_Paulo')).date().isoformat()
        sessions.setdefault((session, event['symbol']), []).append(event)
    rows = []
    for (session, symbol), tape in sessions.items():
        window, next_at = deque(), 0
        proof = (coverage or {}).get(session, {}).get(symbol, {})
        digest = tape_digest(tape)
        for event in tape:
            ts = event['ts_ms']
            verified = coverage_proof_matches(proof, symbol=symbol, digest=digest, start_ms=ts, end_ms=ts+horizon_ms)
            window.append(event)
            while window and window[0]['ts_ms'] < ts-30000:
                window.popleft()
            if ts < next_at or len(window) < 3:
                continue
            next_at = ts + stride_ms
            prices = [float(x['price_points']) for x in window]
            volume = sum(x['quantity'] for x in window)
            delta = sum(x['quantity']*(1 if x['aggressor']=='buy' else -1 if x['aggressor']=='sell' else 0) for x in window)
            features = dict(return_points=prices[-1]-prices[0], volatility_points=statistics.pstdev(prices),
                            delta_ratio=delta/volume if volume else 0, trade_count=len(window), intensity=len(window)/max(1, (ts-window[0]['ts_ms'])/1000))
            entry = decimal(str(event['price_points']))
            if entry % 5:
                continue
            for side, sign in (('buy', 1), ('sell', -1)):
                plan = dict(side=side, entry_points=str(entry), stop_points=str(entry-sign*100), target_points=str(entry+sign*200), entry_ts_ms=ts, horizon_ms=horizon_ms)
                row = dict(id=f'{session}:{symbol}:{ts}:{side}', session=session, symbol=symbol, feature_asof_ms=ts,
                           recipe_version='laboratory-fixed-100-200-v1', **plan,
                           features={**features, 'stop_distance': 100, 'target_distance': 200, 'side_sign': sign})
                context = (contexts or {}).get(row['id'])
                if context and type(context.get('available_at_ms')) is int and context['available_at_ms'] <= ts and context.get('recipe_version') == row['recipe_version']:
                    values = [context.get(k) for k in JEV_FEATURES]
                    if all(type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 1 for v in values):
                        row['features'].update(dict(zip(JEV_FEATURES, values)))
                        row['jev_available_at_ms'] = context['available_at_ms']
                row.update(label_path(plan, tape, coverage_verified=verified))
                rows.append(row)
    return rows


def temporal_split(rows, *, train_fraction=.6, calibration_fraction=.2):
    if not 0 < train_fraction < 1 or not 0 < calibration_fraction < 1-train_fraction:
        raise ValueError('Invalid split fractions')
    for row in rows:
        if any(type(row[k]) is not int for k in ('feature_asof_ms', 'entry_ts_ms', 'outcome_ts_ms')) or row['feature_asof_ms'] > row['entry_ts_ms'] or row.get('jev_available_at_ms', 0) > row['entry_ts_ms'] or row['outcome_ts_ms'] <= row['entry_ts_ms'] or row.get('horizon_end_ms', row['outcome_ts_ms']) < row['outcome_ts_ms']:
            raise ValueError('Future information or invalid horizon')
    ordered = sorted(rows, key=lambda x: x['entry_ts_ms'])
    sessions = list(dict.fromkeys(x['session'] for x in ordered))
    contiguous = [x['session'] for i,x in enumerate(ordered) if i == 0 or x['session'] != ordered[i-1]['session']]
    if len(sessions) < 5 or len(contiguous) != len(sessions):
        raise ValueError('At least five chronological sessions required')
    a, b = max(1, int(len(sessions)*train_fraction)), max(2, int(len(sessions)*(train_fraction+calibration_fraction)))
    if b >= len(sessions):
        b = len(sessions)-1
    train = [x for x in ordered if x['session'] in sessions[:a]]
    calibration = [x for x in ordered if x['session'] in sessions[a:b]]
    test = [x for x in ordered if x['session'] in sessions[b:]]
    if not all((train, calibration, test)):
        raise ValueError('Empty temporal partition')
    # Purge complete outcome horizons, not only the first touch timestamp.
    train = [x for x in train if x.get('horizon_end_ms', x['outcome_ts_ms']) < calibration[0]['entry_ts_ms']]
    calibration = [x for x in calibration if x.get('horizon_end_ms', x['outcome_ts_ms']) < test[0]['entry_ts_ms']]
    return train, calibration, test


def kelly_grid(returns):
    """Finite historical log-growth optimum, with bankruptcy excluded."""
    if not returns or any(not math.isfinite(x) for x in returns):
        raise ValueError('Invalid training returns')
    candidates = [i/100 for i in range(101)]
    return max(candidates, key=lambda f: sum(math.log1p(f*r) for r in returns)/len(returns) if all(1+f*r > 0 for r in returns) else -math.inf)


def risk_quantity(method, *, equity, initial, stop_loss, state=None, fraction=.1, cash=40, delta=100, volatility=20, training_returns=None, kelly_fraction=.25, drawdown_reference=.30):
    """One explicit research variant per name, bounded later by capacity."""
    equity, initial, stop_loss, fraction, cash, delta, volatility, kelly_fraction, drawdown_reference = [decimal(str(v)) for v in (equity, initial, stop_loss, fraction, cash, delta, volatility, kelly_fraction, drawdown_reference)]
    if method not in RISK_METHODS or min(initial, stop_loss, delta, volatility, drawdown_reference) <= 0 or not 0 < fraction <= 1 or not 0 < kelly_fraction <= 1:
        raise ValueError('Invalid policy')
    state = state or {}
    losses, wins = min(20, max(0, state.get('loss_streak', 0))), min(20, max(0, state.get('win_streak', 0)))
    profit = max(0, equity-initial)
    if method == 'fixed_lot': value = 1
    elif method == 'fixed_cash': value = cash/stop_loss
    elif method == 'initial_fraction': value = initial*fraction/stop_loss
    elif method == 'current_fraction': value = max(0, equity)*fraction/stop_loss
    elif method in ('kelly', 'fractional_kelly', 'drawdown_kelly', 'optimal_f'):
        f = state.get('fitted_fraction')
        if f is None: f = kelly_grid(training_returns or [0])
        f = decimal(str(f))
        if method == 'fractional_kelly': f *= kelly_fraction
        if method == 'drawdown_kelly': f *= kelly_fraction/(1+decimal(str(state.get('drawdown', 0)))/drawdown_reference)
        value = max(0, equity)*f/stop_loss
    elif method == 'volatility': value = max(0, equity)*fraction/max(stop_loss, volatility)
    elif method == 'fixed_ratio': value = (1+(1+8*profit/delta).sqrt())/2
    elif method == 'paroli': value = 2**(wins%4)  # reset after the fourth win
    elif method == 'partial_reinvest': value = (cash+profit*decimal('.5'))/stop_loss
    elif method == 'pyramiding': value = 1+max(0, state.get('favorable_steps', 0))  # aggregate lots at confirmed favorable levels
    elif method == 'martingale': value = 2**losses
    elif method == 'dalembert': value = max(1, state.get('unit', 1))
    elif method == 'fibonacci':
        a, b = 1, 1
        for _ in range(losses): a, b = b, a+b
        value = a
    else:
        sequence = state.get('sequence') or [1, 2, 3]
        value = sequence[0]+sequence[-1] if len(sequence)>1 else sequence[0] if sequence else 1
    return max(0, int(value))


def trajectory(net_per_contract, method, *, initial=400, margin=155, stop_loss=20, training_returns=None, kelly_fraction=.25, drawdown_reference=.30):
    initial_money, margin_money, loss_money = [decimal(str(v), nonnegative=True) for v in (initial, margin, stop_loss)]
    if min(initial_money, margin_money, loss_money) <= 0:
        raise ValueError('Positive scenario values required')
    equity, peak = initial_money, initial_money
    path, max_dd, ruined, capacity_lost = [money(equity)], 0., False, False
    realized = []
    state = dict(win_streak=0, loss_streak=0, unit=1, sequence=[1, 2, 3], drawdown=0.)
    if method in ('kelly', 'fractional_kelly', 'drawdown_kelly', 'optimal_f'):
        state['fitted_fraction'] = kelly_grid(training_returns or [0])
    for net in net_per_contract:
        q = risk_quantity(method, equity=equity, initial=initial_money, stop_loss=loss_money, state=state, kelly_fraction=kelly_fraction, drawdown_reference=drawdown_reference)
        capacity = max(0, int(equity/(margin_money+loss_money)))
        q = min(q, capacity, 10000)
        if capacity == 0:
            capacity_lost = True
        result = q*decimal(str(net))
        realized.append(money(result))
        equity = decimal(money(equity+result))
        peak = max(peak, equity)
        state['drawdown'] = float(max(0, (peak-equity)/peak)) if peak else 0
        max_dd = max(max_dd, state['drawdown'])
        ruined |= equity <= 0
        path.append(money(equity))
        if q == 0: continue
        if result > 0:
            state['win_streak'] += 1; state['loss_streak'] = 0
            state['unit'] = max(1, state['unit']-1)
            state['sequence'] = (state['sequence'][1:-1] if len(state['sequence'])>1 else []) or [1, 2, 3]
        elif result < 0:
            state['loss_streak'] += 1; state['win_streak'] = 0
            state['unit'] += 1
            sequence = state['sequence']
            state['sequence'] = (sequence+[sequence[0]+sequence[-1] if len(sequence)>1 else sequence[0] if sequence else 1])[-100:]
    return dict(equity_path=path, final_equity=money(equity), net_growth=float(equity/initial_money-1), log_growth=math.log(float(equity/initial_money)) if equity>0 else None,
                max_drawdown=max_dd, ruined=ruined, capacity_lost=capacity_lost, target_hit=None, realized_net_brl=realized)


def tail_risk(results, alpha=.95):
    if not results or not 0 < alpha < 1 or any(not math.isfinite(x) for x in results):
        raise ValueError('Invalid tail risk input')
    losses = sorted(-float(x) for x in results)
    threshold = losses[max(0, math.ceil(alpha*len(losses))-1)]
    tail_mass = (1-alpha)*len(losses)
    remaining, weighted = tail_mass, 0.
    for loss in reversed(losses):
        weight = min(1., remaining)
        weighted += loss*weight
        remaining -= weight
        if remaining <= 1e-12: break
    return dict(var_loss_brl=threshold, expected_shortfall_brl=weighted/tail_mass, alpha=alpha, sample_count=len(results))


def policy_comparison(rows, costs, *, initial=400, target=4000, bootstrap_runs=100, seed=7):
    if type(bootstrap_runs) is not int or not 1 <= bootstrap_runs <= 10000:
        raise ValueError('Positive bounded bootstrap count required')
    train, calibration, test = temporal_split(rows)
    train_net = [float(decimal(x['gross_points'])*decimal('.20')-costs.total(1)) for x in train if x.get('label')!='censored']
    # Only one non-overlapping opportunity may consume a capital trajectory.
    selected, unavailable_until = [], 0
    for row in test:
        if row.get('label') == 'censored' or row['entry_ts_ms'] <= unavailable_until: continue
        selected.append(row); unavailable_until = row['outcome_ts_ms']
    by_session = {}
    for row in selected:
        by_session.setdefault(row['session'], []).append(float(decimal(row['gross_points'])*decimal('.20')-costs.total(1)))
    nets = [n for values in by_session.values() for n in values]
    if not nets: return {}
    stop_loss = max(1., max(abs(n) for n in train_net if n < 0)) if any(n < 0 for n in train_net) else 23.
    training = [n/stop_loss for n in train_net]
    rng = random.Random(seed)
    report = {}
    sessions = list(by_session.values())
    # All methods receive the same session resamples.
    bootstrap_paths = [[n for _ in sessions for n in rng.choice(sessions)] for _ in range(bootstrap_runs)]
    calibration_net, calibration_until = [], 0
    for row in calibration:
        if row.get('label') == 'censored' or row['entry_ts_ms'] <= calibration_until: continue
        calibration_net.append(float(decimal(row['gross_points'])*decimal('.20')-costs.total(1)))
        calibration_until = row['outcome_ts_ms']
    for method in RISK_METHODS:
        if method == 'pyramiding':
            report[method] = dict(status='INTRA_TRADE_PATH_REQUIRED', reason='Additions require favorable levels and aggregate stop exposure; endpoint outcomes cannot validate this method')
            continue
        parameters = dict(kelly_fraction=.25, drawdown_reference=.30)
        if method in ('fractional_kelly', 'drawdown_kelly') and calibration_net:
            options = [dict(kelly_fraction=f, drawdown_reference=d) for f in (.1, .25, .5, 1.) for d in ((.2, .3, .4) if method=='drawdown_kelly' else (.3,))]
            def score(p):
                growth = trajectory(calibration_net, method, initial=initial, margin=costs.margin_per_contract_brl, stop_loss=stop_loss, training_returns=training, **p)['log_growth']
                return growth if growth is not None else -math.inf
            parameters = max(options, key=score)
        actual = trajectory(nets, method, initial=initial, margin=float(decimal(costs.margin_per_contract_brl)), stop_loss=stop_loss, training_returns=training, **parameters)
        samples = []
        for path in bootstrap_paths:
            samples.append(trajectory(path, method, initial=initial, margin=float(decimal(costs.margin_per_contract_brl)), stop_loss=stop_loss, training_returns=training, **parameters))
        report[method] = dict(observed=actual, sample_count=len(nets), bootstrap_runs=bootstrap_runs,
                              ruin_frequency=sum(x['ruined'] for x in samples)/bootstrap_runs,
                              capacity_loss_frequency=sum(x['capacity_lost'] for x in samples)/bootstrap_runs,
                              target_hit_frequency=sum(max(decimal(v) for v in x['equity_path'])>=decimal(str(target)) for x in samples)/bootstrap_runs,
                              target_brl=target, initial_brl=initial, tail=tail_risk([float(decimal(n)) for n in actual['realized_net_brl']]),
                              parameters=parameters, selection_partition='calibration',
                              status='LAB_ONLY_NO_LIVE_RECOVERY', assumption='session_bootstrap_not_forecast', opportunity_order='chronological_input_order_ties_first_no_outcome_selection',
                              optimal_f_normalization='historical_worst_loss' if method=='optimal_f' else None)
    return report


def economic_replay(rows, predictions, training_distributions, costs, *, initial=400, fraction=.25):
    """Research only: frozen forecasts + training distributions, no API/approval."""
    equity = decimal(str(initial), nonnegative=True)
    if equity <= 0 or not 0 < fraction <= 1: raise ValueError('Invalid economic scenario')
    indexed = {p['id']: p for p in predictions}
    decisions, unavailable_until, peak, max_dd = [], -1, equity, 0.
    for row in sorted(rows, key=lambda r: r['entry_ts_ms']):
        if row['id'] not in indexed or row['entry_ts_ms'] <= unavailable_until: continue
        forecast = indexed[row['id']]['probabilities']
        if not forecast or abs(sum(forecast.values())-1)>1e-6: raise ValueError('Invalid forecast')
        outcomes = [(float(p)/len(training_distributions[label]), decimal(str(gross))*decimal('.20')) for label,p in forecast.items() for gross in training_distributions.get(label, [])]
        if not outcomes or abs(sum(p for p,_ in outcomes)-1)>1e-6: raise ValueError('Missing training outcome distribution')
        worst = max([decimal(0)]+[-gross+costs.total(1) for _,gross in outcomes])
        capacity = min(10000, max(0, int(equity/(decimal(costs.margin_per_contract_brl)+worst))))
        def growth(q):
            nets = [(p, gross*q-costs.total(q)) for p,gross in outcomes]
            return sum(p*math.log1p(float(net/equity)) for p,net in nets) if equity>0 and all(equity+net>0 for _,net in nets) else -math.inf
        best = max(range(capacity+1), key=growth) if equity>0 else 0
        current_dd = float((peak-equity)/peak)
        ceiling = int(decimal(best)*decimal(str(fraction))/(1+decimal(str(current_dd))/decimal('.30')))
        q = max(range(ceiling+1), key=growth) if equity>0 else 0
        before = equity
        net = decimal(row['gross_points'])*decimal('.20')*q-costs.total(q)
        equity = decimal(money(equity+net)); peak=max(peak,equity)
        max_dd = max(max_dd,float((peak-equity)/peak))
        if q: unavailable_until = row['outcome_ts_ms']
        decisions.append(dict(id=row['id'], quantity=q, equity_before_brl=money(before), realized_net_brl=money(net), equity_after_brl=money(equity)))
    return dict(status='RESEARCH_ONLY', deployment_approved=False, final_equity_brl=money(equity), max_drawdown=max_dd, decisions=decisions,
                assumptions='trade_price_proxy_no_latency_no_queue_historical_class_distributions', kelly_fraction=fraction)


def train_baselines(rows, *, synthetic=False, costs=None, initial=400):
    """Dependencies optional; core UI/testing never requires sklearn or paid API."""
    import numpy as np
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.frozen import FrozenEstimator
    from sklearn.metrics import log_loss
    from decision_engine import CostSchedule
    costs = costs or CostSchedule()
    valid = [r for r in rows if r.get('label') in ('target', 'stop', 'time') and r.get('coverage_verified') is True]
    labels = ('stop', 'target', 'time')
    result = {'schema_version': 1, 'synthetic': synthetic, 'deployment_approved': False, 'models': {}, 'excluded_rows': len(rows)-len(valid)}
    for name, features, subset in [('without_jev', BASE_FEATURES, valid), ('with_jev', BASE_FEATURES+JEV_FEATURES, [r for r in valid if all(k in r['features'] for k in JEV_FEATURES)])]:
        try:
            train, calibration, test = temporal_split(subset)
            if any(set(r['label'] for r in group)!=set(labels) for group in (train, calibration, test)):
                raise ValueError('Every temporal partition must include all three outcomes')
            def x(group):
                values = np.asarray([[r['features'][k] for k in features] for r in group], dtype=float)
                if not np.isfinite(values).all(): raise ValueError('Nonfinite features')
                return values
            model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=7))
            model.fit(x(train), [r['label'] for r in train])
            calibrated = CalibratedClassifierCV(FrozenEstimator(model), method='sigmoid')
            calibrated.fit(x(calibration), [r['label'] for r in calibration])
            probabilities = calibrated.predict_proba(x(test))
            classes = list(calibrated.classes_)
            truth = np.asarray([[float(r['label']==label) for label in classes] for r in test])
            brier = float(np.mean(np.sum((probabilities-truth)**2, axis=1)))
            confidence, correct = probabilities.max(axis=1), (probabilities.argmax(axis=1)==truth.argmax(axis=1)).astype(float)
            ece = sum(float(np.mean(mask))*abs(float(confidence[mask].mean()-correct[mask].mean())) for lo in np.arange(0, 1, .1) if (mask := (confidence>=lo)&(confidence<lo+.1)).any())
            distributions = {label: [float(decimal(r['gross_points'])) for r in train if r['label']==label] for label in classes}
            predictions = [dict(id=r['id'], probabilities=dict(zip(classes, p.tolist())), outcome=r['label']) for r, p in zip(test, probabilities)]
            # Resample whole held-out sessions; never tune on these intervals.
            session_indices = [np.asarray([i for i,r in enumerate(test) if r['session']==session]) for session in sorted(set(r['session'] for r in test))]
            rng = random.Random(7)
            losses = -np.sum(truth*np.log(np.clip(probabilities, 1e-15, 1)), axis=1)
            briers = np.sum((probabilities-truth)**2, axis=1)
            samples = []
            for _ in range(200):
                indices = np.concatenate([rng.choice(session_indices) for _ in session_indices])
                samples.append((float(losses[indices].mean()),float(briers[indices].mean())))
            intervals = np.quantile(np.asarray(samples), [.025,.975], axis=0)
            reliability = {label: [dict(count=int(mask.sum()), mean_prediction=float(probabilities[mask,c].mean()), observed_fraction=float(truth[mask,c].mean())) for lo in np.arange(0,1,.1) if (mask := (probabilities[:,c]>=lo)&(probabilities[:,c]<(lo+.1 if lo<.9 else 1.000001))).any()] for c,label in enumerate(classes)}
            result['models'][name] = dict(status='RESEARCH_ONLY', features=list(features), classes=classes,
                counts=dict(train=len(train), calibration=len(calibration), test=len(test)),
                sessions={k: sorted(set(r['session'] for r in group)) for k, group in [('train', train), ('calibration', calibration), ('test', test)]},
                log_loss=float(log_loss([r['label'] for r in test], probabilities, labels=classes)), multiclass_brier=brier, ece=ece,
                reliability=reliability, uncertainty=dict(method='heldout_session_bootstrap', confidence=.95, session_count=len(session_indices), resamples=200, log_loss_interval=intervals[:,0].tolist(), brier_interval=intervals[:,1].tolist()),
                gross_points_training_distributions=distributions,
                predictions=predictions, economic_replay=economic_replay(test,predictions,distributions,costs,initial=initial))
        except ValueError as error:
            result['models'][name] = {'status': 'INSUFFICIENT_EVIDENCE', 'reason': str(error)}
    # A fair JEV comparison uses exactly the same opportunities in both arms.
    common = [r for r in valid if all(k in r['features'] for k in JEV_FEATURES)]
    if common and len(common) != len(valid):
        matched = train_baselines(common, synthetic=synthetic, costs=costs, initial=initial)
        result['matched_jev_comparison'] = {k: {metric: v.get(metric) for metric in ('status', 'counts', 'log_loss', 'multiclass_brier', 'ece')} for k,v in matched['models'].items()}
    elif common:
        result['matched_jev_comparison'] = {k: {metric: v.get(metric) for metric in ('status', 'counts', 'log_loss', 'multiclass_brier', 'ece')} for k,v in result['models'].items()}
    paired = matched['models'] if common and len(common)!=len(valid) else result['models']
    if all(paired[name].get('economic_replay') for name in ('without_jev','with_jev')):
        a = {r['id']:r for r in paired['without_jev']['economic_replay']['decisions']}
        b = {r['id']:r for r in paired['with_jev']['economic_replay']['decisions']}
        result['paired_economic_comparison'] = dict(status='RESEARCH_ONLY', api_cost_brl=None, trajectory_overlap='one_capital_position_at_a_time_per_arm',
            opportunities=[dict(id=key, baseline_net_brl=a[key]['realized_net_brl'], jev_net_brl=b[key]['realized_net_brl'], difference_brl=money(decimal(b[key]['realized_net_brl'])-decimal(a[key]['realized_net_brl']))) for key in sorted(a.keys()&b.keys())])
    return result
