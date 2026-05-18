import unittest

from btc5m_bot.models import MarketQuote, ProbabilityForecast
from btc5m_bot.risk import RiskConfig, RiskManager


class RiskManagerTests(unittest.TestCase):
    def test_hold_when_edge_is_too_small(self) -> None:
        decision = RiskManager(RiskConfig(min_confidence=0.5)).decide(
            forecast=ProbabilityForecast(prob_up=0.56),
            quote=MarketQuote(0.54, 0.48, 500.0, 500.0),
            seconds_to_close=120,
        )
        self.assertEqual(decision.side, "HOLD")
        self.assertEqual(decision.reason, "edge_too_small")

    def test_hold_when_confidence_is_too_low(self) -> None:
        decision = RiskManager(RiskConfig()).decide(
            forecast=ProbabilityForecast(prob_up=0.56),
            quote=MarketQuote(0.40, 0.62, 500.0, 500.0),
            seconds_to_close=120,
        )
        self.assertEqual(decision.side, "HOLD")
        self.assertEqual(decision.reason, "low_confidence")

    def test_trade_when_edge_passes(self) -> None:
        decision = RiskManager(RiskConfig()).decide(
            forecast=ProbabilityForecast(prob_up=0.66),
            quote=MarketQuote(0.55, 0.47, 500.0, 500.0),
            seconds_to_close=120,
        )
        self.assertEqual(decision.side, "UP")
        self.assertEqual(decision.reason, "edge_passed")
        self.assertGreater(decision.size_usd, 0.0)

    def test_hold_when_window_is_nearly_closed(self) -> None:
        decision = RiskManager(RiskConfig()).decide(
            forecast=ProbabilityForecast(prob_up=0.70),
            quote=MarketQuote(0.55, 0.47, 500.0, 500.0),
            seconds_to_close=20,
        )
        self.assertEqual(decision.side, "HOLD")
        self.assertEqual(decision.reason, "too_late")


if __name__ == "__main__":
    unittest.main()
