import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import btc5m_bot.live_execution as live_execution
from btc5m_bot.live_execution import (
    DisabledLiveExecutionAdapter,
    MockExecutionAdapter,
    append_execution_attempt,
    build_execution_adapter,
    run_live_execution_attempt,
    submit_preflighted_order,
)


class LiveExecutionTests(unittest.TestCase):
    def test_disabled_adapter_rejects_allowed_order(self) -> None:
        attempt = submit_preflighted_order(
            proposed_order=_order_dict(),
            preflight=_allowed_preflight(),
            adapter=DisabledLiveExecutionAdapter(),
            now=_now(),
        )
        self.assertFalse(attempt.accepted)
        self.assertEqual(attempt.reason, "live_adapter_disabled")
        self.assertEqual(attempt.status, "rejected")

    def test_mock_adapter_accepts_allowed_order(self) -> None:
        attempt = submit_preflighted_order(
            proposed_order=_order_dict(),
            preflight=_allowed_preflight(),
            adapter=MockExecutionAdapter(),
            now=_now(),
        )
        self.assertTrue(attempt.accepted)
        self.assertEqual(attempt.status, "mock_submitted")
        self.assertTrue(attempt.exchange_order_id.startswith("mock-"))

    def test_safety_failure_blocks_before_adapter(self) -> None:
        attempt = submit_preflighted_order(
            proposed_order=_order_dict(),
            preflight={
                "order_send_allowed": False,
                "assessment": {
                    "reasons": ("insufficient_forward_trades",),
                    "warnings": (),
                },
            },
            adapter=MockExecutionAdapter(),
            now=_now(),
        )
        self.assertFalse(attempt.accepted)
        self.assertEqual(attempt.reason, "safety_preflight_failed")
        self.assertIn("insufficient_forward_trades", attempt.safety_reasons)

    def test_no_actionable_order_rejects_before_adapter(self) -> None:
        attempt = submit_preflighted_order(
            proposed_order=None,
            preflight={
                "order_send_allowed": False,
                "assessment": {
                    "reasons": (),
                    "warnings": ("no_proposed_order",),
                },
            },
            adapter=MockExecutionAdapter(),
            now=_now(),
        )
        self.assertFalse(attempt.accepted)
        self.assertEqual(attempt.reason, "no_actionable_order")
        self.assertIn("no_proposed_order", attempt.safety_warnings)


    def test_run_live_execution_attempt_writes_intent_events(self) -> None:
        original_generate = live_execution.generate_paper_dry_run
        live_execution.generate_paper_dry_run = lambda: _dry_run_payload()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                attempt_log = Path(tmp) / "attempts.csv"
                intent_log = Path(tmp) / "intent_events.csv"
                result = run_live_execution_attempt(
                    adapter_kind="mock",
                    attempt_log_path=attempt_log,
                    intent_event_log_path=intent_log,
                )
                with intent_log.open(newline="", encoding="utf-8") as handle:
                    intent_rows = list(csv.DictReader(handle))
                with attempt_log.open(newline="", encoding="utf-8") as handle:
                    attempt_rows = list(csv.DictReader(handle))
        finally:
            live_execution.generate_paper_dry_run = original_generate
        self.assertEqual(result["intent"]["status"], "mock_submitted")
        self.assertEqual(len(intent_rows), 2)
        self.assertEqual(intent_rows[-1]["status"], "mock_submitted")
        self.assertEqual(len(attempt_rows), 1)
        self.assertEqual(attempt_rows[0]["status"], "mock_submitted")

    def test_build_execution_adapter_rejects_unknown_kind(self) -> None:
        self.assertIsInstance(build_execution_adapter("disabled"), DisabledLiveExecutionAdapter)
        self.assertIsInstance(build_execution_adapter("mock"), MockExecutionAdapter)
        with self.assertRaises(ValueError):
            build_execution_adapter("real")

    def test_append_execution_attempt_writes_audit_row(self) -> None:
        attempt = submit_preflighted_order(
            proposed_order=_order_dict(),
            preflight=_allowed_preflight(),
            adapter=DisabledLiveExecutionAdapter(),
            now=_now(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "attempts.csv"
            append_execution_attempt(path, attempt)
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["reason"], "live_adapter_disabled")
        self.assertEqual(json.loads(rows[0]["safety_reasons_json"]), [])


def _dry_run_payload() -> dict:
    return {
        "timestamp": "2026-05-19T12:00:00+00:00",
        "slug": "btc-updown-demo",
        "decision": "UP",
        "reason": "edge_passed",
        "execution_preflight": {
            "actionable_signal": True,
            "order_send_allowed": True,
            "proposed_order": _order_dict(),
            "assessment": {
                "reasons": (),
                "warnings": (),
            },
        },
    }


def _order_dict() -> dict:
    return {
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


def _allowed_preflight() -> dict:
    return {
        "order_send_allowed": True,
        "assessment": {
            "reasons": (),
            "warnings": (),
        },
    }


def _now() -> datetime:
    return datetime(2026, 5, 19, 12, 0, tzinfo=timezone.utc)


if __name__ == "__main__":
    unittest.main()
