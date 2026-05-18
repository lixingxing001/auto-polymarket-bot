from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .strategy_guardrails import ForwardLedgerSummary


OPEN_EXPOSURE_STATUSES = {
    "submitted",
    "open",
    "partially_filled",
    "filled",
}
CLOSED_STATUSES = {
    "cancelled",
    "canceled",
    "expired",
    "rejected",
    "settled",
    "closed",
}


@dataclass(frozen=True)
class ExecutionSafetyConfig:
    live_trading_enabled: bool = False
    min_live_forward_evaluations: int = 100
    min_live_forward_trades: int = 30
    min_live_win_rate: float = 0.55
    min_live_total_pnl_usd: float = 0.0
    max_stake_usd: float = 10.0
    max_daily_loss_usd: float = 30.0
    max_daily_trades: int = 10
    max_consecutive_losses: int = 3
    min_price: float = 0.05
    max_price: float = 0.95
    min_edge: float = 0.03
    min_confidence: float = 0.65
    max_liquidity_fraction: float = 0.10
    min_seconds_to_close: int = 45
    max_seconds_to_close: int = 260


@dataclass(frozen=True)
class ProposedOrder:
    slug: str
    outcome: str
    price: float
    stake_usd: float
    edge: float
    probability: float
    available_liquidity_usd: float
    seconds_to_close: int
    client_order_id: str = ""

    def normalized_outcome(self) -> str:
        return self.outcome.upper()


@dataclass(frozen=True)
class ExecutionLedgerEntry:
    created_at: datetime
    slug: str
    outcome: str
    status: str
    stake_usd: float
    price: float
    pnl_usd: float | None = None
    client_order_id: str = ""

    def normalized_outcome(self) -> str:
        return self.outcome.upper()

    def normalized_status(self) -> str:
        return self.status.lower()


@dataclass(frozen=True)
class ExecutionLedgerSummary:
    daily_trade_count: int
    daily_realized_pnl_usd: float
    consecutive_losses: int
    open_exposures: tuple[tuple[str, str], ...]
    open_client_order_ids: tuple[str, ...]


@dataclass(frozen=True)
class SafetyAssessment:
    allowed: bool
    reasons: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    metrics: dict[str, Any] = field(default_factory=dict)


def load_execution_ledger_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_execution_ledger_rows(rows: list[dict[str, str]]) -> tuple[ExecutionLedgerEntry, ...]:
    parsed: list[ExecutionLedgerEntry] = []
    for row in rows:
        parsed.append(
            ExecutionLedgerEntry(
                created_at=datetime.fromisoformat(row["created_at"]),
                slug=row["slug"],
                outcome=row["outcome"],
                status=row["status"],
                stake_usd=float(row.get("stake_usd", "0") or 0.0),
                price=float(row.get("price", "0") or 0.0),
                pnl_usd=_optional_float(row.get("pnl_usd", "")),
                client_order_id=row.get("client_order_id", ""),
            )
        )
    return tuple(parsed)


def summarize_execution_ledger(
    entries: tuple[ExecutionLedgerEntry, ...],
    now: datetime | None = None,
) -> ExecutionLedgerSummary:
    now = now or datetime.now(timezone.utc)
    now_date = now.astimezone(timezone.utc).date()
    daily_entries = [
        entry
        for entry in entries
        if entry.created_at.astimezone(timezone.utc).date() == now_date
        and entry.normalized_status() not in {"rejected", "cancelled", "canceled"}
    ]
    daily_realized_pnl = sum(entry.pnl_usd or 0.0 for entry in daily_entries)

    settled = [entry for entry in entries if entry.pnl_usd is not None]
    settled.sort(key=lambda entry: entry.created_at)
    consecutive_losses = 0
    for entry in reversed(settled):
        if entry.pnl_usd is not None and entry.pnl_usd <= 0:
            consecutive_losses += 1
            continue
        break

    open_entries = [
        entry
        for entry in entries
        if entry.normalized_status() in OPEN_EXPOSURE_STATUSES
        or entry.normalized_status() not in CLOSED_STATUSES
    ]
    return ExecutionLedgerSummary(
        daily_trade_count=len(daily_entries),
        daily_realized_pnl_usd=daily_realized_pnl,
        consecutive_losses=consecutive_losses,
        open_exposures=tuple(
            sorted({(entry.slug, entry.normalized_outcome()) for entry in open_entries})
        ),
        open_client_order_ids=tuple(
            sorted({entry.client_order_id for entry in open_entries if entry.client_order_id})
        ),
    )


