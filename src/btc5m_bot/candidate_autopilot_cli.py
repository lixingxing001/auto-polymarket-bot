from __future__ import annotations

import argparse
from pathlib import Path

from .active_strategy import DEFAULT_ACTIVE_STRATEGY_STATE
from .candidate_autopilot import (
    DEFAULT_AUTOPILOT_REPORT,
    CandidateAutopilotPolicy,
    run_candidate_autopilot,
)
from .candidate_lifecycle import (
    DEFAULT_COMPARISON_DIR,
    DEFAULT_FORWARD_LEDGER,
    DEFAULT_LIFECYCLE_REPORT,
    DEFAULT_REGISTRY,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_AUTOPILOT_REPORT)
    parser.add_argument("--lifecycle-output", type=Path, default=DEFAULT_LIFECYCLE_REPORT)
    parser.add_argument("--strategy-state", type=Path, default=DEFAULT_ACTIVE_STRATEGY_STATE)
    parser.add_argument("--forward-ledger", type=Path, default=DEFAULT_FORWARD_LEDGER)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--comparison-dir", type=Path, default=DEFAULT_COMPARISON_DIR)
    parser.add_argument("--enable-auto-promote", action="store_true")
    args = parser.parse_args()

    print(
        run_candidate_autopilot(
            output_path=args.output,
            lifecycle_output_path=args.lifecycle_output,
            strategy_state_path=args.strategy_state,
            forward_ledger_path=args.forward_ledger,
            registry_path=args.registry,
            comparison_dir=args.comparison_dir,
            policy=CandidateAutopilotPolicy(enabled=args.enable_auto_promote),
        )
    )


if __name__ == "__main__":
    main()
