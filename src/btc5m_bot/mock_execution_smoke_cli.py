from __future__ import annotations

import argparse
from pathlib import Path

from .live_execution import DEFAULT_ATTEMPT_LOG
from .mock_execution_smoke import DEFAULT_SMOKE_REPORT, write_mock_execution_smoke_report
from .order_intent import DEFAULT_INTENT_EVENT_LOG


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-log", type=Path, default=DEFAULT_ATTEMPT_LOG)
    parser.add_argument("--intent-event-log", type=Path, default=DEFAULT_INTENT_EVENT_LOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_SMOKE_REPORT)
    args = parser.parse_args()

    print(
        write_mock_execution_smoke_report(
            output_path=args.output,
            attempt_log_path=args.attempt_log,
            intent_event_log_path=args.intent_event_log,
        )
    )


if __name__ == "__main__":
    main()
