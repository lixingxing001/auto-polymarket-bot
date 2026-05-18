from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .execution_backtest import ExecutionBacktestConfig
from .historical import HistoricalSample
from .learning import sample_to_features, train_logistic_regression
from .settled_snapshot_archive import SettledSnapshotWindow
from .snapshot_backtest import SnapshotQuote, backtest_sample_with_snapshot, find_snapshot_at_or_after
from .strategy_guardrails import ACTIVE_STRATEGY_PARAMETERS


@dataclass(frozen=True)
class CandidateStrategy:
    candidate_id: str
    description: str
    rationale: str
    registered_at: datetime
    eligible_after_market_end_time: datetime
    min_confidence: float
    min_edge: float
    stake_usd: float
    max_fill_delay_seconds: int
    filter_kind: str = "none"
    min_abs_return_1m: float | None = None
    min_abs_return_5m: float | None = None
    max_abs_return_5m: float | None = None
    min_abs_distance_to_barrier_bps: float | None = None
    status: str = "registered"

    def to_config(self) -> ExecutionBacktestConfig:
        return ExecutionBacktestConfig(
            min_confidence=self.min_confidence,
            min_edge=self.min_edge,
            stake_usd=self.stake_usd,
            max_fill_delay_seconds=self.max_fill_delay_seconds,
        )


@dataclass(frozen=True)
class CandidateComparisonRow:
    slug: str
    market_end_time: datetime
    label: str
    forecast_prob_up: float
    active_decision: str
    active_reason: str
    active_pnl_usd: float | None
    candidate_decision: str
    candidate_reason: str
    candidate_pnl_usd: float | None
    delta_pnl_usd: float


def load_candidate_registry(path: Path) -> dict[str, CandidateStrategy]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {
        row["candidate_id"]: CandidateStrategy(
            candidate_id=row["candidate_id"],
            description=row["description"],
            rationale=row["rationale"],
            registered_at=datetime.fromisoformat(row["registered_at"]),
            eligible_after_market_end_time=datetime.fromisoformat(
                row["eligible_after_market_end_time"]
            ),
            min_confidence=float(row["min_confidence"]),
            min_edge=float(row["min_edge"]),
            stake_usd=float(row["stake_usd"]),
            max_fill_delay_seconds=int(row["max_fill_delay_seconds"]),
            filter_kind=row.get("filter_kind", "none") or "none",
            min_abs_return_1m=_optional_float(row.get("min_abs_return_1m", "")),
            min_abs_return_5m=_optional_float(row.get("min_abs_return_5m", "")),
            max_abs_return_5m=_optional_float(row.get("max_abs_return_5m", "")),
            min_abs_distance_to_barrier_bps=_optional_float(
                row.get("min_abs_distance_to_barrier_bps", "")
            ),
            status=row["status"],
        )
        for row in rows
    }


def register_candidate(
    path: Path,
    candidate_id: str,
    description: str,
    rationale: str,
    eligible_after_market_end_time: datetime,
    min_confidence: float,
    min_edge: float,
    stake_usd: float,
    max_fill_delay_seconds: int,
    filter_kind: str = "none",
    min_abs_return_1m: float | None = None,
    min_abs_return_5m: float | None = None,
    max_abs_return_5m: float | None = None,
    min_abs_distance_to_barrier_bps: float | None = None,
    registered_at: datetime | None = None,
) -> CandidateStrategy:
    registry = load_candidate_registry(path)
    if candidate_id in registry:
        raise ValueError(f"candidate already exists: {candidate_id}")

    registered_at = registered_at or datetime.now(timezone.utc)
    candidate = CandidateStrategy(
        candidate_id=candidate_id,
        description=description,
        rationale=rationale,
        registered_at=registered_at,
        eligible_after_market_end_time=eligible_after_market_end_time,
        min_confidence=min_confidence,
        min_edge=min_edge,
        stake_usd=stake_usd,
        max_fill_delay_seconds=max_fill_delay_seconds,
        filter_kind=filter_kind,
        min_abs_return_1m=min_abs_return_1m,
        min_abs_return_5m=min_abs_return_5m,
        max_abs_return_5m=max_abs_return_5m,
        min_abs_distance_to_barrier_bps=min_abs_distance_to_barrier_bps,
    )
    write_candidate_registry(path, tuple([*registry.values(), candidate]))
    return candidate


