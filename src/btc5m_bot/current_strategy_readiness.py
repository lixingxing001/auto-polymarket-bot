from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .active_strategy import DEFAULT_ACTIVE_STRATEGY_STATE, load_active_strategy_state
from .canary_readiness import DEFAULT_FORWARD_LEDGER
from .strategy_guardrails import load_forward_ledger_rows, summarize_forward_ledger


DEFAULT_CURRENT_STRATEGY_READINESS_REPORT = Path("current_strategy_readiness_report.md")


@dataclass(frozen=True)
class CurrentStrategyReadinessPolicy:
    min_evaluations: int = 30
    min_trades: int = 30
    min_win_rate: float = 0.55
    min_total_pnl_usd: float = 0.0


@dataclass(frozen=True)
class CurrentStrategyReadinessResult:
    ready: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    metrics: dict[str, Any] = field(default_factory=dict)


def build_current_strategy_readiness_report(
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
    strategy_state_path: Path = DEFAULT_ACTIVE_STRATEGY_STATE,
    policy: CurrentStrategyReadinessPolicy | None = None,
) -> dict[str, Any]:
    policy = policy or CurrentStrategyReadinessPolicy()
    state = load_active_strategy_state(strategy_state_path)
    rows = load_forward_ledger_rows(forward_ledger_path)
    matching_rows = filter_rows_for_current_strategy(rows, state)
    missing_version_rows = [
        row
        for row in rows
        if "active_strategy_source_candidate_id" not in row
        or row.get("active_strategy_source_candidate_id", "") == "legacy_unversioned"
        or (
            row.get("active_strategy_source_candidate_id", "") == "baseline"
            and not row.get("market_end_time", "")
        )
    ]
    summary = summarize_forward_ledger(matching_rows)

    blockers: list[str] = []
    warnings: list[str] = []
    if summary.evaluations < policy.min_evaluations:
        blockers.append("insufficient_current_strategy_evaluations")
    if summary.traded_rows < policy.min_trades:
        blockers.append("insufficient_current_strategy_trades")
    if summary.total_pnl_usd <= policy.min_total_pnl_usd:
        blockers.append("current_strategy_pnl_not_positive")
    if summary.traded_rows and summary.win_rate < policy.min_win_rate:
        blockers.append("current_strategy_win_rate_below_floor")
    if missing_version_rows:
        warnings.append("legacy_forward_rows_without_strategy_version")

    market_end_times = [
        row.get("market_end_time", "")
        for row in matching_rows
        if row.get("market_end_time", "")
    ]
    metrics = {
        "source_candidate_id": state.source_candidate_id,
        "filter_kind": state.filter_kind,
        "activated_at": state.activated_at.isoformat(),
        "live_trading_enabled": state.live_trading_enabled,
        "current_strategy_evaluations": summary.evaluations,
        "current_strategy_trades": summary.traded_rows,
        "current_strategy_wins": summary.wins,
        "current_strategy_losses": summary.losses,
        "current_strategy_win_rate": summary.win_rate,
        "current_strategy_total_pnl_usd": summary.total_pnl_usd,
        "current_strategy_avg_pnl_usd": summary.avg_pnl_usd,
        "current_strategy_hold_reasons": summary.hold_reasons,
        "legacy_rows_without_strategy_version": len(missing_version_rows),
        "first_market_end_time": min(market_end_times) if market_end_times else "",
        "latest_market_end_time": max(market_end_times) if market_end_times else "",
        "policy": asdict(policy),
    }
    result = CurrentStrategyReadinessResult(
        ready=not blockers,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        metrics=metrics,
    )
    return {
        "readiness": result.__dict__,
        "active_strategy_state": {
            "source_candidate_id": state.source_candidate_id,
            "filter_kind": state.filter_kind,
            "activated_at": state.activated_at.isoformat(),
            "live_trading_enabled": state.live_trading_enabled,
            "min_confidence": state.min_confidence,
            "min_edge": state.min_edge,
            "stake_usd": state.stake_usd,
            "max_fill_delay_seconds": state.max_fill_delay_seconds,
        },
        "policy": asdict(policy),
    }


def filter_rows_for_current_strategy(
    rows: list[dict[str, str]],
    state: Any,
) -> list[dict[str, str]]:
    source = state.source_candidate_id
    activation = state.activated_at.isoformat()
    if source == "baseline":
        return [
            row
            for row in rows
            if row.get("active_strategy_source_candidate_id", "") == "baseline"
            and row.get("market_end_time", "")
        ]
    return [
        row
        for row in rows
        if row.get("active_strategy_source_candidate_id", "") == source
        and row.get("active_strategy_activated_at", "") == activation
    ]


def render_current_strategy_readiness_markdown(report: dict[str, Any]) -> str:
    readiness = report["readiness"]
    metrics = readiness["metrics"]
    state = report["active_strategy_state"]
    policy = report["policy"]
    lines = [
        "# Current Strategy Readiness Report",
        "",
        "## Status",
        "",
        f"- ready: {readiness['ready']}",
        f"- source_candidate_id: {state['source_candidate_id']}",
        f"- filter_kind: {state['filter_kind']}",
        f"- activated_at: {state['activated_at']}",
        f"- live_trading_enabled: {state['live_trading_enabled']}",
        "",
        "## Blockers",
        "",
        *(_render_items(readiness["blockers"])),
        "",
        "## Warnings",
        "",
        *(_render_items(readiness["warnings"])),
        "",
        "## Metrics",
        "",
        f"- evaluations: {metrics['current_strategy_evaluations']}",
        f"- trades: {metrics['current_strategy_trades']}",
        f"- wins: {metrics['current_strategy_wins']}",
        f"- losses: {metrics['current_strategy_losses']}",
        f"- win_rate: {metrics['current_strategy_win_rate']}",
        f"- total_pnl_usd: {metrics['current_strategy_total_pnl_usd']}",
        f"- avg_pnl_usd: {metrics['current_strategy_avg_pnl_usd']}",
        f"- hold_reasons: {metrics['current_strategy_hold_reasons']}",
        f"- first_market_end_time: {metrics['first_market_end_time']}",
        f"- latest_market_end_time: {metrics['latest_market_end_time']}",
        f"- legacy_rows_without_strategy_version: {metrics['legacy_rows_without_strategy_version']}",
        "",
        "## Policy",
        "",
        f"- min_evaluations: {policy['min_evaluations']}",
        f"- min_trades: {policy['min_trades']}",
        f"- min_win_rate: {policy['min_win_rate']}",
        f"- min_total_pnl_usd: {policy['min_total_pnl_usd']}",
        "",
        "## Boundary",
        "",
        "This report evaluates the current paper strategy only. It does not enable live trading and it does not submit orders.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_current_strategy_readiness_report(
    output_path: Path = DEFAULT_CURRENT_STRATEGY_READINESS_REPORT,
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
    strategy_state_path: Path = DEFAULT_ACTIVE_STRATEGY_STATE,
    policy: CurrentStrategyReadinessPolicy | None = None,
) -> dict[str, Any]:
    report = build_current_strategy_readiness_report(
        forward_ledger_path=forward_ledger_path,
        strategy_state_path=strategy_state_path,
        policy=policy,
    )
    output_path.write_text(
        render_current_strategy_readiness_markdown(report),
        encoding="utf-8",
    )
    return report


def _render_items(items: tuple[str, ...] | list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]
