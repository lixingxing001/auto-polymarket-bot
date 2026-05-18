import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from btc5m_bot.live_execution import (
    DisabledLiveExecutionAdapter,
    MockExecutionAdapter,
    append_execution_attempt,
    build_execution_adapter,
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
