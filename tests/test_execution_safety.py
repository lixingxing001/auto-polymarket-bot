import unittest
from datetime import datetime, timezone

from btc5m_bot.execution_safety import (
    ExecutionLedgerEntry,
    ExecutionSafetyConfig,
    ProposedOrder,
    assess_execution_safety,
    summarize_execution_ledger,
)
from btc5m_bot.strategy_guardrails import (
    assess_strategy_guardrails,
    summarize_forward_ledger,
)


class ExecutionSafetyTests(unittest.TestCase):
    def test_live_switch_blocks_even_when_evidence_is_ready(self) -> None:
        summary = _ready_forward_summary()
        assessment = assess_execution_safety(
            forward_summary=summary,
            guardrail_assessment=assess_strategy_guardrails(summary),
            ledger_summary=summarize_execution_ledger(tuple(), now=_now()),
            proposed_order=_safe_order(),
        )
        self.assertFalse(assessment.allowed)
        self.assertIn("live_trading_disabled", assessment.reasons)

    def test_collecting_guardrail_blocks_live_trading(self) -> None:
        summary = summarize_forward_ledger(
            [
                {"reason": "traded", "pnl_usd": "1.0", "edge": "0.05"},
            ]
        )
        assessment = assess_execution_safety(
            forward_summary=summary,
            guardrail_assessment=assess_strategy_guardrails(summary),
            ledger_summary=summarize_execution_ledger(tuple(), now=_now()),
            proposed_order=_safe_order(),
            config=ExecutionSafetyConfig(live_trading_enabled=True),
        )
        self.assertFalse(assessment.allowed)
        self.assertIn("strategy_guardrail_stage_collecting", assessment.reasons)
        self.assertIn("insufficient_forward_evaluations", assessment.reasons)

    def test_order_level_guards_block_duplicate_and_oversize(self) -> None:
        summary = _ready_forward_summary()
        ledger_summary = summarize_execution_ledger(
            (
                ExecutionLedgerEntry(
                    created_at=_now(),
                    slug="btc-updown-1",
                    outcome="UP",
                    status="filled",
                    stake_usd=10,
                    price=0.55,
                    client_order_id="existing-1",
                ),
            ),
            now=_now(),
        )
        assessment = assess_execution_safety(
            forward_summary=summary,
            guardrail_assessment=assess_strategy_guardrails(summary),
            ledger_summary=ledger_summary,
            proposed_order=ProposedOrder(
                slug="btc-updown-1",
                outcome="UP",
                price=0.55,
                stake_usd=25.0,
                edge=0.08,
                probability=0.72,
                available_liquidity_usd=80.0,
                seconds_to_close=120,
                client_order_id="existing-1",
            ),
            config=ExecutionSafetyConfig(live_trading_enabled=True),
        )
        self.assertFalse(assessment.allowed)
        self.assertIn("stake_above_max", assessment.reasons)
        self.assertIn("duplicate_open_exposure", assessment.reasons)
        self.assertIn("duplicate_client_order_id", assessment.reasons)

    def test_account_circuit_breakers_block_after_losses(self) -> None:
        summary = _ready_forward_summary()
        ledger_summary = summarize_execution_ledger(
            tuple(
                ExecutionLedgerEntry(
                    created_at=_now(),
                    slug=f"btc-updown-{index}",
                    outcome="DOWN",
                    status="settled",
                    stake_usd=10,
                    price=0.52,
                    pnl_usd=-4.0,
                    client_order_id=f"loss-{index}",
                )
                for index in range(10)
            ),
            now=_now(),
        )
        assessment = assess_execution_safety(
            forward_summary=summary,
            guardrail_assessment=assess_strategy_guardrails(summary),
            ledger_summary=ledger_summary,
            proposed_order=_safe_order(),
            config=ExecutionSafetyConfig(live_trading_enabled=True),
        )
        self.assertFalse(assessment.allowed)
        self.assertIn("daily_loss_limit_reached", assessment.reasons)
        self.assertIn("daily_trade_limit_reached", assessment.reasons)
        self.assertIn("consecutive_loss_limit_reached", assessment.reasons)

    def test_safe_order_allowed_when_all_gates_pass(self) -> None:
        summary = _ready_forward_summary()
        assessment = assess_execution_safety(
            forward_summary=summary,
            guardrail_assessment=assess_strategy_guardrails(summary),
            ledger_summary=summarize_execution_ledger(tuple(), now=_now()),
            proposed_order=_safe_order(),
            config=ExecutionSafetyConfig(live_trading_enabled=True),
        )
        self.assertTrue(assessment.allowed)
        self.assertEqual(assessment.reasons, tuple())


def _ready_forward_summary():
    rows = []
    for index in range(30):
        pnl = "1.0" if index < 20 else "-0.5"
        rows.append({"reason": "traded", "pnl_usd": pnl, "edge": "0.06"})
    rows.extend(
        {"reason": "low_confidence", "pnl_usd": "", "edge": ""}
        for _ in range(70)
    )
    return summarize_forward_ledger(rows)


def _safe_order() -> ProposedOrder:
    return ProposedOrder(
        slug="btc-updown-1",
        outcome="UP",
        price=0.55,
        stake_usd=8.0,
        edge=0.08,
        probability=0.72,
        available_liquidity_usd=100.0,
        seconds_to_close=120,
        client_order_id="order-1",
    )


def _now() -> datetime:
    return datetime(2026, 5, 18, 12, 0, tzinfo=timezone.utc)


if __name__ == "__main__":
    unittest.main()