def write_candidate_registry(path: Path, candidates: tuple[CandidateStrategy, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(CandidateStrategy.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in sorted(candidates, key=lambda item: item.candidate_id):
            writer.writerow(
                {
                    **candidate.__dict__,
                    "registered_at": candidate.registered_at.isoformat(),
                    "eligible_after_market_end_time": candidate.eligible_after_market_end_time.isoformat(),
                    "min_abs_return_1m": (
                        candidate.min_abs_return_1m
                        if candidate.min_abs_return_1m is not None
                        else ""
                    ),
                    "min_abs_return_5m": (
                        candidate.min_abs_return_5m
                        if candidate.min_abs_return_5m is not None
                        else ""
                    ),
                    "max_abs_return_5m": (
                        candidate.max_abs_return_5m
                        if candidate.max_abs_return_5m is not None
                        else ""
                    ),
                    "min_abs_distance_to_barrier_bps": (
                        candidate.min_abs_distance_to_barrier_bps
                        if candidate.min_abs_distance_to_barrier_bps is not None
                        else ""
                    ),
                }
            )


def compare_candidate_strategy(
    candidate: CandidateStrategy,
    archived_windows: tuple[SettledSnapshotWindow, ...],
    samples: tuple[HistoricalSample, ...],
    snapshots: dict[str, list[SnapshotQuote]],
    min_train_size: int = 200,
) -> tuple[CandidateComparisonRow, ...]:
    active_config = ExecutionBacktestConfig(
        min_confidence=ACTIVE_STRATEGY_PARAMETERS.min_confidence,
        min_edge=ACTIVE_STRATEGY_PARAMETERS.min_edge,
        stake_usd=ACTIVE_STRATEGY_PARAMETERS.stake_usd,
        max_fill_delay_seconds=ACTIVE_STRATEGY_PARAMETERS.max_fill_delay_seconds,
    )
    candidate_config = candidate.to_config()
    samples_by_slug = {sample.slug: sample for sample in samples}
    ordered_samples = tuple(sorted(samples, key=lambda sample: sample.window_start))
    rows: list[CandidateComparisonRow] = []

    eligible_windows = [
        window
        for window in archived_windows
        if window.market_end_time > candidate.eligible_after_market_end_time
    ]
    for window in sorted(eligible_windows, key=lambda item: item.market_end_time):
        sample = samples_by_slug.get(window.slug)
        if sample is None:
            continue
        prior_samples = tuple(
            prior
            for prior in ordered_samples
            if prior.window_start < sample.window_start
        )
        if len(prior_samples) < min_train_size:
            continue
        model = train_logistic_regression(prior_samples)
        forecast_prob_up = model.predict_proba(sample_to_features(sample))
        decision_time = sample.window_start + timedelta(seconds=60)
        quote = find_snapshot_at_or_after(
            snapshots.get(sample.slug, []),
            decision_time=decision_time,
            max_delay_seconds=max(
                active_config.max_fill_delay_seconds,
                candidate_config.max_fill_delay_seconds,
            ),
        )
        active_trade, active_reason = backtest_sample_with_snapshot(
            sample=sample,
            quote=quote,
            forecast_prob_up=forecast_prob_up,
            config=active_config,
        )
        candidate_trade, candidate_reason = backtest_sample_with_snapshot(
            sample=sample,
            quote=quote,
            forecast_prob_up=forecast_prob_up,
            config=candidate_config,
        )
        if not candidate_allows_sample(candidate, sample):
            candidate_trade = None
            candidate_reason = "candidate_filter"
        active_pnl = active_trade.pnl_usd if active_trade is not None else None
        candidate_pnl = candidate_trade.pnl_usd if candidate_trade is not None else None
        rows.append(
            CandidateComparisonRow(
                slug=sample.slug,
                market_end_time=window.market_end_time,
                label=sample.label.upper(),
                forecast_prob_up=forecast_prob_up,
                active_decision=active_trade.decision if active_trade is not None else "HOLD",
                active_reason=active_reason,
                active_pnl_usd=active_pnl,
                candidate_decision=candidate_trade.decision if candidate_trade is not None else "HOLD",
                candidate_reason=candidate_reason,
                candidate_pnl_usd=candidate_pnl,
                delta_pnl_usd=(candidate_pnl or 0.0) - (active_pnl or 0.0),
            )
        )
    return tuple(rows)


def summarize_candidate_comparison(rows: tuple[CandidateComparisonRow, ...]) -> dict:
    active_trades = [row for row in rows if row.active_reason == "traded"]
    candidate_trades = [row for row in rows if row.candidate_reason == "traded"]
    return {
        "eligible_windows": len(rows),
        "active_trades": len(active_trades),
        "candidate_trades": len(candidate_trades),
        "active_total_pnl_usd": sum(row.active_pnl_usd or 0.0 for row in rows),
        "candidate_total_pnl_usd": sum(row.candidate_pnl_usd or 0.0 for row in rows),
        "delta_pnl_usd": sum(row.delta_pnl_usd for row in rows),
        "active_wins": sum(
            1 for row in active_trades if row.active_pnl_usd is not None and row.active_pnl_usd > 0
        ),
        "candidate_wins": sum(
            1
            for row in candidate_trades
            if row.candidate_pnl_usd is not None and row.candidate_pnl_usd > 0
        ),
    }


def write_candidate_comparison(path: Path, rows: tuple[CandidateComparisonRow, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(CandidateComparisonRow.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row.__dict__,
                    "market_end_time": row.market_end_time.isoformat(),
                }
            )


def candidate_allows_sample(
    candidate: CandidateStrategy,
    sample: HistoricalSample,
) -> bool:
    if candidate.filter_kind == "none":
        return True
    if candidate.filter_kind == "avoid_low_momentum_near_barrier":
        min_abs_return_1m = candidate.min_abs_return_1m or 0.0
        min_abs_distance = candidate.min_abs_distance_to_barrier_bps or 0.0
        return not (
            abs(sample.features.return_1m) <= min_abs_return_1m
            and abs(sample.features.distance_to_barrier_bps) <= min_abs_distance
        )
    if candidate.filter_kind == "avoid_mid_abs_return_5m":
        min_abs_return_5m = candidate.min_abs_return_5m
        max_abs_return_5m = candidate.max_abs_return_5m
        if min_abs_return_5m is None or max_abs_return_5m is None:
            raise ValueError("mid return filter requires min and max abs return 5m")
        abs_return_5m = abs(sample.features.return_5m)
        return not (min_abs_return_5m < abs_return_5m <= max_abs_return_5m)
    raise ValueError(f"unsupported candidate filter: {candidate.filter_kind}")


def _optional_float(value: str | None) -> float | None:
    return float(value) if value not in {"", None} else None
