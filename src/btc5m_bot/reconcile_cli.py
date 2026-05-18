from __future__ import annotations

import argparse
from pathlib import Path

from .reconcile import reconcile_paper_signals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/paper_signals.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/paper_results.csv"))
    args = parser.parse_args()
    print(reconcile_paper_signals(args.input, args.output))


if __name__ == "__main__":
    main()
