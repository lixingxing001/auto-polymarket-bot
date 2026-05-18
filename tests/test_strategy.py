import unittest

from btc5m_bot.models import FeatureVector
from btc5m_bot.strategy import BaselineSignalModel


class BaselineSignalModelTests(unittest.TestCase):
    def test_bullish_features_raise_prob_up(self) -> None:
        model = BaselineSignalModel()
        bearish = model.predict(
            FeatureVector(-0.001, -0.002, 0.01, -0.2, -5.0, 120)
        )
        bullish = model.predict(
            FeatureVector(0.001, 0.002, 0.01, 0.2, 5.0, 120)
        )
        self.assertGreater(bullish.prob_up, bearish.prob_up)


if __name__ == "__main__":
    unittest.main()
