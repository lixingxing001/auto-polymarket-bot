import unittest
from datetime import datetime, timezone

from btc5m_bot.polymarket import (
    BookLevel,
    OrderBookSnapshot,
    btc_5m_slug_for,
)


class PolymarketHelpersTests(unittest.TestCase):
    def test_slug_uses_five_minute_window_start(self) -> None:
        moment = datetime(2026, 5, 18, 10, 12, 44, tzinfo=timezone.utc)
        self.assertEqual(btc_5m_slug_for(moment), "btc-updown-5m-1779099000")

    def test_best_prices_are_computed_from_unsorted_levels(self) -> None:
        book = OrderBookSnapshot(
            token_id="x",
            bids=(BookLevel(0.01, 10), BookLevel(0.53, 20), BookLevel(0.20, 5)),
            asks=(BookLevel(0.99, 10), BookLevel(0.55, 15), BookLevel(0.70, 3)),
            tick_size=0.01,
            min_order_size=5,
        )
        self.assertEqual(book.best_bid.price, 0.53)
        self.assertEqual(book.best_ask.price, 0.55)


if __name__ == "__main__":
    unittest.main()
