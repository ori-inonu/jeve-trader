from __future__ import annotations

import unittest
from decimal import Decimal

from multimarket.contracts import (
    EvaluationIdentity,
    EventEnvelope,
    InstrumentSpec,
    Registry,
    SourceCapabilities,
    decimal_text,
)


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


if __name__ == "__main__":
    unittest.main()
