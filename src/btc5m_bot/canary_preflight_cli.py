from __future__ import annotations

import argparse
from pathlib import Path

from .canary_preflight import DEFAULT_CANARY_PREFLIGHT_REPORT, write_canary_preflight_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_CANARY_PREFLIGHT_REPORT)
    args = parser.parse_args()
    print(write_canary_preflight_report(output_path=args.output))


if __name__ == "__main__":
    main()
