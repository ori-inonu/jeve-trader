from __future__ import annotations

import unittest
import tempfile
from decimal import Decimal
from pathlib import Path

from multimarket.contracts import (
    EvaluationIdentity,
    EventEnvelope,
    InstrumentSpec,
    Registry,
    SourceCapabilities,
    decimal_text,
)
from multimarket.market_state import MarketState
from multimarket.accounts import AccountLedger
from multimarket.risk import RiskPolicy, evaluate_quantities

_USE_DEFAULT = object()


def instrument(*, instrument_id="spot:BTCUSDT", venue="binance", symbol="BTCUSDT", tick="0.01", step="0.00001", family="spot", verified=True):
    return InstrumentSpec(
        instrument_id=instrument_id,
        venue=venue,
        segment="spot",
        symbol=symbol,
        family=family,
        metadata_version="exchangeInfo:1",
        price_tick=Decimal(tick),
        quantity_step=Decimal(step),
        quantity_min=Decimal(step),
        minimum_notional=Decimal("10"),
        contract_multiplier=Decimal("1"),
        base_asset="BTC",
        quote_currency="USDT",
        settlement_currency="USDT",
        expiry_at_ms=None,
        calendar_id="24x7",
        status="trading",
        constraints_verified=verified,
    )


def source(source_id="binance_public_spot", *, sequence_scope="unknown"):
    return SourceCapabilities(
        source_id=source_id,
        version="1",
        quote=True,
        trades=True,
        book=False,
        account=False,
        trade_semantics="individual",
        side_semantics="aggressor",
        sequence_scope=sequence_scope,
        book_mode="unavailable",
        full_tape=False,
        retention="unknown",
        export="unknown",
    )


class FakeClock:
    def __init__(self, wall_ms=1_000, monotonic_ns=1_000_000_000):
        self.wall = wall_ms
        self.monotonic = monotonic_ns

    def wall_ms(self):
        return self.wall

    def monotonic_ns(self):
        return self.monotonic


def market_event(*, kind="quote", event_id="q-1", epoch=3, metadata_version="exchangeInfo:1", sequence=None, market_ts_ms=1_000, received_monotonic_ns=1_000_000_000, payload=None, workspace_id="w1"):
    if payload is None:
        payload = {"bid": "100", "ask": "101", "bid_quantity": "1", "ask_quantity": "2"}
    return EventEnvelope(
        workspace_id=workspace_id,
        instrument_id="spot:BTCUSDT",
        source_id="binance_public_spot",
        epoch=epoch,
        metadata_version=metadata_version,
        event_id=event_id,
        kind=kind,
        market_ts_ms=market_ts_ms,
        received_at_ms=1_000,
        received_monotonic_ns=received_monotonic_ns,
        sequence_first=sequence,
        sequence_last=sequence,
        payload=payload,
    )