def assess_execution_safety(
    forward_summary: ForwardLedgerSummary,
    guardrail_assessment: dict[str, Any],
    ledger_summary: ExecutionLedgerSummary,
    proposed_order: ProposedOrder | None = None,
    config: ExecutionSafetyConfig | None = None,
) -> SafetyAssessment:
    config = config or ExecutionSafetyConfig()
    reasons: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {
        "forward_evaluations": forward_summary.evaluations,
        "forward_trades": forward_summary.traded_rows,
        "forward_win_rate": forward_summary.win_rate,
        "forward_total_pnl_usd": forward_summary.total_pnl_usd,
        "guardrail_stage": guardrail_assessment.get("stage", "unknown"),
        "daily_trade_count": ledger_summary.daily_trade_count,
        "daily_realized_pnl_usd": ledger_summary.daily_realized_pnl_usd,
        "consecutive_losses": ledger_summary.consecutive_losses,
    }

    if not config.live_trading_enabled:
        reasons.append("live_trading_disabled")

    guardrail_stage = guardrail_assessment.get("stage")
    if guardrail_stage != "change_review_ready":
        reasons.append(f"strategy_guardrail_stage_{guardrail_stage or 'unknown'}")

    if forward_summary.evaluations < config.min_live_forward_evaluations:
        reasons.append("insufficient_forward_evaluations")
    if forward_summary.traded_rows < config.min_live_forward_trades:
        reasons.append("insufficient_forward_trades")
    if forward_summary.traded_rows and forward_summary.win_rate < config.min_live_win_rate:
        reasons.append("forward_win_rate_too_low")
    if forward_summary.total_pnl_usd <= config.min_live_total_pnl_usd:
        reasons.append("forward_pnl_too_low")

    if ledger_summary.daily_realized_pnl_usd <= -config.max_daily_loss_usd:
        reasons.append("daily_loss_limit_reached")
    if ledger_summary.daily_trade_count >= config.max_daily_trades:
        reasons.append("daily_trade_limit_reached")
    if ledger_summary.consecutive_losses >= config.max_consecutive_losses:
        reasons.append("consecutive_loss_limit_reached")

    if proposed_order is None:
        warnings.append("no_proposed_order")
    else:
        reasons.extend(_assess_order(proposed_order, ledger_summary, config))
        metrics.update(
            {
                "order_slug": proposed_order.slug,
                "order_outcome": proposed_order.normalized_outcome(),
                "order_price": proposed_order.price,
                "order_stake_usd": proposed_order.stake_usd,
                "order_edge": proposed_order.edge,
                "order_probability": proposed_order.probability,
                "order_available_liquidity_usd": proposed_order.available_liquidity_usd,
                "order_seconds_to_close": proposed_order.seconds_to_close,
            }
        )

    unique_reasons = tuple(dict.fromkeys(reasons))
    return SafetyAssessment(
        allowed=not unique_reasons,
        reasons=unique_reasons,
        warnings=tuple(dict.fromkeys(warnings)),
        metrics=metrics,
    )


def _assess_order(
    order: ProposedOrder,
    ledger_summary: ExecutionLedgerSummary,
    config: ExecutionSafetyConfig,
) -> list[str]:
    reasons: list[str] = []
    if order.normalized_outcome() not in {"UP", "DOWN"}:
        reasons.append("invalid_outcome")
    if not 0.0 < order.price < 1.0:
        reasons.append("invalid_price")
    elif order.price < config.min_price or order.price > config.max_price:
        reasons.append("price_outside_safety_band")
    if order.stake_usd <= 0:
        reasons.append("invalid_stake")
    elif order.stake_usd > config.max_stake_usd:
        reasons.append("stake_above_max")
    if order.edge < config.min_edge:
        reasons.append("edge_below_minimum")
    if order.probability < config.min_confidence:
        reasons.append("confidence_below_minimum")
    if order.available_liquidity_usd < order.stake_usd:
        reasons.append("insufficient_liquidity")
    elif order.stake_usd > order.available_liquidity_usd * config.max_liquidity_fraction:
        reasons.append("stake_too_large_for_liquidity")
    if order.seconds_to_close < config.min_seconds_to_close:
        reasons.append("too_close_to_market_close")
    if order.seconds_to_close > config.max_seconds_to_close:
        reasons.append("too_early_or_wrong_market_window")
    if (order.slug, order.normalized_outcome()) in ledger_summary.open_exposures:
        reasons.append("duplicate_open_exposure")
    if order.client_order_id and order.client_order_id in ledger_summary.open_client_order_ids:
        reasons.append("duplicate_client_order_id")
    return reasons


def _optional_float(value: str | None) -> float | None:
    return float(value) if value not in {"", None} else None
