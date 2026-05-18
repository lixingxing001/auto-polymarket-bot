import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

from btc5m_bot.coinbase import Candle, build_historical_price_only_features
from btc5m_bot.historical import HistoricalSample, evaluate_directional_baseline
from btc5m_bot.historical import evaluate_market_price_baseline
from btc5m_bot.historical import _read_cached_samples, _write_cached_samples
from btc5m_bot.models import FeatureVector
from btc5m_bot.polymarket import resolved_outcome_from_event


class HistoricalTests(unittest.TestCase):
    def test_resolved_outcome_from_event(self) -> None:
        event = {
            "markets": [
                {
                    "closed": True,
                    "outcomes": "[\"Up\", \"Down\"]",
                    "outcomePrices": "[\"0\", \"1\"]",
                }
            ]
        }
        self.assertEqual(resolved_outcome_from_event(event), "Down")

    def test_historical_features_only_use_completed_candles(self) -> None:
        candles = [
            Candle(
                datetime(2026, 5, 18, 9, 55, tzinfo=timezone.utc) + timedelta(minutes=index),
                0,
                0,
                100 + index,
                100 + index,
                1,
            )
            for index in range(7)
        ]
        features = build_historical_price_only_features(
            candles=candles,
            window_start=datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 5, 18, 10, 5, tzinfo=timezone.utc),
            decision_time=datetime(2026, 5, 18, 10, 1, tzinfo=timezone.utc),
        )
        self.assertGreater(features.return_1m, 0)
        self.assertEqual(features.seconds_to_close, 240)

    def test_evaluation_includes_majority_baseline(self) -> None:
        samples = (
            HistoricalSample(
                datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc),
                datetime(2026, 5, 18, 10, 5, tzinfo=timezone.utc),
                "a",
                "c",
                "Up",
                0.7,
                FeatureVector(0, 0, 0, 0, 0, 0),
                0.7,
                0.3,
            ),
            HistoricalSample(
                datetime(2026, 5, 18, 10, 5, tzinfo=timezone.utc),
                datetime(2026, 5, 18, 10, 10, tzinfo=timezone.utc),
                "b",
                "c",
                "Down",
                0.2,
                FeatureVector(0, 0, 0, 0, 0, 0),
                0.4,
                0.6,
            ),
            HistoricalSample(
                datetime(2026, 5, 18, 10, 10, tzinfo=timezone.utc),
                datetime(2026, 5, 18, 10, 15, tzinfo=timezone.utc),
                "c",
                "c",
                "Down",
                0.8,
                FeatureVector(0, 0, 0, 0, 0, 0),
                0.7,
                0.3,
            ),
        )
        evaluation = evaluate_directional_baseline(samples)
        self.assertEqual(evaluation["majority_accuracy"], 2 / 3)
        self.assertEqual(evaluation["confusion"]["tp"], 1)
        self.assertEqual(evaluate_market_price_baseline(samples)["accuracy"], 2 / 3)

    def test_cached_samples_roundtrip(self) -> None:
        sample = HistoricalSample(
            datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc),
            datetime(2026, 5, 18, 10, 5, tzinfo=timezone.utc),
            "s",
            "c",
            "Up",
            0.7,
            FeatureVector(0, 0, 0, 0, 0, 240),
            0.7,
            0.3,
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cache.csv"
            _write_cached_samples(path, (sample,))
            loaded = _read_cached_samples(path)
        self.assertIn("s", loaded)


if __name__ == "__main__":
    unittest.main()