class ContractTests(unittest.TestCase):
    def test_decimal_wire_contract_is_finite_and_rejects_float(self):
        self.assertEqual(decimal_text(Decimal("0.0100")), "0.01")
        with self.assertRaises((TypeError, ValueError)):
            decimal_text(0.01)
        with self.assertRaises((TypeError, ValueError)):
            decimal_text(Decimal("NaN"))

    def test_instrument_and_source_round_trip_without_losing_identity(self):
        spec = instrument()
        caps = source()
        self.assertEqual(InstrumentSpec.from_wire(spec.to_wire()), spec)
        self.assertEqual(SourceCapabilities.from_wire(caps.to_wire()), caps)
        self.assertEqual(spec.to_wire()["price_tick"], "0.01")
        self.assertFalse(caps.to_wire()["full_tape"])

    def test_event_round_trip_and_evaluation_identity_include_account_id(self):
        event = EventEnvelope(
            workspace_id="w1",
            instrument_id="spot:BTCUSDT",
            source_id="binance_public_spot",
            epoch=3,
            metadata_version="exchangeInfo:1",
            event_id="q-1",
            kind="quote",
            market_ts_ms=1000,
            received_at_ms=1001,
            received_monotonic_ns=100_000,
            sequence_first=None,
            sequence_last=None,
            payload={"bid": "100", "ask": "101", "bid_quantity": "1", "ask_quantity": "2"},
        )
        self.assertEqual(EventEnvelope.from_wire(event.to_wire()), event)
        no_exchange_time = market_event(market_ts_ms=None)
        self.assertIsNone(EventEnvelope.from_wire(no_exchange_time.to_wire()).market_ts_ms)
        identity = EvaluationIdentity(
            workspace_id="w1",
            instrument_id="spot:BTCUSDT",
            source_id="binance_public_spot",
            epoch=3,
            metadata_version="exchangeInfo:1",
            feature_version="features-1",
            question_version="questions-1",
            cost_revision=4,
            account_id="paper-a",
            account_revision=5,
            selection_revision=2,
            event_range=("q-1", "q-4"),
            received_monotonic_ns=200_000,
        )
        self.assertEqual(EvaluationIdentity.from_wire(identity.to_wire()), identity)
        self.assertEqual(identity.to_wire()["account_id"], "paper-a")
        anonymous = EvaluationIdentity.from_wire({**identity.to_wire(), "account_id": None, "account_revision": None})
        self.assertIsNone(anonymous.account_id)
        self.assertIsNone(anonymous.account_revision)

    def test_registry_keeps_same_symbol_separate_by_venue_and_account(self):
        registry = Registry()
        registry.register_instrument(instrument())
        registry.register_instrument(instrument(instrument_id="other:BTCUSDT", venue="other"))
        registry.register_source(source())
        registry.register_source(source("other_public"))
        first = registry.open_workspace(source_id="binance_public_spot", instrument_id="spot:BTCUSDT", account_id="paper-a")
        second = registry.open_workspace(source_id="other_public", instrument_id="other:BTCUSDT", account_id=None)
        registry.select(second.workspace_id)
        self.assertNotEqual(first.workspace_id, second.workspace_id)
        self.assertEqual(registry.get_workspace(first.workspace_id).account_id, "paper-a")
        self.assertEqual(registry.get_instrument("other:BTCUSDT").venue, "other")
        self.assertEqual(registry.snapshot()["selected_workspace_id"], second.workspace_id)


class MarketStateTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.state = MarketState(instrument(), source(sequence_scope="per_domain"), clock=self.clock, workspace_id="w1", epoch=3)

    def test_duplicate_event_is_idempotent(self):
        first = market_event(sequence=10)
        self.assertTrue(self.state.ingest(first).applied)
        duplicate = market_event(event_id="q-1", sequence=10, payload={"bid": "90", "ask": "91", "bid_quantity": "3", "ask_quantity": "4"})
        result = self.state.ingest(duplicate)
        self.assertTrue(result.duplicate)
        self.assertFalse(result.applied)
        self.assertEqual(self.state.snapshot()["quote"]["bid"], "100")

    def test_sequence_gap_invalidates_and_requires_new_epoch_evidence(self):
        self.state.ingest(market_event(event_id="q-10", sequence=10))
        result = self.state.ingest(market_event(event_id="q-12", sequence=12))
        self.assertTrue(result.resync_required)
        self.assertIn("sequence_gap", result.reasons)
        self.assertEqual(result.epoch, 4)
        self.assertIsNone(self.state.snapshot()["quote"])
        self.assertFalse(self.state.ingest(market_event(event_id="old", epoch=3, sequence=11)).applied)
        self.assertTrue(self.state.ingest(market_event(event_id="new", epoch=4, sequence=100)).applied)

    def test_sequence_regression_invalidates(self):
        self.state.ingest(market_event(event_id="q-10", sequence=10))
        result = self.state.ingest(market_event(event_id="q-9", sequence=9))
        self.assertTrue(result.resync_required)
        self.assertIn("sequence_regression", result.reasons)
        self.assertEqual(result.epoch, 4)

    def test_unknown_sequence_scope_does_not_claim_gap_detection(self):
        state = MarketState(instrument(), source(sequence_scope="unknown"), clock=self.clock, workspace_id="w1", epoch=3)
        state.ingest(market_event(event_id="q-1", sequence=1))
        result = state.ingest(market_event(event_id="q-999", sequence=999))
        self.assertTrue(result.applied)
        self.assertFalse(result.resync_required)

    def test_features_are_bounded_observations_and_never_assert_full_tape(self):
        self.state.ingest(market_event(sequence=10))
        trade = market_event(
            kind="trade",
            event_id="t-1",
            sequence=1,
            payload={"price": "100.5", "quantity": "0.2", "aggressor": "buy"},
        )
        self.state.ingest(trade)
        snapshot = self.state.snapshot()
        self.assertEqual(snapshot["quote"]["received_monotonic_ns"], 1_000_000_000)
        self.assertEqual(snapshot["features"]["version"], "mm-features-v1")
        self.assertEqual(snapshot["features"]["trade_count"], 1)
        self.assertEqual(snapshot["features"]["buy_quantity"], "0.2")
        self.assertEqual(snapshot["features"]["sell_quantity"], "0")
        self.assertEqual(snapshot["features"]["spread"], "1")
        self.assertEqual(snapshot["features"]["event_range"], ["t-1", "t-1"])
        self.assertFalse(snapshot["full_tape"])

    def test_recent_trade_buffer_matches_the_frozen_200_trade_bound(self):
        for index in range(201):
            event = market_event(
                kind="trade",
                event_id=f"t-{index}",
                sequence=index + 1,
                payload={"price": "100.5", "quantity": "0.2", "aggressor": "buy"},
            )
            self.assertTrue(self.state.ingest(event).applied)

        snapshot = self.state.snapshot()
        self.assertEqual(len(snapshot["recent_trades"]), 200)
        self.assertEqual(snapshot["features"]["trade_count"], 200)
        self.assertEqual(snapshot["features"]["event_range"], ["t-1", "t-200"])

    def test_l1_capability_never_becomes_l2_book(self):
        caps = SourceCapabilities(**{**source().to_wire(), "book": True, "book_mode": "l1"})
        state = MarketState(instrument(), caps, clock=self.clock, workspace_id="w1", epoch=3)
        event = market_event(kind="book", event_id="b-1", payload={"bids": [], "asks": []})
        result = state.ingest(event)
        self.assertFalse(result.applied)
        self.assertIn("book_unavailable", result.reasons)
        self.assertEqual(state.snapshot()["health"]["book"]["status"], "unavailable")

    def test_metadata_change_invalidates_market_state(self):
        self.state.ingest(market_event(sequence=10))
        changed = market_event(event_id="new-metadata", epoch=3, metadata_version="exchangeInfo:2", sequence=11)
        result = self.state.ingest(changed)
        self.assertTrue(result.resync_required)
        self.assertIn("metadata_version_changed", result.reasons)
        self.assertEqual(result.epoch, 4)
        self.assertIsNone(self.state.snapshot()["quote"])

    def test_quote_freshness_uses_monotonic_clock_not_wall_clock(self):
        self.state.ingest(market_event(sequence=10))
        self.clock.monotonic += 6_000_000_000
        self.clock.wall -= 86_400_000
        snapshot = self.state.snapshot()
        self.assertIsNone(snapshot["quote"])
        self.assertEqual(snapshot["health"]["quote"]["status"], "stale")
        self.assertEqual(snapshot["health"]["quote"]["reason"], "quote_stale")
        self.assertEqual(snapshot["health"]["quote"]["age_ms"], 6_000)

    def test_delayed_book_invalidates_only_book_domain(self):
        caps = source(sequence_scope="per_domain")
        caps = SourceCapabilities(**{**caps.to_wire(), "book": True, "book_mode": "l2"})
        state = MarketState(instrument(), caps, clock=self.clock, workspace_id="w1", epoch=3)
        state.ingest(market_event(kind="book", event_id="b-1", sequence=10, payload={"bids": [["99", "1"]], "asks": [["101", "1"]]}))
        delayed = market_event(kind="book", event_id="b-2", sequence=11, market_ts_ms=999, payload={"bids": [["98", "1"]], "asks": [["102", "1"]]})
        result = state.ingest(delayed)
        self.assertTrue(result.resync_required)
        self.assertIn("delayed_event", result.reasons)
        self.assertIsNone(state.snapshot()["book"])
        self.assertEqual(state.snapshot()["health"]["book"]["status"], "stale")


