from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from .active_strategy import active_strategy_allows_trade, load_optional_active_strategy_state
from .coinbase import (
    CoinbaseExchangeClient,
    build_price_only_features,
    enrich_with_live_microstructure,
)
from .models import TradeDecision
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

    active_strategy = load_optional_active_strategy_state()
    risk_config = (
        RiskConfig(
            min_edge=active_strategy.min_edge,
            min_confidence=active_strategy.min_confidence,
        )
        if active_strategy is not None
        else RiskConfig()
    )
    forecast = BaselineSignalModel().predict(features)
    decision = RiskManager(risk_config).decide(
        forecast=forecast,
        quote=quote,
        seconds_to_close=features.seconds_to_close,
    )
    if (
        active_strategy is not None
        and decision.side != "HOLD"
        and not active_strategy_allows_trade(active_strategy, features, decision.side)
    ):
        decision = TradeDecision(
            "HOLD",
            decision.expected_edge,
            0.0,
            "active_strategy_filter",
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
        "active_strategy": (
            {
                "source_candidate_id": active_strategy.source_candidate_id,
                "filter_kind": active_strategy.filter_kind,
                "live_trading_enabled": active_strategy.live_trading_enabled,
            }
            if active_strategy is not None
            else {"source_candidate_id": "baseline", "filter_kind": "none"}
        ),
        "features": asdict(features),
    }
