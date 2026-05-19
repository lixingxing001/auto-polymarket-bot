import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from btc5m_bot.candidate_strategies import (
    CandidateStrategy,
    candidate_allows_sample,
    compare_candidate_strategy,
    load_candidate_registry,
    register_candidate,
    summarize_candidate_comparison,
)
from btc5m_bot.historical import HistoricalSample
from btc5m_bot.models import FeatureVector
from btc5m_bot.settled_snapshot_archive import SettledSnapshotWindow
from btc5m_bot.snapshot_backtest import SnapshotQuote


class CandidateStrategyTests(unittest.TestCase):
    def test_register_candidate_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.csv"
            candidate = register_candidate(
                path=path,
                candidate_id="edge_008",
                description="Higher edge gate",
                rationale="Test stronger price discipline",
                eligible_after_market_end_time=datetime(2026, 5, 18, 15, 0, tzinfo=timezone.utc),
                min_confidence=0.65,
                min_edge=0.08,
                stake_usd=10.0,
                max_fill_delay_seconds=30,
                registered_at=datetime(2026, 5, 18, 15, 1, tzinfo=timezone.utc),
            )
            loaded = load_candidate_registry(path)["edge_008"]
            self.assertEqual(loaded, candidate)

    def test_candidate_filter_blocks_low_momentum_near_barrier(self) -> None:
        sample = HistoricalSample(
            window_start=datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 5, 18, 0, 5, tzinfo=timezone.utc),
            slug="s",
            condition_id="c",
            label="Up",
            prob_up=0.5,
            features=FeatureVector(
                return_1m=0.0001,
                return_5m=0.0,
                realized_vol_5m=0.0,
                trade_imbalance_30s=0.0,
                distance_to_barrier_bps=0.5,
                seconds_to_close=240,
            ),
            polymarket_up_price=0.5,
            polymarket_down_price=0.5,
        )
        candidate = CandidateStrategy(
            candidate_id="scene",
            description="scene",
            rationale="scene",
            registered_at=datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc),
            eligible_after_market_end_time=datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc),
            min_confidence=0.65,
            min_edge=0.03,
            stake_usd=10.0,
            max_fill_delay_seconds=30,
            filter_kind="avoid_low_momentum_near_barrier",
            min_abs_return_1m=0.001,
            min_abs_distance_to_barrier_bps=1.0,
        )
        self.assertFalse(candidate_allows_sample(candidate, sample))

    def test_candidate_filter_blocks_mid_abs_return_5m(self) -> None:
        sample = HistoricalSample(
            window_start=datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 5, 18, 0, 5, tzinfo=timezone.utc),
            slug="s",
            condition_id="c",
            label="Up",
            prob_up=0.5,
            features=FeatureVector(
                return_1m=0.0,
                return_5m=0.0005,
                realized_vol_5m=0.0,
                trade_imbalance_30s=0.0,
                distance_to_barrier_bps=3.0,
                seconds_to_close=240,
            ),
            polymarket_up_price=0.5,
            polymarket_down_price=0.5,
        )
        candidate = CandidateStrategy(
            candidate_id="mid",
            description="mid",
            rationale="mid",
            registered_at=datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc),
            eligible_after_market_end_time=datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc),
            min_confidence=0.65,
            min_edge=0.03,
            stake_usd=10.0,
            max_fill_delay_seconds=30,
            filter_kind="avoid_mid_abs_return_5m",
            min_abs_return_5m=0.0002,
            max_abs_return_5m=0.0008,
        )
        self.assertFalse(candidate_allows_sample(candidate, sample))

    def test_candidate_filter_blocks_mid_distance_to_barrier_bps(self) -> None:
        sample = HistoricalSample(
            window_start=datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 5, 18, 0, 5, tzinfo=timezone.utc),
            slug="s",
            condition_id="c",
            label="Up",
            prob_up=0.5,
            features=FeatureVector(
                return_1m=0.0,
                return_5m=0.0,
                realized_vol_5m=0.0,
                trade_imbalance_30s=0.0,
                distance_to_barrier_bps=-4.5,
                seconds_to_close=240,
            ),
            polymarket_up_price=0.5,
            polymarket_down_price=0.5,
        )
        candidate = CandidateStrategy(
            candidate_id="mid_distance",
            description="mid_distance",
            rationale="mid_distance",
            registered_at=datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc),
            eligible_after_market_end_time=datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc),
            min_confidence=0.65,
            min_edge=0.03,
            stake_usd=10.0,
            max_fill_delay_seconds=30,
            filter_kind="avoid_mid_distance_to_barrier_bps",
            min_abs_distance_to_barrier_bps=2.0,
            max_abs_distance_to_barrier_bps=6.0,
        )
        self.assertFalse(candidate_allows_sample(candidate, sample))

    def test_compare_candidate_only_uses_future_windows(self) -> None:
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
        candidate = CandidateStrategy(
            candidate_id="future_only_candidate_test",
            description="d",
            rationale="r",
            registered_at=datetime(2026, 5, 18, 1, 0, tzinfo=timezone.utc),
            eligible_after_market_end_time=samples[10].window_end,
            min_confidence=0.65,
            min_edge=0.08,
            stake_usd=10.0,
            max_fill_delay_seconds=30,
        )
        windows = (
            SettledSnapshotWindow(
                slug="s10",
                condition_id="c10",
                title="t",
                market_end_time=samples[10].window_end,
                resolved_outcome="DOWN",
                snapshot_count=1,
                first_captured_at=samples[10].window_start + timedelta(seconds=61),
                last_captured_at=samples[10].window_start + timedelta(seconds=61),
                min_up_best_ask=0.6,
                max_up_best_ask=0.6,
                min_down_best_ask=0.4,
                max_down_best_ask=0.4,
            ),
            SettledSnapshotWindow(
                slug="s11",
                condition_id="c11",
                title="t",
                market_end_time=samples[11].window_end,
                resolved_outcome="UP",
                snapshot_count=1,
                first_captured_at=samples[11].window_start + timedelta(seconds=61),
                last_captured_at=samples[11].window_start + timedelta(seconds=61),
                min_up_best_ask=0.6,
                max_up_best_ask=0.6,
                min_down_best_ask=0.4,
                max_down_best_ask=0.4,
            ),
        )
        quote = SnapshotQuote(
            captured_at=samples[11].window_start + timedelta(seconds=61),
            slug="s11",
            up_best_ask=0.6,
            up_best_ask_size=100.0,
            down_best_ask=0.4,
            down_best_ask_size=100.0,
        )
        rows = compare_candidate_strategy(
            candidate=candidate,
            archived_windows=windows,
            samples=samples,
            snapshots={"s11": [quote]},
            min_train_size=10,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].slug, "s11")
        self.assertEqual(summarize_candidate_comparison(rows)["eligible_windows"], 1)
