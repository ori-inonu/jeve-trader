"""Replay and compare explicitly experimental policies. No network or model deployment."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'app'))
from decision_lab import replay_opportunities, train_baselines, policy_comparison
from decision_engine import CostSchedule
from profit_bridge import read_csv_events


def smoke_rows():
    """Balanced synthetic integration fixture, deliberately unsuitable for WIN inference."""
    rows = []
    for day in range(1, 11):
        for i in range(30):
            label = ('stop', 'target', 'time')[i%3]
            ts = day*86400000+i*120000
            rows.append(dict(id=f'synthetic:{day}:{i}', session=f'synthetic-{day:02}', symbol='WIN_SIM',
                             entry_ts_ms=ts, feature_asof_ms=ts, outcome_ts_ms=ts+60000, horizon_end_ms=ts+60000,
                             label=label, coverage_verified=True, gross_points=('-100', '200', '5')[i%3],
                             features=dict(return_points=(i%7)-3, volatility_points=i%9+1, delta_ratio=(i%5)/5,
                                           trade_count=10+i, intensity=(i%6)+1, stop_distance=100, target_distance=200, side_sign=1,
                                           jev_support=.6, jev_contradiction=.2, jev_insufficient=.1), jev_available_at_ms=ts))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input-csv', type=Path)
    source.add_argument('--dataset', type=Path, help='JSON with a rows array and synthetic flag')
    source.add_argument('--smoke', action='store_true')
    parser.add_argument('--coverage-manifest', type=Path)
    parser.add_argument('--contexts', type=Path)
    parser.add_argument('--costs', type=Path)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'.artifacts'/'decision-lab')
    parser.add_argument('--initial', type=int, default=400)
    parser.add_argument('--target', type=int, default=4000)
    args = parser.parse_args()
    if args.initial <= 0 or args.target <= 0: parser.error('Positive scenario amounts required')
    synthetic = args.smoke
    if args.smoke: rows = smoke_rows()
    elif args.dataset:
        data = json.loads(args.dataset.read_text(encoding='utf-8'))
        rows, synthetic = data['rows'], data.get('synthetic', False)
    else:
        coverage = json.loads(args.coverage_manifest.read_text(encoding='utf-8')) if args.coverage_manifest else {}
        contexts = json.loads(args.contexts.read_text(encoding='utf-8')) if args.contexts else {}
        rows = replay_opportunities(read_csv_events(args.input_csv).events, coverage=coverage, contexts=contexts)
    costs = CostSchedule(**json.loads(args.costs.read_text(encoding='utf-8'))) if args.costs else CostSchedule()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    dataset = {'schema_version': 1, 'rows': rows, 'synthetic': synthetic}
    body = json.dumps(dataset, ensure_ascii=False, allow_nan=False)
    (output/'dataset.json').write_text(body, encoding='utf-8')
    report = train_baselines(rows, synthetic=synthetic, costs=costs, initial=args.initial)
    report.update(dataset_sha256=hashlib.sha256(body.encode()).hexdigest(), costs=asdict(costs),
                  execution_scope='trade_price_proxy_not_fill_validation', scenario=dict(initial_brl=args.initial, target_brl=args.target),
                  policy_comparison=policy_comparison(rows, costs, initial=args.initial, target=args.target) if any(r.get('label')!='censored' for r in rows) else {})
    (output/'report.json').write_text(json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2), encoding='utf-8')
    print(json.dumps({'report': str(output/'report.json'), 'rows': len(rows), 'synthetic': synthetic,
                      'models': {k:v['status'] for k,v in report['models'].items()}, 'deployment_approved': False}))


if __name__ == '__main__': main()
