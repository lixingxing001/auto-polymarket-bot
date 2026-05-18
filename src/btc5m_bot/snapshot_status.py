from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_snapshot_status(path: Path) -> dict:
    if not path.exists():
        return {
            "snapshot_rows": 0,
            "window_count": 0,
            "latest_slug": "",
            "latest_captured_at": "",
            "latest_seconds_to_close": "",
        }

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return {
            "snapshot_rows": 0,
            "window_count": 0,
            "latest_slug": "",
            "latest_captured_at": "",
            "latest_seconds_to_close": "",
        }

    latest = rows[-1]
    return {
        "snapshot_rows": len(rows),
        "window_count": len({row["slug"] for row in rows}),
        "latest_slug": latest["slug"],
        "latest_captured_at": latest["captured_at"],
        "latest_seconds_to_close": latest["seconds_to_close"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshots", type=Path, default=Path("data/orderbook_snapshots.csv"))
    args = parser.parse_args()
    print(read_snapshot_status(args.snapshots))


if __name__ == "__main__":
    main()
