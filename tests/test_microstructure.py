import unittest
from datetime import datetime, timedelta, timezone

from btc5m_bot.coinbase import TopOfBook, Trade, enrich_with_live_microstructure
from btc5m_bot.models import FeatureVector


class MicrostructureTests(unittest.TestCase):
    def test_enrich_with_live_microstructure(self) -> None:
        now = datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc)
        features = FeatureVector(0, 0, 0, 0, 0, 240)
        trades = [
            Trade(now - timedelta(seconds=5), 1, 100, 3, "sell"),
            Trade(now - timedelta(seconds=10), 2, 100, 1, "buy"),
        ]
        top = TopOfBook(99, 4, 101, 2)
        enriched = enrich_with_live_microstructure(features, trades, top, now=now)
        self.assertGreater(enriched.trade_imbalance_30s, 0)
        self.assertGreater(enriched.coinbase_spread_bps, 0)
        self.assertGreater(enriched.book_imbalance_l1, 0)


if __name__ == "__main__":
    unittest.main()
