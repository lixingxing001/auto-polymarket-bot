from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .coinbase import CoinbaseExchangeClient, build_historical_price_only_features
from .models import FeatureVector
from .polymarket import PolymarketPublicClient, floor_to_five_minutes, resolved_outcome_from_event
from .strategy import BaselineSignalModel


@dataclass(frozen=True)
class HistoricalSample:
    window_start: datetime
    window_end: datetime
    slug: str
    condition_id: str
    label: str
    prob_up: float
    features: FeatureVector
    polymarket_up_price: float
    polymarket_down_price: float


@dataclass(frozen=True)
class DatasetBuildResult:
    samples: tuple[HistoricalSample, ...]
    skipped_missing_market: int
    skipped_unresolved: int
    skipped_missing_candles: int


def build_recent_historical_dataset(
    windows: int,
    decision_offset_seconds: int = 60,
    now: datetime | None = None,
    polymarket: PolymarketPublicClient | None = None,
    coinbase: CoinbaseExchangeClient | None = None,
    max_workers: int = 6,
    cache_path: Path | None = Path("data/historical_dataset_cache.csv"),
) -> DatasetBuildResult:
    if windows <= 0:
        raise ValueError("windows must be positive")
    if decision_offset_seconds <= 0 or decision_offset_seconds >= 300:
        raise ValueError("decision_offset_seconds must be between 1 and 299")

    now = now or datetime.now(timezone.utc)
    polymarket = polymarket or PolymarketPublicClient()
    coinbase = coinbase or CoinbaseExchangeClient()

    last_closed_start = floor_to_five_minutes(now) - timedelta(minutes=5)
    starts = [
        last_closed_start - timedelta(minutes=5 * offset)
        for offset in reversed(range(windows))
    ]
    cached_samples = _read_cached_samples(cache_path) if cache_path is not None else {}
    requested_slugs = {f"btc-updown-5m-{int(start.timestamp())}" for start in starts}
    reused = [cached_samples[slug] for slug in requested_slugs if slug in cached_samples]
    missing_starts = [
        start
        for start in starts
        if f"btc-updown-5m-{int(start.timestamp())}" not in cached_samples
    ]

    if not missing_starts:
        ordered = tuple(cached_samples[f"btc-updown-5m-{int(start.timestamp())}"] for start in starts)
        return DatasetBuildResult(
            samples=ordered,
            skipped_missing_market=0,
            skipped_unresolved=0,
            skipped_missing_candles=0,
        )

    candle_start = missing_starts[0] - timedelta(minutes=5)
    candle_end = missing_starts[-1] + timedelta(minutes=2)
    candles = coinbase.get_minute_candles_range(start=candle_start, end=candle_end)

    model = BaselineSignalModel()
    samples: list[HistoricalSample] = []
    skipped_missing_market = 0
    skipped_unresolved = 0
    skipped_missing_candles = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        events = list(executor.map(_fetch_event_for_start, [(polymarket, start) for start in missing_starts]))

    price_contexts = [
        _build_price_context_args(polymarket, window_start, event, decision_offset_seconds)
        if event is not None
        else None
        for window_start, event in zip(missing_starts, events, strict=True)
    ]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        price_results = list(
            executor.map(
                _fetch_price_context,
                [context for context in price_contexts if context is not None],
            )
        )
    price_iter = iter(price_results)

    for window_start, event, context in zip(missing_starts, events, price_contexts, strict=True):
        slug = f"btc-updown-5m-{int(window_start.timestamp())}"
        if event is None:
            skipped_missing_market += 1
            continue

        label = resolved_outcome_from_event(event)
        if label is None:
            skipped_unresolved += 1
            continue
        market_payload = event["markets"][0]

        window_end = window_start + timedelta(minutes=5)
        decision_time = window_start + timedelta(seconds=decision_offset_seconds)
        try:
            features = build_historical_price_only_features(
                candles=candles,
                window_start=window_start,
                window_end=window_end,
                decision_time=decision_time,
            )
        except ValueError:
            skipped_missing_candles += 1
            continue

        market, up_price, down_price = next(price_iter)
        if up_price is None or down_price is None:
            skipped_missing_candles += 1
            continue

        features = FeatureVector(
            **{
                **features.__dict__,
                "polymarket_up_price": up_price,
                "polymarket_down_price": down_price,
                "polymarket_prob_gap": up_price - down_price,
            }
        )
        forecast = model.predict(features)
        samples.append(
            HistoricalSample(
                window_start=window_start,
                window_end=window_end,
                slug=slug,
                condition_id=market_payload["conditionId"],
                label=label,
                prob_up=forecast.prob_up,
                features=features,
                polymarket_up_price=up_price,
                polymarket_down_price=down_price,
            )
        )

    all_samples = tuple(sorted([*reused, *samples], key=lambda sample: sample.window_start))
    if cache_path is not None:
        _write_cached_samples(cache_path, all_samples)

    return DatasetBuildResult(
        samples=all_samples,
        skipped_missing_market=skipped_missing_market,
        skipped_unresolved=skipped_unresolved,
        skipped_missing_candles=skipped_missing_candles,
    )


def _fetch_event_for_start(args: tuple[PolymarketPublicClient, datetime]) -> dict | None:
    polymarket, start = args
    slug = f"btc-updown-5m-{int(start.timestamp())}"
    try:
        return polymarket.get_event_by_slug(slug)
    except Exception:  # noqa: BLE001
        return None


