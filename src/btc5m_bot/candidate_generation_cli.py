from __future__ import annotations

import argparse
from pathlib import Path

from .candidate_generation import (
    DEFAULT_GENERATION_REPORT,
    DEFAULT_REGISTRY,
    write_candidate_generation_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_GENERATION_REPORT)
    args = parser.parse_args()

    print(
        write_candidate_generation_report(
            output_path=args.output,
            registry_path=args.registry,
        )
    )


if __name__ == "__main__":
    main()
