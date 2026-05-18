from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from .execution_backtest import BacktestTrade, ExecutionBacktestConfig, fee_per_share
from .historical import HistoricalSample


@dataclass(frozen=True)
class SnapshotQuote:
    captured_at: datetime
    slug: str
    up_best_ask: float | None
    up_best_ask_size: float | None
    down_best_ask: float | None
    down_best_ask_size: float | None


def load_snapshot_quotes(path: Path) -> dict[str, list[SnapshotQuote]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    grouped: dict[str, list[SnapshotQuote]] = {}
    for row in rows:
        quote = SnapshotQuote(
            captured_at=datetime.fromisoformat(row["captured_at"]),
            slug=row["slug"],
            up_best_ask=_optional_float(row["up_best_ask"]),
            up_best_ask_size=_optional_float(row["up_best_ask_size"]),
            down_best_ask=_optional_float(row["down_best_ask"]),
            down_best_ask_size=_optional_float(row["down_best_ask_size"]),
        )
        grouped.setdefault(quote.slug, []).append(quote)
    return {
        slug: sorted(quotes, key=lambda quote: quote.captured_at)
        for slug, quotes in grouped.items()
    }


def find_snapshot_at_or_after(
    quotes: list[SnapshotQuote],
    decision_time: datetime,
    max_delay_seconds: int,
) -> SnapshotQuote | None:
    eligible = [
        quote
        for quote in quotes
        if decision_time <= quote.captured_at <= decision_time + timedelta(seconds=max_delay_seconds)
    ]
    return eligible[0] if eligible else None


def backtest_sample_with_snapshot(
    sample: HistoricalSample,
    quote: SnapshotQuote | None,
    forecast_prob_up: float,
    config: ExecutionBacktestConfig,
) -> tuple[BacktestTrade | None, str]:
    if quote is None:
        return None, "missing_snapshot"
    if max(forecast_prob_up, 1.0 - forecast_prob_up) < config.min_confidence:
        return None, "low_confidence"

    candidates: list[tuple[str, float, float, float]] = []
    if quote.up_best_ask is not None and quote.up_best_ask_size is not None:
        up_capacity_usd = quote.up_best_ask * quote.up_best_ask_size
        up_edge = (
            forecast_prob_up
            - quote.up_best_ask
            - fee_per_share(quote.up_best_ask, config.taker_fee_rate)
        )
        candidates.append(("UP", quote.up_best_ask, up_capacity_usd, up_edge))
    if quote.down_best_ask is not None and quote.down_best_ask_size is not None:
        down_capacity_usd = quote.down_best_ask * quote.down_best_ask_size
        down_edge = (
            (1.0 - forecast_prob_up)
            - quote.down_best_ask
            - fee_per_share(quote.down_best_ask, config.taker_fee_rate)
        )
        candidates.append(("DOWN", quote.down_best_ask, down_capacity_usd, down_edge))

    if not candidates:
        return None, "missing_ask"

    decision, entry_price, capacity_usd, edge = max(candidates, key=lambda item: item[3])
    if capacity_usd < config.stake_usd:
        return None, "insufficient_snapshot_liquidity"
    if edge < config.min_edge:
        return None, "edge_too_small"

    shares = config.stake_usd / entry_price
    fee = shares * fee_per_share(entry_price, config.taker_fee_rate)
    payout = shares if decision == sample.label.upper() else 0.0
    decision_time = sample.window_start + timedelta(seconds=60)
    return (
        BacktestTrade(
            slug=sample.slug,
            label=sample.label.upper(),
            decision=decision,
            forecast_prob_up=forecast_prob_up,
            entry_price=entry_price,
            fee_per_share=fee_per_share(entry_price, config.taker_fee_rate),
            shares=shares,
            pnl_usd=payout - config.stake_usd - fee,
            edge=edge,
            fill_delay_seconds=int((quote.captured_at - decision_time).total_seconds()),
            trade_count=1,
        ),
        "traded",
    )


def _optional_float(value: str) -> float | None:
    return float(value) if value != "" else None
