from __future__ import annotations

import argparse
from pathlib import Path

from .execution_safety import ExecutionSafetyConfig
from .paper_dry_run import (
    DEFAULT_DRY_RUN_OUTPUT,
    DEFAULT_EXECUTION_LEDGER,
    DEFAULT_FORWARD_LEDGER,
    append_dry_run,
    generate_paper_dry_run,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_DRY_RUN_OUTPUT)
    parser.add_argument("--forward-ledger", type=Path, default=DEFAULT_FORWARD_LEDGER)
    parser.add_argument("--execution-ledger", type=Path, default=DEFAULT_EXECUTION_LEDGER)
    parser.add_argument("--enable-live-trading", action="store_true")
    parser.add_argument("--max-stake-usd", type=float, default=10.0)
    parser.add_argument("--max-daily-loss-usd", type=float, default=30.0)
    parser.add_argument("--max-daily-trades", type=int, default=10)
    parser.add_argument("--max-consecutive-losses", type=int, default=3)
    args = parser.parse_args()

    dry_run = generate_paper_dry_run(
        config=ExecutionSafetyConfig(
            live_trading_enabled=args.enable_live_trading,
            max_stake_usd=args.max_stake_usd,
            max_daily_loss_usd=args.max_daily_loss_usd,
            max_daily_trades=args.max_daily_trades,
            max_consecutive_losses=args.max_consecutive_losses,
        ),
        forward_ledger_path=args.forward_ledger,
        execution_ledger_path=args.execution_ledger,
    )
    append_dry_run(args.output, dry_run)
    print(dry_run)


if __name__ == "__main__":
    main()
