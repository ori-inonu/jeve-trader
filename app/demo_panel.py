"""Generate a clearly synthetic static report using the desktop decision core."""
from __future__ import annotations

import argparse
from pathlib import Path
import time

from app_core import DEFAULT_INPUTS, ObservationSession, build_decision_bundle
from candidate_research import generate_candidate_scenario
from panel_report import export_panel


def demonstration_bundle():
    fixture = generate_candidate_scenario(end_ms=int(time.time() * 1000))
    session = ObservationSession()
    session.mode = 'synthetic'
    session.clock_ms = fixture['now_ms']
    session.engine.set_source_quality(fixture['source_quality'])
    for event in fixture['events']:
        if event['type'] == 'trade':
            session.engine.add_trade(event)
            session.chart.append((event['ts_ms'], float(event['price_points'])))
        else:
            session.engine.set_book(event)
    session.warnings = ['Dados sintéticos criados para demonstrar o painel. Nenhuma API JEV foi consultada.']
    return build_decision_bundle(session, DEFAULT_INPUTS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('Painel_JevWIN_Demonstracao.html'))
    args = parser.parse_args()
    export_panel(args.output, demonstration_bundle())
    print(args.output)


if __name__ == '__main__':
    main()
