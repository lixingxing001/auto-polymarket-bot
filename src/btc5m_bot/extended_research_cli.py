from __future__ import annotations

import argparse

from .historical import build_recent_historical_dataset, evaluate_market_price_baseline
from .learning import (
    chronological_split,
    evaluate_model,
    train_logistic_regression,
    walk_forward_evaluate,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=576)
    parser.add_argument("--walk-forward-min-train", type=int, default=250)
    parser.add_argument("--walk-forward-test-size", type=int, default=75)
    args = parser.parse_args()

    result = build_recent_historical_dataset(windows=args.windows)
    train_samples, test_samples = chronological_split(result.samples)
    model = train_logistic_regression(train_samples)
    print(
        {
            "samples": len(result.samples),
            "market_price_baseline": evaluate_market_price_baseline(result.samples),
            "test_0_65": evaluate_model(model, test_samples, confidence_threshold=0.65),
            "walk_forward_0_65": walk_forward_evaluate(
                result.samples,
                min_train_size=args.walk_forward_min_train,
                test_size=args.walk_forward_test_size,
                confidence_threshold=0.65,
            ),
        }
    )


if __name__ == "__main__":
    main()
