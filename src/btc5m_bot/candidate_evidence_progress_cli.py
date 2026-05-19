from __future__ import annotations

import argparse
from pathlib import Path

from .candidate_evidence_progress import (
    DEFAULT_COMPARISON_DIR,
    DEFAULT_PROGRESS_REPORT,
    DEFAULT_REGISTRY,
    write_candidate_evidence_progress_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--comparison-dir", type=Path, default=DEFAULT_COMPARISON_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_PROGRESS_REPORT)
    args = parser.parse_args()

    print(
        write_candidate_evidence_progress_report(
            output_path=args.output,
            registry_path=args.registry,
            comparison_dir=args.comparison_dir,
        )
    )


if __name__ == "__main__":
    main()
