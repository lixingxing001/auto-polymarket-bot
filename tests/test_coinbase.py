import unittest
from datetime import datetime, timezone

from btc5m_bot.coinbase import Candle, build_price_only_features


class CoinbaseFeatureTests(unittest.TestCase):
    def test_build_price_only_features(self) -> None:
        candles = [
            Candle(datetime(2026, 5, 18, 10, minute, tzinfo=timezone.utc), 0, 0, price, price, 1)
            for minute, price in enumerate([100, 101, 102, 103, 104, 105])
        ]
        features = build_price_only_features(
            candles=candles,
            window_start=datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 5, 18, 10, 5, tzinfo=timezone.utc),
            now=datetime(2026, 5, 18, 10, 4, tzinfo=timezone.utc),
        )
        self.assertGreater(features.return_1m, 0)
        self.assertGreater(features.return_5m, 0)
        self.assertGreater(features.distance_to_barrier_bps, 0)
        self.assertGreater(features.return_2m, 0)
        self.assertGreater(features.return_3m, 0)
        self.assertEqual(features.seconds_to_close, 60)


if __name__ == "__main__":
    unittest.main()
