from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canary_kill_switch import (
    DEFAULT_KILL_SWITCH_FILE,
    build_canary_kill_switch_report,
    render_canary_kill_switch_markdown,
)
from .canary_readiness import build_canary_readiness_report, render_canary_readiness_markdown


DEFAULT_AUTHORIZATION_PACKET = Path("canary_authorization_packet.md")


@dataclass(frozen=True)
class CanaryEnvelope:
    max_order_stake_usd: float = 1.0
    max_daily_loss_usd: float = 3.0
    max_daily_trades: int = 3
    max_open_exposures: int = 1
    max_consecutive_losses: int = 2
    canary_duration_hours: int = 24
    funding_cap_usdc: float = 10.0


def build_canary_authorization_packet(
    envelope: CanaryEnvelope | None = None,
    readiness_report: dict[str, Any] | None = None,
    kill_switch_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    envelope = envelope or CanaryEnvelope()
    readiness = readiness_report or build_canary_readiness_report()
    kill_switch = kill_switch_report or build_canary_kill_switch_report()
    readiness_result = readiness["readiness"]
    kill_switch_result = kill_switch["assessment"]
    blockers = list(readiness_result["blockers"])
    if kill_switch_result["active"]:
        blockers.append("kill_switch_active")
    packet_status = "READY_FOR_LEE_AUTHORIZATION" if not blockers else "NOT_READY"
    return {
        "status": packet_status,
        "blockers": tuple(dict.fromkeys(blockers)),
        "warnings": tuple(readiness_result["warnings"]),
        "envelope": envelope.__dict__,
        "readiness": readiness,
        "kill_switch": kill_switch,
        "operator_checklist": operator_checklist(envelope),
    }


def operator_checklist(envelope: CanaryEnvelope) -> tuple[str, ...]:
    return (
        "Confirm canary readiness report is ready true",
        "Confirm kill switch report is active false",
        f"Fund isolated wallet with at most {envelope.funding_cap_usdc} USDC",
        "Keep private key out of git, reports and logs",
        f"Set max order stake to {envelope.max_order_stake_usd} USDC",
        f"Set daily loss cap to {envelope.max_daily_loss_usd} USDC",
        "Run mock execution smoke before any canary attempt",
        "Manually authorize canary in this thread before enabling real adapter",
    )


def render_canary_authorization_packet(packet: dict[str, Any]) -> str:
    envelope = packet["envelope"]
    lines = [
        "# Canary Authorization Packet",
        "",
        "## Status",
        "",
        f"- status: {packet['status']}",
        "",
        "## Blockers",
        "",
        *(_render_items(packet["blockers"])),
        "",
        "## Warnings",
        "",
        *(_render_items(packet["warnings"])),
        "",
        "## Canary envelope",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in envelope.items())
    lines.extend(
        [
            "",
            "## Operator checklist",
            "",
            *[f"- [ ] {item}" for item in packet["operator_checklist"]],
            "",
            "## Readiness snapshot",
            "",
            render_canary_readiness_markdown(packet["readiness"]).strip(),
            "",
            "## Kill switch snapshot",
            "",
            render_canary_kill_switch_markdown(packet["kill_switch"]).strip(),
            "",
            "## Hard rule",
            "",
            f"A real canary attempt requires Lee authorization and no `{DEFAULT_KILL_SWITCH_FILE}` file present. This packet never contains private keys.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_canary_authorization_packet(
    output_path: Path = DEFAULT_AUTHORIZATION_PACKET,
    envelope: CanaryEnvelope | None = None,
) -> dict[str, Any]:
    packet = build_canary_authorization_packet(envelope=envelope)
    output_path.write_text(render_canary_authorization_packet(packet), encoding="utf-8")
    return packet


def _render_items(items: tuple[str, ...] | list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]
