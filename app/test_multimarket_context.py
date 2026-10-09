"""Synthetic acceptance tests for the pure, bounded multimarket context."""
from __future__ import annotations

import json
import unittest

from market_data_contract import (
    BookView,
    FeedBatch,
    InstrumentSpec,
    SCHEMA_VERSION,
    SourceDescriptor,
    SourceHealth,
)
from multimarket_context import build_multimarket_context


def sample_batch(*, with_book: bool = True) -> FeedBatch:
    instrument = InstrumentSpec(
        instrument_id="binance_spot:BTCUSDT",
        kind="spot",
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        settlement_currency="USDT",
        tick_size="0.01",
        quantity_step="0.0001",
    )
    source = SourceDescriptor(
        source_id="binance_spot_public_btcusdt_v1",
        provider="binance",
        venue="binance_spot",
        market="spot",
        endpoint_version="v1",
        endpoints=("https://example.invalid/public",),
        auth_required=False,
        terms_url="https://example.invalid/terms",
        retention_permission="unknown",
        redistribution_permission="unknown",
        jurisdiction=None,
        cadence_ms=100,
        as_of_ms=1_700_000_000_000,
        evidence_refs=("fixture-ref-1",),
    )
    book = BookView(
        instrument_id=instrument.instrument_id,
        state="live",
        valid=True,
        last_update_id=4,
        bids=tuple((str(1000 - index), "1") for index in range(30)),
        asks=tuple((str(1001 + index), "2") for index in range(30)),
        depth_limit=1000,
        coverage="partial",
        checksum_status="not_provided",
    ) if with_book else None
    health = SourceHealth(
        channel="trades",
        connected=True,
        state="live",
        valid=True,
        stale=False,
        coverage="partial",
        last_exchange_time_ms=1_700_000_000_000,
        last_receive_time_ms=1_700_000_000_001,
        last_receive_monotonic_ns=1234,
        sequence_ok=True,
        gaps=0,
        resyncs=0,
        dropped_events=0,
        dropped_bytes=0,
        reason="",
        metrics={"received": 30, "unsafe_cookie": "synthetic-secret"},
    )
    return FeedBatch(
        source=source,
        instrument=instrument,
        trades=(),
        book=book,
        health=(health,),
    )


class MultimarketContextTests(unittest.TestCase):
    def test_required_fields_are_observational_and_probabilities_default_to_none(self) -> None:
        context = build_multimarket_context(sample_batch(), as_of_ms=1_700_000_000_100)

        self.assertEqual(context["schema_version"], SCHEMA_VERSION)
        self.assertEqual(context["as_of_ms"], 1_700_000_000_100)
        self.assertEqual(context["allowed_actions"], ["wait", "observe"])
        self.assertIsNone(context["jev_comment"])
        self.assertIsNone(context["profit_probability"])
        self.assertIsNone(context["target_probability"])
        self.assertIn("source", context)
        self.assertIn("instrument", context)
        self.assertIn("health", context)
        self.assertIn("missing", context)
        self.assertIn("evidence_refs", context)

    def test_book_and_vap_are_limited_to_top_twenty_without_reordering(self) -> None:
        levels = [{
            "price": str(100 + index), "quantity": "1", "notional": str(100 + index),
            "trade_count": 1,
        } for index in range(30)]
        vap = {
            "unit": "BTC", "coverage": "partial", "full_tape": False,
            "total_quantity": "30", "total_notional": "3435", "trade_count": 30,
            "levels": levels,
        }

        context = build_multimarket_context(
            sample_batch(), features={"volume_at_price": vap}, as_of_ms=100
        )

        self.assertEqual(len(context["features"]["book"]["bids"]), 20)
        self.assertEqual(len(context["features"]["book"]["asks"]), 20)
        self.assertEqual(len(context["features"]["volume_at_price"]["levels"]), 20)
        self.assertEqual(context["features"]["volume_at_price"]["levels"][0]["price"], "100")
        self.assertTrue(context["truncated"])
        self.assertIn("volume_at_price_levels_truncated", context["missing"])

    def test_context_is_sanitized_and_bounded_when_inputs_are_large(self) -> None:
        context = build_multimarket_context(
            sample_batch(),
            features={
                "indicator": "x" * 100_000,
                "oversized_integer": 1 << 16_000,
                "api_key": "must-not-leak",
                "raw_payload": {"secret": "must-not-leak"},
            },
            economics={"account_balance": "must-not-leak", "risk_limit": "0.1"},
            as_of_ms=100,
        )
        encoded = json.dumps(context, ensure_ascii=False, allow_nan=False).encode("utf-8")

        self.assertLessEqual(len(encoded), 64 * 1024)
        self.assertTrue(context["truncated"])
        self.assertIn("context_truncated", context["missing"])
        serialized = encoded.decode("utf-8")
        self.assertNotIn("must-not-leak", serialized)
        self.assertNotIn("unsafe_cookie", serialized)

    def test_missing_book_is_visible_and_javascript_values_are_not_accepted(self) -> None:
        context = build_multimarket_context(sample_batch(with_book=False), as_of_ms=100)

        self.assertIsNone(context["features"]["book"])
        self.assertIn("book_missing", context["missing"])


if __name__ == "__main__":
    unittest.main()