def _build_price_context_args(
    polymarket: PolymarketPublicClient,
    window_start: datetime,
    event: dict,
    decision_offset_seconds: int,
) -> tuple[PolymarketPublicClient, datetime, dict, int]:
    return polymarket, window_start, event, decision_offset_seconds


def _fetch_price_context(
    args: tuple[PolymarketPublicClient, datetime, dict, int]
) -> tuple[object, float | None, float | None]:
    polymarket, window_start, event, decision_offset_seconds = args
    market = polymarket._parse_market(event)
    decision_ts = int((window_start + timedelta(seconds=decision_offset_seconds)).timestamp())
    try:
        return (
            market,
            polymarket.get_price_at_or_before(market.up_token_id, decision_ts),
            polymarket.get_price_at_or_before(market.down_token_id, decision_ts),
        )
    except Exception:  # noqa: BLE001
        return market, None, None


def _read_cached_samples(path: Path) -> dict[str, HistoricalSample]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    samples: dict[str, HistoricalSample] = {}
    feature_fields = set(FeatureVector.__dataclass_fields__.keys())
    for row in rows:
        features = FeatureVector(
            **{
                field: float(row[field])
                for field in feature_fields
                if field in row and row[field] != ""
            }
        )
        sample = HistoricalSample(
            window_start=datetime.fromisoformat(row["window_start"]),
            window_end=datetime.fromisoformat(row["window_end"]),
            slug=row["slug"],
            condition_id=row["condition_id"],
            label=row["label"],
            prob_up=float(row["prob_up"]),
            features=features,
            polymarket_up_price=float(row["polymarket_up_price"]),
            polymarket_down_price=float(row["polymarket_down_price"]),
        )
        samples[sample.slug] = sample
    return samples


def _write_cached_samples(path: Path, samples: tuple[HistoricalSample, ...]) -> None:
    write_dataset_csv(path, samples)


def write_dataset_csv(path: Path, samples: tuple[HistoricalSample, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "window_start",
        "window_end",
        "slug",
        "condition_id",
        "label",
        "prob_up",
        "polymarket_up_price",
        "polymarket_down_price",
        "return_1m",
        "return_5m",
        "realized_vol_5m",
        "trade_imbalance_30s",
        "distance_to_barrier_bps",
        "seconds_to_close",
        "return_2m",
        "return_3m",
        "body_1m_bps",
        "range_1m_bps",
        "range_5m_bps",
        "volume_ratio_1m_vs_5m",
        "coinbase_spread_bps",
        "book_imbalance_l1",
        "polymarket_prob_gap",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for sample in samples:
            writer.writerow(
                {
                    "window_start": sample.window_start.isoformat(),
                    "window_end": sample.window_end.isoformat(),
                    "slug": sample.slug,
                    "condition_id": sample.condition_id,
                    "label": sample.label,
                    "prob_up": round(sample.prob_up, 8),
                    "polymarket_up_price": sample.polymarket_up_price,
                    "polymarket_down_price": sample.polymarket_down_price,
                    **asdict(sample.features),
                }
            )


def evaluate_directional_baseline(samples: tuple[HistoricalSample, ...]) -> dict:
    if not samples:
        raise ValueError("samples cannot be empty")

    y_true = [1 if sample.label == "Up" else 0 for sample in samples]
    probs = [sample.prob_up for sample in samples]
    y_pred = [1 if prob >= 0.5 else 0 for prob in probs]

    correct = sum(int(actual == predicted) for actual, predicted in zip(y_true, y_pred, strict=True))
    brier = sum((prob - actual) ** 2 for prob, actual in zip(probs, y_true, strict=True)) / len(samples)
    positives = sum(y_true)
    negatives = len(samples) - positives
    true_positive = sum(int(actual == 1 and predicted == 1) for actual, predicted in zip(y_true, y_pred, strict=True))
    true_negative = sum(int(actual == 0 and predicted == 0) for actual, predicted in zip(y_true, y_pred, strict=True))
    false_positive = sum(int(actual == 0 and predicted == 1) for actual, predicted in zip(y_true, y_pred, strict=True))
    false_negative = sum(int(actual == 1 and predicted == 0) for actual, predicted in zip(y_true, y_pred, strict=True))
    majority_accuracy = max(positives, negatives) / len(samples)

    return {
        "samples": len(samples),
        "accuracy": correct / len(samples),
        "majority_accuracy": majority_accuracy,
        "lift_vs_majority": correct / len(samples) - majority_accuracy,
        "brier_score": brier,
        "up_rate": positives / len(samples),
        "down_rate": negatives / len(samples),
        "confusion": {
            "tp": true_positive,
            "tn": true_negative,
            "fp": false_positive,
            "fn": false_negative,
        },
    }


def evaluate_market_price_baseline(samples: tuple[HistoricalSample, ...]) -> dict:
    if not samples:
        raise ValueError("samples cannot be empty")

    y_true = [1 if sample.label == "Up" else 0 for sample in samples]
    y_pred = [
        1 if sample.polymarket_up_price >= sample.polymarket_down_price else 0
        for sample in samples
    ]
    correct = sum(int(actual == predicted) for actual, predicted in zip(y_true, y_pred, strict=True))
    return {
        "samples": len(samples),
        "accuracy": correct / len(samples),
    }
