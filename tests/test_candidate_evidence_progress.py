import csv
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from btc5m_bot.candidate_evidence_progress import (
    build_candidate_evidence_progress_report,
    estimate_windows_to_review,
    render_candidate_evidence_progress_markdown,
    write_candidate_evidence_progress_report,
)
from btc5m_bot.candidate_strategies import CandidateStrategy, write_candidate_registry


class CandidateEvidenceProgressTests(unittest.TestCase):
    def test_estimate_windows_uses_divergence_rate(self) -> None:
        self.assertEqual(
            estimate_windows_to_review(
                eligible_windows_needed=4,
                divergent_windows_needed=6,
                observed_divergence_rate=0.25,
            ),
            24,
        )

    def test_unknown_eta_when_divergence_has_not_started(self) -> None:
        self.assertIsNone(
            estimate_windows_to_review(
                eligible_windows_needed=30,
                divergent_windows_needed=10,
                observed_divergence_rate=0.0,
            )
        )

    def test_build_progress_report_ignores_inactive_candidate_for_next_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            registry = base / "registry.csv"
            comparisons = base / "comparisons"
            comparisons.mkdir()
            write_candidate_registry(
                registry,
                (
                    _candidate("active", status="registered"),
                    _candidate("old", status="rejected"),
                ),
            )
            _write_rows(
                comparisons / "active.csv",
                [_hold_row() for _ in range(10)],
            )
            _write_rows(
                comparisons / "old.csv",
                [_avoid_loss_row(active_pnl=-1.0) for _ in range(30)],
            )
            report = build_candidate_evidence_progress_report(
                registry_path=registry,
                comparison_dir=comparisons,
            )
        self.assertEqual(report["active_candidate_count"], 1)
        self.assertEqual(report["next_review_candidate_id"], "active")
        inactive = [item for item in report["items"] if item["candidate_id"] == "old"][0]
        self.assertEqual(inactive["blocker_kind"], "candidate_not_active")

    def test_write_progress_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            registry = base / "registry.csv"
            comparisons = base / "comparisons"
            output = base / "progress.md"
            comparisons.mkdir()
            write_candidate_registry(registry, (_candidate("active"),))
            _write_rows(
                comparisons / "active.csv",
                [
                    *[_avoid_loss_row(active_pnl=-1.0) for _ in range(5)],
                    *[_hold_row() for _ in range(5)],
                ],
            )
            report = write_candidate_evidence_progress_report(
                output_path=output,
                registry_path=registry,
                comparison_dir=comparisons,
            )
            rendered_file = output.read_text(encoding="utf-8")
        rendered = render_candidate_evidence_progress_markdown(report)
        self.assertIn("Candidate Evidence Progress Report", rendered)
        self.assertIn("active", rendered_file)
        self.assertIn("does not approve strategy changes", rendered_file)


def _candidate(candidate_id: str, status: str = "registered") -> CandidateStrategy:
    now = datetime(2026, 5, 19, tzinfo=timezone.utc)
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


def _hold_row() -> dict[str, str]:
    return {
        "active_decision": "HOLD",
        "active_reason": "low_confidence",
        "active_pnl_usd": "",
        "candidate_decision": "HOLD",
        "candidate_reason": "low_confidence",
        "candidate_pnl_usd": "",
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


if __name__ == "__main__":
    unittest.main()
