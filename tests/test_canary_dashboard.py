import tempfile
import unittest
from pathlib import Path

from btc5m_bot.canary_dashboard import (
    consecutive_wins_needed,
    render_canary_dashboard_html,
    write_canary_dashboard,
)


class CanaryDashboardTests(unittest.TestCase):
    def test_consecutive_wins_needed_for_floor(self) -> None:
        self.assertEqual(consecutive_wins_needed(wins=14, trades=32, target=0.55), 8)
        self.assertEqual(consecutive_wins_needed(wins=20, trades=32, target=0.55), 0)
        self.assertEqual(consecutive_wins_needed(wins=0, trades=0, target=0.55), 1)

    def test_render_dashboard_shows_core_status_and_escapes_candidate_id(self) -> None:
        html = render_canary_dashboard_html(_dashboard_data())

        self.assertIn("CANARY BLOCKED", html)
        self.assertIn("真实下单禁用", html)
        self.assertIn("还需连续胜 8 笔", html)
        self.assertIn("43.8%", html)
        self.assertIn("confidence_070&lt;probe&gt;", html)
        self.assertNotIn("confidence_070<probe>", html)

    def test_write_dashboard_uses_real_report_builders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            output = base / "dashboard.html"
            data = write_canary_dashboard(
                output_path=output,
                snapshot_path=base / "missing_snapshots.csv",
                window_summary_path=base / "missing_windows.csv",
                settled_windows_path=base / "missing_settled.csv",
                forward_ledger_path=base / "missing_forward.csv",
            )
            rendered = output.read_text(encoding="utf-8")

        self.assertFalse(data["readiness"]["ready"])
        self.assertIn("BTC Polymarket Canary Dashboard", rendered)
        self.assertIn("真实下单禁用", rendered)


def _dashboard_data() -> dict:
    return {
        "generated_at": "2026-05-19T10:06:02+00:00",
        "readiness": {"ready": False},
        "readiness_metrics": {
            "forward_evaluations": 222,
            "forward_trades": 32,
            "forward_win_rate": 0.4375,
            "forward_total_pnl_usd": 43.46,
            "review_ready_candidates": ["confidence_070<probe>"],
            "quality_passed_candidates": [],
            "accepted_attempts": 1,
        },
        "readiness_blockers": [
            "forward_win_rate_below_canary_floor",
            "no_candidate_passed_change_quality",
        ],
        "forward_summary": {"wins": 14, "losses": 18},
        "forward_wins_needed_for_floor": 8,
        "policy": {
            "canary_win_rate_floor": 0.55,
            "min_candidate_trades": 10,
            "min_trade_retention": 0.50,
            "min_candidate_eligible_windows": 30,
            "min_candidate_divergent_windows": 10,
        },
        "next_candidate": {
            "candidate_id": "confidence_070<probe>",
            "candidate_trades_needed": 8,
            "retention_gap": 0.25,
            "delta_pnl_usd": 11.76,
        },
        "snapshot_status": {"latest_captured_at": "2026-05-19T10:05:55+00:00"},
        "files": {
            "snapshots": {"rows": 55466, "latest": {"slug": "s1"}},
            "window_summary": {"rows": 226, "latest": {"slug": "s2"}},
            "settled_windows": {"rows": 222, "latest": {"slug": "s3"}},
            "forward_evals": {"rows": 222, "latest": {"slug": "s4"}},
        },
        "active_candidates": [
            {
                "candidate_id": "confidence_070<probe>",
                "blocker_kind": "review_ready_quality_failed",
                "review_ready": True,
                "change_quality_passed": False,
                "eligible_windows": 44,
                "divergent_windows": 10,
                "candidate_trades": 2,
                "trade_retention": 0.25,
                "delta_pnl_usd": 11.76,
                "candidate_win_rate": 1.0,
                "estimated_minutes_to_review": 0,
                "review_blockers": [
                    "insufficient_candidate_trades",
                    "candidate_trade_retention_too_low",
                ],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
