from __future__ import annotations

import argparse
from pathlib import Path

from .canary_readiness import (
    DEFAULT_ATTEMPT_LOG,
    DEFAULT_CANARY_REPORT,
    DEFAULT_CANDIDATE_COMPARISON_DIR,
    DEFAULT_FORWARD_LEDGER,
    DEFAULT_INTENT_EVENT_LOG,
    DEFAULT_REGISTRY,
    write_canary_readiness_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward-ledger", type=Path, default=DEFAULT_FORWARD_LEDGER)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--comparison-dir", type=Path, default=DEFAULT_CANDIDATE_COMPARISON_DIR)
    parser.add_argument("--intent-event-log", type=Path, default=DEFAULT_INTENT_EVENT_LOG)
    parser.add_argument("--attempt-log", type=Path, default=DEFAULT_ATTEMPT_LOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_CANARY_REPORT)
    args = parser.parse_args()

    print(
        write_canary_readiness_report(
            output_path=args.output,
            forward_ledger_path=args.forward_ledger,
            registry_path=args.registry,
            comparison_dir=args.comparison_dir,
            intent_event_path=args.intent_event_log,
            attempt_log_path=args.attempt_log,
        )
    )


if __name__ == "__main__":
    main()
