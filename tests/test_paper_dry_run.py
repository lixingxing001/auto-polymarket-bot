import csv
import json
import tempfile
import unittest
from pathlib import Path

from btc5m_bot.execution_safety import ExecutionSafetyConfig
from btc5m_bot.paper_dry_run import (
    append_dry_run,
    assess_signal_execution_preflight,
    build_proposed_order_from_signal,
)


class PaperDryRunTests(unittest.TestCase):
    def test_build_proposed_order_from_up_signal(self) -> None:
        order = build_proposed_order_from_signal(_signal("UP"))
        self.assertIsNotNone(order)
        self.assertEqual(order.outcome, "UP")
        self.assertEqual(order.price, 0.55)
        self.assertEqual(order.probability, 0.72)
        self.assertEqual(order.available_liquidity_usd, 100.0)

    def test_build_proposed_order_from_down_signal_uses_inverse_probability(self) -> None:
        order = build_proposed_order_from_signal(_signal("DOWN"))
        self.assertIsNotNone(order)
        self.assertEqual(order.outcome, "DOWN")
        self.assertEqual(order.price, 0.45)
        self.assertAlmostEqual(order.probability, 0.28)
        self.assertEqual(order.available_liquidity_usd, 120.0)

    def test_hold_signal_has_no_proposed_order_and_warns(self) -> None:
        result = assess_signal_execution_preflight(
            signal=_signal("HOLD"),
            forward_ledger_rows=_ready_forward_rows(),
            execution_ledger_rows=[],
            config=ExecutionSafetyConfig(live_trading_enabled=True),
        )
        self.assertIsNone(result["proposed_order"])
        self.assertFalse(result["actionable_signal"])
        self.assertFalse(result["order_send_allowed"])
        self.assertTrue(result["assessment"]["allowed"])
        self.assertIn("no_proposed_order", result["assessment"]["warnings"])

    def test_dry_run_uses_execution_safety_gate(self) -> None:
        result = assess_signal_execution_preflight(
            signal=_signal("UP"),
            forward_ledger_rows=_ready_forward_rows(),
            execution_ledger_rows=[],
        )
        self.assertFalse(result["order_send_allowed"])
        self.assertFalse(result["assessment"]["allowed"])
        self.assertIn("live_trading_disabled", result["assessment"]["reasons"])
        self.assertEqual(result["guardrails"]["stage"], "change_review_ready")

    def test_append_dry_run_writes_preflight_json(self) -> None:
        dry_run = {
            **_signal("UP"),
            "execution_preflight": assess_signal_execution_preflight(
                signal=_signal("UP"),
                forward_ledger_rows=_ready_forward_rows(),
                execution_ledger_rows=[],
            ),
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dry_runs.csv"
            append_dry_run(path, dry_run)
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1)
        reasons = json.loads(rows[0]["execution_preflight_reasons_json"])
        self.assertIn("live_trading_disabled", reasons)
        proposed_order = json.loads(rows[0]["proposed_order_json"])
        self.assertEqual(proposed_order["outcome"], "UP")


def _signal(decision: str) -> dict:
    payload = {
        "timestamp": "2026-05-18T12:00:00+00:00",
        "slug": "btc-updown-demo",
        "title": "BTC Up or Down",
        "seconds_to_close": 120,
        "prob_up": 0.72,
        "up_ask": 0.55,
        "down_ask": 0.45,
        "up_liquidity_usd": 100.0,
        "down_liquidity_usd": 120.0,
        "decision": decision,
        "edge": 0.08,
        "size_usd": 8.0,
        "reason": "edge_passed" if decision != "HOLD" else "edge_too_small",
        "features": {"return_1m": 0.001},
    }
    if decision == "HOLD":
        payload["size_usd"] = 0.0
    return payload


def _ready_forward_rows() -> list[dict[str, str]]:
    rows = []
    for index in range(30):
        pnl = "1.0" if index < 20 else "-0.5"
        rows.append({"reason": "traded", "pnl_usd": pnl, "edge": "0.06"})
    rows.extend({"reason": "low_confidence", "pnl_usd": "", "edge": ""} for _ in range(70))
    return rows


if __name__ == "__main__":
    unittest.main()
