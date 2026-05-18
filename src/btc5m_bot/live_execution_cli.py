from __future__ import annotations

import argparse
from pathlib import Path

from .live_execution import DEFAULT_ATTEMPT_LOG, run_live_execution_attempt
from .order_intent import DEFAULT_INTENT_EVENT_LOG


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", choices=("disabled", "mock"), default="disabled")
    parser.add_argument("--attempt-log", type=Path, default=DEFAULT_ATTEMPT_LOG)
    parser.add_argument("--intent-event-log", type=Path, default=DEFAULT_INTENT_EVENT_LOG)
    args = parser.parse_args()

    print(
        run_live_execution_attempt(
            adapter_kind=args.adapter,
            attempt_log_path=args.attempt_log,
            intent_event_log_path=args.intent_event_log,
        )
    )


if __name__ == "__main__":
    main()
