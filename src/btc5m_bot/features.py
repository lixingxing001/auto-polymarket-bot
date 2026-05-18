from .models import FeatureVector


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def normalize_features(features: FeatureVector) -> FeatureVector:
    """Keep raw feature spikes from dominating a simple baseline model."""
    return FeatureVector(
        return_1m=clamp(features.return_1m, -0.02, 0.02),
        return_5m=clamp(features.return_5m, -0.05, 0.05),
        realized_vol_5m=clamp(features.realized_vol_5m, 0.0, 0.10),
        trade_imbalance_30s=clamp(features.trade_imbalance_30s, -1.0, 1.0),
        distance_to_barrier_bps=clamp(features.distance_to_barrier_bps, -100.0, 100.0),
        seconds_to_close=max(0, features.seconds_to_close),
        return_2m=clamp(features.return_2m, -0.03, 0.03),
        return_3m=clamp(features.return_3m, -0.04, 0.04),
        body_1m_bps=clamp(features.body_1m_bps, -100.0, 100.0),
        range_1m_bps=clamp(features.range_1m_bps, 0.0, 200.0),
        range_5m_bps=clamp(features.range_5m_bps, 0.0, 300.0),
        volume_ratio_1m_vs_5m=clamp(features.volume_ratio_1m_vs_5m, 0.0, 10.0),
        coinbase_spread_bps=clamp(features.coinbase_spread_bps, 0.0, 100.0),
        book_imbalance_l1=clamp(features.book_imbalance_l1, -1.0, 1.0),
        polymarket_up_price=clamp(features.polymarket_up_price, 0.0, 1.0),
        polymarket_down_price=clamp(features.polymarket_down_price, 0.0, 1.0),
        polymarket_prob_gap=clamp(features.polymarket_prob_gap, -1.0, 1.0),
    )
