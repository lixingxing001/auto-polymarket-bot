import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from btc5m_bot.canary_monitor import (
    CanaryMonitorResult,
    choose_next_action,
    render_canary_monitor_markdown,
    run_canary_monitor,
)


class CanaryMonitorTests(unittest.TestCase):
    def test_choose_next_action_prioritizes_forward_collection(self) -> None:
        action = choose_next_action(
            ("guardrail_stage_collecting", "insufficient_forward_trades"),
            tuple(),
        )
        self.assertEqual(action, "collect_more_forward_evidence")

    def test_choose_next_action_when_ready(self) -> None:
        self.assertEqual(choose_next_action(tuple(), tuple()), "prepare_canary_authorization_packet")

    def test_render_canary_monitor_markdown(self) -> None:
        result = CanaryMonitorResult(
            checked_at="2026-05-19T12:00:00+00:00",
            ready=False,
            blockers=("insufficient_forward_trades",),
            warnings=("candidate_evidence_still_collecting",),
            next_action="collect_more_forward_evidence",
            readiness_report_path="canary_readiness_report.md",
        )
        markdown = render_canary_monitor_markdown(result, _readiness())
        self.assertIn("Canary Monitor Report", markdown)
        self.assertIn("collect_more_forward_evidence", markdown)

    def test_run_canary_monitor_writes_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            readiness_path = base / "readiness.md"
            monitor_path = base / "monitor.md"
            with patch("btc5m_bot.canary_monitor.build_canary_readiness_report", return_value=_readiness()):
                result = run_canary_monitor(
                    readiness_output_path=readiness_path,
                    monitor_output_path=monitor_path,
                )
            readiness_text = readiness_path.read_text(encoding="utf-8")
            monitor_text = monitor_path.read_text(encoding="utf-8")
        self.assertFalse(result["monitor"]["ready"])
        self.assertIn("Canary Readiness Report", readiness_text)
        self.assertIn("Canary Monitor Report", monitor_text)


def _readiness() -> dict:
    return {
        "readiness": {
            "ready": False,
            "blockers": ("insufficient_forward_trades",),
            "warnings": ("candidate_evidence_still_collecting",),
            "metrics": {
                "forward_evaluations": 28,
                "forward_trades": 2,
                "forward_win_rate": 1.0,
                "forward_total_pnl_usd": 12.4,
                "guardrail_stage": "collecting",
                "next_change_review_gap": {"evaluations_needed": 72, "trades_needed": 28},
                "candidate_count": 3,
                "review_ready_candidates": [],
                "collecting_candidates": ["edge_008"],
                "accepted_attempts": 1,
                "rejected_attempts": 2,
            },
        },
        "candidate_statuses": {},
    }


if __name__ == "__main__":
    unittest.main()
