from __future__ import annotations

import argparse

from .historical import build_recent_historical_dataset
from .learning import chronological_split, train_logistic_regression
from .low_information_research import evaluate_low_information_filters


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=288)
    args = parser.parse_args()

    result = build_recent_historical_dataset(windows=args.windows)
    train_samples, test_samples = chronological_split(result.samples)
    model = train_logistic_regression(train_samples)
    print(evaluate_low_information_filters(train_samples, test_samples, model))


if __name__ == "__main__":
    main()
