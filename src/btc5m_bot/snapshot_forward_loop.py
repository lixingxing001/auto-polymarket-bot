from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .candidate_strategies import (
    compare_candidate_strategy,
    load_candidate_registry,
    summarize_candidate_comparison,
    write_candidate_comparison,
)
from .historical import build_recent_historical_dataset
from .settled_snapshot_archive import load_archived_windows
from .snapshot_backtest import load_snapshot_quotes
from .snapshot_forward_eval_cli import run_snapshot_forward_eval
from .active_strategy import DEFAULT_ACTIVE_STRATEGY_STATE
from .strategy_guardrails import ACTIVE_STRATEGY_PARAMETERS


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
    candidate_registry: Path | None = None,
    candidate_output_dir: Path | None = None,
    strategy_state_path: Path | None = DEFAULT_ACTIVE_STRATEGY_STATE,
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
                strategy_state_path=strategy_state_path,
            )
            candidate_summaries = {}
            if candidate_registry is not None and candidate_output_dir is not None:
                archived_windows = tuple(load_archived_windows(archive_output).values())
                historical = build_recent_historical_dataset(windows=windows)
                snapshot_quotes = load_snapshot_quotes(snapshots)
                for candidate_id, candidate in load_candidate_registry(candidate_registry).items():
                    rows = compare_candidate_strategy(
                        candidate=candidate,
                        archived_windows=archived_windows,
                        samples=historical.samples,
                        snapshots=snapshot_quotes,
                        min_train_size=min_train_size,
                    )
                    write_candidate_comparison(
                        candidate_output_dir / f"{candidate_id}.csv",
                        rows,
                    )
                    candidate_summaries[candidate_id] = summarize_candidate_comparison(rows)
            print(
                {
                    "ran_at": datetime.now(timezone.utc).isoformat(),
                    **summary,
                    "candidate_summaries": candidate_summaries,
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
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=ACTIVE_STRATEGY_PARAMETERS.min_confidence,
    )
    parser.add_argument(
        "--min-edge",
        type=float,
        default=ACTIVE_STRATEGY_PARAMETERS.min_edge,
    )
    parser.add_argument(
        "--stake-usd",
        type=float,
        default=ACTIVE_STRATEGY_PARAMETERS.stake_usd,
    )
    parser.add_argument(
        "--max-delay-seconds",
        type=int,
        default=ACTIVE_STRATEGY_PARAMETERS.max_fill_delay_seconds,
    )
    parser.add_argument(
        "--candidate-registry",
        type=Path,
        default=Path("strategy_candidates.csv"),
    )
    parser.add_argument(
        "--candidate-output-dir",
        type=Path,
        default=Path("data/candidate_comparisons"),
    )
    parser.add_argument("--strategy-state", type=Path, default=DEFAULT_ACTIVE_STRATEGY_STATE)
    parser.add_argument("--ignore-strategy-state", action="store_true")
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
        candidate_registry=args.candidate_registry,
        candidate_output_dir=args.candidate_output_dir,
        strategy_state_path=None if args.ignore_strategy_state else args.strategy_state,
        continue_on_error=args.continue_on_error,
    )


if __name__ == "__main__":
    main()
