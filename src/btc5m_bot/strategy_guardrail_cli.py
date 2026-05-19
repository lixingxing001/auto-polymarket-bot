from __future__ import annotations

import argparse
from pathlib import Path

from .active_strategy import DEFAULT_ACTIVE_STRATEGY_STATE, load_optional_active_strategy_state
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
    parser.add_argument("--strategy-state", type=Path, default=DEFAULT_ACTIVE_STRATEGY_STATE)
    args = parser.parse_args()
    summary = summarize_forward_ledger(load_forward_ledger_rows(args.ledger))
    active_strategy_state = load_optional_active_strategy_state(args.strategy_state)
    print(
        {
            "active_strategy_parameters": ACTIVE_STRATEGY_PARAMETERS.__dict__,
            "active_strategy_state": (
                {
                    "source_candidate_id": active_strategy_state.source_candidate_id,
                    "filter_kind": active_strategy_state.filter_kind,
                    "min_confidence": active_strategy_state.min_confidence,
                    "min_edge": active_strategy_state.min_edge,
                    "stake_usd": active_strategy_state.stake_usd,
                    "max_fill_delay_seconds": active_strategy_state.max_fill_delay_seconds,
                    "live_trading_enabled": active_strategy_state.live_trading_enabled,
                }
                if active_strategy_state is not None
                else None
            ),
            "ledger": summary.__dict__,
            "guardrails": assess_strategy_guardrails(summary),
        }
    )


if __name__ == "__main__":
    main()
