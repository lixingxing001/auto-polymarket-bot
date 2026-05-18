from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from .candidate_evidence import (
    assess_candidate_evidence,
    load_candidate_comparison_rows,
    summarize_candidate_evidence,
)
from .candidate_strategies import load_candidate_registry
from .execution_safety import (
    ExecutionSafetyConfig,
    ProposedOrder,
    assess_execution_safety,
    load_execution_ledger_rows,
    parse_execution_ledger_rows,
    summarize_execution_ledger,
)
from .strategy_guardrails import (
    assess_strategy_guardrails,
    load_forward_ledger_rows,
    summarize_forward_ledger,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--forward-ledger",
        type=Path,
        default=Path("data/forward_snapshot_evaluations.csv"),
    )
    parser.add_argument(
        "--execution-ledger",
        type=Path,
        default=Path("data/live_execution_ledger.csv"),
    )
    parser.add_argument("--registry", type=Path, default=Path("strategy_candidates.csv"))
    parser.add_argument(
        "--candidate-comparison-dir",
        type=Path,
        default=Path("data/candidate_comparisons"),
    )
    parser.add_argument("--enable-live-trading", action="store_true")
    parser.add_argument("--min-live-forward-evaluations", type=int, default=100)
    parser.add_argument("--min-live-forward-trades", type=int, default=30)
    parser.add_argument("--min-live-win-rate", type=float, default=0.55)
    parser.add_argument("--min-live-total-pnl-usd", type=float, default=0.0)
    parser.add_argument("--max-stake-usd", type=float, default=10.0)
    parser.add_argument("--max-daily-loss-usd", type=float, default=30.0)
    parser.add_argument("--max-daily-trades", type=int, default=10)
    parser.add_argument("--max-consecutive-losses", type=int, default=3)
    parser.add_argument("--slug", default=None)
    parser.add_argument("--outcome", choices=("UP", "DOWN", "up", "down"), default=None)
    parser.add_argument("--price", type=float, default=None)
    parser.add_argument("--stake-usd", type=float, default=None)
    parser.add_argument("--edge", type=float, default=None)
    parser.add_argument("--probability", type=float, default=None)
    parser.add_argument("--available-liquidity-usd", type=float, default=None)
    parser.add_argument("--seconds-to-close", type=int, default=None)
    parser.add_argument("--client-order-id", default="")
    args = parser.parse_args()

    forward_summary = summarize_forward_ledger(load_forward_ledger_rows(args.forward_ledger))
    guardrails = assess_strategy_guardrails(forward_summary)
    execution_entries = parse_execution_ledger_rows(
        load_execution_ledger_rows(args.execution_ledger)
    )
    ledger_summary = summarize_execution_ledger(execution_entries)
    config = ExecutionSafetyConfig(
        live_trading_enabled=args.enable_live_trading,
        min_live_forward_evaluations=args.min_live_forward_evaluations,
        min_live_forward_trades=args.min_live_forward_trades,
        min_live_win_rate=args.min_live_win_rate,
        min_live_total_pnl_usd=args.min_live_total_pnl_usd,
        max_stake_usd=args.max_stake_usd,
        max_daily_loss_usd=args.max_daily_loss_usd,
        max_daily_trades=args.max_daily_trades,
        max_consecutive_losses=args.max_consecutive_losses,
    )
    proposed_order = _build_proposed_order(args, parser)
    assessment = assess_execution_safety(
        forward_summary=forward_summary,
        guardrail_assessment=guardrails,
        ledger_summary=ledger_summary,
        proposed_order=proposed_order,
        config=config,
    )

    print(
        {
            "config": asdict(config),
            "forward_ledger": asdict(forward_summary),
            "guardrails": guardrails,
            "execution_ledger": asdict(ledger_summary),
            "candidate_evidence": _candidate_evidence_statuses(
                registry_path=args.registry,
                comparison_dir=args.candidate_comparison_dir,
            ),
            "proposed_order": asdict(proposed_order) if proposed_order is not None else None,
            "assessment": asdict(assessment),
        }
    )


def _build_proposed_order(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> ProposedOrder | None:
    order_fields = (
        args.slug,
        args.outcome,
        args.price,
        args.stake_usd,
        args.edge,
        args.probability,
        args.available_liquidity_usd,
        args.seconds_to_close,
    )
    if all(value is None for value in order_fields):
        return None
    if any(value is None for value in order_fields):
        parser.error(
            "order preflight requires slug, outcome, price, stake, edge, probability, liquidity and seconds-to-close"
        )
    return ProposedOrder(
        slug=args.slug,
        outcome=args.outcome,
        price=args.price,
        stake_usd=args.stake_usd,
        edge=args.edge,
        probability=args.probability,
        available_liquidity_usd=args.available_liquidity_usd,
        seconds_to_close=args.seconds_to_close,
        client_order_id=args.client_order_id,
    )


def _candidate_evidence_statuses(
    registry_path: Path,
    comparison_dir: Path,
) -> dict[str, dict]:
    statuses: dict[str, dict] = {}
    for candidate_id, candidate in load_candidate_registry(registry_path).items():
        summary = summarize_candidate_evidence(
            load_candidate_comparison_rows(comparison_dir / f"{candidate_id}.csv")
        )
        statuses[candidate_id] = {
            "filter_kind": candidate.filter_kind,
            "status": candidate.status,
            "summary": asdict(summary),
            "assessment": assess_candidate_evidence(summary),
        }
    return statuses


if __name__ == "__main__":
    main()
