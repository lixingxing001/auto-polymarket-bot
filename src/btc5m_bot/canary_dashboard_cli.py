from __future__ import annotations

import argparse
from pathlib import Path

from .canary_dashboard import DEFAULT_DASHBOARD_OUTPUT, write_canary_dashboard


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_DASHBOARD_OUTPUT)
    args = parser.parse_args()
    data = write_canary_dashboard(output_path=args.output)
    metrics = data["readiness_metrics"]
    print(
        "canary_dashboard "
        f"output={args.output} "
        f"ready={data['readiness']['ready']} "
        f"forward_evaluations={metrics['forward_evaluations']} "
        f"forward_trades={metrics['forward_trades']} "
        f"forward_win_rate={float(metrics['forward_win_rate']):.4f}"
    )


if __name__ == "__main__":
    main()
