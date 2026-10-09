"""Deterministic advisory economics. No order API and no loss-recovery sizing."""
from dataclasses import dataclass, field, asdict
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from datetime import date
import math

SCHEMA_VERSION = 1
CENT = Decimal('.01')
POINT_VALUE = Decimal('.20')


def decimal(value, *, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)) or len(str(value)) > 80:
        raise ValueError('Decimal must be finite text/integer')
    result = Decimal(value)
    if not result.is_finite() or abs(result) > Decimal('1000000000000') or nonnegative and result < 0:
        raise ValueError('Invalid decimal')
    return result


def money(value):
    return format(decimal(value).quantize(CENT, rounding=ROUND_HALF_UP), '.2f')


@dataclass
class AccountState:
    equity_brl: str = '400'
    peak_brl: str = '400'
    available_margin_brl: str = '400'
    positions: list = field(default_factory=list)
    revision: int = 0
    asof_ms: int = 0
    reconciliation_origin: str = 'manual'
    def __post_init__(self):
        for name in ('equity_brl', 'peak_brl', 'available_margin_brl'):
            setattr(self, name, str(decimal(getattr(self, name), nonnegative=name != 'equity_brl')))
        if decimal(self.peak_brl) < max(Decimal(0), decimal(self.equity_brl)):
            raise ValueError('Peak cannot be below current equity')
        if not isinstance(self.positions, list) or type(self.revision) is not int or self.revision < 0:
            raise ValueError('Invalid account')
        if type(self.asof_ms) is not int or self.asof_ms < 0 or self.reconciliation_origin != 'manual':
            raise ValueError('Manual reconciliation required')
    def to_dict(self):
        result = asdict(self)
        peak, equity = decimal(self.peak_brl), decimal(self.equity_brl)
        result['drawdown'] = float(max(Decimal(0), (peak-equity)/peak)) if peak else 0
        result['drawdown_reference'] = .30
        result['profit_stop'] = None
        return result


@dataclass
class MarketSnapshot:
    observation: dict
    source_generation: int
    asof_ms: int
    capabilities: dict
    def __post_init__(self):
        if not isinstance(self.observation, dict) or not isinstance(self.capabilities, dict) or type(self.source_generation) is not int or self.source_generation < 0 or type(self.asof_ms) is not int or self.asof_ms < 0:
            raise ValueError('Invalid market snapshot')
    def to_dict(self):
        return asdict(self)


@dataclass
class OutcomeEstimate:
    model_version: str
    distribution: list
    profit_probability: float | None = None
    probability_interval: list | None = None
    validated: bool = False
    validation: dict = field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.model_version, str) or not self.model_version or type(self.validated) is not bool or not isinstance(self.distribution, list) or not isinstance(self.validation, dict):
            raise ValueError('Invalid outcome estimate')
        if self.probability_interval is not None and (not isinstance(self.probability_interval, list) or len(self.probability_interval) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) for v in self.probability_interval) or not 0 <= self.probability_interval[0] <= self.probability_interval[1] <= 1):
            raise ValueError('Invalid uncertainty interval')
    def to_dict(self):
        return asdict(self)


@dataclass
class DecisionPlan:
    id: str
    action: str
    quantity: int
    entry_points: str | None
    stop_points: str | None
    target_points: str | None
    expires_at_ms: int | None
    evidence_ids: list
    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id or self.action not in ('buy', 'sell', 'wait') or type(self.quantity) is not int or self.quantity < 0 or not isinstance(self.evidence_ids, list):
            raise ValueError('Invalid decision plan')
        if self.action == 'wait':
            if self.quantity != 0 or any(x is not None for x in (self.entry_points, self.stop_points, self.target_points, self.expires_at_ms)):
                raise ValueError('Invalid waiting plan')
        elif self.quantity == 0 or type(self.expires_at_ms) is not int or self.expires_at_ms < 0:
            raise ValueError('Invalid actionable plan')
    def to_dict(self):
        return asdict(self)


