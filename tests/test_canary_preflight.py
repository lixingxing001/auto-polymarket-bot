import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from btc5m_bot.real_adapter_gate import RealAdapterGateAssessment
from btc5m_bot.canary_preflight import (
    assess_canary_preflight,
    render_canary_preflight_markdown,
    write_canary_preflight_report,
)


class CanaryPreflightTests(unittest.TestCase):
    def test_blocked_when_readiness_is_not_ready(self) -> None:
        assessment = assess_canary_preflight(
            readiness_report=_readiness(False),
            kill_switch_report=_kill_switch(False),
            authorization_packet=_authorization(False),
            real_adapter_gate=_gate(False, ("canary_authorization_packet_not_ready",)),
        )
        self.assertEqual(assessment.status, "BLOCKED")
        self.assertFalse(assessment.real_adapter_review_allowed)
        self.assertIn("insufficient_forward_trades", assessment.blockers)

    def test_waits_for_env_when_readiness_and_authorization_are_ready(self) -> None:
        assessment = assess_canary_preflight(
            readiness_report=_readiness(True),
            kill_switch_report=_kill_switch(False),
            authorization_packet=_authorization(True),
            real_adapter_gate=_gate(False, ("lee_authorization_env_missing",)),
        )
        self.assertEqual(assessment.status, "AWAITING_LEE_AUTHORIZATION_ENV")
        self.assertEqual(assessment.next_action, "set_explicit_canary_authorization_env_after_manual_review")

    def test_unlocks_only_when_real_adapter_gate_unlocks(self) -> None:
        assessment = assess_canary_preflight(
            readiness_report=_readiness(True),
            kill_switch_report=_kill_switch(False),
            authorization_packet=_authorization(True),
            real_adapter_gate=_gate(True, tuple()),
        )
        self.assertEqual(assessment.status, "UNLOCKED_FOR_REAL_ADAPTER_REVIEW")
        self.assertTrue(assessment.real_adapter_review_allowed)

    def test_kill_switch_sets_stop_action(self) -> None:
        assessment = assess_canary_preflight(
            readiness_report=_readiness(False),
            kill_switch_report=_kill_switch(True),
            authorization_packet=_authorization(False),
            real_adapter_gate=_gate(False, ("kill_switch_active",)),
        )
        self.assertEqual(assessment.next_action, "stop_canary_work_until_kill_switch_clears")
        self.assertIn("kill_switch_active", assessment.blockers)

    def test_write_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "canary_preflight_report.md"
            with patch(
                "btc5m_bot.canary_preflight.build_canary_readiness_report",
                return_value=_readiness(True),
            ), patch(
                "btc5m_bot.canary_preflight.build_canary_kill_switch_report",
                return_value=_kill_switch(False),
            ):
                report = write_canary_preflight_report(output_path=output, env=_valid_env())
            rendered = output.read_text(encoding="utf-8")
        self.assertEqual(report["assessment"]["status"], "UNLOCKED_FOR_REAL_ADAPTER_REVIEW")
        self.assertIn("Canary Preflight Report", rendered)

    def test_render_report_lists_boundary(self) -> None:
        rendered = render_canary_preflight_markdown(
            {
                "assessment": {
                    "status": "BLOCKED",
                    "real_adapter_review_allowed": False,
                    "next_action": "collect_more_forward_evidence",
                    "blockers": ("insufficient_forward_trades",),
                    "warnings": tuple(),
                    "metrics": {},
                },
            }
        )
        self.assertIn("does not submit orders", rendered)


def _valid_env() -> dict[str, str]:
    return {
        "LEE_CANARY_AUTHORIZED": "I_ACCEPT_CANARY_RISK",
        "CANARY_WALLET_ISOLATED": "YES",
        "CANARY_MAX_FUNDING_USDC": "10",
    }


def _gate(unlock_allowed: bool, blockers: tuple[str, ...]) -> RealAdapterGateAssessment:
    return RealAdapterGateAssessment(
        unlock_allowed=unlock_allowed,
        blockers=blockers,
        warnings=tuple(),
        metrics={},
    )


def _authorization(ready: bool) -> dict:
    return {
        "status": "READY_FOR_LEE_AUTHORIZATION" if ready else "NOT_READY",
        "blockers": tuple() if ready else ("insufficient_forward_trades",),
        "warnings": tuple(),
    }


def _readiness(ready: bool) -> dict:
    return {
        "readiness": {
            "ready": ready,
            "blockers": tuple() if ready else ("insufficient_forward_trades",),
            "warnings": tuple(),
            "metrics": {
                "forward_evaluations": 100 if ready else 31,
                "forward_trades": 30 if ready else 2,
                "forward_total_pnl_usd": 5.0 if ready else 1.0,
                "review_ready_candidates": ["edge_008"] if ready else [],
            },
        },
    }


def _kill_switch(active: bool) -> dict:
    return {
        "assessment": {
            "active": active,
            "warnings": tuple(),
        },
    }


if __name__ == "__main__":
    unittest.main()
