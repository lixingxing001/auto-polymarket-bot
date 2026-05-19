from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from typing import Any

from .candidate_change_review import review_candidate_change
from .candidate_evidence import (
    CandidateEvidencePolicy,
    assess_candidate_evidence,
    load_candidate_comparison_rows,
    summarize_candidate_evidence,
)
from .candidate_strategies import is_candidate_active, load_candidate_registry


DEFAULT_REGISTRY = Path("strategy_candidates.csv")
DEFAULT_COMPARISON_DIR = Path("data/candidate_comparisons")
DEFAULT_PROGRESS_REPORT = Path("candidate_evidence_progress_report.md")
FIVE_MINUTE_WINDOWS_PER_HOUR = 12.0


@dataclass(frozen=True)
class CandidateEvidenceProgress:
    candidate_id: str
    status: str
    active: bool
    filter_kind: str
    review_ready: bool
    change_quality_passed: bool
    eligible_windows: int
    divergent_windows: int
    active_trades: int
    candidate_trades: int
    delta_pnl_usd: float
    candidate_win_rate: float
    eligible_windows_needed: int
    divergent_windows_needed: int
    observed_divergence_rate: float
    estimated_windows_to_review: int | None
    estimated_minutes_to_review: int | None
    eta_confidence: str
    blocker_kind: str
    next_action: str
    warnings: tuple[str, ...] = field(default_factory=tuple)


def build_candidate_evidence_progress_report(
    registry_path: Path = DEFAULT_REGISTRY,
    comparison_dir: Path = DEFAULT_COMPARISON_DIR,
    policy: CandidateEvidencePolicy | None = None,
) -> dict[str, Any]:
    policy = policy or CandidateEvidencePolicy()
    registry = load_candidate_registry(registry_path)
    items = []
    for candidate_id, candidate in registry.items():
        rows = load_candidate_comparison_rows(comparison_dir / f"{candidate_id}.csv")
        summary = summarize_candidate_evidence(rows)
        assessment = assess_candidate_evidence(summary, policy=policy)
        review = review_candidate_change(
            candidate_id=candidate_id,
            filter_kind=candidate.filter_kind,
            rows=rows,
        )
        items.append(
            build_candidate_evidence_progress_item(
                candidate_id=candidate_id,
                status=candidate.status,
                active=is_candidate_active(candidate),
                filter_kind=candidate.filter_kind,
                assessment=assessment,
                review_metrics=review.metrics,
                change_quality_passed=review.change_quality_passed,
                warnings=review.warnings,
            )
        )
    active_items = tuple(item for item in items if item.active)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": policy.__dict__,
        "active_candidate_count": len(active_items),
        "all_candidate_count": len(items),
        "next_review_candidate_id": choose_next_review_candidate(active_items),
        "items": [item.__dict__ for item in sorted(items, key=_sort_key)],
        "summary": summarize_progress_items(active_items),
    }


