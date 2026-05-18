import unittest
from datetime import datetime, timezone

from btc5m_bot.execution_backtest import ExecutionBacktestConfig
from btc5m_bot.historical import HistoricalSample
from btc5m_bot.models import FeatureVector
from btc5m_bot.snapshot_backtest import (
    SnapshotQuote,
    backtest_sample_with_snapshot,
    find_snapshot_at_or_after,
)


class SnapshotBacktestTests(unittest.TestCase):
    def test_find_snapshot_at_or_after(self) -> None:
        decision = datetime(2026, 5, 18, 10, 1, tzinfo=timezone.utc)
        quote = SnapshotQuote(decision, "s", 0.4, 100, 0.6, 100)
        self.assertIs(find_snapshot_at_or_after([quote], decision, 30), quote)

    def test_backtest_sample_with_snapshot(self) -> None:
        sample = HistoricalSample(
            window_start=datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 5, 18, 10, 5, tzinfo=timezone.utc),
            slug="s",
            condition_id="c",
            label="Up",
            prob_up=0.7,
            features=FeatureVector(0, 0, 0, 0, 0, 240),
            polymarket_up_price=0.4,
            polymarket_down_price=0.6,
        )
        quote = SnapshotQuote(
            captured_at=datetime(2026, 5, 18, 10, 1, tzinfo=timezone.utc),
            slug="s",
            up_best_ask=0.4,
            up_best_ask_size=100,
            down_best_ask=0.6,
            down_best_ask_size=100,
        )
        trade, reason = backtest_sample_with_snapshot(
            sample=sample,
            quote=quote,
            forecast_prob_up=0.7,
            config=ExecutionBacktestConfig(stake_usd=10, min_edge=0.03, min_confidence=0.65),
        )
        self.assertEqual(reason, "traded")
        self.assertIsNotNone(trade)
        self.assertGreater(trade.pnl_usd, 0)


if __name__ == "__main__":
    unittest.main()
