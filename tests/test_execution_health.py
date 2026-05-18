import tempfile
import unittest
from pathlib import Path

from btc5m_bot.execution_health import (
    build_execution_health_report,
    diagnose_execution_health,
    render_execution_health_markdown,
    summarize_execution_health,
    write_execution_health_report,
)


class ExecutionHealthTests(unittest.TestCase):
    def test_summarize_execution_health_counts_blockers(self) -> None:
        summary = summarize_execution_health(_intent_rows(), _attempt_rows())
        self.assertEqual(summary.created_intents, 1)
        self.assertEqual(summary.terminal_intents, 1)
        self.assertEqual(summary.attempts, 1)
        self.assertEqual(summary.rejected_attempts, 1)
        self.assertEqual(summary.paper_reason_counts["too_late"], 1)
        self.assertEqual(summary.safety_reason_counts["insufficient_forward_trades"], 2)
        self.assertEqual(summary.safety_warning_counts["no_proposed_order"], 2)

    def test_diagnosis_identifies_no_actionable_signal(self) -> None:
        summary = summarize_execution_health(_intent_rows(), _attempt_rows())
        diagnosis = diagnose_execution_health(summary, {"stage": "collecting"})
        self.assertIn("paper_signal_not_actionable", diagnosis)
        self.assertIn("no_attempts_accepted", diagnosis)
        self.assertIn("guardrail_stage_collecting", diagnosis)

    def test_render_report_contains_forward_gate(self) -> None:
        report = {
            "execution_health": summarize_execution_health(_intent_rows(), _attempt_rows()).__dict__,
            "forward_ledger": {
                "evaluations": 28,
                "traded_rows": 2,
                "wins": 2,
                "losses": 0,
                "win_rate": 1.0,
                "total_pnl_usd": 12.4,
            },
            "guardrails": {
                "stage": "collecting",
                "next_review_gap": {"evaluations_needed": 2, "trades_needed": 8},
                "next_change_review_gap": {"evaluations_needed": 72, "trades_needed": 28},
            },
            "diagnosis": ["paper_signal_not_actionable"],
        }
        markdown = render_execution_health_markdown(report)
        self.assertIn("# Execution Health Report", markdown)
        self.assertIn("paper_signal_not_actionable", markdown)
        self.assertIn("insufficient_forward_trades", markdown)

    def test_write_execution_health_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            intent_path = base / "intent.csv"
            attempt_path = base / "attempt.csv"
            forward_path = base / "forward.csv"
            output_path = base / "report.md"
            intent_path.write_text(_intent_csv(), encoding="utf-8")
            attempt_path.write_text(_attempt_csv(), encoding="utf-8")
            forward_path.write_text(_forward_csv(), encoding="utf-8")
            report = write_execution_health_report(
                output_path=output_path,
                intent_event_path=intent_path,
                attempt_log_path=attempt_path,
                forward_ledger_path=forward_path,
            )
            rendered = output_path.read_text(encoding="utf-8")
        self.assertEqual(report["execution_health"]["created_intents"], 1)
        self.assertIn("Execution Health Report", rendered)


def _intent_rows() -> list[dict[str, str]]:
    return [
        {
            "status": "created",
            "details_json": '{"paper_reason":"too_late","actionable_signal":false,"order_send_allowed":false}',
        },
        {
            "status": "no_actionable_order",
            "details_json": '{"safety_reasons":["insufficient_forward_trades"],"safety_warnings":["no_proposed_order"],"order_send_allowed":false}',
        },
    ]


def _attempt_rows() -> list[dict[str, str]]:
    return [
        {
            "accepted": "False",
            "reason": "no_actionable_order",
            "safety_reasons_json": '["insufficient_forward_trades"]',
            "safety_warnings_json": '["no_proposed_order"]',
        }
    ]


def _intent_csv() -> str:
    return (
        "created_at,intent_id,event_type,status,reason,slug,outcome,adapter,client_order_id,exchange_order_id,details_json\n"
        "t,i,intent_created,created,intent_created,s,,,,,\"{\"\"paper_reason\"\":\"\"too_late\"\",\"\"actionable_signal\"\":false,\"\"order_send_allowed\"\":false}\"\n"
        "t,i,intent_transition,no_actionable_order,no_actionable_order,s,,disabled,,,\"{\"\"safety_reasons\"\":[\"\"insufficient_forward_trades\"\"],\"\"safety_warnings\"\":[\"\"no_proposed_order\"\"],\"\"order_send_allowed\"\":false}\"\n"
    )


def _attempt_csv() -> str:
    return (
        "created_at,adapter,accepted,status,reason,slug,outcome,price,stake_usd,client_order_id,exchange_order_id,safety_reasons_json,safety_warnings_json\n"
        "t,disabled,False,rejected,no_actionable_order,,,0,0,,,\"[\"\"insufficient_forward_trades\"\"]\",\"[\"\"no_proposed_order\"\"]\"\n"
    )


def _forward_csv() -> str:
    return (
        "slug,label,forecast_prob_up,decision,reason,entry_price,edge,pnl_usd,fill_delay_seconds\n"
        "s,UP,0.7,UP,traded,0.5,0.1,1.0,0\n"
    )


if __name__ == "__main__":
    unittest.main()
