from __future__ import annotations

import argparse
from pathlib import Path

from .live_execution import DEFAULT_ATTEMPT_LOG, run_live_execution_attempt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", choices=("disabled", "mock"), default="disabled")
    parser.add_argument("--attempt-log", type=Path, default=DEFAULT_ATTEMPT_LOG)
    args = parser.parse_args()

    print(
        run_live_execution_attempt(
            adapter_kind=args.adapter,
            attempt_log_path=args.attempt_log,
        )
    )


if __name__ == "__main__":
    main()
