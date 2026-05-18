import unittest
from datetime import datetime, timedelta, timezone

from btc5m_bot.historical import HistoricalSample
from btc5m_bot.learning import (
    chronological_split,
    evaluate_model,
    threshold_sweep,
    train_logistic_regression,
    walk_forward_evaluate,
)
from btc5m_bot.models import FeatureVector


class LearningTests(unittest.TestCase):
    def test_train_logistic_regression_fits_simple_signal(self) -> None:
        base = datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc)
        samples = tuple(
            HistoricalSample(
                window_start=base + timedelta(minutes=5 * index),
                window_end=base + timedelta(minutes=5 * (index + 1)),
                slug=str(index),
                condition_id="c",
                label="Up" if index % 2 else "Down",
                prob_up=0.5,
                features=FeatureVector(
                    return_1m=0.01 if index % 2 else -0.01,
                    return_5m=0.0,
                    realized_vol_5m=0.0,
                    trade_imbalance_30s=0.0,
                    distance_to_barrier_bps=10.0 if index % 2 else -10.0,
                    seconds_to_close=240,
                ),
                polymarket_up_price=0.7 if index % 2 else 0.3,
                polymarket_down_price=0.3 if index % 2 else 0.7,
            )
            for index in range(20)
        )
        train, test = chronological_split(samples)
        model = train_logistic_regression(train, epochs=200)
        self.assertGreaterEqual(evaluate_model(model, test)["accuracy"], 0.9)
        self.assertIn(0.55, threshold_sweep(model, test))

    def test_walk_forward_evaluate(self) -> None:
        base = datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc)
        samples = tuple(
            HistoricalSample(
                window_start=base + timedelta(minutes=5 * index),
                window_end=base + timedelta(minutes=5 * (index + 1)),
                slug=str(index),
                condition_id="c",
                label="Up" if index % 2 else "Down",
                prob_up=0.5,
                features=FeatureVector(
                    return_1m=0.01 if index % 2 else -0.01,
                    return_5m=0.0,
                    realized_vol_5m=0.0,
                    trade_imbalance_30s=0.0,
                    distance_to_barrier_bps=10.0 if index % 2 else -10.0,
                    seconds_to_close=240,
                ),
                polymarket_up_price=0.7 if index % 2 else 0.3,
                polymarket_down_price=0.3 if index % 2 else 0.7,
            )
            for index in range(40)
        )
        result = walk_forward_evaluate(samples, min_train_size=20, test_size=10)
        self.assertEqual(result["folds"], 2)


if __name__ == "__main__":
    unittest.main()
