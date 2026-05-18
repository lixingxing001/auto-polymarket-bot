from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from websockets.asyncio.client import connect

from .polymarket import Btc5mMarket, BookLevel, OrderBookSnapshot, PolymarketPublicClient
from .snapshot_recorder import (
    DEFAULT_OUTPUT,
    DEFAULT_SUMMARY_OUTPUT,
    append_snapshot,
    rebuild_window_summary,
    snapshot_row,
)


MARKET_WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"


@dataclass
class MutableOrderBook:
    token_id: str
    bids: dict[float, float] = field(default_factory=dict)
    asks: dict[float, float] = field(default_factory=dict)
    tick_size: float = 0.0
    min_order_size: float = 0.0

    def replace(
        self,
        bids: list[dict[str, Any]],
        asks: list[dict[str, Any]],
    ) -> None:
        self.bids = _levels_to_map(bids)
        self.asks = _levels_to_map(asks)

    def update_level(self, side: str, price: str | float, size: str | float) -> None:
        levels = self.bids if side.upper() == "BUY" else self.asks
        parsed_price = float(price)
        parsed_size = float(size)
        if parsed_size == 0:
            levels.pop(parsed_price, None)
            return
        levels[parsed_price] = parsed_size

    def to_snapshot(self) -> OrderBookSnapshot:
        return OrderBookSnapshot(
            token_id=self.token_id,
            bids=tuple(BookLevel(price=price, size=size) for price, size in self.bids.items()),
            asks=tuple(BookLevel(price=price, size=size) for price, size in self.asks.items()),
            tick_size=self.tick_size,
            min_order_size=self.min_order_size,
        )

    @property
    def ready(self) -> bool:
        return bool(self.bids) and bool(self.asks)


def _levels_to_map(levels: list[dict[str, Any]]) -> dict[float, float]:
    return {float(level["price"]): float(level["size"]) for level in levels}


def subscription_message(market: Btc5mMarket) -> str:
    return json.dumps(
        {
            "assets_ids": [market.up_token_id, market.down_token_id],
            "type": "market",
            "custom_feature_enabled": True,
        }
    )


def parse_ws_messages(raw_message: str) -> list[dict[str, Any]]:
    if isinstance(raw_message, bytes):
        raw_message = raw_message.decode("utf-8")
    if raw_message in {"PONG", "PING"}:
        return []

    payload = json.loads(raw_message)
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        raise TypeError("unexpected websocket payload")
    return [payload]


def apply_market_event(
    books: dict[str, MutableOrderBook],
    payload: dict[str, Any],
) -> bool:
    event_type = payload.get("event_type")
    if event_type == "book":
        asset_id = str(payload["asset_id"])
        if asset_id not in books:
            return False
        books[asset_id].replace(
            bids=list(payload.get("bids", [])),
            asks=list(payload.get("asks", [])),
        )
        if payload.get("tick_size") is not None:
            books[asset_id].tick_size = float(payload["tick_size"])
        return True

    if event_type == "price_change":
        changed = False
        for change in payload.get("price_changes", []):
            asset_id = str(change["asset_id"])
            if asset_id not in books:
                continue
            books[asset_id].update_level(
                side=str(change["side"]),
                price=change["price"],
                size=change["size"],
            )
            changed = True
        return changed

    if event_type == "tick_size_change":
        asset_id = str(payload["asset_id"])
        if asset_id not in books:
            return False
        books[asset_id].tick_size = float(payload["new_tick_size"])
        return True

    return False


def snapshot_row_from_books(
    market: Btc5mMarket,
    books: dict[str, MutableOrderBook],
    captured_at: datetime,
) -> dict:
    return snapshot_row(
        market=market,
        up_book=books[market.up_token_id].to_snapshot(),
        down_book=books[market.down_token_id].to_snapshot(),
        captured_at=captured_at,
    )


def books_are_ready(market: Btc5mMarket, books: dict[str, MutableOrderBook]) -> bool:
    return books[market.up_token_id].ready and books[market.down_token_id].ready


