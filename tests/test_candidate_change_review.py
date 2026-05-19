import csv
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from btc5m_bot.candidate_change_review import (
    CandidateChangeReviewPolicy,
    decide_candidate_change,
    render_candidate_change_review_markdown,
    review_candidate_change,
    write_candidate_change_review_report,
)
from btc5m_bot.candidate_strategies import CandidateStrategy, write_candidate_registry


class CandidateChangeReviewTests(unittest.TestCase):
    def test_review_candidate_accepts_positive_delta_with_enough_evidence(self) -> None:
        rows = [_avoid_loss_row(active_pnl=-1.0) for _ in range(10)]
        rows.extend(_row(active_pnl=1.0, candidate_pnl=1.0) for _ in range(20))
        review = review_candidate_change(
            candidate_id="candidate",
            filter_kind="none",
            rows=rows,
            policy=CandidateChangeReviewPolicy(min_candidate_trades=10),
        )
        self.assertTrue(review.review_ready)
        self.assertTrue(review.change_quality_passed)
        self.assertEqual(review.blockers, tuple())
        self.assertGreater(review.metrics["delta_pnl_usd"], 0.0)

    def test_review_candidate_blocks_negative_delta(self) -> None:
        rows = [_row(active_pnl=1.0, candidate_pnl=-1.0) for _ in range(30)]
        review = review_candidate_change(
            candidate_id="candidate",
            filter_kind="none",
            rows=rows,
        )
        self.assertFalse(review.change_quality_passed)
        self.assertIn("delta_pnl_not_positive", review.blockers)
        self.assertIn("candidate_pnl_not_positive", review.blockers)

    def test_decision_defers_when_guardrail_is_not_change_ready(self) -> None:
        review = review_candidate_change(
            candidate_id="candidate",
            filter_kind="none",
            rows=[
                *[_avoid_loss_row(active_pnl=-1.0) for _ in range(10)],
                *[_row(active_pnl=1.0, candidate_pnl=1.0) for _ in range(20)],
            ],
        )
        decision = decide_candidate_change(
            guardrails={
                "stage": "review_only",
                "change_review_ready": False,
            },
            reviews=(review,),
        )
        self.assertEqual(decision.status, "DEFER_CHANGE")
        self.assertFalse(decision.change_allowed)
        self.assertIn("guardrail_stage_review_only", decision.blockers)

    def test_decision_selects_best_quality_candidate_when_change_ready(self) -> None:
        weaker = review_candidate_change(
            candidate_id="weaker",
            filter_kind="none",
            rows=[
                *[_avoid_loss_row(active_pnl=-1.0) for _ in range(10)],
                *[_row(active_pnl=1.0, candidate_pnl=1.0) for _ in range(20)],
            ],
        )
        stronger = review_candidate_change(
            candidate_id="stronger",
            filter_kind="none",
            rows=[
                *[_avoid_loss_row(active_pnl=-2.0) for _ in range(10)],
                *[_row(active_pnl=1.0, candidate_pnl=2.0) for _ in range(20)],
            ],
        )
        decision = decide_candidate_change(
            guardrails={
                "stage": "change_review_ready",
                "change_review_ready": True,
            },
            reviews=(weaker, stronger),
        )
        self.assertEqual(decision.status, "CHANGE_APPROVED_FOR_MANUAL_FREEZE")
        self.assertEqual(decision.selected_candidate_id, "stronger")
        self.assertTrue(decision.change_allowed)

    def test_write_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            registry = base / "registry.csv"
            comparison_dir = base / "comparisons"
            ledger = base / "forward.csv"
            output = base / "review.md"
            write_candidate_registry(
                registry,
                (
                    CandidateStrategy(
                        candidate_id="mid",
                        description="Mid filter",
                        rationale="Test",
                        registered_at=datetime(2026, 5, 18, tzinfo=timezone.utc),
                        eligible_after_market_end_time=datetime(
                            2026,
                            5,
                            18,
                            tzinfo=timezone.utc,
                        ),
                        min_confidence=0.65,
                        min_edge=0.03,
                        stake_usd=10.0,
                        max_fill_delay_seconds=30,
                        filter_kind="avoid_mid_abs_return_5m",
                    ),
                ),
            )
            comparison_dir.mkdir()
            _write_rows(
                comparison_dir / "mid.csv",
                [
                    *[_avoid_loss_row(active_pnl=-1.0) for _ in range(10)],
                    *[_row(active_pnl=1.0, candidate_pnl=1.0) for _ in range(20)],
                ],
            )
            _write_forward_ledger(ledger, rows=30, trades=30)
            report = write_candidate_change_review_report(
                output_path=output,
                forward_ledger_path=ledger,
                registry_path=registry,
                comparison_dir=comparison_dir,
            )
            rendered = output.read_text(encoding="utf-8")
        self.assertEqual(report["decision"]["selected_candidate_id"], "mid")
        self.assertIn("Candidate Change Review Report", rendered)

    def test_render_lists_boundary(self) -> None:
        rendered = render_candidate_change_review_markdown(
            {
                "decision": {
                    "status": "DEFER_CHANGE",
                    "selected_candidate_id": "mid",
                    "change_allowed": False,
                    "blockers": ("guardrail_stage_review_only",),
                    "warnings": tuple(),
                },
                "guardrails": {
                    "stage": "review_only",
                    "review_ready": True,
                    "change_review_ready": False,
                    "next_change_review_gap": {"evaluations_needed": 0, "trades_needed": 1},
                },
                "forward_summary": {
                    "evaluations": 100,
                    "traded_rows": 29,
                    "win_rate": 0.5,
                    "total_pnl_usd": 1.0,
                },
                "candidate_reviews": [],
            }
        )
        self.assertIn("does not submit orders", rendered)


def _row(active_pnl: float, candidate_pnl: float) -> dict[str, str]:
    return {
        "active_decision": "UP",
        "active_reason": "traded",
        "active_pnl_usd": str(active_pnl),
        "candidate_decision": "UP",
        "candidate_reason": "traded",
        "candidate_pnl_usd": str(candidate_pnl),
    }


def _avoid_loss_row(active_pnl: float) -> dict[str, str]:
    return {
        "active_decision": "UP",
        "active_reason": "traded",
        "active_pnl_usd": str(active_pnl),
        "candidate_decision": "HOLD",
        "candidate_reason": "candidate_filter",
        "candidate_pnl_usd": "",
    }


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_forward_ledger(path: Path, rows: int, trades: int) -> None:
    fieldnames = ["reason", "pnl_usd", "edge"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index in range(rows):
            writer.writerow(
                {
                    "reason": "traded" if index < trades else "low_confidence",
                    "pnl_usd": "1.0" if index < trades else "0.0",
                    "edge": "0.1",
                }
            )


if __name__ == "__main__":
    unittest.main()
