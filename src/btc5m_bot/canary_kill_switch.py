from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .execution_safety import (
    ExecutionLedgerEntry,
    load_execution_ledger_rows,
    parse_execution_ledger_rows,
    summarize_execution_ledger,
)


DEFAULT_EXECUTION_LEDGER = Path("data/live_execution_ledger.csv")
DEFAULT_KILL_SWITCH_FILE = Path("data/CANARY_KILL_SWITCH")
DEFAULT_KILL_SWITCH_REPORT = Path("canary_kill_switch_report.md")


@dataclass(frozen=True)
class CanaryKillSwitchConfig:
    max_daily_loss_usd: float = 3.0
    max_consecutive_losses: int = 2
    max_daily_trades: int = 3
    max_open_exposures: int = 1
    max_order_stake_usd: float = 1.0


@dataclass(frozen=True)
class CanaryKillSwitchAssessment:
    active: bool
    reasons: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    metrics: dict[str, Any] = field(default_factory=dict)


def assess_canary_kill_switch(
    entries: tuple[ExecutionLedgerEntry, ...],
    config: CanaryKillSwitchConfig | None = None,
    kill_switch_file_exists: bool = False,
    proposed_stake_usd: float | None = None,
    now: datetime | None = None,
) -> CanaryKillSwitchAssessment:
    config = config or CanaryKillSwitchConfig()
    summary = summarize_execution_ledger(entries, now=now)
    reasons: list[str] = []
    warnings: list[str] = []

    if kill_switch_file_exists:
        reasons.append("manual_kill_switch_file_present")
    if summary.daily_realized_pnl_usd <= -config.max_daily_loss_usd:
        reasons.append("daily_loss_limit_reached")
    if summary.consecutive_losses >= config.max_consecutive_losses:
        reasons.append("consecutive_loss_limit_reached")
    if summary.daily_trade_count >= config.max_daily_trades:
        reasons.append("daily_trade_limit_reached")
    if len(summary.open_exposures) >= config.max_open_exposures:
        reasons.append("open_exposure_limit_reached")
    if proposed_stake_usd is not None and proposed_stake_usd > config.max_order_stake_usd:
        reasons.append("proposed_stake_above_canary_cap")
    if not entries:
        warnings.append("no_live_execution_ledger_entries")

    metrics = {
        "daily_trade_count": summary.daily_trade_count,
        "daily_realized_pnl_usd": summary.daily_realized_pnl_usd,
        "consecutive_losses": summary.consecutive_losses,
        "open_exposures": len(summary.open_exposures),
        "max_daily_loss_usd": config.max_daily_loss_usd,
        "max_consecutive_losses": config.max_consecutive_losses,
        "max_daily_trades": config.max_daily_trades,
        "max_open_exposures": config.max_open_exposures,
        "max_order_stake_usd": config.max_order_stake_usd,
    }
    return CanaryKillSwitchAssessment(
        active=bool(reasons),
        reasons=tuple(dict.fromkeys(reasons)),
        warnings=tuple(dict.fromkeys(warnings)),
        metrics=metrics,
    )


def build_canary_kill_switch_report(
    ledger_path: Path = DEFAULT_EXECUTION_LEDGER,
    kill_switch_path: Path = DEFAULT_KILL_SWITCH_FILE,
    config: CanaryKillSwitchConfig | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    entries = parse_execution_ledger_rows(load_execution_ledger_rows(ledger_path))
    assessment = assess_canary_kill_switch(
        entries=entries,
        config=config,
        kill_switch_file_exists=kill_switch_path.exists(),
        now=now,
    )
    return {
        "assessment": assessment.__dict__,
        "kill_switch_file": str(kill_switch_path),
        "ledger_path": str(ledger_path),
    }


def render_canary_kill_switch_markdown(report: dict[str, Any]) -> str:
    assessment = report["assessment"]
    lines = [
        "# Canary Kill Switch Report",
        "",
        f"- active: {assessment['active']}",
        f"- kill_switch_file: {report['kill_switch_file']}",
        f"- ledger_path: {report['ledger_path']}",
        "",
        "## Reasons",
        "",
        *(_render_items(assessment["reasons"])),
        "",
        "## Warnings",
        "",
        *(_render_items(assessment["warnings"])),
        "",
        "## Metrics",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in assessment["metrics"].items())
    return "\n".join(lines) + "\n"


def write_canary_kill_switch_report(
    output_path: Path = DEFAULT_KILL_SWITCH_REPORT,
    ledger_path: Path = DEFAULT_EXECUTION_LEDGER,
    kill_switch_path: Path = DEFAULT_KILL_SWITCH_FILE,
    config: CanaryKillSwitchConfig | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    report = build_canary_kill_switch_report(
        ledger_path=ledger_path,
        kill_switch_path=kill_switch_path,
        config=config,
        now=now,
    )
    output_path.write_text(render_canary_kill_switch_markdown(report), encoding="utf-8")
    return report


def _render_items(items: tuple[str, ...] | list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]
