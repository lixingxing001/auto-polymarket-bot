from __future__ import annotations

import argparse
from pathlib import Path

from .historical import build_recent_historical_dataset
from .snapshot_backtest import load_snapshot_quotes
from .snapshot_coverage import compute_snapshot_coverage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=288)
    parser.add_argument("--snapshots", type=Path, default=Path("data/orderbook_snapshots.csv"))
    parser.add_argument("--min-test-windows", type=int, default=30)
    args = parser.parse_args()

    result = build_recent_historical_dataset(windows=args.windows)
    snapshots = load_snapshot_quotes(args.snapshots)
    coverage = compute_snapshot_coverage(
        samples=result.samples,
        recorded_slugs=set(snapshots),
    )
    print(coverage.as_dict(min_test_windows=args.min_test_windows))


if __name__ == "__main__":
    main()
