from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureVector:
    return_1m: float
    return_5m: float
    realized_vol_5m: float
    trade_imbalance_30s: float
    distance_to_barrier_bps: float
    seconds_to_close: int
    return_2m: float = 0.0
    return_3m: float = 0.0
    body_1m_bps: float = 0.0
    range_1m_bps: float = 0.0
    range_5m_bps: float = 0.0
    volume_ratio_1m_vs_5m: float = 0.0
    coinbase_spread_bps: float = 0.0
    book_imbalance_l1: float = 0.0
    polymarket_up_price: float = 0.5
    polymarket_down_price: float = 0.5
    polymarket_prob_gap: float = 0.0


@dataclass(frozen=True)
class MarketQuote:
    up_ask: float
    down_ask: float
    up_liquidity_usd: float
    down_liquidity_usd: float


@dataclass(frozen=True)
class ProbabilityForecast:
    prob_up: float

    @property
    def prob_down(self) -> float:
        return 1.0 - self.prob_up


@dataclass(frozen=True)
class TradeDecision:
    side: str
    expected_edge: float
    size_usd: float
    reason: str
