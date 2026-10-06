"""Offline research illustrations and a static audit of the v0.3.0 payload.

No model, account, market connection, or order. Probabilities below are assumed
solely to demonstrate arithmetic; they are not estimates for the WIN.
"""
from __future__ import annotations

import ast
from decimal import Decimal as D
import hashlib
import json
from math import log1p
from pathlib import Path


def evaluate_binary(gain, loss, probability):
    gain, loss, probability = D(gain), D(loss), D(probability)
    return {
        "net_gain": str(gain), "net_loss": str(loss),
        "probability_assumed_not_estimated": str(probability),
        "net_reward_risk": str(gain / loss),
        "break_even_probability": str(loss / (gain + loss)),
        "expected_net_result": str(probability * gain - (1-probability) * loss),
    }


def main():
    root = Path(__file__).resolve().parent
    source = root / 'audit-source'
    desktop = (source / 'desktop_app.py').read_text(encoding='utf-8')
    projection_line = next(line.strip() for line in desktop.splitlines()
                           if 'state["candidate_setups"].append' in line)
    expression = ast.parse(projection_line).body[0].value
    keys = ast.literal_eval(expression.args[0].generators[0].iter)
    current_questions = json.loads((source / 'observer_questions.json').read_text())
    # Demonstrate exactly the audited projection, with synthetic placeholder
    # values; no captured market state is claimed by this example.
    row = {key: 'SYNTHETIC' for key in keys}
    row.update(premise='Explicit contextual premise', recipe='Synthetic recipe')
    projected = {key: row[key] for key in keys}
    p, gain, loss = .4, 38., 22.
    b = gain / loss
    growth = []
    for f in (0., .01, .05, .10, .15):
        growth.append({
            'fraction_lost_in_binary_stop': f,
            'arithmetic_expected_return': f * (p*b - (1-p)),
            'expected_log_growth': p * log1p(b*f) + (1-p) * log1p(-f),
        })
    report = {
        'study_date': '2026-10-06', 'app_version_audited': '0.3.0',
        'market_data_used': False, 'authenticated_jev_calls': 0,
        'windows_gui_tested': False, 'production_changes': False,
        'audit': {
            'actual_candidate_projection_keys': list(keys),
            'premise_exists_before_projection': 'premise' in row,
            'premise_exists_after_projection': 'premise' in projected,
            'base_question_count': len(current_questions),
            'maximum_questions_at_eight_candidates': len(current_questions)+2*8,
            'first_choice_option': next(iter(current_questions['flow_context']['criteria'])),
            'sources_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(source.iterdir()) if p.is_file()},
        },
        'reward_risk_is_not_expected_value': {
            'A': evaluate_binary('58', '22', '.25'),
            'B': evaluate_binary('38', '22', '.45'),
            'assumptions': 'Binary, net payoffs, certain entry, no timeout, no impact; p is purely assumed.'
        },
        'compound_growth_example': {
            'p_assumed': p, 'gain_assumed': gain, 'loss_assumed': loss,
            'binary_toy_optimal_fraction': (p*b-(1-p))/b,
            'assumptions': 'IID binary returns, no margin, granularity, gaps, impact or timeout. Not a sizing recommendation.',
            'rows': growth,
        },
        'latency_example': {
            'assumed_age_at_submission_ms': 1900,
            'assumed_roundtrip_ms': 300,
            'age_at_response_ms': 2200,
            'configured_source_validity_ms': 2000,
            'expired': 1900+300 > 2000,
            'measured_remotely': False,
        },
    }
    assert report['audit']['premise_exists_before_projection']
    assert not report['audit']['premise_exists_after_projection']
    assert D(report['reward_risk_is_not_expected_value']['A']['expected_net_result']) == D('-2')
    assert D(report['reward_risk_is_not_expected_value']['B']['expected_net_result']) == D('5')
    assert growth[-1]['arithmetic_expected_return'] > 0 and growth[-1]['expected_log_growth'] < 0
    output = root / 'reproduced_examples.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('audit', 'reward_risk_is_not_expected_value', 'compound_growth_example', 'latency_example')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
