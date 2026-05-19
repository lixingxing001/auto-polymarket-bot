import unittest

from btc5m_bot.candidate_generation import (
    build_candidate_proposals,
    render_candidate_generation_markdown,
)


class CandidateGenerationTests(unittest.TestCase):
    def test_proposes_momentum_filter_from_bad_recent_slice(self) -> None:
        proposals = build_candidate_proposals(
            recent_loss_report={
                "worst_slices": [
                    {
                        "dimension": "trade_vs_5m_momentum",
                        "bucket": "against_momentum",
                        "trades": 6,
                        "win_rate": 0.166,
                        "total_pnl_usd": -48.10,
                    }
                ],
            },
            active_filter_kinds=set(),
            has_active_confidence_070=True,
        )
        self.assertEqual(proposals[0].candidate_id, "avoid_trade_against_5m_momentum")
        self.assertEqual(proposals[0].filter_kind, "avoid_trade_against_5m_momentum")

    def test_marks_existing_active_filter_for_evidence_collection(self) -> None:
        proposals = build_candidate_proposals(
            recent_loss_report={
                "worst_slices": [
                    {
                        "dimension": "trade_vs_5m_momentum",
                        "bucket": "against_momentum",
                        "trades": 6,
                        "win_rate": 0.166,
                        "total_pnl_usd": -48.10,
                    }
                ],
            },
            active_filter_kinds={"avoid_trade_against_5m_momentum"},
            has_active_confidence_070=True,
        )
        self.assertEqual(proposals[0].candidate_id, "avoid_trade_against_5m_momentum")
        self.assertEqual(proposals[0].action, "collect_prospective_evidence")

    def test_render_report_lists_boundary(self) -> None:
        rendered = render_candidate_generation_markdown(
            {
                "target": {
                    "forward_win_rate_goal": 0.60,
                    "live_order_goal": "canary",
                },
                "current_forward": {
                    "evaluations": 100,
                    "traded_rows": 30,
                    "win_rate": 0.50,
                    "total_pnl_usd": 1.0,
                },
                "diagnostic_flags": ("recent_hit_rate_too_weak_for_canary",),
                "proposals": [],
            }
        )
        self.assertIn("Candidate Generation Report", rendered)
        self.assertIn("does not promote parameters", rendered)


if __name__ == "__main__":
    unittest.main()
