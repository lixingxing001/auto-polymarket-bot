from __future__ import annotations

import argparse
from pathlib import Path

from .execution_backtest import (
    ExecutionBacktestConfig,
    run_execution_backtest,
    summarize_execution_backtest,
    write_execution_backtest_csv,
)
from .historical import build_recent_historical_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=48)
    parser.add_argument("--stake-usd", type=float, default=10.0)
    parser.add_argument("--min-edge", type=float, default=0.03)
    parser.add_argument("--max-fill-delay-seconds", type=int, default=30)
    parser.add_argument("--output", type=Path, default=Path("data/execution_backtest.csv"))
    args = parser.parse_args()

    result = build_recent_historical_dataset(windows=args.windows)
    backtest = run_execution_backtest(
        samples=result.samples,
        config=ExecutionBacktestConfig(
            stake_usd=args.stake_usd,
            min_edge=args.min_edge,
            max_fill_delay_seconds=args.max_fill_delay_seconds,
        ),
    )
    write_execution_backtest_csv(args.output, backtest.trades)
    print(
        {
            "samples": len(result.samples),
            "skipped_missing_market": result.skipped_missing_market,
            "skipped_unresolved": result.skipped_unresolved,
            "skipped_missing_candles": result.skipped_missing_candles,
            "skipped_insufficient_trade_history": backtest.skipped_insufficient_trade_history,
            "skipped_no_fill": backtest.skipped_no_fill,
            "skipped_edge_too_small": backtest.skipped_edge_too_small,
            "execution": summarize_execution_backtest(backtest.trades),
        }
    )


if __name__ == "__main__":
    main()
