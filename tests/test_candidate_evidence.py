import unittest

from btc5m_bot.candidate_evidence import (
    assess_candidate_evidence,
    summarize_candidate_evidence,
)


class CandidateEvidenceTests(unittest.TestCase):
    def test_summary_counts_divergence(self) -> None:
        summary = summarize_candidate_evidence(
            [
                {
                    "active_decision": "HOLD",
                    "active_reason": "low_confidence",
                    "active_pnl_usd": "",
                    "candidate_decision": "HOLD",
                    "candidate_reason": "low_confidence",
                    "candidate_pnl_usd": "",
                },
                {
                    "active_decision": "UP",
                    "active_reason": "traded",
                    "active_pnl_usd": "1.0",
                    "candidate_decision": "HOLD",
                    "candidate_reason": "candidate_filter",
                    "candidate_pnl_usd": "",
                },
            ]
        )
        self.assertEqual(summary.eligible_windows, 2)
        self.assertEqual(summary.divergent_windows, 1)
        self.assertEqual(summary.candidate_filter_windows, 1)
        self.assertEqual(summary.delta_pnl_usd, -1.0)

    def test_assessment_requires_divergent_windows(self) -> None:
        summary = summarize_candidate_evidence(
            [
                {
                    "active_decision": "HOLD",
                    "active_reason": "low_confidence",
                    "active_pnl_usd": "",
                    "candidate_decision": "HOLD",
                    "candidate_reason": "low_confidence",
                    "candidate_pnl_usd": "",
                }
                for _ in range(30)
            ]
        )
        assessment = assess_candidate_evidence(summary)
        self.assertFalse(assessment["review_ready"])
        self.assertEqual(assessment["next_review_gap"]["eligible_windows_needed"], 0)
        self.assertEqual(assessment["next_review_gap"]["divergent_windows_needed"], 10)
