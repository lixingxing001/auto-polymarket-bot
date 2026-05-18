from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CandidateEvidencePolicy:
    min_eligible_windows_for_review: int = 30
    min_divergent_windows_for_review: int = 10


@dataclass(frozen=True)
class CandidateEvidenceSummary:
    eligible_windows: int
    active_trades: int
    candidate_trades: int
    divergent_windows: int
    candidate_filter_windows: int
    active_total_pnl_usd: float
    candidate_total_pnl_usd: float
    delta_pnl_usd: float


def load_candidate_comparison_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summarize_candidate_evidence(rows: list[dict[str, str]]) -> CandidateEvidenceSummary:
    active_total = sum(_optional_float(row["active_pnl_usd"]) or 0.0 for row in rows)
    candidate_total = sum(_optional_float(row["candidate_pnl_usd"]) or 0.0 for row in rows)
    return CandidateEvidenceSummary(
        eligible_windows=len(rows),
        active_trades=sum(1 for row in rows if row["active_reason"] == "traded"),
        candidate_trades=sum(1 for row in rows if row["candidate_reason"] == "traded"),
        divergent_windows=sum(
            1
            for row in rows
            if row["active_decision"] != row["candidate_decision"]
            or row["active_reason"] != row["candidate_reason"]
        ),
        candidate_filter_windows=sum(
            1 for row in rows if row["candidate_reason"] == "candidate_filter"
        ),
        active_total_pnl_usd=active_total,
        candidate_total_pnl_usd=candidate_total,
        delta_pnl_usd=candidate_total - active_total,
    )


def assess_candidate_evidence(
    summary: CandidateEvidenceSummary,
    policy: CandidateEvidencePolicy | None = None,
) -> dict:
    policy = policy or CandidateEvidencePolicy()
    review_ready = (
        summary.eligible_windows >= policy.min_eligible_windows_for_review
        and summary.divergent_windows >= policy.min_divergent_windows_for_review
    )
    return {
        "stage": "review_ready" if review_ready else "collecting",
        "review_ready": review_ready,
        "next_review_gap": {
            "eligible_windows_needed": max(
                0,
                policy.min_eligible_windows_for_review - summary.eligible_windows,
            ),
            "divergent_windows_needed": max(
                0,
                policy.min_divergent_windows_for_review - summary.divergent_windows,
            ),
        },
    }


def _optional_float(value: str) -> float | None:
    return float(value) if value != "" else None
