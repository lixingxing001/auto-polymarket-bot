from __future__ import annotations

import argparse
from pathlib import Path

from .active_strategy import (
    DEFAULT_ACTIVE_STRATEGY_STATE,
    active_strategy_to_execution_config,
    load_optional_active_strategy_state,
)
from .execution_backtest import ExecutionBacktestConfig
from .forward_snapshot_eval import evaluate_settled_snapshot_windows
from .historical import build_recent_historical_dataset
from .settled_snapshot_archive import (
    archive_settled_snapshot_windows,
    load_archived_windows,
)
from .snapshot_backtest import load_snapshot_quotes
from .strategy_guardrails import ACTIVE_STRATEGY_PARAMETERS


def run_snapshot_forward_eval(
    windows: int = 288,
    snapshots: Path = Path("data/ws_orderbook_snapshots.csv"),
    archive_output: Path = Path("data/settled_snapshot_windows.csv"),
    evaluation_output: Path = Path("data/forward_snapshot_evaluations.csv"),
    min_train_size: int = 200,
    min_confidence: float = ACTIVE_STRATEGY_PARAMETERS.min_confidence,
    min_edge: float = ACTIVE_STRATEGY_PARAMETERS.min_edge,
    stake_usd: float = ACTIVE_STRATEGY_PARAMETERS.stake_usd,
    max_delay_seconds: int = ACTIVE_STRATEGY_PARAMETERS.max_fill_delay_seconds,
    archive_only: bool = False,
    strategy_state_path: Path | None = None,
) -> dict:
    archive_summary = archive_settled_snapshot_windows(
        snapshot_path=snapshots,
        archive_path=archive_output,
    )
    if archive_only:
        return {"archive": archive_summary}

    archived_windows = tuple(load_archived_windows(archive_output).values())
    historical = build_recent_historical_dataset(windows=windows)
    loaded_snapshots = load_snapshot_quotes(snapshots)
    active_strategy_state = (
        load_optional_active_strategy_state(strategy_state_path)
        if strategy_state_path is not None
        else None
    )
    config = (
        active_strategy_to_execution_config(active_strategy_state)
        if active_strategy_state is not None
        else ExecutionBacktestConfig(
            stake_usd=stake_usd,
            min_edge=min_edge,
            min_confidence=min_confidence,
            max_fill_delay_seconds=max_delay_seconds,
        )
    )
    evaluation_summary = evaluate_settled_snapshot_windows(
        archived_windows=archived_windows,
        samples=historical.samples,
        snapshots=loaded_snapshots,
        output_path=evaluation_output,
        min_train_size=min_train_size,
        config=config,
        active_strategy_state=active_strategy_state,
    )
    return {
        "archive": archive_summary,
        "historical_samples": len(historical.samples),
        "evaluation": evaluation_summary,
        "active_strategy": (
            {
                "source_candidate_id": active_strategy_state.source_candidate_id,
                "filter_kind": active_strategy_state.filter_kind,
                "live_trading_enabled": active_strategy_state.live_trading_enabled,
            }
            if active_strategy_state is not None
            else {"source_candidate_id": "baseline", "filter_kind": "none"}
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
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
    parser.add_argument("--strategy-state", type=Path, default=DEFAULT_ACTIVE_STRATEGY_STATE)
    parser.add_argument("--ignore-strategy-state", action="store_true")
    parser.add_argument("--archive-only", action="store_true")
    args = parser.parse_args()
    print(
        run_snapshot_forward_eval(
            windows=args.windows,
            snapshots=args.snapshots,
            archive_output=args.archive_output,
            evaluation_output=args.evaluation_output,
            min_train_size=args.min_train_size,
            min_confidence=args.min_confidence,
            min_edge=args.min_edge,
            stake_usd=args.stake_usd,
            max_delay_seconds=args.max_delay_seconds,
            archive_only=args.archive_only,
            strategy_state_path=None if args.ignore_strategy_state else args.strategy_state,
        )
    )


if __name__ == "__main__":
    main()
