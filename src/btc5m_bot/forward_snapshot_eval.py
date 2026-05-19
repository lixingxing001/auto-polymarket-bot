from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from .active_strategy import ActiveStrategyState, active_strategy_allows_trade
from .execution_backtest import ExecutionBacktestConfig
from .historical import HistoricalSample
from .learning import sample_to_features, train_logistic_regression
from .settled_snapshot_archive import SettledSnapshotWindow
from .snapshot_backtest import backtest_sample_with_snapshot, find_snapshot_at_or_after, SnapshotQuote


@dataclass(frozen=True)
class ForwardSnapshotEvaluation:
    slug: str
    label: str
    forecast_prob_up: float
    decision: str
    reason: str
    entry_price: float | None
    edge: float | None
    pnl_usd: float | None
    fill_delay_seconds: int | None
    market_end_time: str = ""
    active_strategy_source_candidate_id: str = "baseline"
    active_strategy_filter_kind: str = "none"
    active_strategy_activated_at: str = ""


def load_forward_evaluations(path: Path) -> dict[str, ForwardSnapshotEvaluation]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {
        row["slug"]: _parse_forward_evaluation_row(row)
        for row in rows
    }


def _parse_forward_evaluation_row(row: dict[str, str]) -> ForwardSnapshotEvaluation:
    market_end_time = row.get("market_end_time", "")
    source = row.get("active_strategy_source_candidate_id", "")
    if not source or (source == "baseline" and not market_end_time):
        source = "legacy_unversioned"
    return ForwardSnapshotEvaluation(
        slug=row["slug"],
        label=row["label"],
        forecast_prob_up=float(row["forecast_prob_up"]),
        decision=row["decision"],
        reason=row["reason"],
        entry_price=_optional_float(row["entry_price"]),
        edge=_optional_float(row["edge"]),
        pnl_usd=_optional_float(row["pnl_usd"]),
        fill_delay_seconds=_optional_int(row["fill_delay_seconds"]),
        market_end_time=market_end_time,
        active_strategy_source_candidate_id=source,
        active_strategy_filter_kind=row.get("active_strategy_filter_kind", "") or "none",
        active_strategy_activated_at=row.get("active_strategy_activated_at", ""),
    )


def evaluate_settled_snapshot_windows(
    archived_windows: tuple[SettledSnapshotWindow, ...],
    samples: tuple[HistoricalSample, ...],
    snapshots: dict[str, list[SnapshotQuote]],
    output_path: Path,
    min_train_size: int = 200,
    config: ExecutionBacktestConfig | None = None,
    active_strategy_state: ActiveStrategyState | None = None,
) -> dict:
    config = config or ExecutionBacktestConfig(min_confidence=0.65)
    existing = load_forward_evaluations(output_path)
    samples_by_slug = {sample.slug: sample for sample in samples}
    ordered_samples = tuple(sorted(samples, key=lambda sample: sample.window_start))
    new_rows: list[ForwardSnapshotEvaluation] = []
    skipped_missing_sample = 0
    skipped_insufficient_training = 0
    strategy_source = (
        active_strategy_state.source_candidate_id if active_strategy_state else "baseline"
    )
    strategy_filter = active_strategy_state.filter_kind if active_strategy_state else "none"
    strategy_activated_at = (
        active_strategy_state.activated_at.isoformat() if active_strategy_state else ""
    )

    for window in sorted(archived_windows, key=lambda item: item.market_end_time):
        if window.slug in existing:
            continue
        sample = samples_by_slug.get(window.slug)
        if sample is None:
            skipped_missing_sample += 1
            continue

        prior_samples = tuple(
            candidate
            for candidate in ordered_samples
            if candidate.window_start < sample.window_start
        )
        if len(prior_samples) < min_train_size:
            skipped_insufficient_training += 1
            continue

        model = train_logistic_regression(prior_samples)
        forecast_prob_up = model.predict_proba(sample_to_features(sample))
        decision_time = sample.window_start + timedelta(seconds=60)
        quote = find_snapshot_at_or_after(
            snapshots.get(sample.slug, []),
            decision_time=decision_time,
            max_delay_seconds=config.max_fill_delay_seconds,
        )
        trade, reason = backtest_sample_with_snapshot(
            sample=sample,
            quote=quote,
            forecast_prob_up=forecast_prob_up,
            config=config,
        )
        if (
            trade is not None
            and active_strategy_state is not None
            and not active_strategy_allows_trade(
                active_strategy_state,
                sample.features,
                trade.decision,
            )
        ):
            trade = None
            reason = "active_strategy_filter"
        if trade is None:
            new_rows.append(
                ForwardSnapshotEvaluation(
                    slug=sample.slug,
                    label=sample.label.upper(),
                    forecast_prob_up=forecast_prob_up,
                    decision="HOLD",
                    reason=reason,
                    entry_price=None,
                    edge=None,
                    pnl_usd=None,
                    fill_delay_seconds=None,
                    market_end_time=window.market_end_time.isoformat(),
                    active_strategy_source_candidate_id=strategy_source,
                    active_strategy_filter_kind=strategy_filter,
                    active_strategy_activated_at=strategy_activated_at,
                )
            )
            continue

        new_rows.append(
            ForwardSnapshotEvaluation(
                slug=sample.slug,
                label=sample.label.upper(),
                forecast_prob_up=forecast_prob_up,
                decision=trade.decision,
                reason="traded",
                entry_price=trade.entry_price,
                edge=trade.edge,
                pnl_usd=trade.pnl_usd,
                fill_delay_seconds=trade.fill_delay_seconds,
                market_end_time=window.market_end_time.isoformat(),
                active_strategy_source_candidate_id=strategy_source,
                active_strategy_filter_kind=strategy_filter,
                active_strategy_activated_at=strategy_activated_at,
            )
        )

    merged = {
        **existing,
        **{row.slug: row for row in new_rows},
    }
    write_forward_evaluations(
        output_path,
        tuple(sorted(merged.values(), key=lambda row: row.slug)),
    )
    traded_rows = [row for row in merged.values() if row.reason == "traded"]
    wins = sum(1 for row in traded_rows if row.pnl_usd is not None and row.pnl_usd > 0)
    total_pnl = sum(row.pnl_usd or 0.0 for row in traded_rows)
    return {
        "existing_evaluations": len(existing),
        "new_evaluations": len(new_rows),
        "total_evaluations": len(merged),
        "active_strategy_source_candidate_id": strategy_source,
        "active_strategy_filter_kind": strategy_filter,
        "skipped_missing_sample": skipped_missing_sample,
        "skipped_insufficient_training": skipped_insufficient_training,
        "traded_rows": len(traded_rows),
        "wins": wins,
        "win_rate": wins / len(traded_rows) if traded_rows else 0.0,
        "total_pnl_usd": total_pnl,
    }


def write_forward_evaluations(
    path: Path,
    rows: tuple[ForwardSnapshotEvaluation, ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(ForwardSnapshotEvaluation.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def _optional_float(value: str | None) -> float | None:
    return float(value) if value not in {"", None} else None


def _optional_int(value: str | None) -> int | None:
    return int(value) if value not in {"", None} else None
