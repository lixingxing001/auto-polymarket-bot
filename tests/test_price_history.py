import unittest

from btc5m_bot.polymarket import PricePoint


class PriceHistoryTests(unittest.TestCase):
    def test_price_point_shape(self) -> None:
        point = PricePoint(timestamp=1, price=0.5)
        self.assertEqual(point.timestamp, 1)
        self.assertEqual(point.price, 0.5)


if __name__ == "__main__":
    unittest.main()
