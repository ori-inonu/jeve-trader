"""Synthetic owner workload. No native/live/financial performance claims."""
import argparse
import json
import platform
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from multimarket.service import MultimarketService
from test_multimarket_service import Adapter, connected
from test_multimarket_domain import market_event

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
args = parser.parse_args()
latencies = []
with tempfile.TemporaryDirectory() as directory:
    adapter = Adapter()
    service = MultimarketService(directory, adapters={'binance_public_spot': adapter})
    try:
        workspace_id = connected(service, adapter)
        start = time.perf_counter()
        for batch in range(400):
            received = time.perf_counter()
            for item in range(25):
                index = batch*25+item
                adapter.items.append(market_event(kind='trade', event_id='synthetic:'+str(index),
                    epoch=1, workspace_id=workspace_id, market_ts_ms=None,
                    received_monotonic_ns=service.clock.monotonic_ns(),
                    payload={'price':str(100+index%4), 'quantity':'1', 'aggressor':'buy' if index%2 else 'sell'}))
            service.tick()
            if batch%10 == 0:
                json.dumps(service.snapshot(), allow_nan=False)
            latencies.append((time.perf_counter()-received)*1000)
            remaining = start+(batch+1)*.025-time.perf_counter()
            if remaining > 0:
                time.sleep(remaining)
        snapshot = service.snapshot()
        quality = snapshot['metrics']['events'] == 10002 and len(snapshot['selected']['market']['recent_trades']) == 200
        p95 = sorted(latencies)[int(len(latencies)*.95)-1]
        report = dict(kind='synthetic_multimarket_owner', platform=platform.platform(), python=sys.version,
            events=10000, events_per_second=1000, batch_size=25, seconds=time.perf_counter()-start,
            batch_post_receive_p95_ms=p95, batch_post_receive_max_ms=max(latencies),
            quality_pass=quality, threshold_ms=50, threshold_pass=p95<=50 and quality,
            recent_trades=len(snapshot['selected']['market']['recent_trades']), metrics=snapshot['metrics'],
            native_ui_p95_ms=None, gpu_bytes=None, manual_steps=None, financial_gain=None,
            live_performance_certified=False, comparison='Separate modular workload; does not establish native or financial gain')
    finally:
        service.close()
Path(args.output).write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report))
if not report['threshold_pass']:
    raise SystemExit(1)
