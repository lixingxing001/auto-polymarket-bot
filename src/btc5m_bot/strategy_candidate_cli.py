from __future__ import annotations

import argparse
from pathlib import Path

from .candidate_strategies import (
    compare_candidate_strategy,
    load_candidate_registry,
    register_candidate,
    summarize_candidate_comparison,
    write_candidate_comparison,
)
from .historical import build_recent_historical_dataset
from .settled_snapshot_archive import load_archived_windows
from .snapshot_backtest import load_snapshot_quotes
from .strategy_guardrails import ACTIVE_STRATEGY_PARAMETERS


DEFAULT_REGISTRY = Path("strategy_candidates.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_parser = subparsers.add_parser("register")
    register_parser.add_argument("--candidate-id", required=True)
    register_parser.add_argument("--description", required=True)
    register_parser.add_argument("--rationale", required=True)
    register_parser.add_argument("--archive", type=Path, default=Path("data/settled_snapshot_windows.csv"))
    register_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    register_parser.add_argument(
        "--min-confidence",
        type=float,
        default=ACTIVE_STRATEGY_PARAMETERS.min_confidence,
    )
    register_parser.add_argument(
        "--min-edge",
        type=float,
        default=ACTIVE_STRATEGY_PARAMETERS.min_edge,
    )
    register_parser.add_argument(
        "--stake-usd",
        type=float,
        default=ACTIVE_STRATEGY_PARAMETERS.stake_usd,
    )
    register_parser.add_argument(
        "--max-delay-seconds",
        type=int,
        default=ACTIVE_STRATEGY_PARAMETERS.max_fill_delay_seconds,
    )
    register_parser.add_argument("--filter-kind", default="none")
    register_parser.add_argument("--min-abs-return-1m", type=float, default=None)
    register_parser.add_argument(
        "--min-abs-distance-to-barrier-bps",
        type=float,
        default=None,
    )

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--candidate-id", required=True)
    compare_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    compare_parser.add_argument("--archive", type=Path, default=Path("data/settled_snapshot_windows.csv"))
    compare_parser.add_argument("--snapshots", type=Path, default=Path("data/ws_orderbook_snapshots.csv"))
    compare_parser.add_argument("--windows", type=int, default=288)
    compare_parser.add_argument("--min-train-size", type=int, default=200)
    compare_parser.add_argument("--output-dir", type=Path, default=Path("data/candidate_comparisons"))

    args = parser.parse_args()
    if args.command == "register":
        archived = tuple(load_archived_windows(args.archive).values())
        if not archived:
            raise ValueError("cannot register a candidate without an archived cutoff window")
        latest_window = max(archived, key=lambda window: window.market_end_time)
        candidate = register_candidate(
            path=args.registry,
            candidate_id=args.candidate_id,
            description=args.description,
            rationale=args.rationale,
            eligible_after_market_end_time=latest_window.market_end_time,
            min_confidence=args.min_confidence,
            min_edge=args.min_edge,
            stake_usd=args.stake_usd,
            max_fill_delay_seconds=args.max_delay_seconds,
            filter_kind=args.filter_kind,
            min_abs_return_1m=args.min_abs_return_1m,
            min_abs_distance_to_barrier_bps=args.min_abs_distance_to_barrier_bps,
        )
        print(candidate.__dict__)
        return

    registry = load_candidate_registry(args.registry)
    if args.command == "list":
        print({candidate_id: candidate.__dict__ for candidate_id, candidate in registry.items()})
        return

    candidate = registry[args.candidate_id]
    archived = tuple(load_archived_windows(args.archive).values())
    historical = build_recent_historical_dataset(windows=args.windows)
    snapshots = load_snapshot_quotes(args.snapshots)
    rows = compare_candidate_strategy(
        candidate=candidate,
        archived_windows=archived,
        samples=historical.samples,
        snapshots=snapshots,
        min_train_size=args.min_train_size,
    )
    output_path = args.output_dir / f"{candidate.candidate_id}.csv"
    write_candidate_comparison(output_path, rows)
    print(
        {
            "candidate": candidate.__dict__,
            "summary": summarize_candidate_comparison(rows),
            "output": str(output_path),
        }
    )


if __name__ == "__main__":
    main()
