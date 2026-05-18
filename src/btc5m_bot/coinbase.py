from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import sqrt
from statistics import mean
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import FeatureVector


COINBASE_EXCHANGE_BASE_URL = "https://api.exchange.coinbase.com"


@dataclass(frozen=True)
class Candle:
    start_time: datetime
    low: float
    high: float
    open: float
    close: float
    volume: float


@dataclass(frozen=True)
class Trade:
    time: datetime
    trade_id: int
    price: float
    size: float
    maker_side: str


@dataclass(frozen=True)
class TopOfBook:
    bid_price: float
    bid_size: float
    ask_price: float
    ask_size: float


class CoinbaseExchangeClient:
    def __init__(
        self,
        base_url: str = COINBASE_EXCHANGE_BASE_URL,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def get_recent_minute_candles(
        self,
        product_id: str = "BTC-USD",
        now: datetime | None = None,
        lookback_minutes: int = 12,
    ) -> list[Candle]:
        now = now or datetime.now(timezone.utc)
        start = now - timedelta(minutes=lookback_minutes)
        return self.get_minute_candles_range(
            start=start,
            end=now,
            product_id=product_id,
        )

    def get_minute_candles_range(
        self,
        start: datetime,
        end: datetime,
        product_id: str = "BTC-USD",
    ) -> list[Candle]:
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("start and end must be timezone-aware")
        if end <= start:
            raise ValueError("end must be after start")

        candles: dict[datetime, Candle] = {}
        cursor = start.astimezone(timezone.utc)
        end_utc = end.astimezone(timezone.utc)

        while cursor < end_utc:
            chunk_end = min(cursor + timedelta(minutes=300), end_utc)
            for candle in self._fetch_candles(
                product_id=product_id,
                start=cursor,
                end=chunk_end,
            ):
                candles[candle.start_time] = candle
            cursor = chunk_end

        return sorted(candles.values(), key=lambda candle: candle.start_time)

    def _fetch_candles(
        self,
        product_id: str,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:
        query = urlencode(
            {
                "start": start.isoformat().replace("+00:00", "Z"),
                "end": end.isoformat().replace("+00:00", "Z"),
                "granularity": 60,
            }
        )
        payload = self._get_json(
            f"{self.base_url}/products/{product_id}/candles?{query}"
        )
        candles = [
            Candle(
                start_time=datetime.fromtimestamp(row[0], tz=timezone.utc),
                low=float(row[1]),
                high=float(row[2]),
                open=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]),
            )
            for row in payload
        ]
        return sorted(candles, key=lambda candle: candle.start_time)

    def get_recent_trades(
        self,
        product_id: str = "BTC-USD",
        limit: int = 1000,
    ) -> list[Trade]:
        query = urlencode({"limit": limit})
        payload = self._get_json(f"{self.base_url}/products/{product_id}/trades?{query}")
        trades = [
            Trade(
                time=datetime.fromisoformat(row["time"].replace("Z", "+00:00")),
                trade_id=int(row["trade_id"]),
                price=float(row["price"]),
                size=float(row["size"]),
                maker_side=row["side"],
            )
            for row in payload
        ]
        return sorted(trades, key=lambda trade: trade.time)

    def get_top_of_book(self, product_id: str = "BTC-USD") -> TopOfBook:
        payload = self._get_json(f"{self.base_url}/products/{product_id}/book?level=1")
        best_bid = payload["bids"][0]
        best_ask = payload["asks"][0]
        return TopOfBook(
            bid_price=float(best_bid[0]),
            bid_size=float(best_bid[1]),
            ask_price=float(best_ask[0]),
            ask_size=float(best_ask[1]),
        )

    def _get_json(self, url: str) -> list:
        request = Request(url, headers={"User-Agent": "btc5m-bot/0.1"})
        with urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


