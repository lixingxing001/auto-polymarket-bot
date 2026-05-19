import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from btc5m_bot.canary_readiness import (
    assess_canary_readiness,
    build_canary_readiness_report,
    render_canary_readiness_markdown,
    summarize_candidate_statuses,
    write_canary_readiness_report,
)
from btc5m_bot.candidate_strategies import CandidateStrategy, write_candidate_registry


class CanaryReadinessTests(unittest.TestCase):
    def test_assessment_blocks_when_forward_evidence_is_thin(self) -> None:
        result = assess_canary_readiness(
            forward_rows=[{"reason": "traded", "pnl_usd": "1.0", "edge": "0.05"}],
            candidate_registry_path=Path("missing.csv"),
            candidate_comparison_dir=Path("missing"),
            intent_event_path=Path("missing_intents.csv"),
            attempt_log_path=Path("missing_attempts.csv"),
        )
        blockers = result["readiness"]["blockers"]
        self.assertFalse(result["readiness"]["ready"])
        self.assertIn("insufficient_forward_evaluations", blockers)
        self.assertIn("insufficient_forward_trades", blockers)
        self.assertIn("no_candidate_review_ready", blockers)
        self.assertIn("no_candidate_passed_change_quality", blockers)
        self.assertIn("no_mock_submit_seen", blockers)

    def test_candidate_statuses_detect_review_ready_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            registry = base / "candidates.csv"
            comparisons = base / "comparisons"
            comparisons.mkdir()
            write_candidate_registry(registry, (_candidate("edge_008"),))
            (comparisons / "edge_008.csv").write_text(
                _failed_candidate_comparison_csv(),
                encoding="utf-8",
            )
            statuses = summarize_candidate_statuses(registry, comparisons)
        self.assertTrue(statuses["edge_008"]["assessment"]["review_ready"])
        self.assertFalse(statuses["edge_008"]["change_review"]["change_quality_passed"])
        self.assertEqual(statuses["edge_008"]["summary"]["divergent_windows"], 10)

    def test_failed_review_ready_candidate_does_not_unlock_candidate_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            registry = base / "candidates.csv"
            comparisons = base / "comparisons"
            attempts = base / "attempts.csv"
            intents = base / "intents.csv"
            comparisons.mkdir()
            write_candidate_registry(registry, (_candidate("edge_008"),))
            (comparisons / "edge_008.csv").write_text(
                _failed_candidate_comparison_csv(),
                encoding="utf-8",
            )
            attempts.write_text(_accepted_attempt_csv(), encoding="utf-8")
            intents.write_text(_intent_csv(), encoding="utf-8")
            result = assess_canary_readiness(
                forward_rows=_forward_rows(),
                candidate_registry_path=registry,
                candidate_comparison_dir=comparisons,
                intent_event_path=intents,
                attempt_log_path=attempts,
            )
        self.assertFalse(result["readiness"]["ready"])
        self.assertIn(
            "no_candidate_passed_change_quality",
            result["readiness"]["blockers"],
        )

    def test_rejected_review_ready_candidate_is_not_active_for_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            registry = base / "candidates.csv"
            comparisons = base / "comparisons"
            attempts = base / "attempts.csv"
            intents = base / "intents.csv"
            comparisons.mkdir()
            write_candidate_registry(
                registry,
                (_candidate("old", status="rejected"),),
            )
            (comparisons / "old.csv").write_text(
                _quality_passed_candidate_comparison_csv(),
                encoding="utf-8",
            )
            attempts.write_text(_accepted_attempt_csv(), encoding="utf-8")
            intents.write_text(_intent_csv(), encoding="utf-8")
            result = assess_canary_readiness(
                forward_rows=_forward_rows(),
                candidate_registry_path=registry,
                candidate_comparison_dir=comparisons,
                intent_event_path=intents,
                attempt_log_path=attempts,
            )
        self.assertFalse(result["readiness"]["ready"])
        self.assertEqual(result["readiness"]["metrics"]["active_candidate_count"], 0)
        self.assertIn("no_candidate_review_ready", result["readiness"]["blockers"])

    def test_ready_when_all_gates_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            forward = base / "forward.csv"
            registry = base / "candidates.csv"
            comparisons = base / "comparisons"
            attempts = base / "attempts.csv"
            intents = base / "intents.csv"
            output = base / "report.md"
            comparisons.mkdir()
            forward.write_text(_forward_csv(), encoding="utf-8")
            write_candidate_registry(registry, (_candidate("edge_008"),))
            (comparisons / "edge_008.csv").write_text(
                _quality_passed_candidate_comparison_csv(),
                encoding="utf-8",
            )
            attempts.write_text(_accepted_attempt_csv(), encoding="utf-8")
            intents.write_text(_intent_csv(), encoding="utf-8")
            report = write_canary_readiness_report(
                output_path=output,
                forward_ledger_path=forward,
                registry_path=registry,
                comparison_dir=comparisons,
                intent_event_path=intents,
                attempt_log_path=attempts,
            )
            rendered = output.read_text(encoding="utf-8")
        self.assertTrue(report["readiness"]["ready"])
        self.assertEqual(report["readiness"]["blockers"], tuple())
        self.assertIn("ready: True", rendered)

    def test_render_markdown_lists_blockers(self) -> None:
        report = build_canary_readiness_report(
            forward_ledger_path=Path("missing_forward.csv"),
            registry_path=Path("missing_registry.csv"),
            comparison_dir=Path("missing_dir"),
            intent_event_path=Path("missing_intents.csv"),
            attempt_log_path=Path("missing_attempts.csv"),
        )
        markdown = render_canary_readiness_markdown(report)
        self.assertIn("Canary Readiness Report", markdown)
        self.assertIn("no_candidate_review_ready", markdown)


