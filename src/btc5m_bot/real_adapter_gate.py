from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .canary_authorization import build_canary_authorization_packet
from .canary_kill_switch import build_canary_kill_switch_report


DEFAULT_REAL_ADAPTER_GATE_REPORT = Path("real_adapter_gate_report.md")


@dataclass(frozen=True)
class RealAdapterGateConfig:
    lee_authorization_env: str = "LEE_CANARY_AUTHORIZED"
    lee_authorization_value: str = "I_ACCEPT_CANARY_RISK"
    isolated_wallet_env: str = "CANARY_WALLET_ISOLATED"
    isolated_wallet_value: str = "YES"
    max_funding_env: str = "CANARY_MAX_FUNDING_USDC"
    max_funding_usdc: float = 10.0


@dataclass(frozen=True)
class RealAdapterGateAssessment:
    unlock_allowed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    metrics: dict[str, Any] = field(default_factory=dict)


def assess_real_adapter_gate(
    authorization_packet: dict[str, Any] | None = None,
    kill_switch_report: dict[str, Any] | None = None,
    env: Mapping[str, str] | None = None,
    config: RealAdapterGateConfig | None = None,
) -> RealAdapterGateAssessment:
    config = config or RealAdapterGateConfig()
    env = os.environ if env is None else env
    authorization_packet = authorization_packet or build_canary_authorization_packet()
    kill_switch_report = kill_switch_report or build_canary_kill_switch_report()

    blockers: list[str] = []
    warnings: list[str] = []
    if authorization_packet["status"] != "READY_FOR_LEE_AUTHORIZATION":
        blockers.append("canary_authorization_packet_not_ready")
    if kill_switch_report["assessment"]["active"]:
        blockers.append("kill_switch_active")
    if env.get(config.lee_authorization_env) != config.lee_authorization_value:
        blockers.append("lee_authorization_env_missing")
    if env.get(config.isolated_wallet_env) != config.isolated_wallet_value:
        blockers.append("isolated_wallet_confirmation_missing")

    funding_value = env.get(config.max_funding_env)
    parsed_funding = None
    if funding_value is None:
        blockers.append("canary_funding_cap_missing")
    else:
        try:
            parsed_funding = float(funding_value)
            if parsed_funding < 0:
                blockers.append("canary_funding_cap_invalid")
            elif parsed_funding > config.max_funding_usdc:
                blockers.append("canary_funding_cap_too_high")
        except ValueError:
            blockers.append("canary_funding_cap_invalid")

    if not authorization_packet["blockers"] and authorization_packet["status"] == "READY_FOR_LEE_AUTHORIZATION":
        warnings.append("real_adapter_code_still_requires_manual_review")

    metrics = {
        "authorization_status": authorization_packet["status"],
        "authorization_blocker_count": len(authorization_packet["blockers"]),
        "kill_switch_active": kill_switch_report["assessment"]["active"],
        "lee_authorization_env": config.lee_authorization_env,
        "isolated_wallet_env": config.isolated_wallet_env,
        "max_funding_env": config.max_funding_env,
        "parsed_funding_usdc": parsed_funding,
        "max_funding_usdc": config.max_funding_usdc,
    }
    return RealAdapterGateAssessment(
        unlock_allowed=not blockers,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        metrics=metrics,
    )


def build_real_adapter_gate_report(
    env: Mapping[str, str] | None = None,
    config: RealAdapterGateConfig | None = None,
) -> dict[str, Any]:
    authorization_packet = build_canary_authorization_packet()
    kill_switch_report = build_canary_kill_switch_report()
    assessment = assess_real_adapter_gate(
        authorization_packet=authorization_packet,
        kill_switch_report=kill_switch_report,
        env=env,
        config=config,
    )
    return {
        "assessment": assessment.__dict__,
        "authorization_packet_status": authorization_packet["status"],
        "authorization_blockers": authorization_packet["blockers"],
        "kill_switch_active": kill_switch_report["assessment"]["active"],
    }


def render_real_adapter_gate_markdown(report: dict[str, Any]) -> str:
    assessment = report["assessment"]
    lines = [
        "# Real Adapter Gate Report",
        "",
        f"- unlock_allowed: {assessment['unlock_allowed']}",
        f"- authorization_packet_status: {report['authorization_packet_status']}",
        f"- kill_switch_active: {report['kill_switch_active']}",
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
            "This gate only controls whether real adapter development may proceed. It does not submit orders and it does not read private keys.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_real_adapter_gate_report(
    output_path: Path = DEFAULT_REAL_ADAPTER_GATE_REPORT,
    env: Mapping[str, str] | None = None,
    config: RealAdapterGateConfig | None = None,
) -> dict[str, Any]:
    report = build_real_adapter_gate_report(env=env, config=config)
    output_path.write_text(render_real_adapter_gate_markdown(report), encoding="utf-8")
    return report


def _render_items(items: tuple[str, ...] | list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]
