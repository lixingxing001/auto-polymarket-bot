from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .error_diagnostics import PredictionRow, build_prediction_rows
from .historical import HistoricalSample
from .learning import LogisticModel


@dataclass(frozen=True)
class LowInformationThresholds:
    abs_return_1m_low: float
    abs_return_1m_high: float
    abs_return_5m_low: float
    abs_return_5m_high: float
    distance_to_barrier_low: float
    distance_to_barrier_high: float


@dataclass(frozen=True)
class LowInformationFilterResult:
    filter_name: str
    kept_samples: int
    removed_samples: int
    coverage: float
    kept_accuracy: float
    removed_accuracy: float
    baseline_accuracy: float
    accuracy_lift: float


def derive_low_information_thresholds(
    train_samples: tuple[HistoricalSample, ...],
) -> LowInformationThresholds:
    return LowInformationThresholds(
        abs_return_1m_low=_tertile(train_samples, lambda sample: abs(sample.features.return_1m), 1),
        abs_return_1m_high=_tertile(train_samples, lambda sample: abs(sample.features.return_1m), 2),
        abs_return_5m_low=_tertile(train_samples, lambda sample: abs(sample.features.return_5m), 1),
        abs_return_5m_high=_tertile(train_samples, lambda sample: abs(sample.features.return_5m), 2),
        distance_to_barrier_low=_tertile(
            train_samples,
            lambda sample: abs(sample.features.distance_to_barrier_bps),
            1,
        ),
        distance_to_barrier_high=_tertile(
            train_samples,
            lambda sample: abs(sample.features.distance_to_barrier_bps),
            2,
        ),
    )


def evaluate_low_information_filters(
    train_samples: tuple[HistoricalSample, ...],
    test_samples: tuple[HistoricalSample, ...],
    model: LogisticModel,
) -> dict:
    thresholds = derive_low_information_thresholds(train_samples)
    rows = build_prediction_rows(model, test_samples)
    baseline_accuracy = _accuracy(rows)
    filters = _build_filters(thresholds)
    results = tuple(
        _evaluate_filter(
            filter_name=name,
            rows=rows,
            should_remove=should_remove,
            baseline_accuracy=baseline_accuracy,
        )
        for name, should_remove in filters
    )
    useful_results = sorted(
        [
            result
            for result in results
            if result.kept_samples >= 10 and result.accuracy_lift > 0
        ],
        key=lambda result: (result.accuracy_lift, result.kept_samples),
        reverse=True,
    )
    return {
        "thresholds": thresholds.__dict__,
        "baseline_accuracy": baseline_accuracy,
        "results": [result.__dict__ for result in results],
        "most_promising": [result.__dict__ for result in useful_results[:5]],
    }


def _build_filters(
    thresholds: LowInformationThresholds,
) -> tuple[tuple[str, Callable[[PredictionRow], bool]], ...]:
    return (
        (
            "remove_low_abs_return_1m",
            lambda row: row.abs_return_1m <= thresholds.abs_return_1m_low,
        ),
        (
            "remove_near_barrier",
            lambda row: row.distance_to_barrier_bps <= thresholds.distance_to_barrier_low,
        ),
        (
            "remove_low_abs_return_1m_and_near_barrier",
            lambda row: (
                row.abs_return_1m <= thresholds.abs_return_1m_low
                and row.distance_to_barrier_bps <= thresholds.distance_to_barrier_low
            ),
        ),
        (
            "remove_mid_abs_return_5m",
            lambda row: (
                thresholds.abs_return_5m_low
                < row.abs_return_5m
                <= thresholds.abs_return_5m_high
            ),
        ),
        (
            "keep_high_abs_return_1m_only",
            lambda row: row.abs_return_1m <= thresholds.abs_return_1m_high,
        ),
        (
            "keep_far_barrier_only",
            lambda row: row.distance_to_barrier_bps <= thresholds.distance_to_barrier_high,
        ),
        (
            "remove_low_momentum_or_near_barrier",
            lambda row: (
                row.abs_return_1m <= thresholds.abs_return_1m_low
                or row.distance_to_barrier_bps <= thresholds.distance_to_barrier_low
            ),
        ),
    )


def _evaluate_filter(
    filter_name: str,
    rows: tuple[PredictionRow, ...],
    should_remove: Callable[[PredictionRow], bool],
    baseline_accuracy: float,
) -> LowInformationFilterResult:
    kept = tuple(row for row in rows if not should_remove(row))
    removed = tuple(row for row in rows if should_remove(row))
    kept_accuracy = _accuracy(kept)
    return LowInformationFilterResult(
        filter_name=filter_name,
        kept_samples=len(kept),
        removed_samples=len(removed),
        coverage=len(kept) / len(rows) if rows else 0.0,
        kept_accuracy=kept_accuracy,
        removed_accuracy=_accuracy(removed),
        baseline_accuracy=baseline_accuracy,
        accuracy_lift=kept_accuracy - baseline_accuracy,
    )


def _accuracy(rows: tuple[PredictionRow, ...]) -> float:
    return sum(1 for row in rows if row.correct) / len(rows) if rows else 0.0


def _tertile(
    samples: tuple[HistoricalSample, ...],
    value_fn: Callable[[HistoricalSample], float],
    index: int,
) -> float:
    values = sorted(value_fn(sample) for sample in samples)
    if not values:
        raise ValueError("samples cannot be empty")
    return values[(len(values) * index) // 3]
