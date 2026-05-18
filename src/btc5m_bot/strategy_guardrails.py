from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


FROZEN_PARAMETER_NAMES = (
    "min_confidence",
    "min_edge",
    "stake_usd",
    "max_fill_delay_seconds",
)


@dataclass(frozen=True)
class ActiveStrategyParameters:
    min_confidence: float = 0.65
    min_edge: float = 0.03
    stake_usd: float = 10.0
    max_fill_delay_seconds: int = 30


@dataclass(frozen=True)
class GuardrailPolicy:
    min_evaluations_for_review: int = 30
    min_trades_for_review: int = 10
    min_evaluations_for_change_review: int = 100
    min_trades_for_change_review: int = 30


@dataclass(frozen=True)
class ForwardLedgerSummary:
    evaluations: int
    traded_rows: int
    hold_rows: int
    wins: int
    losses: int
    win_rate: float
    total_pnl_usd: float
    avg_pnl_usd: float
    avg_edge: float
    hold_reasons: dict[str, int]


def load_forward_ledger_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summarize_forward_ledger(rows: list[dict[str, str]]) -> ForwardLedgerSummary:
    traded_rows = [row for row in rows if row["reason"] == "traded"]
    hold_rows = [row for row in rows if row["reason"] != "traded"]
    wins = sum(1 for row in traded_rows if float(row["pnl_usd"]) > 0)
    losses = sum(1 for row in traded_rows if float(row["pnl_usd"]) <= 0)
    total_pnl = sum(float(row["pnl_usd"]) for row in traded_rows)
    hold_reasons: dict[str, int] = {}
    for row in hold_rows:
        hold_reasons[row["reason"]] = hold_reasons.get(row["reason"], 0) + 1

    return ForwardLedgerSummary(
        evaluations=len(rows),
        traded_rows=len(traded_rows),
        hold_rows=len(hold_rows),
        wins=wins,
        losses=losses,
        win_rate=wins / len(traded_rows) if traded_rows else 0.0,
        total_pnl_usd=total_pnl,
        avg_pnl_usd=total_pnl / len(traded_rows) if traded_rows else 0.0,
        avg_edge=(
            sum(float(row["edge"]) for row in traded_rows) / len(traded_rows)
            if traded_rows
            else 0.0
        ),
        hold_reasons=hold_reasons,
    )


def assess_strategy_guardrails(
    summary: ForwardLedgerSummary,
    policy: GuardrailPolicy | None = None,
) -> dict:
    policy = policy or GuardrailPolicy()
    review_ready = (
        summary.evaluations >= policy.min_evaluations_for_review
        and summary.traded_rows >= policy.min_trades_for_review
    )
    change_review_ready = (
        summary.evaluations >= policy.min_evaluations_for_change_review
        and summary.traded_rows >= policy.min_trades_for_change_review
    )

    if change_review_ready:
        stage = "change_review_ready"
        allowed_actions = (
            "compare_pre_registered_candidate",
            "review_single_parameter_change",
        )
    elif review_ready:
        stage = "review_only"
        allowed_actions = (
            "analyze_failure_modes",
            "compare_pre_registered_candidate",
        )
    else:
        stage = "collecting"
        allowed_actions = (
            "collect_more_forward_data",
            "inspect_pipeline_health",
        )

    return {
        "stage": stage,
        "review_ready": review_ready,
        "change_review_ready": change_review_ready,
        "frozen_parameters": list(FROZEN_PARAMETER_NAMES) if not change_review_ready else [],
        "allowed_actions": list(allowed_actions),
        "next_review_gap": {
            "evaluations_needed": max(0, policy.min_evaluations_for_review - summary.evaluations),
            "trades_needed": max(0, policy.min_trades_for_review - summary.traded_rows),
        },
        "next_change_review_gap": {
            "evaluations_needed": max(
                0,
                policy.min_evaluations_for_change_review - summary.evaluations,
            ),
            "trades_needed": max(
                0,
                policy.min_trades_for_change_review - summary.traded_rows,
            ),
        },
    }


ACTIVE_STRATEGY_PARAMETERS = ActiveStrategyParameters()
