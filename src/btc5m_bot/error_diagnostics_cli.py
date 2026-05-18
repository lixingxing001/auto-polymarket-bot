from __future__ import annotations

import argparse

from .error_diagnostics import holdout_error_diagnostics
from .historical import build_recent_historical_dataset
from .learning import chronological_split, train_logistic_regression


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=288)
    args = parser.parse_args()

    result = build_recent_historical_dataset(windows=args.windows)
    train_samples, _ = chronological_split(result.samples)
    model = train_logistic_regression(train_samples)
    print(holdout_error_diagnostics(result.samples, model))


if __name__ == "__main__":
    main()
