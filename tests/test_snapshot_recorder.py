import csv
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from btc5m_bot.polymarket import Btc5mMarket, BookLevel, OrderBookSnapshot
from btc5m_bot.snapshot_recorder import (
    append_snapshot,
    build_window_summary,
    snapshot_row,
)


class SnapshotRecorderTests(unittest.TestCase):
    def test_snapshot_row_and_append(self) -> None:
        market = Btc5mMarket(
            slug="s",
            title="t",
            condition_id="c",
            end_time=datetime(2026, 5, 18, 10, 5, tzinfo=timezone.utc),
            up_token_id="u",
            down_token_id="d",
            accepting_orders=True,
        )
        up_book = OrderBookSnapshot(
            token_id="u",
            bids=(BookLevel(0.4, 10),),
            asks=(BookLevel(0.5, 11),),
            tick_size=0.01,
            min_order_size=5,
        )
        down_book = OrderBookSnapshot(
            token_id="d",
            bids=(BookLevel(0.49, 12),),
            asks=(BookLevel(0.6, 13),),
            tick_size=0.01,
            min_order_size=5,
        )
        row = snapshot_row(
            market,
            up_book,
            down_book,
            datetime(2026, 5, 18, 10, 1, tzinfo=timezone.utc),
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snapshots.csv"
            append_snapshot(path, row)
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(rows[0]["slug"], "s")
        self.assertEqual(rows[0]["up_best_ask"], "0.5")
        summary = build_window_summary([row, {**row, "captured_at": "2026-05-18T10:02:00+00:00", "up_best_ask": 0.6}])
        self.assertEqual(summary[0]["snapshot_count"], 2)
        self.assertEqual(summary[0]["max_up_best_ask"], 0.6)


if __name__ == "__main__":
    unittest.main()
