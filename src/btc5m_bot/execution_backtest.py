from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from .historical import HistoricalSample
from .learning import LogisticModel, sample_to_features, train_logistic_regression
from .polymarket import MarketTrade, PolymarketPublicClient


@dataclass(frozen=True)
class ExecutionBacktestConfig:
    stake_usd: float = 10.0
    min_edge: float = 0.03
    taker_fee_rate: float = 0.07
    max_fill_delay_seconds: int = 30
    min_confidence: float = 0.0


@dataclass(frozen=True)
class FillProxy:
    outcome: str
    average_price: float
    notional_usd: float
    first_fill_ts: int
    last_fill_ts: int
    trade_count: int


@dataclass(frozen=True)
class BacktestTrade:
    slug: str
    label: str
    decision: str
    forecast_prob_up: float
    entry_price: float
    fee_per_share: float
    shares: float
    pnl_usd: float
    edge: float
    fill_delay_seconds: int
    trade_count: int


@dataclass(frozen=True)
class ExecutionBacktestResult:
    trades: tuple[BacktestTrade, ...]
    skipped_insufficient_trade_history: int
    skipped_no_fill: int
    skipped_edge_too_small: int
    skipped_low_confidence: int


def build_fill_proxy(
    trades: list[MarketTrade],
    outcome: str,
    decision_ts: int,
    target_notional_usd: float,
    max_fill_delay_seconds: int,
) -> FillProxy | None:
    eligible = [
        trade
        for trade in trades
        if trade.outcome == outcome
        and trade.side == "BUY"
        and decision_ts <= trade.timestamp <= decision_ts + max_fill_delay_seconds
    ]
    eligible.sort(key=lambda trade: trade.timestamp)

    accumulated_notional = 0.0
    accumulated_shares = 0.0
    selected: list[MarketTrade] = []
    for trade in eligible:
        trade_notional = trade.price * trade.size
        accumulated_notional += trade_notional
        accumulated_shares += trade.size
        selected.append(trade)
        if accumulated_notional >= target_notional_usd:
            break

    if accumulated_notional < target_notional_usd or accumulated_shares <= 0:
        return None

    average_price = accumulated_notional / accumulated_shares
    return FillProxy(
        outcome=outcome,
        average_price=average_price,
        notional_usd=accumulated_notional,
        first_fill_ts=selected[0].timestamp,
        last_fill_ts=selected[-1].timestamp,
        trade_count=len(selected),
    )


def fee_per_share(price: float, taker_fee_rate: float) -> float:
    return taker_fee_rate * price * (1.0 - price)


def backtest_sample_with_trades(
    sample: HistoricalSample,
    trades: list[MarketTrade],
    config: ExecutionBacktestConfig,
    forecast_prob_up: float | None = None,
) -> tuple[BacktestTrade | None, str]:
    decision_ts = int((sample.window_start + timedelta(seconds=60)).timestamp())
    if not trades or min(trade.timestamp for trade in trades) > decision_ts:
        return None, "insufficient_trade_history"

    forecast_prob_up = sample.prob_up if forecast_prob_up is None else forecast_prob_up
    if max(forecast_prob_up, 1.0 - forecast_prob_up) < config.min_confidence:
        return None, "low_confidence"

    up_fill = build_fill_proxy(
        trades=trades,
        outcome="Up",
        decision_ts=decision_ts,
        target_notional_usd=config.stake_usd,
        max_fill_delay_seconds=config.max_fill_delay_seconds,
    )
    down_fill = build_fill_proxy(
        trades=trades,
        outcome="Down",
        decision_ts=decision_ts,
        target_notional_usd=config.stake_usd,
        max_fill_delay_seconds=config.max_fill_delay_seconds,
    )

    candidates: list[tuple[str, FillProxy, float]] = []
    if up_fill is not None:
        candidates.append(
            (
                "UP",
                up_fill,
                forecast_prob_up - up_fill.average_price - fee_per_share(up_fill.average_price, config.taker_fee_rate),
            )
        )
    if down_fill is not None:
        candidates.append(
            (
                "DOWN",
                down_fill,
                (1.0 - forecast_prob_up)
                - down_fill.average_price
                - fee_per_share(down_fill.average_price, config.taker_fee_rate),
            )
        )
    if not candidates:
        return None, "no_fill"

    decision, fill, edge = max(candidates, key=lambda item: item[2])
    if edge < config.min_edge:
        return None, "edge_too_small"

    shares = config.stake_usd / fill.average_price
    fee = shares * fee_per_share(fill.average_price, config.taker_fee_rate)
    payout = shares if decision == sample.label.upper() else 0.0
    pnl_usd = payout - config.stake_usd - fee
    return BacktestTrade(
        slug=sample.slug,
        label=sample.label.upper(),
        decision=decision,
        forecast_prob_up=forecast_prob_up,
        entry_price=fill.average_price,
        fee_per_share=fee_per_share(fill.average_price, config.taker_fee_rate),
        shares=shares,
        pnl_usd=pnl_usd,
        edge=edge,
        fill_delay_seconds=fill.first_fill_ts - decision_ts,
        trade_count=fill.trade_count,
    ), "traded"


