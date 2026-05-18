from math import exp

from .features import normalize_features
from .models import FeatureVector, ProbabilityForecast


class BaselineSignalModel:
    """
    A deliberately simple placeholder model.

    Its job is not to be clever. Its job is to give us a stable interface
    that can later be replaced by a calibrated model trained on real data.
    """

    def predict(self, raw: FeatureVector) -> ProbabilityForecast:
        f = normalize_features(raw)

        score = (
            18.0 * f.return_1m
            + 10.0 * f.return_5m
            + 0.012 * f.distance_to_barrier_bps
            + 0.8 * f.trade_imbalance_30s
            - 1.5 * f.realized_vol_5m
        )
        prob_up = 1.0 / (1.0 + exp(-score))
        return ProbabilityForecast(prob_up=prob_up)
