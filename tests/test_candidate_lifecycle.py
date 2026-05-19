import csv
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from btc5m_bot.candidate_change_review import review_candidate_change
from btc5m_bot.candidate_lifecycle import (
    build_candidate_lifecycle_report,
    classify_candidate_lifecycle,
    render_candidate_lifecycle_markdown,
    write_candidate_lifecycle_report,
)
from btc5m_bot.candidate_strategies import CandidateStrategy, write_candidate_registry


class CandidateLifecycleTests(unittest.TestCase):
    def test_collecting_when_evidence_is_not_review_ready(self) -> None:
        review = review_candidate_change(
            candidate_id="collecting",
            filter_kind="none",
            rows=[],
        )
        item = classify_candidate_lifecycle(
            review=review,
            evidence_assessment={
                "review_ready": False,
                "next_review_gap": {
                    "eligible_windows_needed": 30,
                    "divergent_windows_needed": 10,
                },
            },
            guardrails={"stage": "change_review_ready", "change_review_ready": True},
        )
        self.assertEqual(item.lifecycle_status, "COLLECTING")
        self.assertEqual(item.recommended_action, "collect_more_forward_evidence")

    def test_rejects_review_ready_non_positive_delta(self) -> None:
        review = review_candidate_change(
            candidate_id="bad",
            filter_kind="none",
            rows=[_avoid_active_win_row() for _ in range(30)],
        )
        item = classify_candidate_lifecycle(
            review=review,
            evidence_assessment={
                "review_ready": True,
                "next_review_gap": {
                    "eligible_windows_needed": 0,
                    "divergent_windows_needed": 0,
                },
            },
            guardrails={"stage": "change_review_ready", "change_review_ready": True},
        )
        self.assertEqual(item.lifecycle_status, "REJECT_RECOMMENDED")
        self.assertIn("review_ready_but_delta_pnl_not_positive", item.rationale)

    def test_promotes_only_after_quality_and_guardrail_pass(self) -> None:
        review = review_candidate_change(
            candidate_id="good",
            filter_kind="none",
            rows=[
                *[_avoid_active_loss_row() for _ in range(10)],
                *[_candidate_win_row() for _ in range(20)],
            ],
        )
        item = classify_candidate_lifecycle(
            review=review,
            evidence_assessment={
                "review_ready": True,
                "next_review_gap": {
                    "eligible_windows_needed": 0,
                    "divergent_windows_needed": 0,
                },
            },
            guardrails={"stage": "change_review_ready", "change_review_ready": True},
        )
        self.assertEqual(item.lifecycle_status, "PROMOTION_READY")
        self.assertEqual(item.recommended_action, "manual_freeze_review_allowed")

    def test_write_lifecycle_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            registry = base / "registry.csv"
            comparison_dir = base / "comparisons"
            ledger = base / "forward.csv"
            output = base / "lifecycle.md"
            comparison_dir.mkdir()
            write_candidate_registry(
                registry,
                (
                    CandidateStrategy(
                        candidate_id="candidate",
                        description="Candidate",
                        rationale="Test",
                        registered_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
                        eligible_after_market_end_time=datetime(
                            2026,
                            5,
                            19,
                            tzinfo=timezone.utc,
                        ),
                        min_confidence=0.65,
                        min_edge=0.03,
                        stake_usd=10.0,
                        max_fill_delay_seconds=30,
                    ),
                ),
            )
            _write_rows(
                comparison_dir / "candidate.csv",
                [
                    *[_avoid_active_loss_row() for _ in range(10)],
                    *[_candidate_win_row() for _ in range(20)],
                ],
            )
            _write_forward_ledger(ledger)

            report = write_candidate_lifecycle_report(
                output_path=output,
                forward_ledger_path=ledger,
                registry_path=registry,
                comparison_dir=comparison_dir,
            )
            rebuilt = build_candidate_lifecycle_report(
                forward_ledger_path=ledger,
                registry_path=registry,
                comparison_dir=comparison_dir,
            )
            rendered_file = output.read_text(encoding="utf-8")

        rendered = render_candidate_lifecycle_markdown(report)
        self.assertIn("Candidate Lifecycle Report", rendered)
        self.assertIn("PROMOTION_READY", rendered)
        self.assertIn("candidate", rendered_file)
        self.assertEqual(rebuilt["buckets"]["PROMOTION_READY"][0]["candidate_id"], "candidate")


def _avoid_active_win_row() -> dict[str, str]:
    return {
        "active_decision": "UP",
        "active_reason": "traded",
        "active_pnl_usd": "1.0",
        "candidate_decision": "HOLD",
        "candidate_reason": "candidate_filter",
        "candidate_pnl_usd": "",
    }


def _avoid_active_loss_row() -> dict[str, str]:
    return {
        "active_decision": "UP",
        "active_reason": "traded",
        "active_pnl_usd": "-1.0",
        "candidate_decision": "HOLD",
        "candidate_reason": "candidate_filter",
        "candidate_pnl_usd": "",
    }


def _candidate_win_row() -> dict[str, str]:
    return {
        "active_decision": "UP",
        "active_reason": "traded",
        "active_pnl_usd": "0.0",
        "candidate_decision": "UP",
        "candidate_reason": "traded",
        "candidate_pnl_usd": "1.0",
    }


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_forward_ledger(path: Path) -> None:
    fieldnames = ["reason", "pnl_usd", "edge"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index in range(100):
            writer.writerow(
                {
                    "reason": "traded" if index < 30 else "low_confidence",
                    "pnl_usd": "1.0" if index < 30 else "",
                    "edge": "0.1" if index < 30 else "",
                }
            )


if __name__ == "__main__":
    unittest.main()
