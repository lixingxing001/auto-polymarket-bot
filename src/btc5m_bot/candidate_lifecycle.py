from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .candidate_change_review import (
    CandidateChangeReview,
    CandidateChangeReviewPolicy,
    build_candidate_change_review_report,
    review_candidate_change,
)
from .candidate_evidence import (
    assess_candidate_evidence,
    load_candidate_comparison_rows,
    summarize_candidate_evidence,
)
from .candidate_strategies import load_candidate_registry
from .strategy_guardrails import assess_strategy_guardrails, load_forward_ledger_rows, summarize_forward_ledger


DEFAULT_FORWARD_LEDGER = Path("data/forward_snapshot_evaluations.csv")
DEFAULT_REGISTRY = Path("strategy_candidates.csv")
DEFAULT_COMPARISON_DIR = Path("data/candidate_comparisons")
DEFAULT_LIFECYCLE_REPORT = Path("candidate_lifecycle_report.md")


@dataclass(frozen=True)
class CandidateLifecyclePolicy:
    min_candidate_win_rate_for_promotion: float = 0.55
    min_candidate_trades_for_promotion: int = 10
    reject_when_review_ready_and_delta_non_positive: bool = True


@dataclass(frozen=True)
class CandidateLifecycleItem:
    candidate_id: str
    candidate_status: str
    lifecycle_status: str
    recommended_action: str
    rationale: tuple[str, ...]
    filter_kind: str
    review_ready: bool
    change_quality_passed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    metrics: dict[str, Any] = field(default_factory=dict)


def build_candidate_lifecycle_report(
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
    registry_path: Path = DEFAULT_REGISTRY,
    comparison_dir: Path = DEFAULT_COMPARISON_DIR,
    policy: CandidateLifecyclePolicy | None = None,
    change_policy: CandidateChangeReviewPolicy | None = None,
) -> dict[str, Any]:
    policy = policy or CandidateLifecyclePolicy()
    change_policy = change_policy or CandidateChangeReviewPolicy()
    forward_summary = summarize_forward_ledger(load_forward_ledger_rows(forward_ledger_path))
    guardrails = assess_strategy_guardrails(forward_summary)
    change_report = build_candidate_change_review_report(
        forward_ledger_path=forward_ledger_path,
        registry_path=registry_path,
        comparison_dir=comparison_dir,
        policy=change_policy,
    )
    items = []
    registry = load_candidate_registry(registry_path)
    for candidate_id, candidate in registry.items():
        rows = load_candidate_comparison_rows(comparison_dir / f"{candidate_id}.csv")
        evidence = summarize_candidate_evidence(rows)
        evidence_assessment = assess_candidate_evidence(evidence)
        review = review_candidate_change(
            candidate_id=candidate_id,
            filter_kind=candidate.filter_kind,
            rows=rows,
            policy=change_policy,
        )
        items.append(
            classify_candidate_lifecycle(
                candidate_status=candidate.status,
                review=review,
                evidence_assessment=evidence_assessment,
                guardrails=guardrails,
                policy=policy,
            )
        )
    buckets = bucket_lifecycle_items(tuple(items))
    return {
        "forward_summary": forward_summary.__dict__,
        "guardrails": guardrails,
        "change_decision": change_report["decision"],
        "policy": policy.__dict__,
        "items": [item.__dict__ for item in items],
        "buckets": {
            status: [item.__dict__ for item in bucket_items]
            for status, bucket_items in buckets.items()
        },
        "next_action": choose_lifecycle_next_action(
            buckets=buckets,
            forward_summary=forward_summary.__dict__,
        ),
    }