def account_snapshot(*, revision=1, balances=None, positions=None, received_monotonic_ns=1_000_000_000, asof_ms=1_000, status="reconciled"):
    return {
        "account_id": "paper-a",
        "revision": revision,
        "mode": "manual",
        "status": status,
        "asof_ms": asof_ms,
        "received_monotonic_ns": received_monotonic_ns,
        "balances": balances if balances is not None else {"USDT": "1000"},
        "positions": positions if positions is not None else {},
    }


def account_fill(*, fill_id="fill-1", revision=2, received_monotonic_ns=2_000_000_000, quantity="0.1", price="10000"):
    return {
        "account_id": "paper-a",
        "fill_id": fill_id,
        "revision": revision,
        "instrument_id": "spot:BTCUSDT",
        "quantity": quantity,
        "price": price,
        "side": "buy",
        "currency": "USDT",
        "occurred_at_ms": 1_001,
        "received_monotonic_ns": received_monotonic_ns,
    }


class AccountLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.path = Path(self.tempdir.name) / "accounts.sqlite3"
        self.clock = FakeClock()
        self.ledger = AccountLedger(self.path, clock=self.clock)
        self.addCleanup(self.ledger.close)

    def test_reconcile_and_expiry_use_monotonic_receive_time(self):
        result = self.ledger.reconcile(account_snapshot())
        self.assertTrue(result["applied"])
        current = self.ledger.view("paper-a")
        self.assertEqual(current["status"], "reconciled")
        self.assertEqual(current["balances"], {"USDT": "1000"})
        self.clock.monotonic += 60_001_000_000
        self.clock.wall -= 86_400_000
        current = self.ledger.view("paper-a")
        self.assertEqual(current["status"], "stale")
        self.assertEqual(current["reason"], "account_snapshot_expired")
        self.assertEqual(current["age_ms"], 60_001)

    def test_fill_is_persisted_once_and_requires_reconciliation(self):
        self.ledger.reconcile(account_snapshot())
        self.clock.monotonic += 1_000_000_000
        fill = account_fill()
        first = self.ledger.ingest_fill(fill)
        self.assertTrue(first["applied"])
        self.assertEqual(self.ledger.view("paper-a")["status"], "stale")
        self.assertEqual(self.ledger.view("paper-a")["reason"], "fill_requires_reconciliation")
        self.assertEqual(self.ledger.view("paper-a")["positions"]["spot:BTCUSDT"]["quantity"], "0.1")
        self.ledger.close()
        reopened = AccountLedger(self.path, clock=self.clock)
        self.addCleanup(reopened.close)
        duplicate = reopened.ingest_fill(fill)
        self.assertTrue(duplicate["duplicate"])
        self.assertFalse(duplicate["applied"])
        self.assertEqual(reopened.view("paper-a")["positions"]["spot:BTCUSDT"]["quantity"], "0.1")

    def test_out_of_order_snapshot_does_not_replace_newer_balance(self):
        self.ledger.reconcile(account_snapshot(revision=2, balances={"USDT": "900"}))
        result = self.ledger.reconcile(account_snapshot(revision=1, balances={"USDT": "1000"}))
        self.assertEqual(result["status"], "stale")
        current = self.ledger.view("paper-a")
        self.assertEqual(current["balances"], {"USDT": "900"})
        self.assertEqual(current["status"], "stale")

    def test_same_revision_conflicting_snapshot_is_visible(self):
        self.ledger.reconcile(account_snapshot())
        result = self.ledger.reconcile(account_snapshot(balances={"USDT": "999"}, asof_ms=1_001))
        self.assertEqual(result["status"], "conflicted")
        self.assertEqual(self.ledger.view("paper-a")["reason"], "revision_conflict")

    def test_fill_without_account_baseline_is_rejected(self):
        result = self.ledger.ingest_fill(account_fill(received_monotonic_ns=self.clock.monotonic))
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["reason"], "account_not_reconciled")

    def test_persisted_monotonic_clock_reset_expires_snapshot(self):
        self.ledger.reconcile(account_snapshot())
        self.ledger.close()
        reboot_clock = FakeClock(monotonic_ns=100_000_000)
        rebooted = AccountLedger(self.path, clock=reboot_clock)
        self.addCleanup(rebooted.close)
        current = rebooted.view("paper-a")
        self.assertEqual(current["status"], "stale")
        self.assertEqual(current["reason"], "monotonic_clock_reset")
        self.assertIsNone(current["age_ms"])


class RiskTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.clock = FakeClock()
        self.ledger = AccountLedger(Path(self.tempdir.name) / "risk.sqlite3", clock=self.clock)
        self.addCleanup(self.ledger.close)
        self.ledger.reconcile(account_snapshot())
        self.policy = RiskPolicy(currency="USDT", max_quantity=Decimal("1"), max_cash_risk=Decimal("2"))
        self.costs = {"currency": "USDT", "verified": True, "fee_rate": Decimal("0.001"), "slippage": Decimal("0.1")}

    def model_gate(self, **overrides):
        gate = {
            "approved": True,
            "instrument_id": "spot:BTCUSDT",
            "venue": "binance",
            "metadata_version": "exchangeInfo:1",
            "horizon": "1m",
            "origin": "local-temporal-evaluation",
            "evidence_id": "holdout-2026-01",
            "temporal_evaluation": {
                "no_leakage": True,
                "comparators": ["rules", "context", "quantitative", "jev"],
            },
            "profit_probability": Decimal("0.7"),
        }
        gate.update(overrides)
        return gate

    def evaluate(self, *, spec=None, account=_USE_DEFAULT, costs=_USE_DEFAULT, quantities=None, model_gate=None, entry="100", stop="90", target="120", side="buy"):
        return evaluate_quantities(
            spec or instrument(),
            self.ledger.view("paper-a") if account is _USE_DEFAULT else account,
            self.costs if costs is _USE_DEFAULT else costs,
            policy=self.policy,
            entry_price=Decimal(entry),
            stop_price=Decimal(stop),
            target_price=Decimal(target) if target is not None else None,
            side=side,
            quantities=quantities,
            model_gate=model_gate,
        )

    def test_zero_quantity_is_first_and_decimal_risk_is_deterministic(self):
        rows = self.evaluate(quantities=[Decimal("0.1"), Decimal("0.5")], model_gate=self.model_gate())
        self.assertEqual(rows[0]["action"], "wait")
        self.assertEqual(rows[0]["quantity"], "0")
        self.assertIsNone(rows[0]["net_profit"])
        self.assertEqual(rows[1]["quantity"], "0.1")
        self.assertEqual(rows[1]["max_loss"], "1.039")
        self.assertEqual(rows[1]["net_profit"], "1.061")
        self.assertTrue(rows[1]["quantity_recommended"])
        self.assertEqual(rows[2]["reason"], "cash_risk_limit")
        self.assertFalse(rows[2]["quantity_recommended"])

    def test_default_candidates_start_at_minimum_notional_and_respect_bound(self):
        rows = self.evaluate(model_gate=self.model_gate())
        self.assertEqual(rows[0]["quantity"], "0")
        self.assertEqual(rows[1]["quantity"], "0.1")
        self.assertTrue(rows[1]["quantity_recommended"])

    def test_unapproved_model_never_supplies_probability_or_recommendation(self):
        gate = self.model_gate(approved=False, confidence=Decimal("0.999"))
        rows = self.evaluate(quantities=[Decimal("0.1")], model_gate=gate)
        self.assertEqual(rows[1]["action"], "wait")
        self.assertIsNone(rows[1]["profit_probability"])
        self.assertIsNone(rows[1]["net_profit"])
        self.assertFalse(rows[1]["quantity_recommended"])
        self.assertEqual(rows[1]["reason"], "model_not_approved")

    def test_model_gate_requires_exact_scope_and_temporal_comparators(self):
        mismatch = self.model_gate(venue="other")
        no_baselines = self.model_gate(temporal_evaluation={"no_leakage": True, "comparators": ["jev"]})
        for gate in (mismatch, no_baselines):
            rows = self.evaluate(quantities=[Decimal("0.1")], model_gate=gate)
            self.assertIsNone(rows[1]["profit_probability"])
            self.assertFalse(rows[1]["quantity_recommended"])
            self.assertIn(rows[1]["reason"], {"model_scope_mismatch", "model_evidence_incomplete"})

    def test_missing_costs_or_stale_account_blocks_quantity_and_net_profit(self):
        missing_cost_rows = self.evaluate(costs=None, quantities=[Decimal("0.1")], model_gate=self.model_gate())
        self.assertEqual(len(missing_cost_rows), 1)
        self.assertEqual(missing_cost_rows[0]["reason"], "costs_unavailable")
        self.assertIsNone(missing_cost_rows[0]["net_profit"])
        stale_account = {**self.ledger.view("paper-a"), "status": "stale"}
        stale_rows = self.evaluate(account=stale_account, quantities=[Decimal("0.1")], model_gate=self.model_gate())
        self.assertEqual(len(stale_rows), 1)
        self.assertEqual(stale_rows[0]["reason"], "account_not_reconciled")
        self.assertIsNone(stale_rows[0]["net_profit"])

    def test_unknown_or_invalid_account_age_fails_closed_even_with_approved_model(self):
        account = self.ledger.view("paper-a")
        invalid_ages = (None, True, -1, 60_001, "0")
        for age in invalid_ages:
            with self.subTest(age=age):
                rows = self.evaluate(
                    account={**account, "age_ms": age},
                    quantities=[Decimal("0.1")],
                    model_gate=self.model_gate(),
                )
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["reason"], "account_not_reconciled")
                self.assertFalse(rows[0]["quantity_recommended"])

        account_without_age = dict(account)
        account_without_age.pop("age_ms", None)
        rows = self.evaluate(account=account_without_age, quantities=[Decimal("0.1")], model_gate=self.model_gate())
        self.assertEqual(rows[0]["reason"], "account_not_reconciled")
        self.assertFalse(rows[0]["quantity_recommended"])

    def test_tick_step_currency_and_metadata_gates_fail_closed(self):
        changed = instrument(tick="0.1", step="0.01")
        off_tick = self.evaluate(spec=changed, entry="100.05", quantities=[Decimal("0.1")], model_gate=self.model_gate(metadata_version="exchangeInfo:1"))
        self.assertEqual(len(off_tick), 1)
        self.assertEqual(off_tick[0]["reason"], "price_tick_mismatch")
        off_step = self.evaluate(spec=changed, quantities=[Decimal("0.105")], model_gate=self.model_gate())
        self.assertEqual(off_step[1]["reason"], "quantity_step_mismatch")
        bad_currency = {**self.costs, "currency": "EUR"}
        currency_rows = self.evaluate(costs=bad_currency, quantities=[Decimal("0.1")], model_gate=self.model_gate())
        self.assertEqual(currency_rows[0]["reason"], "currency_mismatch")
        unknown_constraints = self.evaluate(spec=instrument(verified=False), quantities=[Decimal("0.1")], model_gate=self.model_gate())
        self.assertEqual(unknown_constraints[0]["reason"], "instrument_constraints_unverified")

    def test_spot_sell_cannot_exceed_reconciled_position(self):
        self.ledger.reconcile(account_snapshot(revision=2, positions={"spot:BTCUSDT": "0.2"}))
        self.policy = RiskPolicy(currency="USDT", max_quantity=Decimal("1"), max_cash_risk=Decimal("10"))
        rows = self.evaluate(side="sell", entry="100", stop="110", target="80", quantities=[Decimal("0.3")], model_gate=self.model_gate())
        self.assertEqual(rows[1]["reason"], "position_limit")
        self.assertFalse(rows[1]["quantity_recommended"])

    def test_spot_sell_needs_position_not_quote_currency_cash(self):
        self.ledger.reconcile(account_snapshot(revision=2, balances={"USDT": "0"}, positions={"spot:BTCUSDT": "0.2"}))
        rows = self.evaluate(side="sell", entry="100", stop="110", target="80", quantities=[Decimal("0.1")], model_gate=self.model_gate())
        self.assertEqual(rows[1]["reason"], "positive_expected_value")
        self.assertTrue(rows[1]["quantity_recommended"])


if __name__ == "__main__":
    unittest.main()
