"""Synthetic acceptance tests for the replay and VAP public seams."""
from __future__ import annotations

import json
from decimal import Decimal, localcontext
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from time import time

from market_data_contract import (
    DataContractError,
    InstrumentSpec,
    MarketEnvelope,
    SCHEMA_VERSION,
    TradeEvent,
    canonical_payload_sha256,
)
from market_replay import JournalWriter, ReplaySession, RetentionPolicy, VolumeAtPrice


def synthetic_header() -> dict:
    return {
        "schema_version": "multimarket.v1",
        "adapter_version": "synthetic-fixture-v1",
        "source": {"source_id": "fixture"},
        "instrument": {"instrument_id": "fixture:BTCUSDT"},
        "origin": "synthetic",
        "permission_ref": None,
        "created_at_ms": int(time() * 1000),
    }


def fixture_instrument() -> InstrumentSpec:
    return InstrumentSpec(
        instrument_id="binance_spot:BTCUSDT",
        kind="spot",
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        settlement_currency="USDT",
        tick_size="0.01",
        quantity_step="0.0001",
    )


def fixture_trade(
    trade_id: str,
    *,
    price: str = "100.00",
    quantity: str = "0.25",
    trade_time_ms: int = 100,
    aggressor: str = "unknown",
    origin: str = "synthetic",
    receive_time_ms: int = 200,
) -> TradeEvent:
    envelope = MarketEnvelope(
        schema_version=SCHEMA_VERSION,
        provider="binance",
        venue="binance_spot",
        instrument_id="binance_spot:BTCUSDT",
        event_kind="trade",
        exchange_time_ms=trade_time_ms,
        receive_time_ms=receive_time_ms,
        receive_monotonic_ns=receive_time_ms * 1_000_000,
        origin=origin,
        session_epoch="synthetic-fixture",
        payload_sha256="0" * 64,
    )
    return TradeEvent(
        instrument_id="binance_spot:BTCUSDT",
        trade_id=trade_id,
        price=price,
        quantity=quantity,
        trade_time_ms=trade_time_ms,
        aggressor=aggressor,
        aggressor_origin="fixture",
        envelope=envelope,
    )