def classify_candidate_lifecycle(
    review: CandidateChangeReview,
    evidence_assessment: dict[str, Any],
    guardrails: dict[str, Any],
    candidate_status: str = "registered",
    policy: CandidateLifecyclePolicy | None = None,
) -> CandidateLifecycleItem:
    policy = policy or CandidateLifecyclePolicy()
    rationale: list[str] = []
    metrics = review.metrics
    if candidate_status not in {"registered", "collecting"}:
        rationale.append("candidate_status_not_active")
        return CandidateLifecycleItem(
            candidate_id=review.candidate_id,
            candidate_status=candidate_status,
            lifecycle_status="REJECTED",
            recommended_action="keep_excluded_from_change_review",
            rationale=tuple(rationale),
            filter_kind=review.filter_kind,
            review_ready=review.review_ready,
            change_quality_passed=review.change_quality_passed,
            blockers=review.blockers,
            warnings=review.warnings,
            metrics=metrics,
        )
    if not review.review_ready:
        gap = evidence_assessment["next_review_gap"]
        rationale.append(
            "needs_more_evidence:"
            f"eligible_windows={gap['eligible_windows_needed']},"
            f"divergent_windows={gap['divergent_windows_needed']}"
        )
        return CandidateLifecycleItem(
            candidate_id=review.candidate_id,
            candidate_status=candidate_status,
            lifecycle_status="COLLECTING",
            recommended_action="collect_more_forward_evidence",
            rationale=tuple(rationale),
            filter_kind=review.filter_kind,
            review_ready=review.review_ready,
            change_quality_passed=review.change_quality_passed,
            blockers=review.blockers,
            warnings=review.warnings,
            metrics=metrics,
        )

    if (
        policy.reject_when_review_ready_and_delta_non_positive
        and metrics["delta_pnl_usd"] <= 0.0
    ):
        rationale.append("review_ready_but_delta_pnl_not_positive")
        if metrics["candidate_win_rate"] < 0.50:
            rationale.append("candidate_win_rate_below_half")
        return CandidateLifecycleItem(
            candidate_id=review.candidate_id,
            candidate_status=candidate_status,
            lifecycle_status="REJECT_RECOMMENDED",
            recommended_action="do_not_promote_candidate",
            rationale=tuple(rationale),
            filter_kind=review.filter_kind,
            review_ready=review.review_ready,
            change_quality_passed=review.change_quality_passed,
            blockers=review.blockers,
            warnings=review.warnings,
            metrics=metrics,
        )

    if not review.change_quality_passed:
        rationale.extend(review.blockers)
        return CandidateLifecycleItem(
            candidate_id=review.candidate_id,
            candidate_status=candidate_status,
            lifecycle_status="REVIEW_READY",
            recommended_action="manual_quality_review",
            rationale=tuple(dict.fromkeys(rationale)),
            filter_kind=review.filter_kind,
            review_ready=review.review_ready,
            change_quality_passed=review.change_quality_passed,
            blockers=review.blockers,
            warnings=review.warnings,
            metrics=metrics,
        )

    if not guardrails["change_review_ready"]:
        rationale.append(f"guardrail_stage_{guardrails['stage']}")
        return CandidateLifecycleItem(
            candidate_id=review.candidate_id,
            candidate_status=candidate_status,
            lifecycle_status="REVIEW_READY",
            recommended_action="wait_for_guardrail_change_review_ready",
            rationale=tuple(rationale),
            filter_kind=review.filter_kind,
            review_ready=review.review_ready,
            change_quality_passed=review.change_quality_passed,
            blockers=review.blockers,
            warnings=review.warnings,
            metrics=metrics,
        )

    if metrics["candidate_trades"] < policy.min_candidate_trades_for_promotion:
        rationale.append("candidate_trades_below_promotion_floor")
    if metrics["candidate_win_rate"] < policy.min_candidate_win_rate_for_promotion:
        rationale.append("candidate_win_rate_below_promotion_floor")
    if rationale:
        return CandidateLifecycleItem(
            candidate_id=review.candidate_id,
            candidate_status=candidate_status,
            lifecycle_status="REVIEW_READY",
            recommended_action="manual_quality_review",
            rationale=tuple(rationale),
            filter_kind=review.filter_kind,
            review_ready=review.review_ready,
            change_quality_passed=review.change_quality_passed,
            blockers=review.blockers,
            warnings=review.warnings,
            metrics=metrics,
        )

    return CandidateLifecycleItem(
        candidate_id=review.candidate_id,
        candidate_status=candidate_status,
        lifecycle_status="PROMOTION_READY",
        recommended_action="manual_freeze_review_allowed",
        rationale=("all_lifecycle_gates_passed",),
        filter_kind=review.filter_kind,
        review_ready=review.review_ready,
        change_quality_passed=review.change_quality_passed,
        blockers=review.blockers,
        warnings=review.warnings,
        metrics=metrics,
    )


def bucket_lifecycle_items(
    items: tuple[CandidateLifecycleItem, ...],
) -> dict[str, tuple[CandidateLifecycleItem, ...]]:
    statuses = (
        "PROMOTION_READY",
        "REVIEW_READY",
        "COLLECTING",
        "REJECT_RECOMMENDED",
        "REJECTED",
    )
    return {
        status: tuple(item for item in items if item.lifecycle_status == status)
        for status in statuses
    }


