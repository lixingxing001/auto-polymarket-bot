from __future__ import annotations

from dataclasses import dataclass

from .historical import HistoricalSample
from .learning import chronological_split


@dataclass(frozen=True)
class SnapshotCoverage:
    dataset_windows: int
    train_windows: int
    test_windows: int
    recorded_windows: int
    matched_dataset_windows: int
    matched_train_windows: int
    matched_test_windows: int
    unmatched_recorded_windows: int

    def as_dict(self, min_test_windows: int) -> dict:
        return {
            "dataset_windows": self.dataset_windows,
            "train_windows": self.train_windows,
            "test_windows": self.test_windows,
            "recorded_windows": self.recorded_windows,
            "matched_dataset_windows": self.matched_dataset_windows,
            "matched_train_windows": self.matched_train_windows,
            "matched_test_windows": self.matched_test_windows,
            "unmatched_recorded_windows": self.unmatched_recorded_windows,
            "ready_for_snapshot_backtest": self.matched_test_windows >= min_test_windows,
            "min_test_windows": min_test_windows,
        }


def compute_snapshot_coverage(
    samples: tuple[HistoricalSample, ...],
    recorded_slugs: set[str],
) -> SnapshotCoverage:
    train_samples, test_samples = chronological_split(samples)
    dataset_slugs = {sample.slug for sample in samples}
    train_slugs = {sample.slug for sample in train_samples}
    test_slugs = {sample.slug for sample in test_samples}
    return SnapshotCoverage(
        dataset_windows=len(dataset_slugs),
        train_windows=len(train_slugs),
        test_windows=len(test_slugs),
        recorded_windows=len(recorded_slugs),
        matched_dataset_windows=len(dataset_slugs & recorded_slugs),
        matched_train_windows=len(train_slugs & recorded_slugs),
        matched_test_windows=len(test_slugs & recorded_slugs),
        unmatched_recorded_windows=len(recorded_slugs - dataset_slugs),
    )
