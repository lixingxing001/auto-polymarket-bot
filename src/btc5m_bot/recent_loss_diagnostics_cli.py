from __future__ import annotations

import argparse
from pathlib import Path

from .recent_loss_diagnostics import (
    DEFAULT_FEATURE_CACHE,
    DEFAULT_FORWARD_LEDGER,
    DEFAULT_RECENT_LOSS_REPORT,
    write_recent_loss_diagnostics_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward-ledger", type=Path, default=DEFAULT_FORWARD_LEDGER)
    parser.add_argument("--feature-cache", type=Path, default=DEFAULT_FEATURE_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_RECENT_LOSS_REPORT)
    parser.add_argument("--recent-trades", type=int, default=12)
    parser.add_argument("--min-slice-trades", type=int, default=3)
    args = parser.parse_args()

    print(
        write_recent_loss_diagnostics_report(
            output_path=args.output,
            forward_ledger_path=args.forward_ledger,
            feature_cache_path=args.feature_cache,
            recent_trade_count=args.recent_trades,
            min_slice_trades=args.min_slice_trades,
        )
    )


if __name__ == "__main__":
    main()
