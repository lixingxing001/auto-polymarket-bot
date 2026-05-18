import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from btc5m_bot.real_adapter_gate import (
    RealAdapterGateConfig,
    assess_real_adapter_gate,
    render_real_adapter_gate_markdown,
    write_real_adapter_gate_report,
)


class RealAdapterGateTests(unittest.TestCase):
    def test_empty_env_blocks_even_when_process_env_has_values(self) -> None:
        packet = _authorization_packet(ready=True)
        kill_switch = _kill_switch(active=False)
        with patch.dict(
            "os.environ",
            {
                "LEE_CANARY_AUTHORIZED": "I_ACCEPT_CANARY_RISK",
                "CANARY_WALLET_ISOLATED": "YES",
                "CANARY_MAX_FUNDING_USDC": "10",
            },
            clear=True,
        ):
            assessment = assess_real_adapter_gate(
                authorization_packet=packet,
                kill_switch_report=kill_switch,
                env={},
            )
        self.assertFalse(assessment.unlock_allowed)
        self.assertIn("lee_authorization_env_missing", assessment.blockers)
        self.assertIn("canary_funding_cap_missing", assessment.blockers)

    def test_all_gates_pass_with_explicit_env(self) -> None:
        assessment = assess_real_adapter_gate(
            authorization_packet=_authorization_packet(ready=True),
            kill_switch_report=_kill_switch(active=False),
            env={
                "LEE_CANARY_AUTHORIZED": "I_ACCEPT_CANARY_RISK",
                "CANARY_WALLET_ISOLATED": "YES",
                "CANARY_MAX_FUNDING_USDC": "10",
            },
        )
        self.assertTrue(assessment.unlock_allowed)
        self.assertEqual(assessment.blockers, tuple())
        self.assertIn("real_adapter_code_still_requires_manual_review", assessment.warnings)

    def test_authorization_packet_blocker_blocks_unlock(self) -> None:
        assessment = assess_real_adapter_gate(
            authorization_packet=_authorization_packet(ready=False),
            kill_switch_report=_kill_switch(active=False),
            env=_valid_env(),
        )
        self.assertFalse(assessment.unlock_allowed)
        self.assertIn("canary_authorization_packet_not_ready", assessment.blockers)

    def test_kill_switch_blocks_unlock(self) -> None:
        assessment = assess_real_adapter_gate(
            authorization_packet=_authorization_packet(ready=True),
            kill_switch_report=_kill_switch(active=True),
            env=_valid_env(),
        )
        self.assertFalse(assessment.unlock_allowed)
        self.assertIn("kill_switch_active", assessment.blockers)

    def test_funding_cap_must_be_valid_and_bounded(self) -> None:
        config = RealAdapterGateConfig(max_funding_usdc=10.0)
        for value, blocker in (
            ("abc", "canary_funding_cap_invalid"),
            ("-1", "canary_funding_cap_invalid"),
            ("10.01", "canary_funding_cap_too_high"),
        ):
            env = _valid_env()
            env["CANARY_MAX_FUNDING_USDC"] = value
            assessment = assess_real_adapter_gate(
                authorization_packet=_authorization_packet(ready=True),
                kill_switch_report=_kill_switch(active=False),
                env=env,
                config=config,
            )
            self.assertFalse(assessment.unlock_allowed)
            self.assertIn(blocker, assessment.blockers)

    def test_write_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "real_adapter_gate_report.md"
            with patch(
                "btc5m_bot.real_adapter_gate.build_canary_authorization_packet",
                return_value=_authorization_packet(ready=True),
            ), patch(
                "btc5m_bot.real_adapter_gate.build_canary_kill_switch_report",
                return_value=_kill_switch(active=False),
            ):
                report = write_real_adapter_gate_report(output_path=output, env=_valid_env())
            rendered = output.read_text(encoding="utf-8")
        self.assertTrue(report["assessment"]["unlock_allowed"])
        self.assertIn("Real Adapter Gate Report", rendered)

    def test_render_report_lists_blockers(self) -> None:
        rendered = render_real_adapter_gate_markdown(
            {
                "assessment": {
                    "unlock_allowed": False,
                    "blockers": ("lee_authorization_env_missing",),
                    "warnings": tuple(),
                    "metrics": {},
                },
                "authorization_packet_status": "NOT_READY",
                "authorization_blockers": ("insufficient_forward_trades",),
                "kill_switch_active": False,
            }
        )
        self.assertIn("lee_authorization_env_missing", rendered)


def _valid_env() -> dict[str, str]:
    return {
        "LEE_CANARY_AUTHORIZED": "I_ACCEPT_CANARY_RISK",
        "CANARY_WALLET_ISOLATED": "YES",
        "CANARY_MAX_FUNDING_USDC": "10",
    }


def _authorization_packet(ready: bool) -> dict:
    return {
        "status": "READY_FOR_LEE_AUTHORIZATION" if ready else "NOT_READY",
        "blockers": tuple() if ready else ("insufficient_forward_trades",),
    }


def _kill_switch(active: bool) -> dict:
    return {
        "assessment": {
            "active": active,
            "reasons": ("manual_kill_switch_file_present",) if active else tuple(),
        },
    }


if __name__ == "__main__":
    unittest.main()
