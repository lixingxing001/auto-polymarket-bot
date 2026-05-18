import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from btc5m_bot.canary_kill_switch import (
    CanaryKillSwitchConfig,
    assess_canary_kill_switch,
    build_canary_kill_switch_report,
    render_canary_kill_switch_markdown,
    write_canary_kill_switch_report,
)
from btc5m_bot.execution_safety import ExecutionLedgerEntry


class CanaryKillSwitchTests(unittest.TestCase):
    def test_empty_ledger_warns_but_does_not_activate(self) -> None:
        assessment = assess_canary_kill_switch(tuple())
        self.assertFalse(assessment.active)
        self.assertIn("no_live_execution_ledger_entries", assessment.warnings)

    def test_manual_kill_file_activates(self) -> None:
        assessment = assess_canary_kill_switch(tuple(), kill_switch_file_exists=True)
        self.assertTrue(assessment.active)
        self.assertIn("manual_kill_switch_file_present", assessment.reasons)

    def test_loss_and_trade_limits_activate(self) -> None:
        entries = tuple(
            ExecutionLedgerEntry(
                created_at=_now(),
                slug=f"s{index}",
                outcome="UP",
                status="settled",
                stake_usd=1.0,
                price=0.5,
                pnl_usd=-1.5,
                client_order_id=f"o{index}",
            )
            for index in range(3)
        )
        assessment = assess_canary_kill_switch(entries, now=_now())
        self.assertTrue(assessment.active)
        self.assertIn("daily_loss_limit_reached", assessment.reasons)
        self.assertIn("consecutive_loss_limit_reached", assessment.reasons)
        self.assertIn("daily_trade_limit_reached", assessment.reasons)

    def test_open_exposure_and_stake_caps_activate(self) -> None:
        entries = (
            ExecutionLedgerEntry(
                created_at=_now(),
                slug="s",
                outcome="UP",
                status="open",
                stake_usd=1.0,
                price=0.5,
                client_order_id="o",
            ),
        )
        assessment = assess_canary_kill_switch(entries, proposed_stake_usd=2.0, now=_now())
        self.assertIn("open_exposure_limit_reached", assessment.reasons)
        self.assertIn("proposed_stake_above_canary_cap", assessment.reasons)

    def test_write_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            ledger = base / "ledger.csv"
            output = base / "report.md"
            ledger.write_text(
                "created_at,slug,outcome,status,stake_usd,price,pnl_usd,client_order_id\n",
                encoding="utf-8",
            )
            report = write_canary_kill_switch_report(output_path=output, ledger_path=ledger)
            rendered = output.read_text(encoding="utf-8")
        self.assertFalse(report["assessment"]["active"])
        self.assertIn("Canary Kill Switch Report", rendered)

    def test_render_report_lists_reasons(self) -> None:
        report = build_canary_kill_switch_report(ledger_path=Path("missing.csv"))
        rendered = render_canary_kill_switch_markdown(report)
        self.assertIn("Canary Kill Switch Report", rendered)


def _now() -> datetime:
    return datetime(2026, 5, 19, 12, 0, tzinfo=timezone.utc)


if __name__ == "__main__":
    unittest.main()
