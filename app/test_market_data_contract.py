import json
import unittest
from decimal import Decimal

from market_data_contract import (
    BookDelta,
    BookSnapshot,
    DataContractError,
    FeedBatch,
    InstrumentSpec,
    MarketEnvelope,
    SCHEMA_VERSION,
    SourceDescriptor,
    SourceHealth,
    TradeEvent,
    decimal_value,
)


def envelope(kind="trade", payload_hash="a" * 64, first_sequence=10, last_sequence=11):
    return MarketEnvelope(
        schema_version=SCHEMA_VERSION,
        provider="binance",
        venue="binance_spot",
        instrument_id="binance_spot:BTCUSDT",
        event_kind=kind,
        exchange_time_ms=1700000000000,
        receive_time_ms=1700000000001,
        receive_monotonic_ns=4000000000,
        origin="synthetic",
        session_epoch="test-epoch",
        payload_sha256=payload_hash,
        sequence_namespace="depth",
        first_sequence=first_sequence,
        last_sequence=last_sequence,
    )


def instrument():
    return InstrumentSpec(
        instrument_id="binance_spot:BTCUSDT",
        kind="spot",
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        settlement_currency="USDT",
        tick_size="0.010000",
        quantity_step="0.00001000",
        as_of_ms=1700000000000,
        metadata={"filters": {"PRICE_FILTER": "0.010000"}},
    )


class DecimalContractTests(unittest.TestCase):
    def test_decimal_values_are_exact_and_strictly_string_typed(self):
        self.assertEqual(decimal_value("0.00001000"), Decimal("0.00001000"))
        self.assertEqual(decimal_value("0", allow_zero=True), Decimal("0"))
        for invalid in (0.1, True, "", "NaN", "Infinity", "-0.01", "0"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(DataContractError):
                    decimal_value(invalid)

    def test_decimal_string_lexical_limit_is_enforced(self):
        with self.assertRaises(DataContractError):
            decimal_value("1" * 129)


class JsonContractTests(unittest.TestCase):
    def test_contracts_round_trip_json_without_float_coercion(self):
        trade = TradeEvent(
            instrument_id="binance_spot:BTCUSDT",
            trade_id="981234",
            price="67500.12000000",
            quantity="0.00125000",
            trade_time_ms=1700000000000,
            aggressor="sell",
            aggressor_origin="derived:buyer_is_maker",
            envelope=envelope(),
        )
        batch = FeedBatch(
            source=SourceDescriptor(
                source_id="binance_spot_public_btcusdt_v1",
                provider="binance",
                venue="binance_spot",
                market="spot",
                endpoint_version="binance-spot-json-v1",
                endpoints=("https://data-api.binance.vision",),
                auth_required=False,
                terms_url="https://www.binance.com/en/terms",
                retention_permission="unknown",
                redistribution_permission="unknown",
                jurisdiction=None,
                cadence_ms=100,
                as_of_ms=1700000000000,
                evidence_refs=("docs/primary.md",),
            ),
            instrument=instrument(),
            trades=(trade,),
            book=None,
            health=(SourceHealth(
                channel="trades",
                connected=True,
                state="live",
                valid=True,
                stale=False,
                coverage="partial",
                last_exchange_time_ms=trade.trade_time_ms,
                last_receive_time_ms=1700000000001,
                last_receive_monotonic_ns=4000000000,
                sequence_ok=True,
                gaps=0,
                resyncs=0,
                dropped_events=0,
                dropped_bytes=0,
                reason="",
            ),),
        )
        encoded = json.dumps(batch.to_dict(), allow_nan=False, sort_keys=True)
        decoded = json.loads(encoded)
        self.assertEqual(decoded["trades"][0]["price"], "67500.12000000")
        self.assertEqual(decoded["trades"][0]["quantity"], "0.00125000")
        self.assertEqual(decoded["trades"][0]["envelope"]["receive_monotonic_ns"], 4000000000)
        self.assertEqual(decoded["source"]["retention_permission"], "unknown")
        self.assertEqual(decoded["instrument"]["quantity_step"], "0.00001000")

    def test_invalid_ids_and_hashes_are_rejected(self):
        with self.assertRaises(DataContractError):
            TradeEvent(
                instrument_id="binance_spot:BTCUSDT",
                trade_id="bad id",
                price="1",
                quantity="1",
                trade_time_ms=1,
                aggressor="unknown",
                aggressor_origin="unknown",
                envelope=envelope(),
            )
        with self.assertRaises(DataContractError):
            envelope(payload_hash="not-a-hash")


class BookContractTests(unittest.TestCase):
    def test_snapshot_and_delta_keep_sequence_clocks_and_string_levels(self):
        snap = BookSnapshot(
            instrument_id="binance_spot:BTCUSDT",
            last_update_id=15,
            bids=(("100.10", "2.000"),),
            asks=(("100.20", "1.250"),),
            envelope=envelope("book_snapshot"),
        )
        delta = BookDelta(
            instrument_id="binance_spot:BTCUSDT",
            first_update_id=16,
            last_update_id=17,
            bids=(("100.10", "0"),),
            asks=(("100.20", "0.5"),),
            envelope=envelope("book_delta", first_sequence=16, last_sequence=17),
        )
        self.assertEqual(snap.to_dict()["bids"], [["100.10", "2.000"]])
        self.assertEqual(delta.to_dict()["first_update_id"], 16)

    def test_delta_rejects_invalid_sequence_and_negative_size(self):
        with self.assertRaises(DataContractError):
            BookDelta(
                instrument_id="binance_spot:BTCUSDT",
                first_update_id=19,
                last_update_id=18,
                bids=(),
                asks=(),
                envelope=envelope("book_delta"),
            )
        with self.assertRaises(DataContractError):
            BookDelta(
                instrument_id="binance_spot:BTCUSDT",
                first_update_id=18,
                last_update_id=19,
                bids=(("100", "-1"),),
                asks=(),
                envelope=envelope("book_delta"),
            )


if __name__ == "__main__":
    unittest.main()
