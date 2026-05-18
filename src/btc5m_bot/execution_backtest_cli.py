from __future__ import annotations

import argparse
from pathlib import Path

from .execution_backtest import (
    ExecutionBacktestConfig,
    run_holdout_market_aware_execution_backtest,
    run_walk_forward_market_aware_execution_backtest,
    summarize_execution_backtest,
    write_execution_backtest_csv,
)
from .historical import build_recent_historical_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=48)
    parser.add_argument("--stake-usd", type=float, default=10.0)
    parser.add_argument("--min-edge", type=float, default=0.03)
    parser.add_argument("--min-confidence", type=float, default=0.65)
    parser.add_argument("--max-fill-delay-seconds", type=int, default=30)
    parser.add_argument("--walk-forward-min-train", type=int, default=180)
    parser.add_argument("--walk-forward-test-size", type=int, default=50)
    parser.add_argument("--output", type=Path, default=Path("data/execution_backtest.csv"))
    args = parser.parse_args()

    result = build_recent_historical_dataset(windows=args.windows)
    config = ExecutionBacktestConfig(
        stake_usd=args.stake_usd,
        min_edge=args.min_edge,
        max_fill_delay_seconds=args.max_fill_delay_seconds,
        min_confidence=args.min_confidence,
    )
    trade_cache = {}
    holdout = run_holdout_market_aware_execution_backtest(
        samples=result.samples,
        config=config,
        trade_cache=trade_cache,
    )
    walk_forward = run_walk_forward_market_aware_execution_backtest(
        samples=result.samples,
        min_train_size=args.walk_forward_min_train,
        test_size=args.walk_forward_test_size,
        config=config,
        trade_cache=trade_cache,
    )
    write_execution_backtest_csv(args.output, holdout["result"].trades)
    print(
        {
            "samples": len(result.samples),
            "skipped_missing_market": result.skipped_missing_market,
            "skipped_unresolved": result.skipped_unresolved,
            "skipped_missing_candles": result.skipped_missing_candles,
            "holdout": {
                "train_samples": holdout["train_samples"],
                "test_samples": holdout["test_samples"],
                "skipped_insufficient_trade_history": holdout["result"].skipped_insufficient_trade_history,
                "skipped_no_fill": holdout["result"].skipped_no_fill,
                "skipped_edge_too_small": holdout["result"].skipped_edge_too_small,
                "skipped_low_confidence": holdout["result"].skipped_low_confidence,
                "execution": summarize_execution_backtest(holdout["result"].trades),
            },
            "walk_forward": {
                "folds": len(walk_forward["folds"]),
                "skipped_insufficient_trade_history": walk_forward["skipped_insufficient_trade_history"],
                "skipped_no_fill": walk_forward["skipped_no_fill"],
                "skipped_edge_too_small": walk_forward["skipped_edge_too_small"],
                "skipped_low_confidence": walk_forward["skipped_low_confidence"],
                "execution": walk_forward["summary"],
            },
        }
    )


if __name__ == "__main__":
    main()