@dataclass
class CostSchedule:
    b3_entry_brl: str = '0.50'
    b3_exit_brl: str = '0.50'
    brokerage_entry_brl: str = '0'
    brokerage_exit_brl: str = '0'
    slippage_points: str = '5'
    margin_per_contract_brl: str = '155'
    source: str = 'manual_experimental_not_verified_tariff'
    effective_from: str = '2026-10-07'
    account_id: str = 'manual'
    version: str = 'manual-v1'
    verified: bool = False
    def __post_init__(self):
        for name in ('b3_entry_brl', 'b3_exit_brl', 'brokerage_entry_brl', 'brokerage_exit_brl', 'slippage_points', 'margin_per_contract_brl'):
            setattr(self, name, str(decimal(getattr(self, name), nonnegative=True)))
        if decimal(self.margin_per_contract_brl) <= 0:
            raise ValueError('Margin must be positive')
        if not all(isinstance(getattr(self, name), str) and getattr(self, name).strip() for name in ('source', 'effective_from', 'account_id', 'version')) or type(self.verified) is not bool:
            raise ValueError('Cost provenance required')
        date.fromisoformat(self.effective_from)
    def total(self, quantity):
        if type(quantity) is not int or quantity < 0:
            raise ValueError('Invalid cost quantity')
        # Market-side entry uses ask/bid already: spread must not be charged again.
        fees = sum((decimal(getattr(self, key)) for key in ('b3_entry_brl', 'b3_exit_brl', 'brokerage_entry_brl', 'brokerage_exit_brl')), Decimal(0))
        return ((fees + 2*decimal(self.slippage_points)*POINT_VALUE)*quantity).quantize(CENT, rounding=ROUND_CEILING)


def compare_plans(rows, account: AccountState, costs: CostSchedule, *, max_quantity=100, estimates=None, now_ms=0, horizon_ms=60000):
    if type(max_quantity) is not int or not 1 <= max_quantity <= 10000 or type(now_ms) is not int or now_ms < 0 or type(horizon_ms) is not int or horizon_ms <= 0:
        raise ValueError('Invalid bounds')
    equity, available = decimal(account.equity_brl), decimal(account.available_margin_brl)
    margin = decimal(costs.margin_per_contract_brl)
    wait = DecisionPlan('wait', 'wait', 0, None, None, None, None, []).to_dict()
    wait.update(account_equity_brl=account.equity_brl, costs_brl='0.00', loss_brl='0.00', target_net_brl='0.00', margin_brl='0.00', expected_log_growth=0., profit_probability=None, order_sent=False, experimental=True, reason='FINANCIAL_MODEL_NOT_VALIDATED')
    plans = [wait]
    if equity <= 0 or account.positions:
        wait['reason'] = 'CAPITAL_EXHAUSTED' if equity <= 0 else 'RECONCILE_OR_CLOSE_EXISTING_POSITION'
        return plans
    for row in rows[:8]:
        side = row['side']
        entry, stop, target = [decimal(row[key], nonnegative=True) for key in ('entry_points', 'stop_points', 'target_points')]
        if side not in ('buy', 'sell') or any(x <= 0 or x % 5 for x in (entry, stop, target)) or not (stop < entry < target if side == 'buy' else target < entry < stop):
            raise ValueError('Invalid plan geometry')
        bound = min(max_quantity, int(min(available, equity)/margin))
        for quantity in range(1, bound+1):
            fee = costs.total(quantity)
            loss = abs(entry-stop)*POINT_VALUE*quantity + fee
            target_net = abs(entry-target)*POINT_VALUE*quantity - fee
            required = margin*quantity
            if required+loss > equity or required > available:
                continue
            plan = DecisionPlan(f"{row['id']}:q{quantity}", side, quantity, str(entry), str(stop), str(target), now_ms+2000, row.get('reference_evidence_ids', [])).to_dict()
            plan.update(candidate_id=row['id'], horizon_ms=horizon_ms, account_equity_brl=account.equity_brl,
                        account_revision=account.revision, costs_brl=money(fee), loss_brl=money(loss),
                        target_net_brl=money(target_net), margin_brl=money(required),
                        cost_version=costs.version, cost_verified=costs.verified, premise=row.get('premise'),
                        expected_log_growth=None, profit_probability=None, probability_interval=None,
                        order_sent=False, experimental=True, reason='FINANCIAL_MODEL_NOT_VALIDATED')
            estimate = (estimates or {}).get(row['id'])
            if isinstance(estimate, OutcomeEstimate) and estimate.validated and estimate.validation.get('temporal_holdout') is True and estimate.validation.get('deployment_approved') is True and estimate.validation.get('synthetic') is False:
                distribution = estimate.distribution
                if not distribution or abs(sum(float(x['probability']) for x in distribution)-1) > 1e-6:
                    raise ValueError('Invalid outcome probabilities')
                outcomes = []
                for outcome in distribution:
                    probability = float(outcome['probability'])
                    if not math.isfinite(probability) or not 0 <= probability <= 1:
                        raise ValueError('Invalid probability')
                    net = decimal(outcome['gross_points'])*POINT_VALUE*quantity-fee
                    outcomes.append((probability, net))
                growth = sum(p*math.log1p(float(net/equity)) for p, net in outcomes) if all(equity+net > 0 for p, net in outcomes) else -math.inf
                if math.isfinite(growth):
                    probability = sum(p for p, net in outcomes if net > 0)
                    plan.update(expected_log_growth=growth, profit_probability=probability,
                                probability_interval=estimate.probability_interval, distribution=[{'probability': p, 'net_brl': money(net)} for p, net in outcomes],
                                model_version=estimate.model_version, reason='TEMPORALLY_VALIDATED_ESTIMATE')
            plans.append(plan)
    return plans


