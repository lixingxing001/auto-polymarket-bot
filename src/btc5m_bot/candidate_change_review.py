from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .candidate_evidence import (
    assess_candidate_evidence,
    load_candidate_comparison_rows,
    summarize_candidate_evidence,
)
from .candidate_strategies import load_candidate_registry
from .strategy_guardrails import (
    assess_strategy_guardrails,
    load_forward_ledger_rows,
    summarize_forward_ledger,
)


DEFAULT_FORWARD_LEDGER = Path("data/forward_snapshot_evaluations.csv")
DEFAULT_REGISTRY = Path("strategy_candidates.csv")
DEFAULT_COMPARISON_DIR = Path("data/candidate_comparisons")
DEFAULT_CHANGE_REVIEW_REPORT = Path("candidate_change_review_report.md")


@dataclass(frozen=True)
class CandidateChangeReviewPolicy:
    min_delta_pnl_usd: float = 0.0
    min_candidate_total_pnl_usd: float = 0.0
    min_candidate_trades: int = 10
    min_trade_retention: float = 0.50


@dataclass(frozen=True)
class CandidateChangeReview:
    candidate_id: str
    filter_kind: str
    review_ready: bool
    change_quality_passed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateChangeReviewDecision:
    status: str
    selected_candidate_id: str
    change_allowed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    metrics: dict[str, Any] = field(default_factory=dict)


def build_candidate_change_review_report(
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
    registry_path: Path = DEFAULT_REGISTRY,
    comparison_dir: Path = DEFAULT_COMPARISON_DIR,
    policy: CandidateChangeReviewPolicy | None = None,
) -> dict[str, Any]:
    policy = policy or CandidateChangeReviewPolicy()
    forward_summary = summarize_forward_ledger(load_forward_ledger_rows(forward_ledger_path))
    guardrails = assess_strategy_guardrails(forward_summary)
    reviews = []
    for candidate_id, candidate in load_candidate_registry(registry_path).items():
        rows = load_candidate_comparison_rows(comparison_dir / f"{candidate_id}.csv")
        reviews.append(
            review_candidate_change(
                candidate_id=candidate_id,
                filter_kind=candidate.filter_kind,
                rows=rows,
                policy=policy,
            )
        )
    decision = decide_candidate_change(guardrails=guardrails, reviews=tuple(reviews))
    return {
        "decision": decision.__dict__,
        "guardrails": guardrails,
        "forward_summary": forward_summary.__dict__,
        "candidate_reviews": [review.__dict__ for review in reviews],
        "policy": policy.__dict__,
    }


def review_candidate_change(
    candidate_id: str,
    filter_kind: str,
    rows: list[dict[str, str]],
    policy: CandidateChangeReviewPolicy | None = None,
) -> CandidateChangeReview:
    policy = policy or CandidateChangeReviewPolicy()
    evidence_summary = summarize_candidate_evidence(rows)
    evidence_assessment = assess_candidate_evidence(evidence_summary)
    metrics = {
        **evidence_summary.__dict__,
        **_trade_quality_metrics(rows),
    }
    blockers: list[str] = []
    warnings: list[str] = []
    if not evidence_assessment["review_ready"]:
        blockers.append("candidate_evidence_not_review_ready")
    if evidence_summary.delta_pnl_usd <= policy.min_delta_pnl_usd:
        blockers.append("delta_pnl_not_positive")
    if evidence_summary.candidate_total_pnl_usd <= policy.min_candidate_total_pnl_usd:
        blockers.append("candidate_pnl_not_positive")
    if evidence_summary.candidate_trades < policy.min_candidate_trades:
        blockers.append("insufficient_candidate_trades")
    if metrics["trade_retention"] < policy.min_trade_retention:
        blockers.append("candidate_trade_retention_too_low")
    if metrics["candidate_win_rate"] < 0.50:
        warnings.append("candidate_win_rate_below_half")
    if metrics["candidate_win_rate"] < metrics["active_win_rate"]:
        warnings.append("candidate_win_rate_below_active")
    return CandidateChangeReview(
        candidate_id=candidate_id,
        filter_kind=filter_kind,
        review_ready=evidence_assessment["review_ready"],
        change_quality_passed=not blockers,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        metrics=metrics,
    )


def decide_candidate_change(
    guardrails: dict[str, Any],
    reviews: tuple[CandidateChangeReview, ...],
) -> CandidateChangeReviewDecision:
    quality_passed_reviews = sorted(
        (review for review in reviews if review.change_quality_passed),
        key=lambda item: (
            item.metrics["delta_pnl_usd"],
            item.metrics["candidate_total_pnl_usd"],
        ),
        reverse=True,
    )
    failed_reviews = sorted(
        (review for review in reviews if not review.change_quality_passed),
        key=lambda item: (
            item.review_ready,
            item.metrics["delta_pnl_usd"],
            item.metrics["candidate_total_pnl_usd"],
        ),
        reverse=True,
    )
    selected = quality_passed_reviews[0] if quality_passed_reviews else None
    best_failed = failed_reviews[0] if failed_reviews else None
    blockers: list[str] = []
    warnings: list[str] = []
    if not guardrails["change_review_ready"]:
        blockers.append(f"guardrail_stage_{guardrails['stage']}")
    if not reviews:
        blockers.append("no_candidate_available")
    elif selected is None:
        blockers.append("no_candidate_passed_change_quality")
    elif selected.metrics["candidate_win_rate"] < 0.55:
        warnings.append("selected_candidate_win_rate_below_canary_floor")

    change_allowed = not blockers
    status = "CHANGE_APPROVED_FOR_MANUAL_FREEZE" if change_allowed else "DEFER_CHANGE"
    return CandidateChangeReviewDecision(
        status=status,
        selected_candidate_id=selected.candidate_id if selected else "",
        change_allowed=change_allowed,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        metrics={
            "guardrail_stage": guardrails["stage"],
            "guardrail_change_review_ready": guardrails["change_review_ready"],
            "candidate_count": len(reviews),
            "quality_passed_candidates": [
                review.candidate_id for review in reviews if review.change_quality_passed
            ],
            "best_failed_candidate_id": best_failed.candidate_id if best_failed else "",
            "selected_delta_pnl_usd": selected.metrics["delta_pnl_usd"] if selected else 0.0,
            "selected_candidate_total_pnl_usd": (
                selected.metrics["candidate_total_pnl_usd"] if selected else 0.0
            ),
            "selected_candidate_win_rate": (
                selected.metrics["candidate_win_rate"] if selected else 0.0
            ),
        },
    )


