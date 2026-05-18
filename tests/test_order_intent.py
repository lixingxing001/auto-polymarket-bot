import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from btc5m_bot.live_execution import ExecutionAttempt
from btc5m_bot.order_intent import (
    STATUS_ADAPTER_REJECTED,
    STATUS_MOCK_SUBMITTED,
    STATUS_NO_ACTIONABLE_ORDER,
    STATUS_SAFETY_BLOCKED,
    append_order_intent_events,
    build_order_intent_flow,
    create_order_intent_from_dry_run,
    transition_order_intent,
)


class OrderIntentTests(unittest.TestCase):
    def test_create_intent_from_actionable_dry_run(self) -> None:
        intent, event = create_order_intent_from_dry_run(_dry_run(order_send_allowed=True), now=_now())
        self.assertEqual(intent.status, "created")
        self.assertEqual(intent.slug, "btc-updown-demo")
        self.assertEqual(intent.outcome, "UP")
        self.assertEqual(intent.price, 0.55)
        self.assertEqual(event.event_type, "intent_created")

    def test_no_actionable_order_transition(self) -> None:
        intent, events = build_order_intent_flow(
            dry_run=_dry_run(proposed_order=None),
            attempt=_attempt(reason="no_actionable_order", accepted=False),
            now=_now(),
        )
        self.assertEqual(intent.status, STATUS_NO_ACTIONABLE_ORDER)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[-1].status, STATUS_NO_ACTIONABLE_ORDER)

    def test_safety_blocked_transition(self) -> None:
        intent, events = build_order_intent_flow(
            dry_run=_dry_run(order_send_allowed=False),
            attempt=_attempt(reason="safety_preflight_failed", accepted=False),
            now=_now(),
        )
        self.assertEqual(intent.status, STATUS_SAFETY_BLOCKED)
        self.assertIn("insufficient_forward_trades", events[-1].details["safety_reasons"])

    def test_adapter_rejected_transition(self) -> None:
        intent, _ = build_order_intent_flow(
            dry_run=_dry_run(order_send_allowed=True),
            attempt=_attempt(reason="live_adapter_disabled", accepted=False),
            now=_now(),
        )
        self.assertEqual(intent.status, STATUS_ADAPTER_REJECTED)

    def test_mock_submitted_transition(self) -> None:
        intent, events = build_order_intent_flow(
            dry_run=_dry_run(order_send_allowed=True),
            attempt=_attempt(reason="mock_order_accepted", accepted=True, status="mock_submitted"),
            now=_now(),
        )
        self.assertEqual(intent.status, STATUS_MOCK_SUBMITTED)
        self.assertEqual(events[-1].exchange_order_id, "mock-order-1")

    def test_invalid_transition_is_rejected(self) -> None:
        intent, _ = create_order_intent_from_dry_run(_dry_run(order_send_allowed=True), now=_now())
        final_intent, _ = transition_order_intent(
            intent=intent,
            next_status=STATUS_MOCK_SUBMITTED,
            reason="mock_order_accepted",
            now=_now(),
        )
        with self.assertRaises(ValueError):
            transition_order_intent(
                intent=final_intent,
                next_status=STATUS_ADAPTER_REJECTED,
                reason="late_reject",
                now=_now(),
            )

    def test_append_order_intent_events_writes_csv(self) -> None:
        _, events = build_order_intent_flow(
            dry_run=_dry_run(order_send_allowed=False),
            attempt=_attempt(reason="safety_preflight_failed", accepted=False),
            now=_now(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "intent_events.csv"
            append_order_intent_events(path, events)
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]["status"], STATUS_SAFETY_BLOCKED)
        details = json.loads(rows[-1]["details_json"])
        self.assertIn("insufficient_forward_trades", details["safety_reasons"])


def _dry_run(order_send_allowed: bool = False, proposed_order: dict | None | object = object()) -> dict:
    if not isinstance(proposed_order, dict) and proposed_order is not None:
        proposed_order = {
            "slug": "btc-updown-demo",
            "outcome": "UP",
            "price": 0.55,
            "stake_usd": 8.0,
            "edge": 0.08,
            "probability": 0.72,
            "available_liquidity_usd": 100.0,
            "seconds_to_close": 120,
            "client_order_id": "order-1",
        }
    reasons = () if order_send_allowed else ("insufficient_forward_trades",)
    return {
        "timestamp": "2026-05-19T12:00:00+00:00",
        "slug": "btc-updown-demo",
        "decision": "UP" if proposed_order else "HOLD",
        "reason": "edge_passed" if proposed_order else "low_confidence",
        "execution_preflight": {
            "actionable_signal": proposed_order is not None,
            "order_send_allowed": order_send_allowed,
            "proposed_order": proposed_order,
            "assessment": {
                "reasons": reasons,
                "warnings": () if proposed_order else ("no_proposed_order",),
            },
        },
    }


def _attempt(reason: str, accepted: bool, status: str = "rejected") -> ExecutionAttempt:
    return ExecutionAttempt(
        created_at=_now(),
        adapter="mock" if accepted else "disabled",
        accepted=accepted,
        status=status,
        reason=reason,
        slug="btc-updown-demo" if reason != "no_actionable_order" else "",
        outcome="UP" if reason != "no_actionable_order" else "",
        price=0.55 if reason != "no_actionable_order" else 0.0,
        stake_usd=8.0 if reason != "no_actionable_order" else 0.0,
        client_order_id="order-1" if reason != "no_actionable_order" else "",
        exchange_order_id="mock-order-1" if accepted else "",
        safety_reasons=("insufficient_forward_trades",) if reason == "safety_preflight_failed" else (),
        safety_warnings=("no_proposed_order",) if reason == "no_actionable_order" else (),
    )


def _now() -> datetime:
    return datetime(2026, 5, 19, 12, 0, tzinfo=timezone.utc)


if __name__ == "__main__":
    unittest.main()
