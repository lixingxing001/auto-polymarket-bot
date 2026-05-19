import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from btc5m_bot.active_strategy import ActiveStrategyState
from btc5m_bot.forward_snapshot_eval import evaluate_settled_snapshot_windows
from btc5m_bot.historical import HistoricalSample
from btc5m_bot.models import FeatureVector
from btc5m_bot.settled_snapshot_archive import SettledSnapshotWindow
from btc5m_bot.snapshot_backtest import SnapshotQuote


class ForwardSnapshotEvalTests(unittest.TestCase):
    def test_evaluate_settled_snapshot_windows(self) -> None:
        start = datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc)
        samples = tuple(
            HistoricalSample(
                window_start=start + timedelta(minutes=5 * index),
                window_end=start + timedelta(minutes=5 * (index + 1)),
                slug=f"s{index}",
                condition_id=f"c{index}",
                label="Up" if index % 2 else "Down",
                prob_up=0.5,
                features=FeatureVector(
                    return_1m=float(index % 2),
                    return_5m=float(index % 2),
                    realized_vol_5m=0.1,
                    trade_imbalance_30s=0.0,
                    distance_to_barrier_bps=0.0,
                    seconds_to_close=240,
                    polymarket_up_price=0.7 if index % 2 else 0.3,
                    polymarket_down_price=0.3 if index % 2 else 0.7,
                    polymarket_prob_gap=0.4 if index % 2 else -0.4,
                ),
                polymarket_up_price=0.7 if index % 2 else 0.3,
                polymarket_down_price=0.3 if index % 2 else 0.7,
            )
            for index in range(12)
        )
        window = SettledSnapshotWindow(
            slug="s11",
            condition_id="c11",
            title="t",
            market_end_time=samples[-1].window_end,
            resolved_outcome="UP",
            snapshot_count=1,
            first_captured_at=samples[-1].window_start + timedelta(seconds=61),
            last_captured_at=samples[-1].window_start + timedelta(seconds=61),
            min_up_best_ask=0.6,
            max_up_best_ask=0.6,
            min_down_best_ask=0.4,
            max_down_best_ask=0.4,
        )
        quote = SnapshotQuote(
            captured_at=samples[-1].window_start + timedelta(seconds=61),
            slug="s11",
            up_best_ask=0.6,
            up_best_ask_size=100.0,
            down_best_ask=0.4,
            down_best_ask_size=100.0,
        )
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "eval.csv"
            summary = evaluate_settled_snapshot_windows(
                archived_windows=(window,),
                samples=samples,
                snapshots={"s11": [quote]},
                output_path=output_path,
                min_train_size=10,
                active_strategy_state=ActiveStrategyState(
                    mode="paper",
                    source_candidate_id="candidate",
                    description="Candidate",
                    rationale="Test",
                    activated_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
                    live_trading_enabled=False,
                    min_confidence=0.65,
                    min_edge=0.03,
                    stake_usd=10.0,
                    max_fill_delay_seconds=30,
                ),
            )
            rendered = output_path.read_text(encoding="utf-8")
            self.assertEqual(summary["new_evaluations"], 1)
            self.assertEqual(summary["total_evaluations"], 1)
            self.assertEqual(summary["active_strategy_source_candidate_id"], "candidate")
            self.assertIn("active_strategy_source_candidate_id", rendered)
            self.assertIn("candidate", rendered)
            self.assertTrue(output_path.exists())
