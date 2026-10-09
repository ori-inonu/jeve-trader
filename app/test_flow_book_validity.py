import unittest

from flow_engine import FlowEngine


class BookValidityTests(unittest.TestCase):
    def setUp(self):
        self.engine = FlowEngine("WIN_SIM")
        self.engine.set_source_quality({"feed_connected": True, "sequence_ok": True})

    def book(self, ts_ms, *, bids_qty, asks_qty, bids_depth=3, asks_depth=3):
        return {
            "symbol": "WIN_SIM",
            "ts_ms": ts_ms,
            "bids": [
                {"price_points": str(131000 - 5 * level), "quantity": bids_qty}
                for level in range(bids_depth)
            ],
            "asks": [
                {"price_points": str(131005 + 5 * level), "quantity": asks_qty}
                for level in range(asks_depth)
            ],
        }

    def hypothesis(self, side, now_ms):
        snapshot = self.engine.snapshot(now_ms)
        return next(
            item for item in snapshot["hypotheses"]
            if item["kind"] == "liquidity_withdrawal" and item["side"] == side
        )

    def test_latest_top_only_snapshot_interrupts_deep_comparison(self):
        self.engine.set_book(self.book(10000, bids_qty=100, asks_qty=100))
        self.engine.set_book(self.book(10100, bids_qty=20, asks_qty=20))
        self.engine.set_book(self.book(10200, bids_qty=90, asks_qty=90, bids_depth=1, asks_depth=1))

        for side in ("bids", "asks"):
            result = self.hypothesis(side, 10200)
            self.assertEqual(result["status"], "inconclusive")
            self.assertIsNone(result["evidence"]["displayed_quantity_reduction_fraction"])
            self.assertIn("DEPTH_SEQUENCE_REQUIRED", result["missing"])
            self.assertEqual(
                result["evidence"]["comparison"],
                {
                    "scope": "consecutive_observed_snapshots",
                    "before_ts_ms": 10100,
                    "after_ts_ms": 10200,
                    "elapsed_ms": 100,
                    "before_age_ms": 100,
                    "after_age_ms": 0,
                    "before_depth_levels": 3,
                    "after_depth_levels": 1,
                },
            )
            self.assertTrue(result["descriptive_only"])
            self.assertIsNone(result["future_profit_probability"])


    def test_depth_loss_on_one_side_preserves_other_side_evaluation(self):
        self.engine.set_book(self.book(10000, bids_qty=100, asks_qty=100))
        self.engine.set_book(
            self.book(10100, bids_qty=100, asks_qty=50, bids_depth=1, asks_depth=3)
        )

        bids = self.hypothesis("bids", 10100)
        asks = self.hypothesis("asks", 10100)
        self.assertEqual(bids["status"], "inconclusive")
        self.assertIsNone(bids["evidence"]["displayed_quantity_reduction_fraction"])
        self.assertIn("DEPTH_SEQUENCE_REQUIRED", bids["missing"])
        self.assertEqual(asks["status"], "potential")
        self.assertEqual(asks["evidence"]["displayed_quantity_reduction_fraction"], "0.5")
        self.assertEqual(asks["evidence"]["comparison"]["before_depth_levels"], 3)
        self.assertEqual(asks["evidence"]["comparison"]["after_depth_levels"], 3)
    def test_depth_evaluation_recovers_only_after_two_new_deep_snapshots(self):
        self.engine.set_book(self.book(10000, bids_qty=100, asks_qty=100))
        self.engine.set_book(self.book(10100, bids_qty=20, asks_qty=20))
        self.engine.set_book(self.book(10200, bids_qty=90, asks_qty=90, bids_depth=1, asks_depth=1))
        self.engine.set_book(self.book(10300, bids_qty=10, asks_qty=10))

        first_recovery = self.hypothesis("asks", 10300)
        self.assertEqual(first_recovery["status"], "inconclusive")
        self.assertIsNone(first_recovery["evidence"]["displayed_quantity_reduction_fraction"])
        self.assertEqual(first_recovery["evidence"]["comparison"]["before_ts_ms"], 10200)
        self.assertEqual(first_recovery["evidence"]["comparison"]["after_ts_ms"], 10300)

        self.engine.set_book(self.book(10400, bids_qty=5, asks_qty=5))
        recovered = self.hypothesis("asks", 10400)
        self.assertEqual(recovered["status"], "potential")
        self.assertEqual(recovered["evidence"]["displayed_quantity_reduction_fraction"], "0.5")
        self.assertEqual(recovered["evidence"]["comparison"]["before_ts_ms"], 10300)
        self.assertEqual(recovered["evidence"]["comparison"]["after_ts_ms"], 10400)
    def test_both_comparison_endpoints_must_be_fresh_at_2000ms_boundary(self):
        def evaluated_at(now_ms):
            engine = FlowEngine("WIN_SIM")
            engine.set_source_quality({"feed_connected": True, "sequence_ok": True})
            engine.set_book(self.book(10000, bids_qty=100, asks_qty=100))
            engine.set_book(self.book(11000, bids_qty=20, asks_qty=20))
            return next(
                item for item in engine.snapshot(now_ms)["hypotheses"]
                if item["kind"] == "liquidity_withdrawal" and item["side"] == "asks"
            )

        at_limit = evaluated_at(12000)
        past_limit = evaluated_at(12001)
        self.assertEqual(at_limit["status"], "potential")
        self.assertEqual(at_limit["evidence"]["displayed_quantity_reduction_fraction"], "0.8")
        self.assertEqual(at_limit["evidence"]["comparison"]["before_age_ms"], 2000)
        self.assertEqual(past_limit["status"], "inconclusive")
        self.assertIsNone(past_limit["evidence"]["displayed_quantity_reduction_fraction"])
        self.assertIn("BOOK_COMPARISON_EXPIRED", past_limit["missing"])
        self.assertEqual(past_limit["evidence"]["comparison"]["before_age_ms"], 2001)
    def test_recent_tape_does_not_refresh_book_comparison_age(self):
        self.engine.set_book(self.book(10000, bids_qty=100, asks_qty=100))
        self.engine.set_book(self.book(11000, bids_qty=20, asks_qty=20))
        self.assertTrue(
            self.engine.add_trade({
                "id": "recent-tape",
                "symbol": "WIN_SIM",
                "ts_ms": 12199,
                "price_points": "131000",
                "quantity": 1,
                "aggressor": "buy",
            })["accepted"]
        )

        result = self.hypothesis("asks", 12200)
        self.assertEqual(result["status"], "inconclusive")
        self.assertIsNone(result["evidence"]["displayed_quantity_reduction_fraction"])
        self.assertIn("BOOK_COMPARISON_EXPIRED", result["missing"])
        self.assertEqual(result["evidence"]["comparison"]["before_age_ms"], 2200)
        self.assertEqual(result["evidence"]["comparison"]["after_age_ms"], 1200)
    def test_price_grid_change_keeps_comparison_but_withholds_fraction(self):
        self.engine.set_book(self.book(10000, bids_qty=100, asks_qty=100))
        changed = self.book(10100, bids_qty=20, asks_qty=20)
        for side in ("bids", "asks"):
            for level in changed[side]:
                level["price_points"] = str(int(level["price_points"]) + 5)
        self.engine.set_book(changed)

        result = self.hypothesis("asks", 10100)
        self.assertEqual(result["status"], "inconclusive")
        self.assertIsNone(result["evidence"]["displayed_quantity_reduction_fraction"])
        self.assertIn("DEPTH_PRICE_GRID_CHANGED", result["missing"])
        self.assertEqual(result["evidence"]["comparison"]["before_ts_ms"], 10000)
        self.assertEqual(result["evidence"]["comparison"]["after_ts_ms"], 10100)

    def test_quantity_increase_is_negative_and_not_a_withdrawal(self):
        self.engine.set_book(self.book(10000, bids_qty=20, asks_qty=20))
        self.engine.set_book(self.book(10100, bids_qty=30, asks_qty=30))

        for side in ("bids", "asks"):
            result = self.hypothesis(side, 10100)
            self.assertEqual(result["status"], "not_observed")
            self.assertEqual(result["evidence"]["displayed_quantity_reduction_fraction"], "-0.5")
            self.assertEqual(result["missing"], [])

    def test_absent_comparison_metadata_stays_null(self):
        expected = {
            "scope": "consecutive_observed_snapshots",
            "before_ts_ms": None, "after_ts_ms": None, "elapsed_ms": None,
            "before_age_ms": None, "after_age_ms": None,
            "before_depth_levels": None, "after_depth_levels": None,
        }
        for side in ("bids", "asks"):
            result = self.hypothesis(side, 10000)
            self.assertEqual(result["status"], "inconclusive")
            self.assertEqual(result["evidence"]["comparison"], expected)
            self.assertIsNone(result["evidence"]["displayed_quantity_reduction_fraction"])
            self.assertIn("DEPTH_SEQUENCE_REQUIRED", result["missing"])

        self.engine.set_book(self.book(10100, bids_qty=20, asks_qty=20))
        expected.update(after_ts_ms=10100, after_age_ms=0, after_depth_levels=3)
        for side in ("bids", "asks"):
            result = self.hypothesis(side, 10100)
            self.assertEqual(result["evidence"]["comparison"], expected)
            self.assertEqual(result["status"], "inconclusive")
            self.assertIsNone(result["evidence"]["displayed_quantity_reduction_fraction"])

    def test_bad_source_or_integrity_blocks_numerically_comparable_books(self):
        cases = (
            ({"feed_connected": False}, False, "SOURCE_INTEGRITY_NOT_VERIFIED"),
            ({"sequence_ok": None}, False, "SOURCE_INTEGRITY_NOT_VERIFIED"),
            ({"sequence_ok": False}, False, "SOURCE_SEQUENCE_GAP_RESET_REQUIRED"),
            ({}, True, "INVALID_BOOK"),
        )
        for quality, invalid_book, reason in cases:
            with self.subTest(quality=quality, invalid_book=invalid_book):
                engine = FlowEngine("WIN_SIM")
                engine.set_source_quality({"feed_connected": True, "sequence_ok": True})
                engine.set_book(self.book(10000, bids_qty=100, asks_qty=100))
                engine.set_book(self.book(10100, bids_qty=20, asks_qty=20))
                engine.set_source_quality(quality)
                if invalid_book:
                    bad = self.book(10200, bids_qty=-1, asks_qty=20)
                    self.assertEqual(engine.set_book(bad)["reason"], "INVALID_BOOK")
                snapshot = engine.snapshot(10100)
                self.assertFalse(snapshot["actionable_live_signal"])
                self.assertIsNone(snapshot["win_probability"])
                for result in snapshot["hypotheses"]:
                    if result["kind"] == "liquidity_withdrawal":
                        self.assertEqual(result["status"], "inconclusive")
                        self.assertIn(reason, result["missing"])
                        self.assertEqual(result["evidence"]["comparison"]["after_ts_ms"], 10100)
                        self.assertTrue(result["descriptive_only"])
                        self.assertIsNone(result["future_profit_probability"])

    def test_both_comparison_endpoints_must_belong_to_short_window(self):
        engine = FlowEngine("WIN_SIM", rules={"short_window_ms": 1000})
        engine.set_source_quality({"feed_connected": True, "sequence_ok": True})
        engine.set_book(self.book(10000, bids_qty=100, asks_qty=100))
        engine.set_book(self.book(11000, bids_qty=20, asks_qty=20))

        result = next(
            item for item in engine.snapshot(11500)["hypotheses"]
            if item["kind"] == "liquidity_withdrawal" and item["side"] == "asks"
        )

        self.assertEqual(result["status"], "inconclusive")
        self.assertIsNone(result["evidence"]["displayed_quantity_reduction_fraction"])
        self.assertIn("DEPTH_SEQUENCE_REQUIRED", result["missing"])
        self.assertEqual(
            result["evidence"]["comparison"],
            {
                "scope": "consecutive_observed_snapshots",
                "before_ts_ms": 10000,
                "after_ts_ms": 11000,
                "elapsed_ms": 1000,
                "before_age_ms": 1500,
                "after_age_ms": 500,
                "before_depth_levels": 3,
                "after_depth_levels": 3,
            },
        )

if __name__ == "__main__":
    unittest.main()
