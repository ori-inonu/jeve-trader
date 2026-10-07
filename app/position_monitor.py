"""Mark-to-market and observed crossings are alerts, never fills."""
from decision_engine import decimal, money, POINT_VALUE


def monitor_position(account, *, price, price_at_ms, now_ms, costs, context_status):
    if not account.positions:return None
    p=account.positions[0];alerts=[];gross=None;net=None
    fresh=type(price_at_ms) is int and 0<=now_ms-price_at_ms<=2000 and price is not None
    if fresh:
        price=decimal(price,nonnegative=True)
        direction=1 if p['side']=='buy' else -1
        gross=(price-decimal(p['entry_points']))*direction*POINT_VALUE*p['quantity']
        exit_cost=(decimal(costs.b3_exit_brl)+decimal(costs.brokerage_exit_brl)+decimal(costs.slippage_points)*POINT_VALUE)*p['quantity']
        net=gross-exit_cost
        if p.get('stop_points') and (price-decimal(p['stop_points']))*direction<=0:alerts.append('STOP_CROSSED_OBSERVED')
        if p.get('target_points') and (price-decimal(p['target_points']))*direction>=0:alerts.append('TARGET_CROSSED_OBSERVED')
    else:alerts.append('MARK_PRICE_UNAVAILABLE_OR_STALE')
    if context_status in ('incompatible','expired','unavailable'):alerts.append('CONTEXT_INVALIDATED')
    return dict(position=p,realized_brl=p.get('realized_brl','0.00'),open_gross_estimated_brl=money(gross) if gross is not None else None,
                open_net_estimated_brl=money(net) if net is not None else None,mark_price_points=str(price) if fresh else None,
                mark_at_ms=price_at_ms,alerts=alerts,alerts_are_executions=False,
                estimate_scope='remaining_quantity_after_estimated_exit_costs; actual_entry_fees_already_realized')
