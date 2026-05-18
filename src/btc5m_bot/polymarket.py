from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import (
    BTC_5M_SLUG_PREFIX,
    POLYMARKET_CLOB_BASE_URL,
    POLYMARKET_DATA_BASE_URL,
    POLYMARKET_GAMMA_BASE_URL,
)
from .models import MarketQuote


@dataclass(frozen=True)
class Btc5mMarket:
    slug: str
    title: str
    condition_id: str
    end_time: datetime
    up_token_id: str
    down_token_id: str
    accepting_orders: bool


@dataclass(frozen=True)
class BookLevel:
    price: float
    size: float


@dataclass(frozen=True)
class OrderBookSnapshot:
    token_id: str
    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]
    tick_size: float
    min_order_size: float

    @property
    def best_bid(self) -> BookLevel | None:
        return max(self.bids, key=lambda level: level.price, default=None)

    @property
    def best_ask(self) -> BookLevel | None:
        return min(self.asks, key=lambda level: level.price, default=None)


@dataclass(frozen=True)
class MarketTrade:
    asset_id: str
    condition_id: str
    outcome: str
    side: str
    size: float
    price: float
    timestamp: int


@dataclass(frozen=True)
class PricePoint:
    timestamp: int
    price: float


def floor_to_five_minutes(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        raise ValueError("moment must be timezone-aware")

    utc_moment = moment.astimezone(timezone.utc)
    floored_epoch = int(utc_moment.timestamp()) // 300 * 300
    return datetime.fromtimestamp(floored_epoch, tz=timezone.utc)


def btc_5m_slug_for(moment: datetime) -> str:
    start = floor_to_five_minutes(moment)
    return f"{BTC_5M_SLUG_PREFIX}-{int(start.timestamp())}"


class PolymarketPublicClient:
    def __init__(
        self,
        gamma_base_url: str = POLYMARKET_GAMMA_BASE_URL,
        clob_base_url: str = POLYMARKET_CLOB_BASE_URL,
        data_base_url: str = POLYMARKET_DATA_BASE_URL,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.gamma_base_url = gamma_base_url.rstrip("/")
        self.clob_base_url = clob_base_url.rstrip("/")
        self.data_base_url = data_base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def get_event_by_slug(self, slug: str) -> dict:
        return self._get_json(f"{self.gamma_base_url}/events/slug/{slug}")

    def get_btc_5m_market_by_start(self, start: datetime) -> Btc5mMarket:
        slug = btc_5m_slug_for(start)
        event = self.get_event_by_slug(slug)
        return self._parse_market(event)

    def get_order_book(self, token_id: str) -> OrderBookSnapshot:
        query = urlencode({"token_id": token_id})
        payload = self._get_json(f"{self.clob_base_url}/book?{query}")

        bids = tuple(
            BookLevel(price=float(level["price"]), size=float(level["size"]))
            for level in payload.get("bids", [])
        )
        asks = tuple(
            BookLevel(price=float(level["price"]), size=float(level["size"]))
            for level in payload.get("asks", [])
        )
        return OrderBookSnapshot(
            token_id=token_id,
            bids=bids,
            asks=asks,
            tick_size=float(payload["tick_size"]),
            min_order_size=float(payload["min_order_size"]),
        )

    def get_market_trades(
        self,
        condition_id: str,
        limit: int = 1000,
        max_pages: int = 10,
        stop_at_or_before_ts: int | None = None,
    ) -> list[MarketTrade]:
        trades: list[MarketTrade] = []
        for page in range(max_pages):
            query = urlencode(
                {
                    "market": condition_id,
                    "limit": limit,
                    "offset": page * limit,
                    "takerOnly": "true",
                }
            )
            try:
                payload = self._get_json(f"{self.data_base_url}/trades?{query}")
            except HTTPError as exc:
                if page > 0 and exc.code == 400:
                    break
                raise
            if not payload:
                break

            page_trades = [
                MarketTrade(
                    asset_id=str(row["asset"]),
                    condition_id=row["conditionId"],
                    outcome=row["outcome"],
                    side=row["side"],
                    size=float(row["size"]),
                    price=float(row["price"]),
                    timestamp=int(row["timestamp"]),
                )
                for row in payload
            ]
            trades.extend(page_trades)

            if stop_at_or_before_ts is not None and min(trade.timestamp for trade in page_trades) <= stop_at_or_before_ts:
                break
            if len(page_trades) < limit:
                break

        return sorted(trades, key=lambda trade: trade.timestamp)

    def get_price_history(
        self,
        token_id: str,
        start_ts: int,
        end_ts: int,
        fidelity_minutes: int = 1,
    ) -> list[PricePoint]:
        query = urlencode(
            {
                "market": token_id,
                "startTs": start_ts,
                "endTs": end_ts,
                "fidelity": fidelity_minutes,
            }
        )
        payload = self._get_json(f"{self.clob_base_url}/prices-history?{query}")
        return [
            PricePoint(timestamp=int(row["t"]), price=float(row["p"]))
            for row in payload.get("history", [])
        ]

    def get_price_at_or_before(
        self,
        token_id: str,
        target_ts: int,
        lookback_seconds: int = 120,
    ) -> float | None:
        history = self.get_price_history(
            token_id=token_id,
            start_ts=target_ts - lookback_seconds,
            end_ts=target_ts,
        )
        eligible = [point for point in history if point.timestamp <= target_ts]
        if not eligible:
            return None
        return max(eligible, key=lambda point: point.timestamp).price

    def find_live_btc_5m_market(self, now: datetime | None = None) -> Btc5mMarket:
        now = now or datetime.now(timezone.utc)
        start = floor_to_five_minutes(now)
        offsets = (0, -300, 300)
        errors: list[str] = []
        for offset_seconds in offsets:
            candidate = datetime.fromtimestamp(
                int(start.timestamp()) + offset_seconds,
                tz=timezone.utc,
            )
            slug = f"{BTC_5M_SLUG_PREFIX}-{int(candidate.timestamp())}"
            try:
                event = self.get_event_by_slug(slug)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{slug}: {exc}")
                continue

            parsed = self._parse_market(event)
            if parsed.accepting_orders and parsed.end_time > now:
                return parsed

        joined_errors = "; ".join(errors)
        raise LookupError(f"no live BTC 5m market found near {start.isoformat()}; {joined_errors}")

    def quote_for_market(self, market: Btc5mMarket) -> MarketQuote:
        up_book = self.get_order_book(market.up_token_id)
        down_book = self.get_order_book(market.down_token_id)

        up_ask = up_book.best_ask
        down_ask = down_book.best_ask
        if up_ask is None or down_ask is None:
            raise LookupError("missing ask liquidity for one or both outcomes")

        return MarketQuote(
            up_ask=up_ask.price,
            down_ask=down_ask.price,
            up_liquidity_usd=up_ask.price * up_ask.size,
            down_liquidity_usd=down_ask.price * down_ask.size,
        )

    def _parse_market(self, event: dict) -> Btc5mMarket:
        markets: Iterable[dict] = event.get("markets", [])
        market = next(iter(markets), None)
        if market is None:
            raise LookupError("event does not contain a market")

        outcomes = json.loads(market["outcomes"])
        token_ids = json.loads(market["clobTokenIds"])
        token_by_outcome = dict(zip(outcomes, token_ids, strict=True))

        return Btc5mMarket(
            slug=market["slug"],
            title=market["question"],
            condition_id=market["conditionId"],
            end_time=datetime.fromisoformat(market["endDate"].replace("Z", "+00:00")),
            up_token_id=token_by_outcome["Up"],
            down_token_id=token_by_outcome["Down"],
            accepting_orders=bool(market.get("acceptingOrders")),
        )

    def _get_json(self, url: str) -> dict:
        last_error: Exception | None = None
        for attempt in range(3):
            request = Request(url, headers={"User-Agent": "btc5m-bot/0.1"})
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError:
                raise
            except (URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(0.25 * (attempt + 1))
                    continue
                raise
        raise RuntimeError("unreachable") from last_error


def resolved_outcome_from_event(event: dict) -> str | None:
    markets: Iterable[dict] = event.get("markets", [])
    market = next(iter(markets), None)
    if market is None or not market.get("closed"):
        return None

    outcomes = json.loads(market["outcomes"])
    prices = [float(value) for value in json.loads(market["outcomePrices"])]
    if len(outcomes) != len(prices):
        return None

    winners = [outcome for outcome, price in zip(outcomes, prices, strict=True) if price == 1.0]
    return winners[0] if len(winners) == 1 else None