def build_price_only_features(
    candles: list[Candle],
    window_start: datetime,
    window_end: datetime,
    now: datetime | None = None,
) -> FeatureVector:
    if len(candles) < 6:
        raise ValueError("need at least 6 one-minute candles")

    now = now or datetime.now(timezone.utc)
    latest = candles[-1]
    previous = candles[-2]
    two_minutes_ago = candles[-3]
    three_minutes_ago = candles[-4]
    five_minutes_ago = candles[-6]
    one_minute_returns = [
        candles[index].close / candles[index - 1].close - 1.0
        for index in range(len(candles) - 5, len(candles))
    ]

    opening_candle = next(
        (candle for candle in candles if candle.start_time >= window_start),
        None,
    )
    if opening_candle is None:
        raise ValueError("missing candle for current market window")

    return_1m = latest.close / previous.close - 1.0
    return_2m = latest.close / two_minutes_ago.close - 1.0
    return_3m = latest.close / three_minutes_ago.close - 1.0
    return_5m = latest.close / five_minutes_ago.close - 1.0
    avg = mean(one_minute_returns)
    realized_vol_5m = sqrt(
        sum((value - avg) ** 2 for value in one_minute_returns)
        / len(one_minute_returns)
    )
    distance_to_barrier_bps = (latest.close / opening_candle.open - 1.0) * 10_000
    seconds_to_close = max(0, int((window_end - now).total_seconds()))
    recent = candles[-5:]
    avg_volume_5m = sum(candle.volume for candle in recent) / len(recent)
    min_recent_low = min(candle.low for candle in recent)

    return FeatureVector(
        return_1m=return_1m,
        return_5m=return_5m,
        realized_vol_5m=realized_vol_5m,
        trade_imbalance_30s=0.0,
        distance_to_barrier_bps=distance_to_barrier_bps,
        seconds_to_close=seconds_to_close,
        return_2m=return_2m,
        return_3m=return_3m,
        body_1m_bps=(latest.close / latest.open - 1.0) * 10_000,
        range_1m_bps=(latest.high / latest.low - 1.0) * 10_000 if latest.low else 0.0,
        range_5m_bps=(max(candle.high for candle in recent) / min_recent_low - 1.0) * 10_000
        if min_recent_low
        else 0.0,
        volume_ratio_1m_vs_5m=latest.volume / avg_volume_5m if avg_volume_5m else 0.0,
    )


def enrich_with_live_microstructure(
    features: FeatureVector,
    trades: list[Trade],
    top_of_book: TopOfBook,
    now: datetime | None = None,
    lookback_seconds: int = 30,
) -> FeatureVector:
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=lookback_seconds)
    recent_trades = [trade for trade in trades if trade.time >= cutoff]

    up_volume = sum(trade.size for trade in recent_trades if trade.maker_side == "sell")
    down_volume = sum(trade.size for trade in recent_trades if trade.maker_side == "buy")
    total_volume = up_volume + down_volume
    trade_imbalance = (up_volume - down_volume) / total_volume if total_volume else 0.0

    mid = (top_of_book.bid_price + top_of_book.ask_price) / 2
    spread_bps = ((top_of_book.ask_price - top_of_book.bid_price) / mid) * 10_000 if mid else 0.0
    total_size = top_of_book.bid_size + top_of_book.ask_size
    book_imbalance = (
        (top_of_book.bid_size - top_of_book.ask_size) / total_size if total_size else 0.0
    )

    return FeatureVector(
        **{
            **features.__dict__,
            "trade_imbalance_30s": trade_imbalance,
            "coinbase_spread_bps": spread_bps,
            "book_imbalance_l1": book_imbalance,
        }
    )


def build_historical_price_only_features(
    candles: list[Candle],
    window_start: datetime,
    window_end: datetime,
    decision_time: datetime,
) -> FeatureVector:
    if decision_time.tzinfo is None:
        raise ValueError("decision_time must be timezone-aware")

    eligible = [candle for candle in candles if candle.start_time < decision_time]
    if len(eligible) < 6:
        raise ValueError("need at least 6 completed one-minute candles")

    latest = eligible[-1]
    previous = eligible[-2]
    two_minutes_ago = eligible[-3]
    three_minutes_ago = eligible[-4]
    five_minutes_ago = eligible[-6]
    trailing = eligible[-6:]
    one_minute_returns = [
        trailing[index].close / trailing[index - 1].close - 1.0
        for index in range(1, len(trailing))
    ]

    opening_candle = next(
        (candle for candle in eligible if candle.start_time == window_start),
        None,
    )
    if opening_candle is None:
        raise ValueError("missing completed opening candle for current market window")

    avg = mean(one_minute_returns)
    realized_vol_5m = sqrt(
        sum((value - avg) ** 2 for value in one_minute_returns)
        / len(one_minute_returns)
    )
    recent = trailing[-5:]
    min_recent_low = min(candle.low for candle in recent)
    avg_volume_5m = sum(candle.volume for candle in recent) / len(recent)

    return FeatureVector(
        return_1m=latest.close / previous.close - 1.0,
        return_5m=latest.close / five_minutes_ago.close - 1.0,
        realized_vol_5m=realized_vol_5m,
        trade_imbalance_30s=0.0,
        distance_to_barrier_bps=(latest.close / opening_candle.open - 1.0) * 10_000,
        seconds_to_close=max(0, int((window_end - decision_time).total_seconds())),
        return_2m=latest.close / two_minutes_ago.close - 1.0,
        return_3m=latest.close / three_minutes_ago.close - 1.0,
        body_1m_bps=(latest.close / latest.open - 1.0) * 10_000,
        range_1m_bps=(latest.high / latest.low - 1.0) * 10_000 if latest.low else 0.0,
        range_5m_bps=(max(candle.high for candle in recent) / min_recent_low - 1.0) * 10_000
        if min_recent_low
        else 0.0,
        volume_ratio_1m_vs_5m=latest.volume / avg_volume_5m
        if avg_volume_5m
        else 0.0,
    )
