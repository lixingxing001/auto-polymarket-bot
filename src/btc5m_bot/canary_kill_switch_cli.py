from __future__ import annotations

import argparse
from pathlib import Path

from .canary_kill_switch import (
    DEFAULT_EXECUTION_LEDGER,
    DEFAULT_KILL_SWITCH_FILE,
    DEFAULT_KILL_SWITCH_REPORT,
    write_canary_kill_switch_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, default=DEFAULT_EXECUTION_LEDGER)
    parser.add_argument("--kill-switch-file", type=Path, default=DEFAULT_KILL_SWITCH_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_KILL_SWITCH_REPORT)
    args = parser.parse_args()

    print(
        write_canary_kill_switch_report(
            output_path=args.output,
            ledger_path=args.ledger,
            kill_switch_path=args.kill_switch_file,
        )
    )


if __name__ == "__main__":
    main()
