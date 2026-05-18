from __future__ import annotations

import argparse
from pathlib import Path

from .strategy_guardrails import (
    ACTIVE_STRATEGY_PARAMETERS,
    assess_strategy_guardrails,
    load_forward_ledger_rows,
    summarize_forward_ledger,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ledger",
        type=Path,
        default=Path("data/forward_snapshot_evaluations.csv"),
    )
    args = parser.parse_args()
    summary = summarize_forward_ledger(load_forward_ledger_rows(args.ledger))
    print(
        {
            "active_strategy_parameters": ACTIVE_STRATEGY_PARAMETERS.__dict__,
            "ledger": summary.__dict__,
            "guardrails": assess_strategy_guardrails(summary),
        }
    )


if __name__ == "__main__":
    main()
