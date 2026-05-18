from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_INTENT_EVENT_LOG = Path("data/order_intent_events.csv")

STATUS_CREATED = "created"
STATUS_NO_ACTIONABLE_ORDER = "no_actionable_order"
STATUS_SAFETY_BLOCKED = "safety_blocked"
STATUS_ADAPTER_REJECTED = "adapter_rejected"
STATUS_MOCK_SUBMITTED = "mock_submitted"

VALID_TRANSITIONS = {
    STATUS_CREATED: {
        STATUS_NO_ACTIONABLE_ORDER,
        STATUS_SAFETY_BLOCKED,
        STATUS_ADAPTER_REJECTED,
        STATUS_MOCK_SUBMITTED,
    },
}


@dataclass(frozen=True)
class OrderIntent:
    intent_id: str
    created_at: datetime
    status: str
    slug: str
    outcome: str
    price: float
    stake_usd: float
    client_order_id: str
    source: str = "paper_dry_run"


@dataclass(frozen=True)
class OrderIntentEvent:
    created_at: datetime
    intent_id: str
    event_type: str
    status: str
    reason: str
    slug: str
    outcome: str
    adapter: str = ""
    client_order_id: str = ""
    exchange_order_id: str = ""
    details: dict[str, Any] | None = None

    def to_row(self) -> dict[str, str]:
        return {
            "created_at": self.created_at.isoformat(),
            "intent_id": self.intent_id,
            "event_type": self.event_type,
            "status": self.status,
            "reason": self.reason,
            "slug": self.slug,
            "outcome": self.outcome,
            "adapter": self.adapter,
            "client_order_id": self.client_order_id,
            "exchange_order_id": self.exchange_order_id,
            "details_json": json.dumps(
                self.details or {},
                separators=(",", ":"),
                sort_keys=True,
            ),
        }


def create_order_intent_from_dry_run(
    dry_run: dict[str, Any],
    now: datetime | None = None,
) -> tuple[OrderIntent, OrderIntentEvent]:
    now = now or datetime.now(timezone.utc)
    preflight = dry_run.get("execution_preflight", {})
    proposed_order = preflight.get("proposed_order") or {}
    slug = str(proposed_order.get("slug") or dry_run.get("slug", ""))
    outcome = str(proposed_order.get("outcome") or dry_run.get("decision", ""))
    if outcome.upper() == "HOLD":
        outcome = ""
    client_order_id = str(proposed_order.get("client_order_id", ""))
    intent = OrderIntent(
        intent_id=build_intent_id(dry_run, proposed_order),
        created_at=now,
        status=STATUS_CREATED,
        slug=slug,
        outcome=outcome.upper(),
        price=float(proposed_order.get("price") or 0.0),
        stake_usd=float(proposed_order.get("stake_usd") or 0.0),
        client_order_id=client_order_id,
    )
    event = OrderIntentEvent(
        created_at=now,
        intent_id=intent.intent_id,
        event_type="intent_created",
        status=intent.status,
        reason="intent_created",
        slug=intent.slug,
        outcome=intent.outcome,
        client_order_id=intent.client_order_id,
        details={
            "source": intent.source,
            "paper_decision": dry_run.get("decision", ""),
            "paper_reason": dry_run.get("reason", ""),
            "actionable_signal": preflight.get("actionable_signal", False),
            "order_send_allowed": preflight.get("order_send_allowed", False),
        },
    )
    return intent, event


def transition_order_intent(
    intent: OrderIntent,
    next_status: str,
    reason: str,
    now: datetime | None = None,
    adapter: str = "",
    exchange_order_id: str = "",
    details: dict[str, Any] | None = None,
) -> tuple[OrderIntent, OrderIntentEvent]:
    allowed_next = VALID_TRANSITIONS.get(intent.status, set())
    if next_status not in allowed_next:
        raise ValueError(f"invalid intent transition: {intent.status} -> {next_status}")
    now = now or datetime.now(timezone.utc)
    updated = OrderIntent(
        intent_id=intent.intent_id,
        created_at=intent.created_at,
        status=next_status,
        slug=intent.slug,
        outcome=intent.outcome,
        price=intent.price,
        stake_usd=intent.stake_usd,
        client_order_id=intent.client_order_id,
        source=intent.source,
    )
    event = OrderIntentEvent(
        created_at=now,
        intent_id=intent.intent_id,
        event_type="intent_transition",
        status=next_status,
        reason=reason,
        slug=intent.slug,
        outcome=intent.outcome,
        adapter=adapter,
        client_order_id=intent.client_order_id,
        exchange_order_id=exchange_order_id,
        details=details or {},
    )
    return updated, event


def build_order_intent_flow(
    dry_run: dict[str, Any],
    attempt: Any,
    now: datetime | None = None,
) -> tuple[OrderIntent, tuple[OrderIntentEvent, ...]]:
    now = now or datetime.now(timezone.utc)
    intent, created_event = create_order_intent_from_dry_run(dry_run, now=now)
    preflight = dry_run.get("execution_preflight", {})
    assessment = preflight.get("assessment", {})
    details = {
        "attempt_status": getattr(attempt, "status", ""),
        "attempt_reason": getattr(attempt, "reason", ""),
        "safety_reasons": tuple(assessment.get("reasons", ())),
        "safety_warnings": tuple(assessment.get("warnings", ())),
        "order_send_allowed": preflight.get("order_send_allowed", False),
    }
    adapter = str(getattr(attempt, "adapter", ""))
    exchange_order_id = str(getattr(attempt, "exchange_order_id", ""))

    if preflight.get("proposed_order") is None:
        final_status = STATUS_NO_ACTIONABLE_ORDER
    elif not preflight.get("order_send_allowed", False):
        final_status = STATUS_SAFETY_BLOCKED
    elif getattr(attempt, "accepted", False):
        final_status = STATUS_MOCK_SUBMITTED
    else:
        final_status = STATUS_ADAPTER_REJECTED

    final_intent, transition_event = transition_order_intent(
        intent=intent,
        next_status=final_status,
        reason=str(getattr(attempt, "reason", final_status)),
        now=now,
        adapter=adapter,
        exchange_order_id=exchange_order_id,
        details=details,
    )
    return final_intent, (created_event, transition_event)


def append_order_intent_events(path: Path, events: tuple[OrderIntentEvent, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        fieldnames = list(OrderIntentEvent.__dataclass_fields__.keys())
        fieldnames[-1] = "details_json"
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for event in events:
            writer.writerow(event.to_row())


def build_intent_id(dry_run: dict[str, Any], proposed_order: dict[str, Any]) -> str:
    client_order_id = str(proposed_order.get("client_order_id", ""))
    if client_order_id:
        return f"intent-{client_order_id}"
    timestamp = str(dry_run.get("timestamp", "unknown"))
    slug = str(dry_run.get("slug", "unknown"))
    decision = str(dry_run.get("decision", "hold")).lower()
    cleaned_timestamp = (
        timestamp.replace(":", "")
        .replace("+", "")
        .replace(".", "")
    )
    return f"intent-{slug}-{decision}-{cleaned_timestamp}"


def intent_to_dict(intent: OrderIntent) -> dict[str, Any]:
    return asdict(intent)
