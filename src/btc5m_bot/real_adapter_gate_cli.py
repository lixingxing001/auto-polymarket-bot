from __future__ import annotations

import argparse
from pathlib import Path

from .real_adapter_gate import DEFAULT_REAL_ADAPTER_GATE_REPORT, write_real_adapter_gate_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_REAL_ADAPTER_GATE_REPORT)
    args = parser.parse_args()
    print(write_real_adapter_gate_report(output_path=args.output))


if __name__ == "__main__":
    main()
