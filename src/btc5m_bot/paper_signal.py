from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from .coinbase import (
    CoinbaseExchangeClient,
    build_price_only_features,
    enrich_with_live_microstructure,
)
from .polymarket import PolymarketPublicClient, floor_to_five_minutes
from .risk import RiskConfig, RiskManager
from .strategy import BaselineSignalModel


def generate_paper_signal(now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    polymarket = PolymarketPublicClient()
    coinbase = CoinbaseExchangeClient()

    market = polymarket.find_live_btc_5m_market(now=now)
    try:
        quote = polymarket.quote_for_market(market)
    except LookupError as exc:
        return {
            "timestamp": now.isoformat(),
            "slug": market.slug,
            "title": market.title,
            "seconds_to_close": max(0, int((market.end_time - now).total_seconds())),
            "decision": "HOLD",
            "reason": str(exc),
        }

    candles = coinbase.get_recent_minute_candles(now=now)
    features = build_price_only_features(
        candles=candles,
        window_start=floor_to_five_minutes(now),
        window_end=market.end_time,
        now=now,
    )
    features = enrich_with_live_microstructure(
        features=features,
        trades=coinbase.get_recent_trades(),
        top_of_book=coinbase.get_top_of_book(),
        now=now,
    )

    forecast = BaselineSignalModel().predict(features)
    decision = RiskManager(RiskConfig()).decide(
        forecast=forecast,
        quote=quote,
        seconds_to_close=features.seconds_to_close,
    )

    return {
        "timestamp": now.isoformat(),
        "slug": market.slug,
        "title": market.title,
        "seconds_to_close": features.seconds_to_close,
        "prob_up": round(forecast.prob_up, 6),
        "up_ask": quote.up_ask,
        "down_ask": quote.down_ask,
        "up_liquidity_usd": round(quote.up_liquidity_usd, 6),
        "down_liquidity_usd": round(quote.down_liquidity_usd, 6),
        "decision": decision.side,
        "edge": round(decision.expected_edge, 6),
        "size_usd": round(decision.size_usd, 6),
        "reason": decision.reason,
        "features": asdict(features),
    }
