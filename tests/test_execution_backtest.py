import unittest
from datetime import datetime, timezone

from btc5m_bot.execution_backtest import (
    ExecutionBacktestConfig,
    backtest_sample_with_trades,
    build_fill_proxy,
    run_holdout_market_aware_execution_backtest,
)
from btc5m_bot.historical import HistoricalSample
from btc5m_bot.models import FeatureVector
from btc5m_bot.polymarket import MarketTrade


class ExecutionBacktestTests(unittest.TestCase):
    def test_build_fill_proxy_accumulates_real_buys(self) -> None:
        trades = [
            MarketTrade("a", "c", "Up", "BUY", 10, 0.4, 100),
            MarketTrade("a", "c", "Up", "BUY", 15, 0.5, 101),
        ]
        fill = build_fill_proxy(trades, "Up", 100, 10.0, 30)
        self.assertIsNotNone(fill)
        self.assertEqual(fill.trade_count, 2)

    def test_backtest_uses_edge_and_fee(self) -> None:
        sample = HistoricalSample(
            window_start=datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 5, 18, 10, 5, tzinfo=timezone.utc),
            slug="s",
            condition_id="c",
            label="Up",
            prob_up=0.70,
            features=FeatureVector(0, 0, 0, 0, 0, 240),
            polymarket_up_price=0.4,
            polymarket_down_price=0.6,
        )
        trades = [
            MarketTrade("a", "c", "Up", "BUY", 30, 0.4, 1779098460),
            MarketTrade("b", "c", "Down", "BUY", 30, 0.6, 1779098460),
        ]
        simulated = backtest_sample_with_trades(
            sample,
            trades,
            ExecutionBacktestConfig(stake_usd=10.0, min_edge=0.03),
        )
        self.assertIsNotNone(simulated[0])
        self.assertEqual(simulated[0].decision, "UP")
        self.assertGreater(simulated[0].pnl_usd, 0)

    def test_low_confidence_is_skipped(self) -> None:
        sample = HistoricalSample(
            window_start=datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 5, 18, 10, 5, tzinfo=timezone.utc),
            slug="s",
            condition_id="c",
            label="Up",
            prob_up=0.55,
            features=FeatureVector(0, 0, 0, 0, 0, 240),
            polymarket_up_price=0.5,
            polymarket_down_price=0.5,
        )
        simulated = backtest_sample_with_trades(
            sample,
            [MarketTrade("a", "c", "Up", "BUY", 30, 0.4, 1779098460)],
            ExecutionBacktestConfig(stake_usd=10.0, min_confidence=0.65),
        )
        self.assertIsNone(simulated[0])
        self.assertEqual(simulated[1], "low_confidence")


if __name__ == "__main__":
    unittest.main()
