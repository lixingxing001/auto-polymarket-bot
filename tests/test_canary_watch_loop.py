import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from btc5m_bot.canary_watch_loop import (
    render_canary_watch_markdown,
    run_canary_watch_once,
)


class CanaryWatchLoopTests(unittest.TestCase):
    def test_run_once_writes_watch_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "watch.md"
            with patch(
                "btc5m_bot.canary_watch_loop.run_canary_monitor",
                return_value=_monitor_payload(),
            ), patch(
                "btc5m_bot.canary_watch_loop.write_canary_preflight_report",
                return_value={"assessment": _preflight_payload()},
            ), patch(
                "btc5m_bot.canary_watch_loop.write_candidate_change_review_report",
                return_value={"decision": _change_review_payload()},
            ):
                report = run_canary_watch_once(watch_output_path=output)
            rendered = output.read_text(encoding="utf-8")
        self.assertFalse(report["monitor"]["ready"])
        self.assertIn("Canary Watch Report", rendered)
        self.assertIn("does not submit orders", rendered)

    def test_render_watch_report_lists_selected_candidate(self) -> None:
        rendered = render_canary_watch_markdown(
            {
                "checked_at": "2026-05-19T00:00:00+00:00",
                "monitor": _monitor_payload()["monitor"],
                "readiness": _monitor_payload()["readiness"]["readiness"],
                "preflight": _preflight_payload(),
                "change_review": _change_review_payload(),
            }
        )
        self.assertIn("avoid_mid_abs_return_5m", rendered)


def _monitor_payload() -> dict:
    return {
        "monitor": {
            "ready": False,
            "blockers": ("insufficient_forward_trades",),
            "warnings": tuple(),
            "next_action": "collect_more_forward_evidence",
        },
        "readiness": {
            "readiness": {
                "blockers": ("insufficient_forward_trades",),
                "warnings": tuple(),
                "metrics": {
                    "forward_evaluations": 135,
                    "forward_trades": 18,
                    "forward_win_rate": 0.44,
                    "forward_total_pnl_usd": 53.6,
                    "next_change_review_gap": {"evaluations_needed": 0, "trades_needed": 12},
                },
            },
        },
    }


def _preflight_payload() -> dict:
    return {
        "status": "BLOCKED",
        "real_adapter_review_allowed": False,
        "blockers": ("insufficient_forward_trades",),
    }


def _change_review_payload() -> dict:
    return {
        "status": "DEFER_CHANGE",
        "selected_candidate_id": "avoid_mid_abs_return_5m",
        "change_allowed": False,
        "blockers": ("guardrail_stage_review_only",),
        "warnings": ("selected_candidate_win_rate_below_canary_floor",),
    }


if __name__ == "__main__":
    unittest.main()