def admissible_choices(plans, *, kelly_fraction=.25, drawdown=0.):
    if not 0 < kelly_fraction <= 1 or not 0 <= drawdown <= 1:
        raise ValueError('Invalid policy parameters')
    estimated = [p for p in plans[1:] if p.get('expected_log_growth') is not None and p['expected_log_growth'] > 0]
    if not estimated:
        return []
    best = max(estimated, key=lambda p: (p['expected_log_growth'], -p['quantity'], p['id']))
    # Smooth adaptation: 30% is a reference, never a switch or pause rule.
    ceiling = int(best['quantity']*kelly_fraction/(1+drawdown/.30))
    eligible = [p for p in estimated if p['quantity'] <= ceiling]
    return sorted(eligible, key=lambda p: (-p['expected_log_growth'], p['quantity'], p['id']))


def build_decision_choice(plans, *, kelly_fraction=.25, drawdown=0.):
    """JEV selects typed identifiers; financial numbers are immutable inputs."""
    eligible = admissible_choices(plans, kelly_fraction=kelly_fraction, drawdown=drawdown)
    if not eligible:
        return None
    # Every quantity was compared before this documented API shortlist (255 labels).
    shortlist = [plans[0], *eligible[:254]]
    state = dict(schema_version=SCHEMA_VERSION, policy_version='fractional-kelly-smooth-dd-v1',
                 compared_plan_count=len(plans), eligible_plan_count=len(eligible), plans=shortlist)
    questions = {'decision_plan': {'type': 'choice', 'instructions': 'Select exactly one immutable plan ID. Prefer net compound growth supported by current evidence. Choose wait when evidence invalidates the opportunity. Contextual confidence is not a financial profit probability. Do not change prices, quantity, costs or validity.',
                                  'criteria': {p['id']: dict(action=p['action'], quantity=p['quantity'], premise=p.get('premise'), expected_log_growth=p.get('expected_log_growth')) for p in shortlist}}}
    return state, questions


def select_plan(plans, *, kelly_fraction=.25, drawdown=0., chosen_id=None):
    wait = dict(plans[0])
    ranked = admissible_choices(plans, kelly_fraction=kelly_fraction, drawdown=drawdown)
    if not ranked:
        if any(p.get('expected_log_growth') is not None and p['expected_log_growth'] > 0 for p in plans[1:]):
            wait['reason'] = 'FRACTIONAL_KELLY_ROUNDS_TO_ZERO'
        return wait
    winner = ranked[0]
    if chosen_id is not None:
        if chosen_id == 'wait':
            return {**wait, 'reason': 'JEV_CONTEXTUAL_ABSTENTION'}
        selected = next((p for p in ranked[:254] if p['id'] == chosen_id), None)
        if selected is None:
            return {**wait, 'reason': 'JEV_SELECTION_NOT_ECONOMICALLY_ADMISSIBLE'}
        winner = selected
    return {**winner, 'policy_version': 'fractional-kelly-smooth-dd-v1', 'kelly_fraction': kelly_fraction, 'drawdown': drawdown}
