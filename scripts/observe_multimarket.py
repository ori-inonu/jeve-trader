"""Offline fixture by default; --live explicitly starts a finite public session."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from multimarket_observer import MultimarketObserver


def duration(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('Duração deve ser inteira') from None
    if not 1 <= number <= 1800:
        raise argparse.ArgumentTypeError('Duração deve estar entre 1 e 1800 segundos')
    return number


def diagnostics(snapshot):
    # Live prices/sizes and payloads are deliberately absent from diagnostic output.
    return {key: snapshot[key] for key in ('status', 'origin', 'error', 'health', 'transport',
        'received_trades', 'remaining_seconds', 'evaluation', 'missing', 'orders_enabled',
        'retention_enabled', 'profit_probability', 'target_probability', 'ruin_probability',
        'objective')}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Observar BTCUSDT spot público explicitamente')
    parser.add_argument('--duration-seconds', type=duration, default=60)
    args = parser.parse_args(argv)
    observer = MultimarketObserver()
    exit_code = 0
    value = None
    try:
        if args.live:
            observer.start(duration_seconds=args.duration_seconds)
            deadline = time.monotonic() + args.duration_seconds
            while time.monotonic() < deadline and observer.feed is not None:
                observer.poll()
                value = diagnostics(observer.snapshot())
                time.sleep(.1)
            value = value or diagnostics(observer.snapshot())
            if (value['error'] or not value['health'] or
                    any(not h['valid'] or h['stale'] for h in value['health'])):
                exit_code = 1
        else:
            observer.synthetic()
            value = diagnostics(observer.snapshot())
    except KeyboardInterrupt:
        exit_code = 130
        value = {'status': 'interrupted', 'origin': 'live' if args.live else 'synthetic',
                 'orders_enabled': False, 'retention_enabled': False}
    except Exception:
        exit_code = 1
        value = {'status': 'unavailable', 'origin': 'live' if args.live else 'synthetic',
                 'error': 'Observador indisponível; confira dependência opcional e status da fonte.',
                 'orders_enabled': False, 'retention_enabled': False}
    finally:
        observer.stop()
    if args.live:
        stopped = observer.snapshot()
        value['shutdown'] = {'status': stopped['status'], 'transport': stopped['transport']}
        if stopped['enabled']:
            exit_code = exit_code or 1
    print(json.dumps(value, ensure_ascii=False, allow_nan=False))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
