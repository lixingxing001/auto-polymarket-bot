from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .snapshot_forward_eval_cli import run_snapshot_forward_eval


def run_loop(
    iterations: int,
    interval_seconds: float,
    windows: int,
    snapshots: Path,
    archive_output: Path,
    evaluation_output: Path,
    min_train_size: int,
    min_confidence: float,
    min_edge: float,
    stake_usd: float,
    max_delay_seconds: int,
    continue_on_error: bool = False,
) -> None:
    index = 0
    while iterations == 0 or index < iterations:
        try:
            summary = run_snapshot_forward_eval(
                windows=windows,
                snapshots=snapshots,
                archive_output=archive_output,
                evaluation_output=evaluation_output,
                min_train_size=min_train_size,
                min_confidence=min_confidence,
                min_edge=min_edge,
                stake_usd=stake_usd,
                max_delay_seconds=max_delay_seconds,
            )
            print(
                {
                    "ran_at": datetime.now(timezone.utc).isoformat(),
                    **summary,
                },
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001
            print(
                {
                    "ran_at": datetime.now(timezone.utc).isoformat(),
                    "error": type(exc).__name__,
                    "message": str(exc),
                },
                file=sys.stderr,
                flush=True,
            )
            if not continue_on_error:
                raise
        index += 1
        if iterations == 0 or index < iterations:
            time.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--interval-seconds", type=float, default=300.0)
    parser.add_argument("--windows", type=int, default=288)
    parser.add_argument("--snapshots", type=Path, default=Path("data/ws_orderbook_snapshots.csv"))
    parser.add_argument("--archive-output", type=Path, default=Path("data/settled_snapshot_windows.csv"))
    parser.add_argument("--evaluation-output", type=Path, default=Path("data/forward_snapshot_evaluations.csv"))
    parser.add_argument("--min-train-size", type=int, default=200)
    parser.add_argument("--min-confidence", type=float, default=0.65)
    parser.add_argument("--min-edge", type=float, default=0.03)
    parser.add_argument("--stake-usd", type=float, default=10.0)
    parser.add_argument("--max-delay-seconds", type=int, default=30)
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()
    run_loop(
        iterations=args.iterations,
        interval_seconds=args.interval_seconds,
        windows=args.windows,
        snapshots=args.snapshots,
        archive_output=args.archive_output,
        evaluation_output=args.evaluation_output,
        min_train_size=args.min_train_size,
        min_confidence=args.min_confidence,
        min_edge=args.min_edge,
        stake_usd=args.stake_usd,
        max_delay_seconds=args.max_delay_seconds,
        continue_on_error=args.continue_on_error,
    )


if __name__ == "__main__":
    main()
