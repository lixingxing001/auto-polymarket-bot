import csv
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from btc5m_bot.mock_execution_smoke import (
    build_mock_smoke_dry_run,
    render_mock_smoke_report,
    run_mock_execution_smoke,
    write_mock_execution_smoke_report,
)


class MockExecutionSmokeTests(unittest.TestCase):
    def test_build_mock_smoke_dry_run_is_allowed_fixture(self) -> None:
        dry_run = build_mock_smoke_dry_run(now=_now())
        preflight = dry_run["execution_preflight"]
        self.assertTrue(preflight["actionable_signal"])
        self.assertTrue(preflight["order_send_allowed"])
        self.assertEqual(preflight["proposed_order"]["stake_usd"], 1.0)
        self.assertEqual(dry_run["reason"], "mock_smoke_fixture")

    def test_run_mock_execution_smoke_writes_attempt_and_intent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            attempt_log = base / "attempts.csv"
            intent_log = base / "intent_events.csv"
            result = run_mock_execution_smoke(
                attempt_log_path=attempt_log,
                intent_event_log_path=intent_log,
                now=_now(),
            )
            with attempt_log.open(newline="", encoding="utf-8") as handle:
                attempts = list(csv.DictReader(handle))
            with intent_log.open(newline="", encoding="utf-8") as handle:
                events = list(csv.DictReader(handle))
        self.assertTrue(result["attempt"]["accepted"])
        self.assertEqual(result["intent"]["status"], "mock_submitted")
        self.assertEqual(attempts[0]["status"], "mock_submitted")
        self.assertEqual(events[-1]["status"], "mock_submitted")

    def test_write_mock_execution_smoke_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            output = base / "report.md"
            result = write_mock_execution_smoke_report(
                output_path=output,
                attempt_log_path=base / "attempts.csv",
                intent_event_log_path=base / "intent_events.csv",
                now=_now(),
            )
            rendered = output.read_text(encoding="utf-8")
        self.assertTrue(result["attempt"]["accepted"])
        self.assertIn("Mock Execution Smoke Report", rendered)
        self.assertIn("mock_submitted", rendered)

    def test_render_mock_smoke_report_states_boundary(self) -> None:
        result = run_mock_execution_smoke(
            attempt_log_path=Path("NUL"),
            intent_event_log_path=Path("NUL"),
            now=_now(),
        )
        rendered = render_mock_smoke_report(result)
        self.assertIn("mock adapter only", rendered)


def _now() -> datetime:
    return datetime(2026, 5, 19, 12, 0, tzinfo=timezone.utc)


if __name__ == "__main__":
    unittest.main()
