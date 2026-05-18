from __future__ import annotations

from dataclasses import dataclass
from math import exp, log
from statistics import mean, pstdev

from .historical import HistoricalSample


FEATURE_NAMES = (
    "polymarket_up_price",
    "polymarket_down_price",
    "polymarket_prob_gap",
    "return_1m",
    "return_2m",
    "return_3m",
    "return_5m",
    "realized_vol_5m",
    "distance_to_barrier_bps",
    "body_1m_bps",
    "range_1m_bps",
    "range_5m_bps",
    "volume_ratio_1m_vs_5m",
)


@dataclass(frozen=True)
class Standardizer:
    means: tuple[float, ...]
    scales: tuple[float, ...]

    def transform_one(self, values: tuple[float, ...]) -> tuple[float, ...]:
        return tuple(
            (value - avg) / scale
            for value, avg, scale in zip(values, self.means, self.scales, strict=True)
        )


@dataclass(frozen=True)
class LogisticModel:
    weights: tuple[float, ...]
    bias: float
    standardizer: Standardizer

    def predict_proba(self, values: tuple[float, ...]) -> float:
        scaled = self.standardizer.transform_one(values)
        score = self.bias + sum(weight * value for weight, value in zip(self.weights, scaled, strict=True))
        return 1.0 / (1.0 + exp(-score))


def sample_to_features(sample: HistoricalSample) -> tuple[float, ...]:
    return tuple(float(getattr(sample.features, name)) for name in FEATURE_NAMES)


def fit_standardizer(samples: tuple[HistoricalSample, ...]) -> Standardizer:
    columns = list(zip(*(sample_to_features(sample) for sample in samples), strict=True))
    means = tuple(mean(column) for column in columns)
    scales = tuple(pstdev(column) or 1.0 for column in columns)
    return Standardizer(means=means, scales=scales)


def train_logistic_regression(
    samples: tuple[HistoricalSample, ...],
    learning_rate: float = 0.05,
    epochs: int = 600,
    l2: float = 0.01,
) -> LogisticModel:
    if len(samples) < 10:
        raise ValueError("need at least 10 samples")

    standardizer = fit_standardizer(samples)
    x_rows = [standardizer.transform_one(sample_to_features(sample)) for sample in samples]
    y_values = [1.0 if sample.label == "Up" else 0.0 for sample in samples]

    weights = [0.0 for _ in FEATURE_NAMES]
    bias = 0.0
    n = len(samples)

    for _ in range(epochs):
        grad_w = [0.0 for _ in FEATURE_NAMES]
        grad_b = 0.0
        for x_row, y_value in zip(x_rows, y_values, strict=True):
            score = bias + sum(weight * value for weight, value in zip(weights, x_row, strict=True))
            prob = 1.0 / (1.0 + exp(-score))
            error = prob - y_value
            for index, value in enumerate(x_row):
                grad_w[index] += error * value
            grad_b += error

        for index in range(len(weights)):
            grad_w[index] = grad_w[index] / n + l2 * weights[index]
            weights[index] -= learning_rate * grad_w[index]
        bias -= learning_rate * (grad_b / n)

    return LogisticModel(weights=tuple(weights), bias=bias, standardizer=standardizer)


def evaluate_model(
    model: LogisticModel,
    samples: tuple[HistoricalSample, ...],
    confidence_threshold: float = 0.0,
) -> dict:
    if not samples:
        raise ValueError("samples cannot be empty")

    probs = [model.predict_proba(sample_to_features(sample)) for sample in samples]
    labels = [1 if sample.label == "Up" else 0 for sample in samples]
    predictions = [1 if prob >= 0.5 else 0 for prob in probs]
    correct = sum(int(pred == actual) for pred, actual in zip(predictions, labels, strict=True))
    log_loss = -sum(
        actual * log(max(prob, 1e-9)) + (1 - actual) * log(max(1 - prob, 1e-9))
        for prob, actual in zip(probs, labels, strict=True)
    ) / len(samples)

    selected = [
        (prob, actual)
        for prob, actual in zip(probs, labels, strict=True)
        if max(prob, 1.0 - prob) >= confidence_threshold
    ]
    selected_correct = sum(
        int((prob >= 0.5) == bool(actual))
        for prob, actual in selected
    )

    return {
        "samples": len(samples),
        "accuracy": correct / len(samples),
        "log_loss": log_loss,
        "selected_samples": len(selected),
        "selected_accuracy": selected_correct / len(selected) if selected else 0.0,
        "coverage": len(selected) / len(samples),
    }


def chronological_split(
    samples: tuple[HistoricalSample, ...],
    train_fraction: float = 0.7,
) -> tuple[tuple[HistoricalSample, ...], tuple[HistoricalSample, ...]]:
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    split_index = int(len(samples) * train_fraction)
    return samples[:split_index], samples[split_index:]


def walk_forward_evaluate(
    samples: tuple[HistoricalSample, ...],
    min_train_size: int,
    test_size: int,
    confidence_threshold: float = 0.65,
) -> dict:
    if min_train_size <= 0 or test_size <= 0:
        raise ValueError("min_train_size and test_size must be positive")
    if len(samples) < min_train_size + test_size:
        raise ValueError("not enough samples for walk-forward evaluation")

    folds: list[dict] = []
    train_end = min_train_size
    while train_end + test_size <= len(samples):
        train_samples = samples[:train_end]
        test_samples = samples[train_end : train_end + test_size]
        model = train_logistic_regression(train_samples)
        folds.append(evaluate_model(model, test_samples, confidence_threshold=confidence_threshold))
        train_end += test_size

    return {
        "folds": len(folds),
        "mean_accuracy": sum(fold["accuracy"] for fold in folds) / len(folds),
        "mean_selected_accuracy": sum(fold["selected_accuracy"] for fold in folds) / len(folds),
        "mean_coverage": sum(fold["coverage"] for fold in folds) / len(folds),
        "details": folds,
    }


def threshold_sweep(
    model: LogisticModel,
    samples: tuple[HistoricalSample, ...],
    thresholds: tuple[float, ...] = (0.55, 0.60, 0.65, 0.70, 0.75, 0.80),
) -> dict[float, dict]:
    return {
        threshold: evaluate_model(model, samples, confidence_threshold=threshold)
        for threshold in thresholds
    }
