from __future__ import annotations

import argparse
from pathlib import Path

from .canary_monitor import DEFAULT_MONITOR_REPORT, run_canary_monitor
from .canary_readiness import DEFAULT_CANARY_REPORT


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--readiness-output", type=Path, default=DEFAULT_CANARY_REPORT)
    parser.add_argument("--monitor-output", type=Path, default=DEFAULT_MONITOR_REPORT)
    parser.add_argument("--fail-if-not-ready", action="store_true")
    args = parser.parse_args()

    result = run_canary_monitor(
        readiness_output_path=args.readiness_output,
        monitor_output_path=args.monitor_output,
    )
    print(result)
    if args.fail_if_not_ready and not result["monitor"]["ready"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