def build_candidate_evidence_progress_item(
    candidate_id: str,
    status: str,
    active: bool,
    filter_kind: str,
    assessment: dict[str, Any],
    review_metrics: dict[str, Any],
    change_quality_passed: bool,
    warnings: tuple[str, ...],
) -> CandidateEvidenceProgress:
    eligible_windows = int(review_metrics["eligible_windows"])
    divergent_windows = int(review_metrics["divergent_windows"])
    eligible_needed = int(assessment["next_review_gap"]["eligible_windows_needed"])
    divergent_needed = int(assessment["next_review_gap"]["divergent_windows_needed"])
    observed_divergence_rate = (
        divergent_windows / eligible_windows if eligible_windows else 0.0
    )
    windows_to_review = estimate_windows_to_review(
        eligible_windows_needed=eligible_needed,
        divergent_windows_needed=divergent_needed,
        observed_divergence_rate=observed_divergence_rate,
    )
    blocker_kind = classify_progress_blocker(
        active=active,
        review_ready=bool(assessment["review_ready"]),
        change_quality_passed=change_quality_passed,
        eligible_windows_needed=eligible_needed,
        divergent_windows_needed=divergent_needed,
        observed_divergence_rate=observed_divergence_rate,
    )
    return CandidateEvidenceProgress(
        candidate_id=candidate_id,
        status=status,
        active=active,
        filter_kind=filter_kind,
        review_ready=bool(assessment["review_ready"]),
        change_quality_passed=change_quality_passed,
        eligible_windows=eligible_windows,
        divergent_windows=divergent_windows,
        active_trades=int(review_metrics["active_trades"]),
        candidate_trades=int(review_metrics["candidate_trades"]),
        delta_pnl_usd=float(review_metrics["delta_pnl_usd"]),
        candidate_win_rate=float(review_metrics["candidate_win_rate"]),
        eligible_windows_needed=eligible_needed,
        divergent_windows_needed=divergent_needed,
        observed_divergence_rate=observed_divergence_rate,
        estimated_windows_to_review=windows_to_review,
        estimated_minutes_to_review=(
            windows_to_review * 5 if windows_to_review is not None else None
        ),
        eta_confidence=classify_eta_confidence(
            active=active,
            eligible_windows=eligible_windows,
            observed_divergence_rate=observed_divergence_rate,
            windows_to_review=windows_to_review,
        ),
        blocker_kind=blocker_kind,
        next_action=choose_item_next_action(blocker_kind),
        warnings=warnings,
    )


def estimate_windows_to_review(
    eligible_windows_needed: int,
    divergent_windows_needed: int,
    observed_divergence_rate: float,
) -> int | None:
    if eligible_windows_needed <= 0 and divergent_windows_needed <= 0:
        return 0
    if divergent_windows_needed > 0 and observed_divergence_rate <= 0.0:
        return None
    divergent_windows_needed_as_elapsed = (
        ceil(divergent_windows_needed / observed_divergence_rate)
        if divergent_windows_needed > 0
        else 0
    )
    return max(eligible_windows_needed, divergent_windows_needed_as_elapsed)


def classify_progress_blocker(
    active: bool,
    review_ready: bool,
    change_quality_passed: bool,
    eligible_windows_needed: int,
    divergent_windows_needed: int,
    observed_divergence_rate: float,
) -> str:
    if not active:
        return "candidate_not_active"
    if change_quality_passed:
        return "change_quality_passed"
    if review_ready:
        return "review_ready_quality_failed"
    if eligible_windows_needed > 0 and divergent_windows_needed <= 0:
        return "needs_eligible_windows"
    if divergent_windows_needed > 0 and observed_divergence_rate <= 0.0:
        return "waiting_for_first_divergence"
    if divergent_windows_needed > 0:
        return "needs_divergent_windows"
    return "collecting"


def classify_eta_confidence(
    active: bool,
    eligible_windows: int,
    observed_divergence_rate: float,
    windows_to_review: int | None,
) -> str:
    if not active:
        return "inactive"
    if windows_to_review == 0:
        return "ready"
    if windows_to_review is None:
        return "unknown_until_divergence_observed"
    if eligible_windows >= 10 and observed_divergence_rate > 0.0:
        return "observed_rate"
    return "thin_sample"


def choose_item_next_action(blocker_kind: str) -> str:
    return {
        "candidate_not_active": "keep_archived",
        "change_quality_passed": "run_candidate_change_review",
        "review_ready_quality_failed": "reject_or_redesign_candidate",
        "needs_eligible_windows": "wait_for_more_settled_windows",
        "waiting_for_first_divergence": "wait_for_divergent_decision",
        "needs_divergent_windows": "wait_for_more_divergent_windows",
        "collecting": "wait_for_more_evidence",
    }[blocker_kind]


def choose_next_review_candidate(
    items: tuple[CandidateEvidenceProgress, ...],
) -> str:
    review_ready = [item for item in items if item.review_ready]
    if review_ready:
        return sorted(review_ready, key=lambda item: (-item.delta_pnl_usd, item.candidate_id))[0].candidate_id
    estimable = [
        item
        for item in items
        if item.estimated_windows_to_review is not None
        and item.estimated_windows_to_review > 0
    ]
    if estimable:
        return sorted(
            estimable,
            key=lambda item: (
                item.estimated_windows_to_review or 10**9,
                -item.delta_pnl_usd,
                item.candidate_id,
            ),
        )[0].candidate_id
    if items:
        return sorted(items, key=lambda item: item.candidate_id)[0].candidate_id
    return "none"


