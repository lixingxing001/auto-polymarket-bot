from __future__ import annotations

import argparse

from .historical import build_recent_historical_dataset
from .historical import evaluate_market_price_baseline
from .learning import (
    chronological_split,
    evaluate_model,
    FEATURE_NAMES,
    train_logistic_regression,
    threshold_sweep,
    walk_forward_evaluate,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=288)
    parser.add_argument("--decision-offset-seconds", type=int, default=60)
    parser.add_argument("--walk-forward-min-train", type=int, default=200)
    parser.add_argument("--walk-forward-test-size", type=int, default=50)
    args = parser.parse_args()

    result = build_recent_historical_dataset(
        windows=args.windows,
        decision_offset_seconds=args.decision_offset_seconds,
    )
    train_samples, test_samples = chronological_split(result.samples)
    model = train_logistic_regression(train_samples)

    print(
        {
            "written": len(result.samples),
            "market_price_baseline": evaluate_market_price_baseline(result.samples),
            "train": evaluate_model(model, train_samples, confidence_threshold=0.6),
            "test": evaluate_model(model, test_samples, confidence_threshold=0.6),
            "test_threshold_sweep": threshold_sweep(model, test_samples),
            "weights": dict(zip(FEATURE_NAMES, model.weights, strict=True)),
            "walk_forward_0_65": walk_forward_evaluate(
                result.samples,
                min_train_size=args.walk_forward_min_train,
                test_size=args.walk_forward_test_size,
                confidence_threshold=0.65,
            )
            if len(result.samples) >= args.walk_forward_min_train + args.walk_forward_test_size
            else None,
        }
    )


if __name__ == "__main__":
    main()
