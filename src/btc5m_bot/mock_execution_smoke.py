from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .live_execution import (
    DEFAULT_ATTEMPT_LOG,
    MockExecutionAdapter,
    append_execution_attempt,
    submit_preflighted_order,
)
from .order_intent import (
    DEFAULT_INTENT_EVENT_LOG,
    append_order_intent_events,
    build_order_intent_flow,
    intent_to_dict,
)


DEFAULT_SMOKE_REPORT = Path("mock_execution_smoke_report.md")


def build_mock_smoke_dry_run(now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    timestamp = now.isoformat()
    proposed_order = {
        "slug": "mock-smoke-btc-updown",
        "outcome": "UP",
        "price": 0.55,
        "stake_usd": 1.0,
        "edge": 0.08,
        "probability": 0.72,
        "available_liquidity_usd": 100.0,
        "seconds_to_close": 120,
        "client_order_id": f"mock-smoke-{timestamp.replace(':', '').replace('+', '')}",
    }
    return {
        "timestamp": timestamp,
        "slug": proposed_order["slug"],
        "title": "Mock smoke BTC Up or Down",
        "seconds_to_close": proposed_order["seconds_to_close"],
        "prob_up": proposed_order["probability"],
        "up_ask": proposed_order["price"],
        "down_ask": 1.0 - proposed_order["price"],
        "up_liquidity_usd": proposed_order["available_liquidity_usd"],
        "down_liquidity_usd": proposed_order["available_liquidity_usd"],
        "decision": proposed_order["outcome"],
        "edge": proposed_order["edge"],
        "size_usd": proposed_order["stake_usd"],
        "reason": "mock_smoke_fixture",
        "features": {},
        "execution_preflight": {
            "actionable_signal": True,
            "order_send_allowed": True,
            "proposed_order": proposed_order,
            "assessment": {
                "allowed": True,
                "reasons": (),
                "warnings": ("mock_smoke_fixture",),
                "metrics": {
                    "fixture": True,
                },
            },
        },
    }


def run_mock_execution_smoke(
    attempt_log_path: Path = DEFAULT_ATTEMPT_LOG,
    intent_event_log_path: Path = DEFAULT_INTENT_EVENT_LOG,
    now: datetime | None = None,
) -> dict[str, Any]:
    dry_run = build_mock_smoke_dry_run(now=now)
    preflight = dry_run["execution_preflight"]
    attempt = submit_preflighted_order(
        proposed_order=preflight["proposed_order"],
        preflight=preflight,
        adapter=MockExecutionAdapter(),
        now=now,
    )
    intent, events = build_order_intent_flow(dry_run=dry_run, attempt=attempt, now=now)
    append_execution_attempt(attempt_log_path, attempt)
    append_order_intent_events(intent_event_log_path, events)
    return {
        "dry_run": dry_run,
        "intent": intent_to_dict(intent),
        "intent_events": [asdict(event) for event in events],
        "attempt": asdict(attempt),
    }


def render_mock_smoke_report(result: dict[str, Any]) -> str:
    attempt = result["attempt"]
    intent = result["intent"]
    return (
        "# Mock Execution Smoke Report\n\n"
        "## Result\n\n"
        f"- attempt_accepted: {attempt['accepted']}\n"
        f"- attempt_status: {attempt['status']}\n"
        f"- attempt_reason: {attempt['reason']}\n"
        f"- intent_status: {intent['status']}\n"
        f"- exchange_order_id: {attempt['exchange_order_id']}\n\n"
        "## Boundary\n\n"
        "This smoke test uses a fixed mock fixture and the mock adapter only. It does not prove strategy profitability and it does not submit a real Polymarket order.\n"
    )


def write_mock_execution_smoke_report(
    output_path: Path = DEFAULT_SMOKE_REPORT,
    attempt_log_path: Path = DEFAULT_ATTEMPT_LOG,
    intent_event_log_path: Path = DEFAULT_INTENT_EVENT_LOG,
    now: datetime | None = None,
) -> dict[str, Any]:
    result = run_mock_execution_smoke(
        attempt_log_path=attempt_log_path,
        intent_event_log_path=intent_event_log_path,
        now=now,
    )
    output_path.write_text(render_mock_smoke_report(result), encoding="utf-8")
    return result
