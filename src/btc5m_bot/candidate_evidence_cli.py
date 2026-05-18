from __future__ import annotations

import argparse
from pathlib import Path

from .candidate_evidence import (
    assess_candidate_evidence,
    load_candidate_comparison_rows,
    summarize_candidate_evidence,
)
from .candidate_strategies import load_candidate_registry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("strategy_candidates.csv"))
    parser.add_argument(
        "--comparison-dir",
        type=Path,
        default=Path("data/candidate_comparisons"),
    )
    args = parser.parse_args()

    output = {}
    for candidate_id, candidate in load_candidate_registry(args.registry).items():
        summary = summarize_candidate_evidence(
            load_candidate_comparison_rows(args.comparison_dir / f"{candidate_id}.csv")
        )
        output[candidate_id] = {
            "candidate": candidate.__dict__,
            "summary": summary.__dict__,
            "assessment": assess_candidate_evidence(summary),
        }
    print(output)


if __name__ == "__main__":
    main()
