import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from btc5m_bot.canary_authorization import (
    CanaryEnvelope,
    build_canary_authorization_packet,
    operator_checklist,
    render_canary_authorization_packet,
    write_canary_authorization_packet,
)


class CanaryAuthorizationTests(unittest.TestCase):
    def test_packet_not_ready_when_readiness_has_blockers(self) -> None:
        with patch("btc5m_bot.canary_authorization.build_canary_readiness_report", return_value=_readiness(False)), patch(
            "btc5m_bot.canary_authorization.build_canary_kill_switch_report",
            return_value=_kill_switch(False),
        ):
            packet = build_canary_authorization_packet()
        self.assertEqual(packet["status"], "NOT_READY")
        self.assertIn("insufficient_forward_trades", packet["blockers"])

    def test_packet_ready_when_no_blockers_and_kill_switch_inactive(self) -> None:
        with patch("btc5m_bot.canary_authorization.build_canary_readiness_report", return_value=_readiness(True)), patch(
            "btc5m_bot.canary_authorization.build_canary_kill_switch_report",
            return_value=_kill_switch(False),
        ):
            packet = build_canary_authorization_packet()
        self.assertEqual(packet["status"], "READY_FOR_LEE_AUTHORIZATION")
        self.assertEqual(packet["blockers"], tuple())

    def test_kill_switch_active_blocks_packet(self) -> None:
        with patch("btc5m_bot.canary_authorization.build_canary_readiness_report", return_value=_readiness(True)), patch(
            "btc5m_bot.canary_authorization.build_canary_kill_switch_report",
            return_value=_kill_switch(True),
        ):
            packet = build_canary_authorization_packet()
        self.assertEqual(packet["status"], "NOT_READY")
        self.assertIn("kill_switch_active", packet["blockers"])

    def test_operator_checklist_contains_limits(self) -> None:
        checklist = operator_checklist(CanaryEnvelope(max_order_stake_usd=1.0, max_daily_loss_usd=3.0))
        self.assertTrue(any("1.0 USDC" in item for item in checklist))
        self.assertTrue(any("3.0 USDC" in item for item in checklist))

    def test_write_authorization_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "packet.md"
            with patch("btc5m_bot.canary_authorization.build_canary_readiness_report", return_value=_readiness(False)), patch(
                "btc5m_bot.canary_authorization.build_canary_kill_switch_report",
                return_value=_kill_switch(False),
            ):
                packet = write_canary_authorization_packet(output_path=output)
            rendered = output.read_text(encoding="utf-8")
        self.assertEqual(packet["status"], "NOT_READY")
        self.assertIn("Canary Authorization Packet", rendered)
        self.assertIn("This packet never contains private keys", rendered)

    def test_render_packet(self) -> None:
        packet = {
            "status": "NOT_READY",
            "blockers": ("insufficient_forward_trades",),
            "warnings": tuple(),
            "envelope": CanaryEnvelope().__dict__,
            "readiness": _readiness(False),
            "kill_switch": _kill_switch(False),
            "operator_checklist": ("Confirm readiness",),
        }
        rendered = render_canary_authorization_packet(packet)
        self.assertIn("insufficient_forward_trades", rendered)


def _readiness(ready: bool) -> dict:
    return {
        "readiness": {
            "ready": ready,
            "blockers": tuple() if ready else ("insufficient_forward_trades",),
            "warnings": tuple(),
            "metrics": {
                "forward_evaluations": 100 if ready else 28,
                "forward_trades": 30 if ready else 2,
                "forward_win_rate": 0.6,
                "forward_total_pnl_usd": 5.0,
                "guardrail_stage": "change_review_ready" if ready else "collecting",
                "next_change_review_gap": {"evaluations_needed": 0, "trades_needed": 0},
                "candidate_count": 1,
                "review_ready_candidates": ["edge_008"] if ready else [],
                "collecting_candidates": [],
                "accepted_attempts": 1,
                "rejected_attempts": 0,
            },
        },
        "candidate_statuses": {},
    }


def _kill_switch(active: bool) -> dict:
    return {
        "assessment": {
            "active": active,
            "reasons": ("manual_kill_switch_file_present",) if active else tuple(),
            "warnings": tuple(),
            "metrics": {
                "daily_trade_count": 0,
                "daily_realized_pnl_usd": 0.0,
            },
        },
        "kill_switch_file": "data/CANARY_KILL_SWITCH",
        "ledger_path": "data/live_execution_ledger.csv",
    }


if __name__ == "__main__":
    unittest.main()
