from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .candidate_evidence import (
    assess_candidate_evidence,
    load_candidate_comparison_rows,
    summarize_candidate_evidence,
)
from .candidate_change_review import review_candidate_change
from .candidate_strategies import is_candidate_active, load_candidate_registry
from .execution_health import (
    DEFAULT_ATTEMPT_LOG,
    DEFAULT_INTENT_EVENT_LOG,
    build_execution_health_report,
)
from .strategy_guardrails import (
    assess_strategy_guardrails,
    load_forward_ledger_rows,
    summarize_forward_ledger,
)


DEFAULT_FORWARD_LEDGER = Path("data/forward_snapshot_evaluations.csv")
DEFAULT_REGISTRY = Path("strategy_candidates.csv")
DEFAULT_CANDIDATE_COMPARISON_DIR = Path("data/candidate_comparisons")
DEFAULT_CANARY_REPORT = Path("canary_readiness_report.md")


@dataclass(frozen=True)
class CanaryReadinessPolicy:
    require_guardrail_change_review_ready: bool = True
    require_candidate_review_ready: bool = True
    require_candidate_change_quality_passed: bool = True
    require_mock_submit_seen: bool = True
    min_forward_evaluations: int = 100
    min_forward_trades: int = 30
    min_forward_total_pnl_usd: float = 0.0
    min_forward_win_rate: float = 0.55


@dataclass(frozen=True)
class CanaryReadinessResult:
    ready: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    metrics: dict[str, Any] = field(default_factory=dict)


def assess_canary_readiness(
    forward_rows: list[dict[str, str]],
    candidate_registry_path: Path = DEFAULT_REGISTRY,
    candidate_comparison_dir: Path = DEFAULT_CANDIDATE_COMPARISON_DIR,
    intent_event_path: Path = DEFAULT_INTENT_EVENT_LOG,
    attempt_log_path: Path = DEFAULT_ATTEMPT_LOG,
    policy: CanaryReadinessPolicy | None = None,
) -> dict[str, Any]:
    policy = policy or CanaryReadinessPolicy()
    forward_summary = summarize_forward_ledger(forward_rows)
    guardrails = assess_strategy_guardrails(forward_summary)
    candidate_statuses = summarize_candidate_statuses(
        registry_path=candidate_registry_path,
        comparison_dir=candidate_comparison_dir,
    )
    execution_health = build_execution_health_report(
        intent_event_path=intent_event_path,
        attempt_log_path=attempt_log_path,
        forward_ledger_path=DEFAULT_FORWARD_LEDGER,
    )["execution_health"]

    blockers: list[str] = []
    warnings: list[str] = []
    if policy.require_guardrail_change_review_ready and guardrails["stage"] != "change_review_ready":
        blockers.append(f"guardrail_stage_{guardrails['stage']}")
    if forward_summary.evaluations < policy.min_forward_evaluations:
        blockers.append("insufficient_forward_evaluations")
    if forward_summary.traded_rows < policy.min_forward_trades:
        blockers.append("insufficient_forward_trades")
    if forward_summary.total_pnl_usd <= policy.min_forward_total_pnl_usd:
        blockers.append("forward_pnl_not_positive")
    if forward_summary.traded_rows and forward_summary.win_rate < policy.min_forward_win_rate:
        blockers.append("forward_win_rate_below_canary_floor")

    review_ready_candidates = [
        candidate_id
        for candidate_id, item in candidate_statuses.items()
        if item["active"] and item["assessment"]["review_ready"]
    ]
    if policy.require_candidate_review_ready and not review_ready_candidates:
        blockers.append("no_candidate_review_ready")
    quality_passed_candidates = [
        candidate_id
        for candidate_id, item in candidate_statuses.items()
        if item["active"] and item["change_review"]["change_quality_passed"]
    ]
    if policy.require_candidate_change_quality_passed and not quality_passed_candidates:
        blockers.append("no_candidate_passed_change_quality")
    collecting_candidates = [
        candidate_id
        for candidate_id, item in candidate_statuses.items()
        if item["active"] and item["assessment"]["stage"] == "collecting"
    ]
    if collecting_candidates:
        warnings.append("candidate_evidence_still_collecting")

    if policy.require_mock_submit_seen and execution_health["accepted_attempts"] <= 0:
        blockers.append("no_mock_submit_seen")

    metrics = {
        "forward_evaluations": forward_summary.evaluations,
        "forward_trades": forward_summary.traded_rows,
        "forward_win_rate": forward_summary.win_rate,
        "forward_total_pnl_usd": forward_summary.total_pnl_usd,
        "guardrail_stage": guardrails["stage"],
        "next_review_gap": guardrails["next_review_gap"],
        "next_change_review_gap": guardrails["next_change_review_gap"],
        "candidate_count": len(candidate_statuses),
        "active_candidate_count": sum(1 for item in candidate_statuses.values() if item["active"]),
        "review_ready_candidates": review_ready_candidates,
        "quality_passed_candidates": quality_passed_candidates,
        "collecting_candidates": collecting_candidates,
        "accepted_attempts": execution_health["accepted_attempts"],
        "rejected_attempts": execution_health["rejected_attempts"],
    }
    result = CanaryReadinessResult(
        ready=not blockers,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        metrics=metrics,
    )
    return {
        "readiness": result.__dict__,
        "guardrails": guardrails,
        "candidate_statuses": candidate_statuses,
        "execution_health": execution_health,
    }