def run_execution_backtest(
    samples: tuple[HistoricalSample, ...],
    polymarket: PolymarketPublicClient | None = None,
    config: ExecutionBacktestConfig | None = None,
    model: LogisticModel | None = None,
    trade_cache: dict[str, list[MarketTrade]] | None = None,
    max_workers: int = 8,
) -> ExecutionBacktestResult:
    polymarket = polymarket or PolymarketPublicClient()
    config = config or ExecutionBacktestConfig()
    trades: list[BacktestTrade] = []
    skipped_insufficient_trade_history = 0
    skipped_no_fill = 0
    skipped_edge_too_small = 0
    skipped_low_confidence = 0
    trade_cache = trade_cache or {}

    missing_samples = [sample for sample in samples if sample.condition_id not in trade_cache]
    if missing_samples:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            fetched = list(
                executor.map(
                    _fetch_market_trades_for_sample,
                    [(polymarket, sample) for sample in missing_samples],
                )
            )
        for sample, market_trades in zip(missing_samples, fetched, strict=True):
            trade_cache[sample.condition_id] = market_trades

    for sample in samples:
        market_trades = trade_cache[sample.condition_id]
        simulated, reason = backtest_sample_with_trades(
            sample=sample,
            trades=market_trades,
            config=config,
            forecast_prob_up=(
                model.predict_proba(sample_to_features(sample))
                if model is not None
                else sample.prob_up
            ),
        )
        if simulated is not None:
            trades.append(simulated)
        elif reason == "insufficient_trade_history":
            skipped_insufficient_trade_history += 1
        elif reason == "no_fill":
            skipped_no_fill += 1
        elif reason == "edge_too_small":
            skipped_edge_too_small += 1
        elif reason == "low_confidence":
            skipped_low_confidence += 1

    return ExecutionBacktestResult(
        trades=tuple(trades),
        skipped_insufficient_trade_history=skipped_insufficient_trade_history,
        skipped_no_fill=skipped_no_fill,
        skipped_edge_too_small=skipped_edge_too_small,
        skipped_low_confidence=skipped_low_confidence,
    )


def _fetch_market_trades_for_sample(
    args: tuple[PolymarketPublicClient, HistoricalSample]
) -> list[MarketTrade]:
    polymarket, sample = args
    decision_ts = int((sample.window_start + timedelta(seconds=60)).timestamp())
    try:
        return polymarket.get_market_trades(
            condition_id=sample.condition_id,
            stop_at_or_before_ts=decision_ts,
        )
    except Exception:  # noqa: BLE001
        return []


def run_holdout_market_aware_execution_backtest(
    samples: tuple[HistoricalSample, ...],
    train_fraction: float = 0.7,
    polymarket: PolymarketPublicClient | None = None,
    config: ExecutionBacktestConfig | None = None,
    trade_cache: dict[str, list[MarketTrade]] | None = None,
) -> dict:
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    split_index = int(len(samples) * train_fraction)
    train_samples = samples[:split_index]
    test_samples = samples[split_index:]
    model = train_logistic_regression(train_samples)
    trade_cache = trade_cache or {}
    result = run_execution_backtest(
        samples=test_samples,
        polymarket=polymarket,
        config=config,
        model=model,
        trade_cache=trade_cache,
    )
    return {
        "train_samples": len(train_samples),
        "test_samples": len(test_samples),
        "result": result,
    }


def run_walk_forward_market_aware_execution_backtest(
    samples: tuple[HistoricalSample, ...],
    min_train_size: int,
    test_size: int,
    polymarket: PolymarketPublicClient | None = None,
    config: ExecutionBacktestConfig | None = None,
    trade_cache: dict[str, list[MarketTrade]] | None = None,
) -> dict:
    if min_train_size <= 0 or test_size <= 0:
        raise ValueError("min_train_size and test_size must be positive")
    if len(samples) < min_train_size + test_size:
        raise ValueError("not enough samples for walk-forward execution backtest")

    folds: list[ExecutionBacktestResult] = []
    trade_cache = trade_cache or {}
    train_end = min_train_size
    while train_end + test_size <= len(samples):
        train_samples = samples[:train_end]
        test_samples = samples[train_end : train_end + test_size]
        model = train_logistic_regression(train_samples)
        folds.append(
            run_execution_backtest(
                samples=test_samples,
                polymarket=polymarket,
                config=config,
                model=model,
                trade_cache=trade_cache,
            )
        )
        train_end += test_size

    combined_trades = tuple(trade for fold in folds for trade in fold.trades)
    return {
        "folds": folds,
        "combined_trades": combined_trades,
        "summary": summarize_execution_backtest(combined_trades),
        "skipped_insufficient_trade_history": sum(fold.skipped_insufficient_trade_history for fold in folds),
        "skipped_no_fill": sum(fold.skipped_no_fill for fold in folds),
        "skipped_edge_too_small": sum(fold.skipped_edge_too_small for fold in folds),
        "skipped_low_confidence": sum(fold.skipped_low_confidence for fold in folds),
    }


def summarize_execution_backtest(trades: tuple[BacktestTrade, ...]) -> dict:
    total_pnl = sum(trade.pnl_usd for trade in trades)
    wins = sum(1 for trade in trades if trade.pnl_usd > 0)
    return {
        "trades": len(trades),
        "wins": wins,
        "win_rate": wins / len(trades) if trades else 0.0,
        "total_pnl_usd": total_pnl,
        "avg_pnl_usd": total_pnl / len(trades) if trades else 0.0,
        "avg_entry_price": sum(trade.entry_price for trade in trades) / len(trades) if trades else 0.0,
        "avg_edge": sum(trade.edge for trade in trades) / len(trades) if trades else 0.0,
        "avg_fill_delay_seconds": sum(trade.fill_delay_seconds for trade in trades) / len(trades) if trades else 0.0,
    }


def write_execution_backtest_csv(path: Path, trades: tuple[BacktestTrade, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(BacktestTrade.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for trade in trades:
            writer.writerow(trade.__dict__)
