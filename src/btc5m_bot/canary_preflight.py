from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .canary_authorization import build_canary_authorization_packet
from .canary_kill_switch import build_canary_kill_switch_report
from .canary_readiness import build_canary_readiness_report
from .real_adapter_gate import RealAdapterGateAssessment, assess_real_adapter_gate


DEFAULT_CANARY_PREFLIGHT_REPORT = Path("canary_preflight_report.md")


@dataclass(frozen=True)
class CanaryPreflightAssessment:
    status: str
    real_adapter_review_allowed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    next_action: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)


def assess_canary_preflight(
    readiness_report: dict[str, Any],
    kill_switch_report: dict[str, Any],
    authorization_packet: dict[str, Any],
    real_adapter_gate: RealAdapterGateAssessment,
) -> CanaryPreflightAssessment:
    readiness = readiness_report["readiness"]
    kill_switch = kill_switch_report["assessment"]
    blockers: list[str] = []
    warnings: list[str] = []
    blockers.extend(readiness["blockers"])
    blockers.extend(authorization_packet["blockers"])
    blockers.extend(real_adapter_gate.blockers)
    warnings.extend(readiness["warnings"])
    warnings.extend(kill_switch["warnings"])
    warnings.extend(authorization_packet["warnings"])
    warnings.extend(real_adapter_gate.warnings)

    status = "BLOCKED"
    next_action = "collect_more_forward_evidence"
    if kill_switch["active"]:
        next_action = "stop_canary_work_until_kill_switch_clears"
    elif readiness["ready"] and authorization_packet["status"] == "READY_FOR_LEE_AUTHORIZATION":
        status = "AWAITING_LEE_AUTHORIZATION_ENV"
        next_action = "set_explicit_canary_authorization_env_after_manual_review"
    if real_adapter_gate.unlock_allowed:
        status = "UNLOCKED_FOR_REAL_ADAPTER_REVIEW"
        next_action = "perform_manual_code_review_before_any_real_order_adapter"

    metrics = {
        "readiness_ready": readiness["ready"],
        "authorization_status": authorization_packet["status"],
        "kill_switch_active": kill_switch["active"],
        "real_adapter_unlock_allowed": real_adapter_gate.unlock_allowed,
        "forward_evaluations": readiness["metrics"]["forward_evaluations"],
        "forward_trades": readiness["metrics"]["forward_trades"],
        "forward_total_pnl_usd": readiness["metrics"]["forward_total_pnl_usd"],
        "review_ready_candidates": readiness["metrics"]["review_ready_candidates"],
    }
    unique_blockers = tuple(dict.fromkeys(blockers))
    return CanaryPreflightAssessment(
        status=status,
        real_adapter_review_allowed=real_adapter_gate.unlock_allowed,
        blockers=unique_blockers,
        warnings=tuple(dict.fromkeys(warnings)),
        next_action=next_action,
        metrics=metrics,
    )


def build_canary_preflight_report(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    readiness_report = build_canary_readiness_report()
    kill_switch_report = build_canary_kill_switch_report()
    authorization_packet = build_canary_authorization_packet(
        readiness_report=readiness_report,
        kill_switch_report=kill_switch_report,
    )
    real_adapter_gate = assess_real_adapter_gate(
        authorization_packet=authorization_packet,
        kill_switch_report=kill_switch_report,
        env=env,
    )
    assessment = assess_canary_preflight(
        readiness_report=readiness_report,
        kill_switch_report=kill_switch_report,
        authorization_packet=authorization_packet,
        real_adapter_gate=real_adapter_gate,
    )
    return {
        "assessment": assessment.__dict__,
        "readiness": readiness_report["readiness"],
        "authorization_status": authorization_packet["status"],
        "kill_switch_active": kill_switch_report["assessment"]["active"],
        "real_adapter_gate": real_adapter_gate.__dict__,
    }


def render_canary_preflight_markdown(report: dict[str, Any]) -> str:
    assessment = report["assessment"]
    lines = [
        "# Canary Preflight Report",
        "",
        "## Status",
        "",
        f"- status: {assessment['status']}",
        f"- real_adapter_review_allowed: {assessment['real_adapter_review_allowed']}",
        f"- next_action: {assessment['next_action']}",
        "",
        "## Blockers",
        "",
        *(_render_items(assessment["blockers"])),
        "",
        "## Warnings",
        "",
        *(_render_items(assessment["warnings"])),
        "",
        "## Metrics",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in assessment["metrics"].items())
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This report is a preflight summary only. It does not read private keys and it does not submit orders.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_canary_preflight_report(
    output_path: Path = DEFAULT_CANARY_PREFLIGHT_REPORT,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    report = build_canary_preflight_report(env=env)
    output_path.write_text(render_canary_preflight_markdown(report), encoding="utf-8")
    return report


def _render_items(items: tuple[str, ...] | list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]