def summarize_candidate_statuses(
    registry_path: Path,
    comparison_dir: Path,
) -> dict[str, dict[str, Any]]:
    statuses: dict[str, dict[str, Any]] = {}
    for candidate_id, candidate in load_candidate_registry(registry_path).items():
        rows = load_candidate_comparison_rows(comparison_dir / f"{candidate_id}.csv")
        summary = summarize_candidate_evidence(rows)
        change_review = review_candidate_change(
            candidate_id=candidate_id,
            filter_kind=candidate.filter_kind,
            rows=rows,
        )
        assessment = assess_candidate_evidence(summary)
        statuses[candidate_id] = {
            "filter_kind": candidate.filter_kind,
            "status": candidate.status,
            "active": is_candidate_active(candidate),
            "summary": summary.__dict__,
            "assessment": assessment,
            "change_review": change_review.__dict__,
        }
    return statuses


def build_canary_readiness_report(
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
    registry_path: Path = DEFAULT_REGISTRY,
    comparison_dir: Path = DEFAULT_CANDIDATE_COMPARISON_DIR,
    intent_event_path: Path = DEFAULT_INTENT_EVENT_LOG,
    attempt_log_path: Path = DEFAULT_ATTEMPT_LOG,
) -> dict[str, Any]:
    return assess_canary_readiness(
        forward_rows=load_forward_ledger_rows(forward_ledger_path),
        candidate_registry_path=registry_path,
        candidate_comparison_dir=comparison_dir,
        intent_event_path=intent_event_path,
        attempt_log_path=attempt_log_path,
    )


def render_canary_readiness_markdown(report: dict[str, Any]) -> str:
    readiness = report["readiness"]
    metrics = readiness["metrics"]
    lines = [
        "# Canary Readiness Report",
        "",
        "## Status",
        "",
        f"- ready: {readiness['ready']}",
        "",
        "## Blockers",
        "",
        *(_render_items(readiness["blockers"])),
        "",
        "## Warnings",
        "",
        *(_render_items(readiness["warnings"])),
        "",
        "## Core metrics",
        "",
        f"- forward_evaluations: {metrics['forward_evaluations']}",
        f"- forward_trades: {metrics['forward_trades']}",
        f"- forward_win_rate: {metrics['forward_win_rate']}",
        f"- forward_total_pnl_usd: {metrics['forward_total_pnl_usd']}",
        f"- guardrail_stage: {metrics['guardrail_stage']}",
        f"- next_change_review_gap: {metrics['next_change_review_gap']}",
        f"- candidate_count: {metrics['candidate_count']}",
        f"- active_candidate_count: {metrics.get('active_candidate_count', metrics['candidate_count'])}",
        f"- review_ready_candidates: {metrics['review_ready_candidates']}",
        f"- quality_passed_candidates: {metrics.get('quality_passed_candidates', [])}",
        f"- collecting_candidates: {metrics['collecting_candidates']}",
        f"- accepted_attempts: {metrics['accepted_attempts']}",
        f"- rejected_attempts: {metrics['rejected_attempts']}",
        "",
        "## Candidate evidence",
        "",
    ]
    for candidate_id, item in report["candidate_statuses"].items():
        summary = item["summary"]
        assessment = item["assessment"]
        change_review = item.get(
            "change_review",
            {"change_quality_passed": False, "blockers": ()},
        )
        lines.extend(
            [
                f"### {candidate_id}",
                "",
                f"- filter_kind: {item['filter_kind']}",
                f"- status: {item.get('status', 'registered')}",
                f"- active: {item.get('active', True)}",
                f"- stage: {assessment['stage']}",
                f"- change_quality_passed: {change_review['change_quality_passed']}",
                f"- change_blockers: {list(change_review['blockers'])}",
                f"- eligible_windows: {summary['eligible_windows']}",
                f"- divergent_windows: {summary['divergent_windows']}",
                f"- delta_pnl_usd: {summary['delta_pnl_usd']}",
                f"- next_review_gap: {assessment['next_review_gap']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_canary_readiness_report(
    output_path: Path = DEFAULT_CANARY_REPORT,
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
    registry_path: Path = DEFAULT_REGISTRY,
    comparison_dir: Path = DEFAULT_CANDIDATE_COMPARISON_DIR,
    intent_event_path: Path = DEFAULT_INTENT_EVENT_LOG,
    attempt_log_path: Path = DEFAULT_ATTEMPT_LOG,
) -> dict[str, Any]:
    report = build_canary_readiness_report(
        forward_ledger_path=forward_ledger_path,
        registry_path=registry_path,
        comparison_dir=comparison_dir,
        intent_event_path=intent_event_path,
        attempt_log_path=attempt_log_path,
    )
    output_path.write_text(render_canary_readiness_markdown(report), encoding="utf-8")
    return report


def _render_items(items: tuple[str, ...] | list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]
