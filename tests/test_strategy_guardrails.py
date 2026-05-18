import unittest

from btc5m_bot.strategy_guardrails import (
    assess_strategy_guardrails,
    summarize_forward_ledger,
)


class StrategyGuardrailTests(unittest.TestCase):
    def test_collecting_stage_blocks_parameter_changes(self) -> None:
        summary = summarize_forward_ledger(
            [
                {
                    "reason": "traded",
                    "pnl_usd": "1.0",
                    "edge": "0.05",
                },
                {
                    "reason": "low_confidence",
                    "pnl_usd": "",
                    "edge": "",
                },
            ]
        )
        assessment = assess_strategy_guardrails(summary)
        self.assertEqual(assessment["stage"], "collecting")
        self.assertFalse(assessment["review_ready"])
        self.assertIn("min_confidence", assessment["frozen_parameters"])

    def test_change_review_ready_after_thresholds(self) -> None:
        rows = [
            {
                "reason": "traded",
                "pnl_usd": "1.0",
                "edge": "0.05",
            }
            for _ in range(30)
        ] + [
            {
                "reason": "low_confidence",
                "pnl_usd": "",
                "edge": "",
            }
            for _ in range(70)
        ]
        assessment = assess_strategy_guardrails(summarize_forward_ledger(rows))
        self.assertEqual(assessment["stage"], "change_review_ready")
        self.assertEqual(assessment["frozen_parameters"], [])
