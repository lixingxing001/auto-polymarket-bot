import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from btc5m_bot.active_strategy import (
    ActiveStrategyState,
    active_strategy_allows_trade,
    load_active_strategy_state,
    write_active_strategy_state,
)
from btc5m_bot.models import FeatureVector


class ActiveStrategyTests(unittest.TestCase):
    def test_round_trips_strategy_state(self) -> None:
        state = _state()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            write_active_strategy_state(path, state)
            loaded = load_active_strategy_state(path)

        self.assertEqual(loaded.source_candidate_id, "candidate")
        self.assertEqual(loaded.filter_kind, "avoid_mid_distance_to_barrier_bps")
        self.assertFalse(loaded.live_trading_enabled)

    def test_mid_distance_filter_blocks_matching_trade(self) -> None:
        state = _state()
        blocked = _features(distance_to_barrier_bps=3.0)
        allowed = _features(distance_to_barrier_bps=8.0)

        self.assertFalse(active_strategy_allows_trade(state, blocked, "UP"))
        self.assertTrue(active_strategy_allows_trade(state, allowed, "UP"))


def _state() -> ActiveStrategyState:
    return ActiveStrategyState(
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
        filter_kind="avoid_mid_distance_to_barrier_bps",
        min_abs_distance_to_barrier_bps=2.0,
        max_abs_distance_to_barrier_bps=6.0,
    )


def _features(distance_to_barrier_bps: float) -> FeatureVector:
    return FeatureVector(
        return_1m=0.0,
        return_5m=0.0,
        realized_vol_5m=0.0,
        trade_imbalance_30s=0.0,
        distance_to_barrier_bps=distance_to_barrier_bps,
        seconds_to_close=120,
    )


if __name__ == "__main__":
    unittest.main()
