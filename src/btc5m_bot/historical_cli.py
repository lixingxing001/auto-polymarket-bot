from __future__ import annotations

import argparse
from pathlib import Path

from .historical import (
    build_recent_historical_dataset,
    evaluate_directional_baseline,
    evaluate_market_price_baseline,
    write_dataset_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=24)
    parser.add_argument("--decision-offset-seconds", type=int, default=60)
    parser.add_argument("--output", type=Path, default=Path("data/historical_dataset.csv"))
    args = parser.parse_args()

    result = build_recent_historical_dataset(
        windows=args.windows,
        decision_offset_seconds=args.decision_offset_seconds,
    )
    write_dataset_csv(args.output, result.samples)

    payload = {
        "written": len(result.samples),
        "skipped_missing_market": result.skipped_missing_market,
        "skipped_unresolved": result.skipped_unresolved,
        "skipped_missing_candles": result.skipped_missing_candles,
    }
    if result.samples:
        payload["evaluation"] = evaluate_directional_baseline(result.samples)
        payload["market_price_baseline"] = evaluate_market_price_baseline(result.samples)
    print(payload)


if __name__ == "__main__":
    main()
