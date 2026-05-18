from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

from .paper_signal import generate_paper_signal


DEFAULT_OUTPUT = Path("data/paper_signals.csv")


def append_signal(path: Path, signal: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        **{key: value for key, value in signal.items() if key != "features"},
        "features_json": json.dumps(signal.get("features", {}), separators=(",", ":")),
    }
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--interval-seconds", type=float, default=15.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    for index in range(args.iterations):
        signal = generate_paper_signal()
        append_signal(args.output, signal)
        print(signal)
        if index < args.iterations - 1:
            time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
