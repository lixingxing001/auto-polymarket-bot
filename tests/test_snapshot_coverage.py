import unittest
from datetime import datetime, timedelta, timezone

from btc5m_bot.historical import HistoricalSample
from btc5m_bot.models import FeatureVector
from btc5m_bot.snapshot_coverage import compute_snapshot_coverage


class SnapshotCoverageTests(unittest.TestCase):
    def test_compute_snapshot_coverage(self) -> None:
        start = datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc)
        samples = tuple(
            HistoricalSample(
                window_start=start + timedelta(minutes=5 * index),
                window_end=start + timedelta(minutes=5 * (index + 1)),
                slug=f"s{index}",
                condition_id=f"c{index}",
                label="UP",
                prob_up=0.5,
                features=FeatureVector(0.0, 0.0, 0.0, 0.0, 0.0, 300),
                polymarket_up_price=0.5,
                polymarket_down_price=0.5,
            )
            for index in range(10)
        )

        coverage = compute_snapshot_coverage(
            samples=samples,
            recorded_slugs={"s0", "s1", "s8", "s9", "future"},
        )

        self.assertEqual(coverage.dataset_windows, 10)
        self.assertEqual(coverage.train_windows, 7)
        self.assertEqual(coverage.test_windows, 3)
        self.assertEqual(coverage.matched_train_windows, 2)
        self.assertEqual(coverage.matched_test_windows, 2)
        self.assertEqual(coverage.unmatched_recorded_windows, 1)
