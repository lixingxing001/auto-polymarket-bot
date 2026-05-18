from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .polymarket import Btc5mMarket, OrderBookSnapshot, PolymarketPublicClient


DEFAULT_OUTPUT = Path("data/orderbook_snapshots.csv")
DEFAULT_SUMMARY_OUTPUT = Path("data/orderbook_window_summary.csv")


def snapshot_row(
    market: Btc5mMarket,
    up_book: OrderBookSnapshot,
    down_book: OrderBookSnapshot,
    captured_at: datetime,
) -> dict:
    up_bid = up_book.best_bid
    up_ask = up_book.best_ask
    down_bid = down_book.best_bid
    down_ask = down_book.best_ask
    return {
        "captured_at": captured_at.isoformat(),
        "slug": market.slug,
        "condition_id": market.condition_id,
        "title": market.title,
        "market_end_time": market.end_time.isoformat(),
        "seconds_to_close": max(0, int((market.end_time - captured_at).total_seconds())),
        "up_token_id": market.up_token_id,
        "down_token_id": market.down_token_id,
        "up_best_bid": up_bid.price if up_bid else "",
        "up_best_bid_size": up_bid.size if up_bid else "",
        "up_best_ask": up_ask.price if up_ask else "",
        "up_best_ask_size": up_ask.size if up_ask else "",
        "down_best_bid": down_bid.price if down_bid else "",
        "down_best_bid_size": down_bid.size if down_bid else "",
        "down_best_ask": down_ask.price if down_ask else "",
        "down_best_ask_size": down_ask.size if down_ask else "",
    }


def append_snapshot(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def build_window_summary(snapshot_rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in snapshot_rows:
        grouped.setdefault(row["slug"], []).append(row)

    summaries: list[dict] = []
    for slug, rows in grouped.items():
        ordered = sorted(rows, key=lambda row: row["captured_at"])
        summaries.append(
            {
                "slug": slug,
                "condition_id": ordered[0]["condition_id"],
                "snapshot_count": len(ordered),
                "first_captured_at": ordered[0]["captured_at"],
                "last_captured_at": ordered[-1]["captured_at"],
                "min_up_best_ask": min(
                    float(row["up_best_ask"]) for row in ordered if row["up_best_ask"] != ""
                ),
                "max_up_best_ask": max(
                    float(row["up_best_ask"]) for row in ordered if row["up_best_ask"] != ""
                ),
                "min_down_best_ask": min(
                    float(row["down_best_ask"]) for row in ordered if row["down_best_ask"] != ""
                ),
                "max_down_best_ask": max(
                    float(row["down_best_ask"]) for row in ordered if row["down_best_ask"] != ""
                ),
            }
        )
    return summaries


def rebuild_window_summary(snapshot_path: Path, summary_path: Path) -> None:
    if not snapshot_path.exists():
        return
    with snapshot_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    summaries = build_window_summary(rows)
    if not summaries:
        return
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)


def capture_once(client: PolymarketPublicClient | None = None) -> dict:
    client = client or PolymarketPublicClient()
    captured_at = datetime.now(timezone.utc)
    market = client.find_live_btc_5m_market(now=captured_at)
    up_book = client.get_order_book(market.up_token_id)
    down_book = client.get_order_book(market.down_token_id)
    return snapshot_row(
        market=market,
        up_book=up_book,
        down_book=down_book,
        captured_at=captured_at,
    )


def run_capture_loop(
    iterations: int,
    interval_seconds: float,
    output: Path,
    summary_output: Path,
    continue_on_error: bool = False,
) -> None:
    index = 0
    while iterations == 0 or index < iterations:
        try:
            row = capture_once()
            append_snapshot(output, row)
            print(row, flush=True)
        except Exception as exc:  # noqa: BLE001
            print(
                {
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "error": type(exc).__name__,
                    "message": str(exc),
                },
                file=sys.stderr,
                flush=True,
            )
            if not continue_on_error:
                raise
        index += 1
        rebuild_window_summary(output, summary_output)
        if iterations == 0 or index < iterations:
            time.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--interval-seconds", type=float, default=5.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()

    run_capture_loop(
        iterations=args.iterations,
        interval_seconds=args.interval_seconds,
        output=args.output,
        summary_output=args.summary_output,
        continue_on_error=args.continue_on_error,
    )


if __name__ == "__main__":
    main()
