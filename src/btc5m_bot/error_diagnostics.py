from __future__ import annotations

from dataclasses import dataclass

from .historical import HistoricalSample
from .learning import LogisticModel, chronological_split, sample_to_features


@dataclass(frozen=True)
class PredictionRow:
    slug: str
    actual: int
    predicted: int
    prob_up: float
    confidence: float
    correct: bool
    polymarket_price_confidence: float
    prob_gap: float
    abs_return_1m: float
    abs_return_5m: float
    realized_vol_5m: float
    range_5m_bps: float
    distance_to_barrier_bps: float
    market_agrees_with_model: bool


def build_prediction_rows(
    model: LogisticModel,
    samples: tuple[HistoricalSample, ...],
) -> tuple[PredictionRow, ...]:
    rows: list[PredictionRow] = []
    for sample in samples:
        prob_up = model.predict_proba(sample_to_features(sample))
        actual = 1 if sample.label == "Up" else 0
        predicted = 1 if prob_up >= 0.5 else 0
        market_predicted = 1 if sample.polymarket_up_price >= sample.polymarket_down_price else 0
        rows.append(
            PredictionRow(
                slug=sample.slug,
                actual=actual,
                predicted=predicted,
                prob_up=prob_up,
                confidence=max(prob_up, 1.0 - prob_up),
                correct=actual == predicted,
                polymarket_price_confidence=max(
                    sample.polymarket_up_price,
                    sample.polymarket_down_price,
                ),
                prob_gap=sample.features.polymarket_prob_gap,
                abs_return_1m=abs(sample.features.return_1m),
                abs_return_5m=abs(sample.features.return_5m),
                realized_vol_5m=sample.features.realized_vol_5m,
                range_5m_bps=sample.features.range_5m_bps,
                distance_to_barrier_bps=abs(sample.features.distance_to_barrier_bps),
                market_agrees_with_model=market_predicted == predicted,
            )
        )
    return tuple(rows)


def diagnose_error_slices(
    rows: tuple[PredictionRow, ...],
) -> dict[str, list[dict]]:
    return {
        "model_confidence": _bucketize(
            rows,
            value_fn=lambda row: row.confidence,
            buckets=(
                ("0.50-0.60", 0.50, 0.60),
                ("0.60-0.70", 0.60, 0.70),
                ("0.70-0.80", 0.70, 0.80),
                ("0.80-1.00", 0.80, 1.01),
            ),
        ),
        "market_price_confidence": _bucketize(
            rows,
            value_fn=lambda row: row.polymarket_price_confidence,
            buckets=(
                ("0.50-0.60", 0.50, 0.60),
                ("0.60-0.70", 0.60, 0.70),
                ("0.70-0.80", 0.70, 0.80),
                ("0.80-1.00", 0.80, 1.01),
            ),
        ),
        "market_alignment": [
            _summarize_subset(
                "agree",
                tuple(row for row in rows if row.market_agrees_with_model),
            ),
            _summarize_subset(
                "disagree",
                tuple(row for row in rows if not row.market_agrees_with_model),
            ),
        ],
        "abs_return_1m": _quantile_slices(
            rows,
            value_fn=lambda row: row.abs_return_1m,
        ),
        "abs_return_5m": _quantile_slices(
            rows,
            value_fn=lambda row: row.abs_return_5m,
        ),
        "realized_vol_5m": _quantile_slices(
            rows,
            value_fn=lambda row: row.realized_vol_5m,
        ),
        "range_5m_bps": _quantile_slices(
            rows,
            value_fn=lambda row: row.range_5m_bps,
        ),
        "distance_to_barrier_bps": _quantile_slices(
            rows,
            value_fn=lambda row: row.distance_to_barrier_bps,
        ),
    }


def holdout_error_diagnostics(
    samples: tuple[HistoricalSample, ...],
    model: LogisticModel,
) -> dict:
    _, test_samples = chronological_split(samples)
    rows = build_prediction_rows(model, test_samples)
    wrong_rows = tuple(row for row in rows if not row.correct)
    return {
        "samples": len(rows),
        "correct": sum(1 for row in rows if row.correct),
        "incorrect": len(wrong_rows),
        "accuracy": sum(1 for row in rows if row.correct) / len(rows) if rows else 0.0,
        "slices": diagnose_error_slices(rows),
        "worst_slices": find_worst_slices(diagnose_error_slices(rows)),
    }


def find_worst_slices(
    slices: dict[str, list[dict]],
    min_samples: int = 8,
    limit: int = 8,
) -> list[dict]:
    flattened: list[dict] = []
    for dimension, entries in slices.items():
        for entry in entries:
            if entry["samples"] < min_samples:
                continue
            flattened.append({"dimension": dimension, **entry})
    return sorted(flattened, key=lambda entry: (entry["accuracy"], -entry["samples"]))[:limit]


def _bucketize(rows, value_fn, buckets):
    return [
        _summarize_subset(
            label,
            tuple(
                row
                for row in rows
                if lower <= value_fn(row) < upper
            ),
        )
        for label, lower, upper in buckets
    ]


def _quantile_slices(rows, value_fn):
    ordered_values = sorted(value_fn(row) for row in rows)
    if not ordered_values:
        return []
    q1 = ordered_values[len(ordered_values) // 3]
    q2 = ordered_values[(2 * len(ordered_values)) // 3]
    return [
        _summarize_subset("low", tuple(row for row in rows if value_fn(row) <= q1)),
        _summarize_subset("mid", tuple(row for row in rows if q1 < value_fn(row) <= q2)),
        _summarize_subset("high", tuple(row for row in rows if value_fn(row) > q2)),
    ]


def _summarize_subset(label: str, rows: tuple[PredictionRow, ...]) -> dict:
    correct = sum(1 for row in rows if row.correct)
    return {
        "bucket": label,
        "samples": len(rows),
        "accuracy": correct / len(rows) if rows else 0.0,
        "error_rate": 1.0 - (correct / len(rows)) if rows else 0.0,
        "avg_confidence": (
            sum(row.confidence for row in rows) / len(rows)
            if rows
            else 0.0
        ),
    }