def choose_lifecycle_next_action(
    buckets: dict[str, tuple[CandidateLifecycleItem, ...]],
    forward_summary: dict[str, Any],
) -> str:
    if buckets["PROMOTION_READY"]:
        return "review_promotion_candidate_before_manual_freeze"
    if forward_summary["win_rate"] < 0.55:
        return "keep_canary_blocked_and_collect_or_replace_candidates"
    if buckets["REVIEW_READY"]:
        return "manual_review_ready_candidates"
    if buckets["COLLECTING"]:
        return "collect_more_candidate_evidence"
    return "return_to_feature_layer"


def render_candidate_lifecycle_markdown(report: dict[str, Any]) -> str:
    forward = report["forward_summary"]
    guardrails = report["guardrails"]
    change = report["change_decision"]
    lines = [
        "# Candidate Lifecycle Report",
        "",
        "## Executive decision",
        "",
        f"- next_action: {report['next_action']}",
        f"- guardrail_stage: {guardrails['stage']}",
        f"- forward_trades: {forward['traded_rows']}",
        f"- forward_win_rate: {_pct(forward['win_rate'])}",
        f"- forward_total_pnl_usd: {_money(forward['total_pnl_usd'])}",
        f"- change_review_status: {change['status']}",
        f"- change_allowed: {change['change_allowed']}",
        f"- selected_candidate_id: {_display_candidate_id(change['selected_candidate_id'])}",
        "",
        "## Lifecycle buckets",
        "",
    ]
    for status in (
        "PROMOTION_READY",
        "REVIEW_READY",
        "COLLECTING",
        "REJECT_RECOMMENDED",
        "REJECTED",
    ):
        items = report["buckets"][status]
        lines.extend(
            [
                f"### {status}",
                "",
                *(_render_item_ids(items)),
                "",
            ]
        )
    lines.extend(
        [
            "## Candidate details",
            "",
            "| candidate_id | status | lifecycle | action | review_ready | delta_pnl | candidate_trades | candidate_win_rate | blockers | rationale |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for item in sorted(
        report["items"],
        key=lambda candidate: (
            _status_rank(candidate["lifecycle_status"]),
            -candidate["metrics"]["delta_pnl_usd"],
            candidate["candidate_id"],
        ),
    ):
        metrics = item["metrics"]
        lines.append(
            "| "
            + " | ".join(
                [
                    item["candidate_id"],
                    item["candidate_status"],
                    item["lifecycle_status"],
                    item["recommended_action"],
                    str(item["review_ready"]),
                    _money(metrics["delta_pnl_usd"]),
                    str(metrics["candidate_trades"]),
                    _pct(metrics["candidate_win_rate"]),
                    ", ".join(item["blockers"]) if item["blockers"] else "none",
                    ", ".join(item["rationale"]) if item["rationale"] else "none",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This report manages candidate evidence only. It does not freeze parameters, enable live trading or submit orders.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_candidate_lifecycle_report(
    output_path: Path = DEFAULT_LIFECYCLE_REPORT,
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
    registry_path: Path = DEFAULT_REGISTRY,
    comparison_dir: Path = DEFAULT_COMPARISON_DIR,
    policy: CandidateLifecyclePolicy | None = None,
    change_policy: CandidateChangeReviewPolicy | None = None,
) -> dict[str, Any]:
    report = build_candidate_lifecycle_report(
        forward_ledger_path=forward_ledger_path,
        registry_path=registry_path,
        comparison_dir=comparison_dir,
        policy=policy,
        change_policy=change_policy,
    )
    output_path.write_text(render_candidate_lifecycle_markdown(report), encoding="utf-8")
    return report


def _render_item_ids(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item['candidate_id']}" for item in items]


def _status_rank(status: str) -> int:
    return {
        "PROMOTION_READY": 0,
        "REVIEW_READY": 1,
        "COLLECTING": 2,
        "REJECT_RECOMMENDED": 3,
        "REJECTED": 4,
    }[status]


def _pct(value: float) -> str:
    return f"{value:.1%}"


def _money(value: float) -> str:
    return f"{value:.2f}"


def _display_candidate_id(candidate_id: str) -> str:
    return candidate_id or "none"
