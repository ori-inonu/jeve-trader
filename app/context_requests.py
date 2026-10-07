"""Versioned literal hypotheses, shared by both desktop controllers."""
from copy import deepcopy

CONTEXT_VERSION = 'literal-hypotheses-v2'
FIELDS = ('id', 'side', 'entry_points', 'stop_points', 'target_points', 'reference_levels',
          'reference_evidence_ids', 'premise', 'hypothesis_version', 'hypotheses', 'recipe')


def attach_candidates(state, questions, rows):
    state['context_contract_version'] = CONTEXT_VERSION
    state['candidate_setups'] = []
    for row in rows[:8]:
        if not isinstance(row.get('premise'), str) or not row['premise'].strip():
            raise ValueError('Literal candidate premise required')
        index = len(state['candidate_setups'])
        state['candidate_setups'].append(deepcopy({k: row[k] for k in FIELDS if k in row}))
        reference = f'state.candidate_setups[{index}]'
        dimensions = {
            'support': f'Does observed evidence support the exact literal premise in {reference}.premise? Assess continuation only; do not substitute absorption or a reversal hypothesis.',
            'contradiction': f'Does observed evidence contradict the exact literal premise in {reference}.premise? Only contrary observations count; absent evidence belongs to insufficiency.',
            'insufficient': f'Is observed evidence insufficient to assess the exact literal premise in {reference}.premise? Evaluate missing, partial, stale or inconsistent coverage independently of contradiction.',
        }
        for dimension, instruction in dimensions.items():
            questions[f'candidate_{index}_{dimension}'] = {'type': 'noul', 'instructions': instruction + ' This is contextual evidence, never probability of profit. Do not use account size.'}
        if row.get('hypotheses', {}).get('absorption'):
            questions[f'candidate_{index}_absorption_support'] = {'type': 'noul', 'instructions': f'Does evidence support the separate literal absorption claim in {reference}.hypotheses.absorption? Do not combine it with continuation or infer reversal/profit.'}

