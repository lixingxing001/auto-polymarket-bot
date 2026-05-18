from __future__ import annotations

import argparse
from datetime import timedelta
from pathlib import Path

from .execution_backtest import ExecutionBacktestConfig, summarize_execution_backtest
from .historical import build_recent_historical_dataset
from .learning import chronological_split, sample_to_features, train_logistic_regression
from .snapshot_backtest import (
    backtest_sample_with_snapshot,
    find_snapshot_at_or_after,
    load_snapshot_quotes,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=288)
    parser.add_argument("--snapshots", type=Path, default=Path("data/orderbook_snapshots.csv"))
    parser.add_argument("--min-confidence", type=float, default=0.65)
    parser.add_argument("--min-edge", type=float, default=0.03)
    parser.add_argument("--stake-usd", type=float, default=10.0)
    parser.add_argument("--max-delay-seconds", type=int, default=30)
    args = parser.parse_args()

    result = build_recent_historical_dataset(windows=args.windows)
    train_samples, test_samples = chronological_split(result.samples)
    model = train_logistic_regression(train_samples)
    snapshots = load_snapshot_quotes(args.snapshots)
    config = ExecutionBacktestConfig(
        stake_usd=args.stake_usd,
        min_edge=args.min_edge,
        min_confidence=args.min_confidence,
        max_fill_delay_seconds=args.max_delay_seconds,
    )

    trades = []
    skipped: dict[str, int] = {}
    for sample in test_samples:
        decision_time = sample.window_start + timedelta(seconds=60)
        quote = find_snapshot_at_or_after(
            snapshots.get(sample.slug, []),
            decision_time=decision_time,
            max_delay_seconds=args.max_delay_seconds,
        )
        trade, reason = backtest_sample_with_snapshot(
            sample=sample,
            quote=quote,
            forecast_prob_up=model.predict_proba(sample_to_features(sample)),
            config=config,
        )
        if trade is not None:
            trades.append(trade)
        else:
            skipped[reason] = skipped.get(reason, 0) + 1

    print(
        {
            "samples": len(result.samples),
            "train_samples": len(train_samples),
            "test_samples": len(test_samples),
            "snapshot_windows": len(snapshots),
            "skipped": skipped,
            "execution": summarize_execution_backtest(tuple(trades)),
        }
    )


if __name__ == "__main__":
    main()
