from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .execution_safety import ProposedOrder
from .order_intent import (
    DEFAULT_INTENT_EVENT_LOG,
    append_order_intent_events,
    build_order_intent_flow,
    intent_to_dict,
)
from .paper_dry_run import generate_paper_dry_run


DEFAULT_ATTEMPT_LOG = Path("data/live_execution_attempts.csv")


class ExecutionAdapter(Protocol):
    adapter_name: str

    def submit_order(
        self,
        order: ProposedOrder,
        preflight: dict[str, Any],
        now: datetime | None = None,
    ) -> "ExecutionAttempt":
        ...


@dataclass(frozen=True)
class ExecutionAttempt:
    created_at: datetime
    adapter: str
    accepted: bool
    status: str
    reason: str
    slug: str
    outcome: str
    price: float
    stake_usd: float
    client_order_id: str
    exchange_order_id: str = ""
    safety_reasons: tuple[str, ...] = ()
    safety_warnings: tuple[str, ...] = ()

    def to_row(self) -> dict[str, str]:
        return {
            "created_at": self.created_at.isoformat(),
            "adapter": self.adapter,
            "accepted": str(self.accepted),
            "status": self.status,
            "reason": self.reason,
            "slug": self.slug,
            "outcome": self.outcome,
            "price": str(self.price),
            "stake_usd": str(self.stake_usd),
            "client_order_id": self.client_order_id,
            "exchange_order_id": self.exchange_order_id,
            "safety_reasons_json": json.dumps(self.safety_reasons, separators=(",", ":")),
            "safety_warnings_json": json.dumps(self.safety_warnings, separators=(",", ":")),
        }


class DisabledLiveExecutionAdapter:
    adapter_name = "disabled"

    def submit_order(
        self,
        order: ProposedOrder,
        preflight: dict[str, Any],
        now: datetime | None = None,
    ) -> ExecutionAttempt:
        return _attempt_from_order(
            order=order,
            preflight=preflight,
            adapter=self.adapter_name,
            accepted=False,
            status="rejected",
            reason="live_adapter_disabled",
            now=now,
        )


class MockExecutionAdapter:
    adapter_name = "mock"

    def submit_order(
        self,
        order: ProposedOrder,
        preflight: dict[str, Any],
        now: datetime | None = None,
    ) -> ExecutionAttempt:
        return _attempt_from_order(
            order=order,
            preflight=preflight,
            adapter=self.adapter_name,
            accepted=True,
            status="mock_submitted",
            reason="mock_order_accepted",
            exchange_order_id=f"mock-{order.client_order_id or order.slug}",
            now=now,
        )


def build_execution_adapter(kind: str) -> ExecutionAdapter:
    normalized = kind.lower()
    if normalized == "disabled":
        return DisabledLiveExecutionAdapter()
    if normalized == "mock":
        return MockExecutionAdapter()
    raise ValueError(f"unsupported execution adapter: {kind}")


def submit_preflighted_order(
    proposed_order: dict[str, Any] | None,
    preflight: dict[str, Any],
    adapter: ExecutionAdapter,
    now: datetime | None = None,
) -> ExecutionAttempt:
    now = now or datetime.now(timezone.utc)
    assessment = preflight.get("assessment", {})
    safety_reasons = tuple(assessment.get("reasons", ()))
    safety_warnings = tuple(assessment.get("warnings", ()))
    if proposed_order is None:
        return _empty_rejection(
            adapter=adapter.adapter_name,
            reason="no_actionable_order",
            safety_reasons=safety_reasons,
            safety_warnings=safety_warnings,
            now=now,
        )
    order = _order_from_dict(proposed_order)
    if not preflight.get("order_send_allowed", False):
        return _attempt_from_order(
            order=order,
            preflight=preflight,
            adapter=adapter.adapter_name,
            accepted=False,
            status="rejected",
            reason="safety_preflight_failed",
            now=now,
        )
    return adapter.submit_order(order, preflight, now=now)


def run_live_execution_attempt(
    adapter_kind: str = "disabled",
    attempt_log_path: Path = DEFAULT_ATTEMPT_LOG,
    intent_event_log_path: Path = DEFAULT_INTENT_EVENT_LOG,
) -> dict[str, Any]:
    dry_run = generate_paper_dry_run()
    preflight = dry_run["execution_preflight"]
    adapter = build_execution_adapter(adapter_kind)
    attempt = submit_preflighted_order(
        proposed_order=preflight.get("proposed_order"),
        preflight=preflight,
        adapter=adapter,
    )
    intent, intent_events = build_order_intent_flow(dry_run=dry_run, attempt=attempt)
    append_execution_attempt(attempt_log_path, attempt)
    append_order_intent_events(intent_event_log_path, intent_events)
    return {
        "adapter": adapter.adapter_name,
        "dry_run": dry_run,
        "intent": intent_to_dict(intent),
        "intent_events": [asdict(event) for event in intent_events],
        "attempt": asdict(attempt),
    }


def append_execution_attempt(path: Path, attempt: ExecutionAttempt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = attempt.to_row()
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _attempt_from_order(
    order: ProposedOrder,
    preflight: dict[str, Any],
    adapter: str,
    accepted: bool,
    status: str,
    reason: str,
    now: datetime | None = None,
    exchange_order_id: str = "",
) -> ExecutionAttempt:
    now = now or datetime.now(timezone.utc)
    assessment = preflight.get("assessment", {})
    return ExecutionAttempt(
        created_at=now,
        adapter=adapter,
        accepted=accepted,
        status=status,
        reason=reason,
        slug=order.slug,
        outcome=order.normalized_outcome(),
        price=order.price,
        stake_usd=order.stake_usd,
        client_order_id=order.client_order_id,
        exchange_order_id=exchange_order_id,
        safety_reasons=tuple(assessment.get("reasons", ())),
        safety_warnings=tuple(assessment.get("warnings", ())),
    )


def _empty_rejection(
    adapter: str,
    reason: str,
    safety_reasons: tuple[str, ...],
    safety_warnings: tuple[str, ...],
    now: datetime,
) -> ExecutionAttempt:
    return ExecutionAttempt(
        created_at=now,
        adapter=adapter,
        accepted=False,
        status="rejected",
        reason=reason,
        slug="",
        outcome="",
        price=0.0,
        stake_usd=0.0,
        client_order_id="",
        safety_reasons=safety_reasons,
        safety_warnings=safety_warnings,
    )


def _order_from_dict(payload: dict[str, Any]) -> ProposedOrder:
    return ProposedOrder(
        slug=str(payload["slug"]),
        outcome=str(payload["outcome"]),
        price=float(payload["price"]),
        stake_usd=float(payload["stake_usd"]),
        edge=float(payload["edge"]),
        probability=float(payload["probability"]),
        available_liquidity_usd=float(payload["available_liquidity_usd"]),
        seconds_to_close=int(payload["seconds_to_close"]),
        client_order_id=str(payload.get("client_order_id", "")),
    )