def render_candidate_change_review_markdown(report: dict[str, Any]) -> str:
    decision = report["decision"]
    guardrails = report["guardrails"]
    forward = report["forward_summary"]
    lines = [
        "# Candidate Change Review Report",
        "",
        "## Decision",
        "",
        f"- status: {decision['status']}",
        f"- selected_candidate_id: {_display_candidate_id(decision['selected_candidate_id'])}",
        f"- change_allowed: {decision['change_allowed']}",
        "",
        "## Blockers",
        "",
        *(_render_items(decision["blockers"])),
        "",
        "## Warnings",
        "",
        *(_render_items(decision["warnings"])),
        "",
        "## Guardrail snapshot",
        "",
        f"- stage: {guardrails['stage']}",
        f"- review_ready: {guardrails['review_ready']}",
        f"- change_review_ready: {guardrails['change_review_ready']}",
        f"- next_change_review_gap: {guardrails['next_change_review_gap']}",
        "",
        "## Forward snapshot",
        "",
        f"- evaluations: {forward['evaluations']}",
        f"- traded_rows: {forward['traded_rows']}",
        f"- win_rate: {forward['win_rate']}",
        f"- total_pnl_usd: {forward['total_pnl_usd']}",
        "",
        "## Candidate reviews",
        "",
    ]
    for review in sorted(
        report["candidate_reviews"],
        key=lambda item: (
            item["change_quality_passed"],
            item["review_ready"],
            item["metrics"]["delta_pnl_usd"],
        ),
        reverse=True,
    ):
        metrics = review["metrics"]
        lines.extend(
            [
                f"### {review['candidate_id']}",
                "",
                f"- filter_kind: {review['filter_kind']}",
                f"- review_ready: {review['review_ready']}",
                f"- change_quality_passed: {review['change_quality_passed']}",
                f"- blockers: {list(review['blockers'])}",
                f"- warnings: {list(review['warnings'])}",
                f"- active_trades: {metrics['active_trades']}",
                f"- candidate_trades: {metrics['candidate_trades']}",
                f"- candidate_win_rate: {metrics['candidate_win_rate']}",
                f"- trade_retention: {metrics['trade_retention']}",
                f"- active_total_pnl_usd: {metrics['active_total_pnl_usd']}",
                f"- candidate_total_pnl_usd: {metrics['candidate_total_pnl_usd']}",
                f"- delta_pnl_usd: {metrics['delta_pnl_usd']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "This report can approve only a manual freeze review. It does not enable live trading and it does not submit orders.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_candidate_change_review_report(
    output_path: Path = DEFAULT_CHANGE_REVIEW_REPORT,
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
    registry_path: Path = DEFAULT_REGISTRY,
    comparison_dir: Path = DEFAULT_COMPARISON_DIR,
    policy: CandidateChangeReviewPolicy | None = None,
) -> dict[str, Any]:
    report = build_candidate_change_review_report(
        forward_ledger_path=forward_ledger_path,
        registry_path=registry_path,
        comparison_dir=comparison_dir,
        policy=policy,
    )
    output_path.write_text(render_candidate_change_review_markdown(report), encoding="utf-8")
    return report


def _trade_quality_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    active_pnls = [
        float(row["active_pnl_usd"])
        for row in rows
        if row["active_reason"] == "traded" and row["active_pnl_usd"] != ""
    ]
    candidate_pnls = [
        float(row["candidate_pnl_usd"])
        for row in rows
        if row["candidate_reason"] == "traded" and row["candidate_pnl_usd"] != ""
    ]
    return {
        "active_win_rate": _win_rate(active_pnls),
        "candidate_win_rate": _win_rate(candidate_pnls),
        "trade_retention": (len(candidate_pnls) / len(active_pnls)) if active_pnls else 0.0,
        "active_avg_pnl_usd": (sum(active_pnls) / len(active_pnls)) if active_pnls else 0.0,
        "candidate_avg_pnl_usd": (
            sum(candidate_pnls) / len(candidate_pnls) if candidate_pnls else 0.0
        ),
    }


def _win_rate(pnls: list[float]) -> float:
    return (sum(1 for pnl in pnls if pnl > 0) / len(pnls)) if pnls else 0.0


def _render_items(items: tuple[str, ...] | list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]


def _display_candidate_id(candidate_id: str) -> str:
    return candidate_id or "none"