def summarize_progress_items(
    active_items: tuple[CandidateEvidenceProgress, ...],
) -> dict[str, Any]:
    return {
        "active_candidates": len(active_items),
        "review_ready_candidates": [
            item.candidate_id for item in active_items if item.review_ready
        ],
        "change_quality_passed_candidates": [
            item.candidate_id for item in active_items if item.change_quality_passed
        ],
        "waiting_for_first_divergence": [
            item.candidate_id
            for item in active_items
            if item.blocker_kind == "waiting_for_first_divergence"
        ],
        "needs_divergent_windows": [
            item.candidate_id
            for item in active_items
            if item.blocker_kind == "needs_divergent_windows"
        ],
    }


def render_candidate_evidence_progress_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Candidate Evidence Progress Report",
        "",
        "## Status",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- active_candidate_count: {report['active_candidate_count']}",
        f"- all_candidate_count: {report['all_candidate_count']}",
        f"- next_review_candidate_id: {report['next_review_candidate_id']}",
        f"- review_ready_candidates: {summary['review_ready_candidates']}",
        f"- change_quality_passed_candidates: {summary['change_quality_passed_candidates']}",
        f"- waiting_for_first_divergence: {summary['waiting_for_first_divergence']}",
        f"- needs_divergent_windows: {summary['needs_divergent_windows']}",
        "",
        "## Active candidates",
        "",
        "| candidate_id | blocker | eligible | divergent | eligible_gap | divergent_gap | eta_minutes | eta_confidence | delta_pnl | win_rate | next_action |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    active_items = [item for item in report["items"] if item["active"]]
    if not active_items:
        lines.append("| none | none | 0 | 0 | 0 | 0 | n/a | n/a | 0.00 | 0.0% | register_candidate |")
    for item in active_items:
        lines.append(
            "| "
            + " | ".join(
                [
                    item["candidate_id"],
                    item["blocker_kind"],
                    str(item["eligible_windows"]),
                    str(item["divergent_windows"]),
                    str(item["eligible_windows_needed"]),
                    str(item["divergent_windows_needed"]),
                    _display_optional_int(item["estimated_minutes_to_review"]),
                    item["eta_confidence"],
                    _money(item["delta_pnl_usd"]),
                    _pct(item["candidate_win_rate"]),
                    item["next_action"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Inactive candidates",
            "",
        ]
    )
    inactive_items = [item for item in report["items"] if not item["active"]]
    if not inactive_items:
        lines.append("- none")
    for item in inactive_items:
        lines.append(
            f"- {item['candidate_id']}: status={item['status']}, delta_pnl={_money(item['delta_pnl_usd'])}"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This report estimates evidence maturity only. It does not approve strategy changes, enable live trading or submit orders.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_candidate_evidence_progress_report(
    output_path: Path = DEFAULT_PROGRESS_REPORT,
    registry_path: Path = DEFAULT_REGISTRY,
    comparison_dir: Path = DEFAULT_COMPARISON_DIR,
) -> dict[str, Any]:
    report = build_candidate_evidence_progress_report(
        registry_path=registry_path,
        comparison_dir=comparison_dir,
    )
    output_path.write_text(render_candidate_evidence_progress_markdown(report), encoding="utf-8")
    return report


def _sort_key(item: CandidateEvidenceProgress) -> tuple[int, int, float, str]:
    status_rank = 0 if item.active else 1
    eta_rank = item.estimated_windows_to_review if item.estimated_windows_to_review is not None else 10**9
    return (status_rank, eta_rank, -item.delta_pnl_usd, item.candidate_id)


def _display_optional_int(value: int | None) -> str:
    return str(value) if value is not None else "unknown"


def _pct(value: float) -> str:
    return f"{value:.1%}"


def _money(value: float) -> str:
    return f"{value:.2f}"