def _candidate(candidate_id: str, status: str = "registered") -> CandidateStrategy:
    now = datetime(2026, 5, 19, 12, 0, tzinfo=timezone.utc)
    return CandidateStrategy(
        candidate_id=candidate_id,
        description="test",
        rationale="test",
        registered_at=now,
        eligible_after_market_end_time=now,
        min_confidence=0.65,
        min_edge=0.03,
        stake_usd=10.0,
        max_fill_delay_seconds=30,
        status=status,
    )


def _failed_candidate_comparison_csv() -> str:
    rows = [
        "slug,market_end_time,label,forecast_prob_up,active_decision,active_reason,active_pnl_usd,candidate_decision,candidate_reason,candidate_pnl_usd,delta_pnl_usd"
    ]
    for index in range(30):
        divergent = index < 10
        rows.append(
            f"s{index},2026-05-19T12:00:00+00:00,UP,0.7,UP,traded,1.0,{('HOLD' if divergent else 'UP')},{('candidate_filter' if divergent else 'traded')},{('' if divergent else '1.0')},{('-1.0' if divergent else '0.0')}"
        )
    return "\n".join(rows) + "\n"


def _quality_passed_candidate_comparison_csv() -> str:
    rows = [
        "slug,market_end_time,label,forecast_prob_up,active_decision,active_reason,active_pnl_usd,candidate_decision,candidate_reason,candidate_pnl_usd,delta_pnl_usd"
    ]
    for index in range(30):
        divergent = index < 10
        if divergent:
            rows.append(
                f"s{index},2026-05-19T12:00:00+00:00,UP,0.7,UP,traded,-1.0,HOLD,candidate_filter,,1.0"
            )
        else:
            rows.append(
                f"s{index},2026-05-19T12:00:00+00:00,UP,0.7,UP,traded,0.0,UP,traded,1.0,1.0"
            )
    return "\n".join(rows) + "\n"


def _forward_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index in range(30):
        rows.append(
            {
                "reason": "traded",
                "pnl_usd": "1.0" if index < 20 else "-0.5",
                "edge": "0.06",
            }
        )
    for _ in range(70):
        rows.append({"reason": "low_confidence", "pnl_usd": "", "edge": ""})
    return rows


def _forward_csv() -> str:
    rows = ["slug,label,forecast_prob_up,decision,reason,entry_price,edge,pnl_usd,fill_delay_seconds"]
    for index in range(30):
        pnl = "1.0" if index < 20 else "-0.5"
        rows.append(f"t{index},UP,0.7,UP,traded,0.5,0.06,{pnl},0")
    for index in range(70):
        rows.append(f"h{index},UP,0.51,HOLD,low_confidence,,,,")
    return "\n".join(rows) + "\n"


def _accepted_attempt_csv() -> str:
    return (
        "created_at,adapter,accepted,status,reason,slug,outcome,price,stake_usd,client_order_id,exchange_order_id,safety_reasons_json,safety_warnings_json\n"
        "t,mock,True,mock_submitted,mock_order_accepted,s,UP,0.5,10,c,mock-c,[],[]\n"
    )


def _intent_csv() -> str:
    return "created_at,intent_id,event_type,status,reason,slug,outcome,adapter,client_order_id,exchange_order_id,details_json\n"


if __name__ == "__main__":
    unittest.main()