def top_of_book_signature(
    market: Btc5mMarket,
    books: dict[str, MutableOrderBook],
) -> tuple[float, float, float, float, float, float, float, float]:
    up_snapshot = books[market.up_token_id].to_snapshot()
    down_snapshot = books[market.down_token_id].to_snapshot()
    up_bid = up_snapshot.best_bid
    up_ask = up_snapshot.best_ask
    down_bid = down_snapshot.best_bid
    down_ask = down_snapshot.best_ask
    if up_bid is None or up_ask is None or down_bid is None or down_ask is None:
        raise LookupError("top of book is incomplete")
    return (
        up_bid.price,
        up_bid.size,
        up_ask.price,
        up_ask.size,
        down_bid.price,
        down_bid.size,
        down_ask.price,
        down_ask.size,
    )


async def _send_heartbeats(websocket, interval_seconds: float = 10.0) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        await websocket.send("PING")


async def capture_market_window(
    market: Btc5mMarket,
    output: Path,
    max_seconds: float | None = None,
    min_write_interval_seconds: float = 1.0,
) -> int:
    started_at = datetime.now(timezone.utc)
    books = {
        market.up_token_id: MutableOrderBook(token_id=market.up_token_id),
        market.down_token_id: MutableOrderBook(token_id=market.down_token_id),
    }
    snapshot_count = 0
    last_signature: tuple[float, float, float, float, float, float, float, float] | None = None
    last_written_at: datetime | None = None

    async with connect(MARKET_WS_URL) as websocket:
        await websocket.send(subscription_message(market))
        heartbeat_task = asyncio.create_task(_send_heartbeats(websocket))
        try:
            while datetime.now(timezone.utc) < market.end_time:
                if max_seconds is not None:
                    elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
                    if elapsed >= max_seconds:
                        break
                try:
                    raw_message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                except TimeoutError:
                    continue

                for payload in parse_ws_messages(raw_message):
                    if payload.get("event_type") == "market_resolved":
                        return snapshot_count

                    if not apply_market_event(books, payload):
                        continue

                    if not books_are_ready(market, books):
                        continue

                    signature = top_of_book_signature(market, books)
                    if signature == last_signature:
                        continue
                    captured_at = datetime.now(timezone.utc)
                    if (
                        last_written_at is not None
                        and (captured_at - last_written_at).total_seconds()
                        < min_write_interval_seconds
                    ):
                        last_signature = signature
                        continue

                    row = snapshot_row_from_books(
                        market=market,
                        books=books,
                        captured_at=captured_at,
                    )
                    append_snapshot(output, row)
                    snapshot_count += 1
                    last_signature = signature
                    last_written_at = captured_at
        finally:
            heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await heartbeat_task

    return snapshot_count


async def run_ws_capture_loop(
    output: Path,
    summary_output: Path,
    max_windows: int = 0,
    max_seconds_per_window: float | None = None,
    min_write_interval_seconds: float = 1.0,
    continue_on_error: bool = False,
) -> None:
    client = PolymarketPublicClient()
    windows_completed = 0

    while max_windows == 0 or windows_completed < max_windows:
        try:
            market = client.find_live_btc_5m_market()
            snapshot_count = await capture_market_window(
                market=market,
                output=output,
                max_seconds=max_seconds_per_window,
                min_write_interval_seconds=min_write_interval_seconds,
            )
            print(
                {
                    "slug": market.slug,
                    "captured_snapshots": snapshot_count,
                    "window_end_time": market.end_time.isoformat(),
                },
                flush=True,
            )
            windows_completed += 1
            rebuild_window_summary(output, summary_output)
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
            await asyncio.sleep(1.0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--max-windows", type=int, default=1)
    parser.add_argument("--max-seconds-per-window", type=float, default=None)
    parser.add_argument("--min-write-interval-seconds", type=float, default=1.0)
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()

    asyncio.run(
        run_ws_capture_loop(
            output=args.output,
            summary_output=args.summary_output,
            max_windows=args.max_windows,
            max_seconds_per_window=args.max_seconds_per_window,
            min_write_interval_seconds=args.min_write_interval_seconds,
            continue_on_error=args.continue_on_error,
        )
    )


if __name__ == "__main__":
    main()