class JournalWriterTests(unittest.TestCase):
    def test_disabled_writer_never_creates_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "disabled.jsonl"
            writer = JournalWriter(target)

            self.assertFalse(writer.append({"record_kind": "header"}))
            writer.close()

            self.assertFalse(target.exists())
            self.assertEqual(writer.status()["state"], "disabled")

    def test_opt_in_writer_hashes_records_and_reports_disk_budget(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            dedicated = Path(folder) / "journal"
            dedicated.mkdir()
            target = dedicated / "capture.jsonl"
            writer = JournalWriter(
                target,
                policy=RetentionPolicy(enabled=True, max_bytes=4096, max_chunk_bytes=2048),
            )

            self.assertTrue(writer.append(synthetic_header()))
            payload = {"trade_id": "fixture-1", "price": "100.00", "quantity": "0.25"}
            self.assertTrue(writer.append({"record_kind": "trade", "payload": payload}))
            writer.close()

            rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[0]["schema_version"], "multimarket.v1")
            self.assertEqual(rows[1]["record_index"], 0)
            self.assertEqual(rows[1]["payload_sha256"], canonical_payload_sha256(payload))
            self.assertLessEqual(writer.status()["bytes_written"], 4096)
            self.assertEqual(writer.status()["state"], "closed")

            events = list(ReplaySession(target).events())
            self.assertEqual([event["record_kind"] for event in events], ["trade"])
            self.assertEqual(events[0]["payload"]["trade_id"], "fixture-1")

    def test_live_journal_requires_permission_before_creating_files(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            dedicated = Path(folder) / "journal"
            dedicated.mkdir()
            target = dedicated / "capture.jsonl"
            writer = JournalWriter(target, policy=RetentionPolicy(enabled=True))
            header = synthetic_header() | {"origin": "live"}

            with self.assertRaises(DataContractError):
                writer.append(header)

            self.assertFalse(target.exists())
            self.assertFalse(list(dedicated.iterdir()))

    def test_live_journal_requires_policy_permission_matching_header(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            dedicated = Path(folder) / "journal"
            dedicated.mkdir()
            header = synthetic_header() | {
                "origin": "live", "permission_ref": "permission-fixture-1"
            }
            target = dedicated / "capture.jsonl"
            writer = JournalWriter(target, policy=RetentionPolicy(enabled=True))

            with self.assertRaises(DataContractError):
                writer.append(header)

            self.assertFalse(target.exists())
            self.assertFalse(list(dedicated.iterdir()))

            allowed = JournalWriter(
                target,
                policy=RetentionPolicy(enabled=True, permission_ref="permission-fixture-1"),
            )
            self.assertTrue(allowed.append(header))
            allowed.close()

            mismatch_target = dedicated / "mismatch.jsonl"
            mismatch = JournalWriter(
                mismatch_target,
                policy=RetentionPolicy(enabled=True, permission_ref="permission-fixture-2"),
            )
            with self.assertRaises(DataContractError):
                mismatch.append(header)
            self.assertFalse(mismatch_target.exists())

    def test_age_and_disk_quotas_stop_recording_without_exceeding_limits(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            dedicated = Path(folder) / "journal"
            dedicated.mkdir()
            target = dedicated / "age.jsonl"
            with patch("market_replay.time.monotonic", side_effect=[100.0, 101.0]):
                aged = JournalWriter(
                    target,
                    policy=RetentionPolicy(enabled=True, max_age_seconds=1),
                )
                self.assertFalse(aged.append(synthetic_header()))
            self.assertEqual(aged.status()["state"], "budget_reached")
            self.assertEqual(aged.status()["reason"], "max_age_seconds")
            self.assertFalse(target.exists())

            size_target = dedicated / "size.jsonl"
            bounded = JournalWriter(
                size_target,
                policy=RetentionPolicy(enabled=True, max_bytes=512, max_chunk_bytes=512),
            )
            self.assertTrue(bounded.append(synthetic_header()))
            self.assertFalse(bounded.append({
                "record_kind": "trade", "payload": {"padding": "x" * 400}
            }))
            self.assertLessEqual(bounded.status()["bytes_written"], 512)
            self.assertEqual(bounded.status()["state"], "budget_reached")
            bounded.close()

    def test_rotated_chunks_replay_in_stored_order(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            dedicated = Path(folder) / "journal"
            dedicated.mkdir()
            target = dedicated / "capture.jsonl"
            writer = JournalWriter(
                target,
                policy=RetentionPolicy(enabled=True, max_bytes=4096, max_chunk_bytes=700),
            )
            self.assertTrue(writer.append(synthetic_header()))
            for index in range(4):
                self.assertTrue(writer.append({
                    "record_kind": "trade",
                    "payload": {"trade_id": f"fixture-{index}", "padding": "x" * 170},
                }))
            self.assertGreaterEqual(writer.status()["chunks"], 2)
            writer.close()

            replay = ReplaySession(target)
            events = list(replay.events())

            self.assertEqual([event["record_index"] for event in events], [0, 1, 2, 3])
            self.assertEqual(
                [event["payload"]["trade_id"] for event in events],
                ["fixture-0", "fixture-1", "fixture-2", "fixture-3"],
            )
            self.assertEqual(replay.status()["state"], "complete")

    def test_replay_hash_corruption_is_invalid_and_never_repaired(self) -> None:
        payload = {"trade_id": "fixture-corrupt", "price": "100", "quantity": "1"}
        corrupted = {
            "record_index": 0,
            "record_kind": "trade",
            "payload": payload,
            "payload_sha256": "0" * 64,
        }
        replay = ReplaySession([synthetic_header(), corrupted])

        with self.assertRaises(DataContractError):
            list(replay.events())

        self.assertEqual(replay.status()["state"], "invalid")
        self.assertIn("hash mismatch", replay.status()["reason"])

    def test_opt_in_path_inside_repository_is_rejected_before_write(self) -> None:
        target = Path(__file__).resolve().parent / "must-not-create.jsonl"

        with self.assertRaises(DataContractError):
            JournalWriter(target, policy=RetentionPolicy(enabled=True))

        self.assertFalse(target.exists())


class VolumeAtPriceTests(unittest.TestCase):
    def test_exact_decimal_aggregation_deduplicates_equivalent_execution(self) -> None:
        vap = VolumeAtPrice(fixture_instrument())
        self.assertTrue(vap.accept(fixture_trade("a", price="100.0", quantity="0.2")))
        self.assertFalse(vap.accept(fixture_trade(
            "a", price="100.00", quantity="0.20", receive_time_ms=999
        )))
        self.assertTrue(vap.accept(fixture_trade("b", price="100", quantity="0.5", trade_time_ms=150)))
        self.assertTrue(vap.accept(fixture_trade("c", price="101", quantity="9", trade_time_ms=200)))

        result = vap.snapshot(start_ms=100, end_ms=200)

        self.assertEqual(result["total_quantity"], "0.7")
        self.assertEqual(result["total_notional"], "70")
        self.assertEqual(result["trade_count"], 2)
        self.assertEqual(result["duplicates"], 1)
        self.assertEqual(result["unit"], "BTC")
        self.assertEqual(result["coverage"], "bounded_complete")
        self.assertFalse(result["full_tape"])
        self.assertEqual(result["levels"], [{
            "price": "100", "quantity": "0.7", "notional": "70", "trade_count": 2,
            "aggressor_counts": {"buy": 0, "sell": 0, "unknown": 2},
        }])

    def test_long_decimal_significands_are_not_rounded_by_default_context(self) -> None:
        price = "123456789012345678901234567890.12345678"
        quantity = "0.12345678901234567890123456789012"
        vap = VolumeAtPrice(fixture_instrument())
        vap.accept(fixture_trade("long-a", price=price, quantity=quantity))
        vap.accept(fixture_trade("long-b", price=price, quantity=quantity, trade_time_ms=101))

        with localcontext() as decimal_context:
            decimal_context.prec = 200
            expected_quantity = Decimal(quantity) + Decimal(quantity)
            expected_notional = Decimal(price) * expected_quantity
            format_exact = lambda value: format(value, "f").rstrip("0").rstrip(".")
            expected_quantity_text = format_exact(expected_quantity)
            expected_notional_text = format_exact(expected_notional)
        result = vap.snapshot(start_ms=100, end_ms=200)

        self.assertEqual(result["total_quantity"], expected_quantity_text)
        self.assertEqual(result["total_notional"], expected_notional_text)

    def test_decimal_exponent_spread_is_exact_within_bounded_arithmetic_budget(self) -> None:
        vap = VolumeAtPrice(fixture_instrument())
        vap.accept(fixture_trade("large", price="1", quantity="1e1000"))
        vap.accept(fixture_trade("small", price="1", quantity="1", trade_time_ms=101))

        result = vap.snapshot(start_ms=100, end_ms=200)

        expected = f"1{'0' * 999}1"
        self.assertEqual(result["total_quantity"], expected)
        self.assertEqual(result["total_notional"], expected)

    def test_decimal_expansion_over_budget_is_rejected_before_mutation(self) -> None:
        vap = VolumeAtPrice(fixture_instrument())

        with self.assertRaises(DataContractError):
            vap.accept(fixture_trade("huge", price="1", quantity="1e5000"))

        self.assertEqual(vap.status()["trade_count"], 0)
        self.assertTrue(vap.status()["valid"])
        self.assertEqual(vap.status()["resource_rejections"], 1)
        self.assertEqual(vap.snapshot(start_ms=0, end_ms=200)["coverage"], "partial")
        self.assertIn("decimal_resource_budget", vap.snapshot(start_ms=0, end_ms=200)["missing"])

    def test_conflicting_duplicate_invalidates_the_snapshot(self) -> None:
        vap = VolumeAtPrice(fixture_instrument())
        vap.accept(fixture_trade("same", quantity="1"))

        with self.assertRaises(DataContractError):
            vap.accept(fixture_trade("same", quantity="2"))

        result = vap.snapshot(start_ms=0, end_ms=200)
        self.assertEqual(result["conflicts"], 1)
        self.assertEqual(result["coverage"], "invalid")
        self.assertIn("conflicting_duplicate", result["missing"])
        self.assertFalse(vap.status()["valid"])

    def test_eviction_is_bounded_and_visible_as_partial_coverage(self) -> None:
        vap = VolumeAtPrice(fixture_instrument(), max_trades=2, max_levels=2)
        vap.accept(fixture_trade("old", price="100", quantity="1", trade_time_ms=100))
        vap.accept(fixture_trade("mid", price="101", quantity="2", trade_time_ms=101))
        vap.accept(fixture_trade("new", price="102", quantity="3", trade_time_ms=102))

        result = vap.snapshot(start_ms=0, end_ms=200)

        self.assertEqual(result["evictions"], 1)
        self.assertEqual(result["trade_count"], 2)
        self.assertEqual(result["total_quantity"], "5")
        self.assertEqual(result["coverage"], "partial")
        self.assertIn("evictions", result["missing"])

    def test_live_trade_coverage_is_partial_and_interval_is_semi_open(self) -> None:
        vap = VolumeAtPrice(fixture_instrument())
        vap.accept(fixture_trade("inside", trade_time_ms=100, origin="live"))
        vap.accept(fixture_trade("at-end", trade_time_ms=200, origin="live"))

        result = vap.snapshot(start_ms=100, end_ms=200)

        self.assertEqual(result["trade_count"], 1)
        self.assertEqual(result["levels"][0]["aggressor_counts"]["unknown"], 1)
        self.assertEqual(result["coverage"], "partial")
        self.assertIn("live_partial_tape", result["missing"])

    def test_snapshot_rejects_windows_longer_than_five_minutes(self) -> None:
        vap = VolumeAtPrice(fixture_instrument())
        with self.assertRaises(DataContractError):
            vap.snapshot(start_ms=0, end_ms=300_001)


class ReplaySessionTests(unittest.TestCase):
    def test_replay_rejects_missing_or_out_of_order_record_index(self) -> None:
        payload = {"trade_id": "fixture-2", "price": "101", "quantity": "1"}
        row = {
            "record_index": 1,
            "record_kind": "trade",
            "payload": payload,
            "payload_sha256": canonical_payload_sha256(payload),
        }
        replay = ReplaySession([synthetic_header(), row])

        with self.assertRaises(DataContractError):
            list(replay.events())

        self.assertEqual(replay.status()["state"], "invalid")

    def test_replay_keeps_gap_in_stored_order_and_reports_degraded_status(self) -> None:
        payloads = [
            ("gap", {"expected": 4, "received": 6}),
            ("trade", {"trade_id": "fixture-3", "price": "102", "quantity": "2"}),
        ]
        rows = [synthetic_header()]
        for index, (kind, payload) in enumerate(payloads):
            rows.append({
                "record_index": index,
                "record_kind": kind,
                "payload": payload,
                "payload_sha256": canonical_payload_sha256(payload),
            })
        replay = ReplaySession(rows)

        events = list(replay.events())

        self.assertEqual([event["record_kind"] for event in events], ["gap", "trade"])
        self.assertEqual(replay.status()["gaps"], 1)
        self.assertFalse(replay.status()["valid"])
        self.assertEqual(replay.status()["state"], "degraded")


if __name__ == "__main__":
    unittest.main()
