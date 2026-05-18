from __future__ import annotations

import argparse
from pathlib import Path

from .execution_health import (
    DEFAULT_ATTEMPT_LOG,
    DEFAULT_FORWARD_LEDGER,
    DEFAULT_INTENT_EVENT_LOG,
    DEFAULT_REPORT,
    write_execution_health_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent-event-log", type=Path, default=DEFAULT_INTENT_EVENT_LOG)
    parser.add_argument("--attempt-log", type=Path, default=DEFAULT_ATTEMPT_LOG)
    parser.add_argument("--forward-ledger", type=Path, default=DEFAULT_FORWARD_LEDGER)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    print(
        write_execution_health_report(
            output_path=args.output,
            intent_event_path=args.intent_event_log,
            attempt_log_path=args.attempt_log,
            forward_ledger_path=args.forward_ledger,
        )
    )


if __name__ == "__main__":
    main()
