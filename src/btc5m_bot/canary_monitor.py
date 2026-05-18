from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .canary_readiness import (
    DEFAULT_CANARY_REPORT,
    build_canary_readiness_report,
    render_canary_readiness_markdown,
)


DEFAULT_MONITOR_REPORT = Path("canary_monitor_report.md")


@dataclass(frozen=True)
class CanaryMonitorResult:
    checked_at: str
    ready: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    next_action: str
    readiness_report_path: str


def run_canary_monitor(
    readiness_output_path: Path = DEFAULT_CANARY_REPORT,
    monitor_output_path: Path = DEFAULT_MONITOR_REPORT,
) -> dict[str, Any]:
    readiness = build_canary_readiness_report()
    readiness_output_path.write_text(render_canary_readiness_markdown(readiness), encoding="utf-8")
    readiness_result = readiness["readiness"]
    blockers = tuple(readiness_result["blockers"])
    warnings = tuple(readiness_result["warnings"])
    result = CanaryMonitorResult(
        checked_at=datetime.now(timezone.utc).isoformat(),
        ready=bool(readiness_result["ready"]),
        blockers=blockers,
        warnings=warnings,
        next_action=choose_next_action(blockers, warnings),
        readiness_report_path=str(readiness_output_path),
    )
    monitor_output_path.write_text(render_canary_monitor_markdown(result, readiness), encoding="utf-8")
    return {
        "monitor": result.__dict__,
        "readiness": readiness,
    }


def choose_next_action(blockers: tuple[str, ...], warnings: tuple[str, ...]) -> str:
    if not blockers:
        return "prepare_canary_authorization_packet"
    if "insufficient_forward_trades" in blockers or "insufficient_forward_evaluations" in blockers:
        return "collect_more_forward_evidence"
    if "no_candidate_review_ready" in blockers:
        return "wait_for_candidate_evidence_or_register_new_candidate"
    if "guardrail_stage_collecting" in blockers:
        return "continue_forward_collection"
    return "inspect_blockers"


def render_canary_monitor_markdown(
    result: CanaryMonitorResult,
    readiness: dict[str, Any],
) -> str:
    metrics = readiness["readiness"]["metrics"]
    lines = [
        "# Canary Monitor Report",
        "",
        f"- checked_at: {result.checked_at}",
        f"- ready: {result.ready}",
        f"- next_action: {result.next_action}",
        f"- readiness_report_path: {result.readiness_report_path}",
        "",
        "## Blockers",
        "",
        *(_render_items(result.blockers)),
        "",
        "## Warnings",
        "",
        *(_render_items(result.warnings)),
        "",
        "## Evidence gap",
        "",
        f"- forward_evaluations: {metrics['forward_evaluations']}",
        f"- forward_trades: {metrics['forward_trades']}",
        f"- next_change_review_gap: {metrics['next_change_review_gap']}",
        f"- review_ready_candidates: {metrics['review_ready_candidates']}",
        f"- collecting_candidates: {metrics['collecting_candidates']}",
    ]
    return "\n".join(lines) + "\n"


def _render_items(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]
