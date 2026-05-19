from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .active_strategy import (
    DEFAULT_ACTIVE_STRATEGY_STATE,
    active_strategy_state_from_candidate,
    default_active_strategy_state,
    load_optional_active_strategy_state,
    write_active_strategy_state,
)
from .candidate_change_review import CandidateChangeReviewPolicy
from .candidate_lifecycle import (
    DEFAULT_COMPARISON_DIR,
    DEFAULT_FORWARD_LEDGER,
    DEFAULT_LIFECYCLE_REPORT,
    DEFAULT_REGISTRY,
    CandidateLifecyclePolicy,
    build_candidate_lifecycle_report,
    render_candidate_lifecycle_markdown,
)
from .candidate_strategies import load_candidate_registry, update_candidate_status


DEFAULT_AUTOPILOT_REPORT = Path("candidate_autopilot_report.md")


@dataclass(frozen=True)
class CandidateAutopilotPolicy:
    enabled: bool = False
    demote_degraded_active_strategy: bool = True
    reject_degraded_active_candidate: bool = True


def run_candidate_autopilot(
    output_path: Path = DEFAULT_AUTOPILOT_REPORT,
    lifecycle_output_path: Path = DEFAULT_LIFECYCLE_REPORT,
    strategy_state_path: Path = DEFAULT_ACTIVE_STRATEGY_STATE,
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
    registry_path: Path = DEFAULT_REGISTRY,
    comparison_dir: Path = DEFAULT_COMPARISON_DIR,
    policy: CandidateAutopilotPolicy | None = None,
    lifecycle_policy: CandidateLifecyclePolicy | None = None,
    change_policy: CandidateChangeReviewPolicy | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    policy = policy or CandidateAutopilotPolicy()
    now = now or datetime.now(timezone.utc)
    lifecycle = build_candidate_lifecycle_report(
        forward_ledger_path=forward_ledger_path,
        registry_path=registry_path,
        comparison_dir=comparison_dir,
        policy=lifecycle_policy,
        change_policy=change_policy,
    )
    lifecycle_output_path.write_text(
        render_candidate_lifecycle_markdown(lifecycle),
        encoding="utf-8",
    )
    selected = _select_promotion_candidate(lifecycle)
    existing_state = load_optional_active_strategy_state(strategy_state_path)
    registry = load_candidate_registry(registry_path)
    active_degradation = _detect_active_strategy_degradation(
        existing_state=existing_state,
        lifecycle=lifecycle,
        registry=registry,
    )
    action = "NOOP"
    blockers: list[str] = []
    written_state = existing_state
    rejected_candidate_id = ""

    if selected is None and active_degradation is None:
        blockers.append("no_promotion_ready_candidate")
    elif not policy.enabled:
        action = (
            "DRY_RUN_DEMOTION_READY"
            if selected is None and active_degradation is not None
            else "DRY_RUN_PROMOTION_READY"
        )
        blockers.append("autopilot_disabled")
    elif (
        selected is not None
        and existing_state is not None
        and existing_state.source_candidate_id == selected["candidate_id"]
    ):
        action = "NOOP_ALREADY_ACTIVE"
    elif selected is not None:
        candidate = registry[selected["candidate_id"]]
        written_state = write_active_strategy_state(
            strategy_state_path,
            active_strategy_state_from_candidate(candidate, now=now),
        )
        action = "PAPER_STRATEGY_PROMOTED"
    elif policy.demote_degraded_active_strategy:
        written_state = write_active_strategy_state(
            strategy_state_path,
            default_active_strategy_state(now=now),
        )
        action = "PAPER_STRATEGY_DEMOTED_TO_BASELINE"
        candidate_id = active_degradation["candidate_id"]
        if policy.reject_degraded_active_candidate and candidate_id in registry:
            update_candidate_status(registry_path, candidate_id, "rejected")
            rejected_candidate_id = candidate_id
    else:
        action = "NOOP_ACTIVE_STRATEGY_DEGRADED"
        blockers.append("active_strategy_degraded")

    report = {
        "generated_at": now.isoformat(),
        "policy": asdict(policy),
        "action": action,
        "selected_candidate_id": selected["candidate_id"] if selected else "",
        "blockers": tuple(blockers),
        "active_strategy_degradation": active_degradation,
        "rejected_candidate_id": rejected_candidate_id,
        "strategy_state_path": str(strategy_state_path),
        "active_strategy_state": (
            {
                "source_candidate_id": written_state.source_candidate_id,
                "filter_kind": written_state.filter_kind,
                "min_confidence": written_state.min_confidence,
                "min_edge": written_state.min_edge,
                "live_trading_enabled": written_state.live_trading_enabled,
            }
            if written_state is not None
            else None
        ),
        "promotion_ready_candidates": [
            item["candidate_id"] for item in lifecycle["buckets"]["PROMOTION_READY"]
        ],
        "change_decision": lifecycle["change_decision"],
    }
    output_path.write_text(render_candidate_autopilot_markdown(report), encoding="utf-8")
    return report


def render_candidate_autopilot_markdown(report: dict[str, Any]) -> str:
    state = report["active_strategy_state"] or {}
    lines = [
        "# Candidate Autopilot Report",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- enabled: {report['policy']['enabled']}",
        f"- action: {report['action']}",
        f"- selected_candidate_id: {_display(report['selected_candidate_id'])}",
        f"- blockers: {list(report['blockers'])}",
        f"- promotion_ready_candidates: {report['promotion_ready_candidates']}",
        f"- active_strategy_degradation: {report['active_strategy_degradation'] or 'none'}",
        f"- rejected_candidate_id: {_display(report['rejected_candidate_id'])}",
        "",
        "## Active Paper Strategy",
        "",
        f"- strategy_state_path: {report['strategy_state_path']}",
        f"- source_candidate_id: {_display(state.get('source_candidate_id', ''))}",
        f"- filter_kind: {_display(state.get('filter_kind', ''))}",
        f"- min_confidence: {state.get('min_confidence', '')}",
        f"- min_edge: {state.get('min_edge', '')}",
        f"- live_trading_enabled: {state.get('live_trading_enabled', False)}",
        "",
        "## Change Decision",
        "",
        f"- status: {report['change_decision']['status']}",
        f"- change_allowed: {report['change_decision']['change_allowed']}",
        f"- selected_candidate_id: {_display(report['change_decision']['selected_candidate_id'])}",
        f"- blockers: {list(report['change_decision']['blockers'])}",
        "",
        "## Boundary",
        "",
        "This autopilot can update only the paper active strategy state. It does not enable live trading, read private keys or submit orders.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _select_promotion_candidate(lifecycle: dict[str, Any]) -> dict[str, Any] | None:
    promotion_ready = lifecycle["buckets"]["PROMOTION_READY"]
    if not promotion_ready:
        return None
    selected_id = lifecycle["change_decision"].get("selected_candidate_id")
    for item in promotion_ready:
        if item["candidate_id"] == selected_id:
            return item
    return max(
        promotion_ready,
        key=lambda item: (
            item["metrics"]["delta_pnl_usd"],
            item["metrics"]["candidate_win_rate"],
            item["candidate_id"],
        ),
    )


def _detect_active_strategy_degradation(
    existing_state: Any,
    lifecycle: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, Any] | None:
    if existing_state is None or existing_state.source_candidate_id in {"", "baseline"}:
        return None
    candidate_id = existing_state.source_candidate_id
    if candidate_id not in registry:
        return {
            "candidate_id": candidate_id,
            "reason": "active_candidate_missing",
            "blockers": ("active_candidate_missing",),
        }
    for item in lifecycle["items"]:
        if item["candidate_id"] != candidate_id:
            continue
        if item["candidate_status"] not in {"registered", "collecting", "promoted"}:
            return {
                "candidate_id": candidate_id,
                "reason": "active_candidate_inactive",
                "candidate_status": item["candidate_status"],
                "lifecycle_status": item["lifecycle_status"],
                "blockers": tuple(item["blockers"]),
            }
        if item["review_ready"] and not item["change_quality_passed"]:
            return {
                "candidate_id": candidate_id,
                "reason": "active_candidate_failed_change_quality",
                "candidate_status": item["candidate_status"],
                "lifecycle_status": item["lifecycle_status"],
                "blockers": tuple(item["blockers"]),
                "warnings": tuple(item["warnings"]),
                "metrics": {
                    "candidate_total_pnl_usd": item["metrics"][
                        "candidate_total_pnl_usd"
                    ],
                    "candidate_win_rate": item["metrics"]["candidate_win_rate"],
                    "delta_pnl_usd": item["metrics"]["delta_pnl_usd"],
                    "candidate_trades": item["metrics"]["candidate_trades"],
                },
            }
        return None
    return {
        "candidate_id": candidate_id,
        "reason": "active_candidate_missing_lifecycle_item",
        "blockers": ("active_candidate_missing_lifecycle_item",),
    }


def _display(value: str) -> str:
    return value or "none"
