from dataclasses import dataclass

from .models import MarketQuote, ProbabilityForecast, TradeDecision


@dataclass(frozen=True)
class RiskConfig:
    bankroll_usd: float = 1_000.0
    min_edge: float = 0.03
    max_bankroll_fraction: float = 0.02
    max_liquidity_fraction: float = 0.10
    min_seconds_to_close: int = 45
    taker_fee_rate: float = 0.07


class RiskManager:
    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def decide(
        self,
        forecast: ProbabilityForecast,
        quote: MarketQuote,
        seconds_to_close: int,
    ) -> TradeDecision:
        if seconds_to_close < self.config.min_seconds_to_close:
            return TradeDecision("HOLD", 0.0, 0.0, "too_late")

        up_fee = self._fee_per_share(quote.up_ask)
        down_fee = self._fee_per_share(quote.down_ask)
        up_edge = forecast.prob_up - quote.up_ask - up_fee
        down_edge = forecast.prob_down - quote.down_ask - down_fee

        if max(up_edge, down_edge) < self.config.min_edge:
            return TradeDecision("HOLD", max(up_edge, down_edge), 0.0, "edge_too_small")

        if up_edge >= down_edge:
            side = "UP"
            edge = up_edge
            available_liquidity = quote.up_liquidity_usd
        else:
            side = "DOWN"
            edge = down_edge
            available_liquidity = quote.down_liquidity_usd

        bankroll_cap = self.config.bankroll_usd * self.config.max_bankroll_fraction
        liquidity_cap = available_liquidity * self.config.max_liquidity_fraction
        size_usd = min(bankroll_cap, liquidity_cap)

        if size_usd <= 0:
            return TradeDecision("HOLD", edge, 0.0, "no_liquidity")

        return TradeDecision(side, edge, size_usd, "edge_passed")

    def _fee_per_share(self, price: float) -> float:
        return self.config.taker_fee_rate * price * (1.0 - price)
