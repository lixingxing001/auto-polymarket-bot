from __future__ import annotations

import argparse
from pathlib import Path

from .candidate_change_review import (
    DEFAULT_CHANGE_REVIEW_REPORT,
    DEFAULT_COMPARISON_DIR,
    DEFAULT_FORWARD_LEDGER,
    DEFAULT_REGISTRY,
    write_candidate_change_review_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_CHANGE_REVIEW_REPORT)
    parser.add_argument("--forward-ledger", type=Path, default=DEFAULT_FORWARD_LEDGER)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--comparison-dir", type=Path, default=DEFAULT_COMPARISON_DIR)
    args = parser.parse_args()
    print(
        write_candidate_change_review_report(
            output_path=args.output,
            forward_ledger_path=args.forward_ledger,
            registry_path=args.registry,
            comparison_dir=args.comparison_dir,
        )
    )


if __name__ == "__main__":
    main()
