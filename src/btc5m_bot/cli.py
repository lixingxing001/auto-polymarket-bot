from .models import FeatureVector, MarketQuote
from .risk import RiskConfig, RiskManager
from .strategy import BaselineSignalModel


def main() -> None:
    features = FeatureVector(
        return_1m=0.0012,
        return_5m=0.0028,
        realized_vol_5m=0.006,
        trade_imbalance_30s=0.35,
        distance_to_barrier_bps=8.0,
        seconds_to_close=120,
    )
    quote = MarketQuote(
        up_ask=0.53,
        down_ask=0.49,
        up_liquidity_usd=500.0,
        down_liquidity_usd=450.0,
    )

    model = BaselineSignalModel()
    forecast = model.predict(features)
    decision = RiskManager(RiskConfig()).decide(
        forecast=forecast,
        quote=quote,
        seconds_to_close=features.seconds_to_close,
    )

    print(
        {
            "prob_up": round(forecast.prob_up, 4),
            "decision": decision.side,
            "edge": round(decision.expected_edge, 4),
            "size_usd": round(decision.size_usd, 2),
            "reason": decision.reason,
        }
    )


if __name__ == "__main__":
    main()
