import unittest
from datetime import datetime, timedelta, timezone

from btc5m_bot.error_diagnostics import (
    build_prediction_rows,
    diagnose_error_slices,
    find_worst_slices,
)
from btc5m_bot.historical import HistoricalSample
from btc5m_bot.learning import train_logistic_regression
from btc5m_bot.models import FeatureVector


class ErrorDiagnosticsTests(unittest.TestCase):
    def test_diagnostics_build_slices(self) -> None:
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
                    return_1m=float(index % 3),
                    return_5m=float(index % 4),
                    realized_vol_5m=float(index % 5),
                    trade_imbalance_30s=0.0,
                    distance_to_barrier_bps=float(index % 6),
                    seconds_to_close=240,
                    range_5m_bps=float(index % 7),
                    polymarket_up_price=0.7 if index % 2 else 0.3,
                    polymarket_down_price=0.3 if index % 2 else 0.7,
                    polymarket_prob_gap=0.4 if index % 2 else -0.4,
                ),
                polymarket_up_price=0.7 if index % 2 else 0.3,
                polymarket_down_price=0.3 if index % 2 else 0.7,
            )
            for index in range(20)
        )
        model = train_logistic_regression(samples[:15])
        rows = build_prediction_rows(model, samples[15:])
        slices = diagnose_error_slices(rows)
        self.assertIn("model_confidence", slices)
        self.assertIn("market_alignment", slices)
        self.assertTrue(find_worst_slices(slices, min_samples=1))
