from __future__ import annotations

import argparse
from pathlib import Path

from .active_strategy import DEFAULT_ACTIVE_STRATEGY_STATE
from .canary_readiness import DEFAULT_FORWARD_LEDGER
from .current_strategy_readiness import (
    DEFAULT_CURRENT_STRATEGY_READINESS_REPORT,
    write_current_strategy_readiness_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_CURRENT_STRATEGY_READINESS_REPORT)
    parser.add_argument("--forward-ledger", type=Path, default=DEFAULT_FORWARD_LEDGER)
    parser.add_argument("--strategy-state", type=Path, default=DEFAULT_ACTIVE_STRATEGY_STATE)
    args = parser.parse_args()

    print(
        write_current_strategy_readiness_report(
            output_path=args.output,
            forward_ledger_path=args.forward_ledger,
            strategy_state_path=args.strategy_state,
        )
    )


if __name__ == "__main__":
    main()
