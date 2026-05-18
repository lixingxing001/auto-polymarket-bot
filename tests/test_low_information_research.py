import unittest
from datetime import datetime, timedelta, timezone

from btc5m_bot.historical import HistoricalSample
from btc5m_bot.learning import train_logistic_regression
from btc5m_bot.low_information_research import evaluate_low_information_filters
from btc5m_bot.models import FeatureVector


class LowInformationResearchTests(unittest.TestCase):
    def test_evaluate_low_information_filters(self) -> None:
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
                    return_1m=float(index % 5),
                    return_5m=float(index % 7),
                    realized_vol_5m=float(index % 3),
                    trade_imbalance_30s=0.0,
                    distance_to_barrier_bps=float(index % 6),
                    seconds_to_close=240,
                    polymarket_up_price=0.7 if index % 2 else 0.3,
                    polymarket_down_price=0.3 if index % 2 else 0.7,
                    polymarket_prob_gap=0.4 if index % 2 else -0.4,
                ),
                polymarket_up_price=0.7 if index % 2 else 0.3,
                polymarket_down_price=0.3 if index % 2 else 0.7,
            )
            for index in range(30)
        )
        train_samples = samples[:20]
        test_samples = samples[20:]
        model = train_logistic_regression(train_samples)
        result = evaluate_low_information_filters(train_samples, test_samples, model)
        self.assertIn("thresholds", result)
        self.assertIn("results", result)
        self.assertTrue(result["results"])
