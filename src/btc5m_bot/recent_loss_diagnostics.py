from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .strategy_guardrails import load_forward_ledger_rows, summarize_forward_ledger


DEFAULT_FORWARD_LEDGER = Path("data/forward_snapshot_evaluations.csv")
DEFAULT_FEATURE_CACHE = Path("data/historical_dataset_cache.csv")
DEFAULT_RECENT_LOSS_REPORT = Path("recent_loss_diagnostics_report.md")


@dataclass(frozen=True)
class TradeDiagnosticRow:
    slug: str
    market_start_time: datetime
    label: str
    decision: str
    forecast_prob_up: float
    model_side: str
    contrarian_to_model: bool
    confidence: float
    entry_price: float
    edge: float
    pnl_usd: float
    fill_delay_seconds: int
    return_1m: float
    return_5m: float
    realized_vol_5m: float
    distance_to_barrier_bps: float
    range_1m_bps: float
    range_5m_bps: float
    polymarket_prob_gap: float

    @property
    def won(self) -> bool:
        return self.pnl_usd > 0


def load_feature_rows(path: Path = DEFAULT_FEATURE_CACHE) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["slug"]: row for row in csv.DictReader(handle)}


def build_trade_diagnostic_rows(
    forward_rows: list[dict[str, str]],
    feature_rows: dict[str, dict[str, str]],
) -> tuple[TradeDiagnosticRow, ...]:
    rows: list[TradeDiagnosticRow] = []
    for row in forward_rows:
        if row["reason"] != "traded":
            continue
        forecast_prob_up = float(row["forecast_prob_up"])
        model_side = "UP" if forecast_prob_up >= 0.5 else "DOWN"
        decision = row["decision"].upper()
        features = feature_rows.get(row["slug"], {})
        rows.append(
            TradeDiagnosticRow(
                slug=row["slug"],
                market_start_time=_market_start_time(row["slug"]),
                label=row["label"].upper(),
                decision=decision,
                forecast_prob_up=forecast_prob_up,
                model_side=model_side,
                contrarian_to_model=decision != model_side,
                confidence=max(forecast_prob_up, 1.0 - forecast_prob_up),
                entry_price=float(row["entry_price"]),
                edge=float(row["edge"]),
                pnl_usd=float(row["pnl_usd"]),
                fill_delay_seconds=int(row["fill_delay_seconds"] or 0),
                return_1m=_feature_float(features, "return_1m"),
                return_5m=_feature_float(features, "return_5m"),
                realized_vol_5m=_feature_float(features, "realized_vol_5m"),
                distance_to_barrier_bps=_feature_float(features, "distance_to_barrier_bps"),
                range_1m_bps=_feature_float(features, "range_1m_bps"),
                range_5m_bps=_feature_float(features, "range_5m_bps"),
                polymarket_prob_gap=_feature_float(features, "polymarket_prob_gap"),
            )
        )
    return tuple(sorted(rows, key=lambda item: item.market_start_time))


def build_recent_loss_diagnostics_report(
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
    feature_cache_path: Path = DEFAULT_FEATURE_CACHE,
    recent_trade_count: int = 12,
    min_slice_trades: int = 3,
) -> dict[str, Any]:
    forward_rows = load_forward_ledger_rows(forward_ledger_path)
    feature_rows = load_feature_rows(feature_cache_path)
    trade_rows = build_trade_diagnostic_rows(forward_rows, feature_rows)
    recent_rows = trade_rows[-recent_trade_count:] if recent_trade_count > 0 else trade_rows
    recent_losses = tuple(row for row in recent_rows if not row.won)
    slices = build_slice_diagnostics(recent_rows)
    return {
        "ledger_summary": summarize_forward_ledger(forward_rows).__dict__,
        "all_trades": summarize_trade_rows(trade_rows),
        "recent_trades": summarize_trade_rows(recent_rows),
        "profit_concentration": summarize_profit_concentration(trade_rows),
        "tail_loss_streak": count_tail_losses(trade_rows),
        "recent_loss_count": len(recent_losses),
        "recent_losses": [row.__dict__ for row in recent_losses[-8:]],
        "slices": slices,
        "worst_slices": find_worst_slices(slices, min_trades=min_slice_trades),
        "flags": build_diagnostic_flags(trade_rows, recent_rows, slices),
        "config": {
            "forward_ledger_path": str(forward_ledger_path),
            "feature_cache_path": str(feature_cache_path),
            "recent_trade_count": recent_trade_count,
            "min_slice_trades": min_slice_trades,
        },
    }


def summarize_trade_rows(rows: tuple[TradeDiagnosticRow, ...]) -> dict[str, Any]:
    wins = sum(1 for row in rows if row.won)
    losses = len(rows) - wins
    total_pnl = sum(row.pnl_usd for row in rows)
    contrarian_rows = tuple(row for row in rows if row.contrarian_to_model)
    aligned_rows = tuple(row for row in rows if not row.contrarian_to_model)
    return {
        "trades": len(rows),
        "wins": wins,
        "losses": losses,
        "win_rate": wins / len(rows) if rows else 0.0,
        "total_pnl_usd": total_pnl,
        "avg_pnl_usd": total_pnl / len(rows) if rows else 0.0,
        "avg_edge": sum(row.edge for row in rows) / len(rows) if rows else 0.0,
        "avg_entry_price": sum(row.entry_price for row in rows) / len(rows) if rows else 0.0,
        "contrarian_trades": len(contrarian_rows),
        "contrarian_win_rate": _win_rate(contrarian_rows),
        "contrarian_total_pnl_usd": sum(row.pnl_usd for row in contrarian_rows),
        "aligned_trades": len(aligned_rows),
        "aligned_win_rate": _win_rate(aligned_rows),
        "aligned_total_pnl_usd": sum(row.pnl_usd for row in aligned_rows),
    }


def summarize_profit_concentration(rows: tuple[TradeDiagnosticRow, ...]) -> dict[str, Any]:
    winning_pnls = sorted((row.pnl_usd for row in rows if row.pnl_usd > 0), reverse=True)
    losing_pnls = [row.pnl_usd for row in rows if row.pnl_usd <= 0]
    positive_total = sum(winning_pnls)
    largest_win = winning_pnls[0] if winning_pnls else 0.0
    top_three_total = sum(winning_pnls[:3])
    return {
        "positive_pnl_usd": positive_total,
        "negative_pnl_usd": sum(losing_pnls),
        "largest_win_pnl_usd": largest_win,
        "largest_win_share_of_positive_pnl": (
            largest_win / positive_total if positive_total else 0.0
        ),
        "top_three_win_share_of_positive_pnl": (
            top_three_total / positive_total if positive_total else 0.0
        ),
        "largest_loss_pnl_usd": min(losing_pnls) if losing_pnls else 0.0,
    }


def count_tail_losses(rows: tuple[TradeDiagnosticRow, ...]) -> int:
    streak = 0
    for row in reversed(rows):
        if row.won:
            break
        streak += 1
    return streak


def build_slice_diagnostics(
    rows: tuple[TradeDiagnosticRow, ...],
) -> dict[str, list[dict[str, Any]]]:
    return {
        "decision_side": _categorical_slices(rows, lambda row: row.decision),
        "model_side": _categorical_slices(rows, lambda row: row.model_side),
        "model_trade_alignment": _categorical_slices(
            rows,
            lambda row: "contrarian" if row.contrarian_to_model else "aligned",
        ),
        "confidence": _categorical_slices(rows, lambda row: _confidence_bucket(row.confidence)),
        "edge": _categorical_slices(rows, lambda row: _edge_bucket(row.edge)),
        "entry_price": _categorical_slices(rows, lambda row: _entry_price_bucket(row.entry_price)),
        "fill_delay": _categorical_slices(rows, lambda row: _fill_delay_bucket(row.fill_delay_seconds)),
        "return_1m_direction": _categorical_slices(rows, lambda row: _signed_bucket(row.return_1m)),
        "return_5m_direction": _categorical_slices(rows, lambda row: _signed_bucket(row.return_5m)),
        "trade_vs_1m_momentum": _categorical_slices(
            rows,
            lambda row: _momentum_alignment(row.decision, row.return_1m),
        ),
        "trade_vs_5m_momentum": _categorical_slices(
            rows,
            lambda row: _momentum_alignment(row.decision, row.return_5m),
        ),
        "market_gap_alignment": _categorical_slices(
            rows,
            lambda row: _market_gap_alignment(row.decision, row.polymarket_prob_gap),
        ),
        "abs_return_5m": _categorical_slices(
            rows,
            lambda row: _abs_return_5m_bucket(abs(row.return_5m)),
        ),
        "distance_to_barrier_bps": _categorical_slices(
            rows,
            lambda row: _distance_bucket(abs(row.distance_to_barrier_bps)),
        ),
    }


def find_worst_slices(
    slices: dict[str, list[dict[str, Any]]],
    min_trades: int = 3,
    limit: int = 10,
) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for dimension, entries in slices.items():
        for entry in entries:
            if entry["trades"] < min_trades:
                continue
            flattened.append({"dimension": dimension, **entry})
    return sorted(
        flattened,
        key=lambda item: (
            item["win_rate"],
            item["total_pnl_usd"],
            -item["trades"],
        ),
    )[:limit]


def build_diagnostic_flags(
    all_rows: tuple[TradeDiagnosticRow, ...],
    recent_rows: tuple[TradeDiagnosticRow, ...],
    slices: dict[str, list[dict[str, Any]]],
) -> tuple[str, ...]:
    flags: list[str] = []
    all_summary = summarize_trade_rows(all_rows)
    recent_summary = summarize_trade_rows(recent_rows)
    concentration = summarize_profit_concentration(all_rows)
    if recent_summary["trades"] and recent_summary["win_rate"] < all_summary["win_rate"]:
        flags.append("recent_win_rate_below_full_forward_set")
    if recent_summary["trades"] >= 6 and recent_summary["win_rate"] < 0.45:
        flags.append("recent_hit_rate_too_weak_for_canary")
    if concentration["top_three_win_share_of_positive_pnl"] > 0.65:
        flags.append("positive_pnl_concentrated_in_top_winners")
    if count_tail_losses(all_rows) >= 3:
        flags.append("active_tail_loss_streak")
    contrarian_slice = _find_slice(slices, "model_trade_alignment", "contrarian")
    if (
        contrarian_slice is not None
        and contrarian_slice["trades"] >= 3
        and contrarian_slice["win_rate"] < 0.45
    ):
        flags.append("recent_contrarian_trades_underperform")
    return tuple(dict.fromkeys(flags))


def render_recent_loss_diagnostics_markdown(report: dict[str, Any]) -> str:
    ledger = report["ledger_summary"]
    all_summary = report["all_trades"]
    recent = report["recent_trades"]
    concentration = report["profit_concentration"]
    lines = [
        "# Recent Loss Diagnostics Report",
        "",
        "## Status",
        "",
        f"- forward_evaluations: {ledger['evaluations']}",
        f"- forward_trades: {ledger['traded_rows']}",
        f"- forward_win_rate: {_pct(ledger['win_rate'])}",
        f"- forward_total_pnl_usd: {_money(ledger['total_pnl_usd'])}",
        f"- recent_trades: {recent['trades']}",
        f"- recent_win_rate: {_pct(recent['win_rate'])}",
        f"- recent_total_pnl_usd: {_money(recent['total_pnl_usd'])}",
        f"- tail_loss_streak: {report['tail_loss_streak']}",
        "",
        "## Diagnostic flags",
        "",
        *(_render_items(report["flags"])),
        "",
        "## Full trade structure",
        "",
        f"- all_trades: {all_summary['trades']}",
        f"- all_wins: {all_summary['wins']}",
        f"- all_losses: {all_summary['losses']}",
        f"- all_win_rate: {_pct(all_summary['win_rate'])}",
        f"- all_total_pnl_usd: {_money(all_summary['total_pnl_usd'])}",
        f"- contrarian_trades: {all_summary['contrarian_trades']}",
        f"- contrarian_win_rate: {_pct(all_summary['contrarian_win_rate'])}",
        f"- contrarian_total_pnl_usd: {_money(all_summary['contrarian_total_pnl_usd'])}",
        f"- aligned_trades: {all_summary['aligned_trades']}",
        f"- aligned_win_rate: {_pct(all_summary['aligned_win_rate'])}",
        f"- aligned_total_pnl_usd: {_money(all_summary['aligned_total_pnl_usd'])}",
        "",
        "## PnL concentration",
        "",
        f"- positive_pnl_usd: {_money(concentration['positive_pnl_usd'])}",
        f"- negative_pnl_usd: {_money(concentration['negative_pnl_usd'])}",
        f"- largest_win_pnl_usd: {_money(concentration['largest_win_pnl_usd'])}",
        f"- largest_win_share_of_positive_pnl: {_pct(concentration['largest_win_share_of_positive_pnl'])}",
        f"- top_three_win_share_of_positive_pnl: {_pct(concentration['top_three_win_share_of_positive_pnl'])}",
        f"- largest_loss_pnl_usd: {_money(concentration['largest_loss_pnl_usd'])}",
        "",
        "## Worst recent slices",
        "",
        "| dimension | bucket | trades | win_rate | total_pnl_usd | avg_pnl_usd |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in report["worst_slices"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    item["dimension"],
                    str(item["bucket"]),
                    str(item["trades"]),
                    _pct(item["win_rate"]),
                    _money(item["total_pnl_usd"]),
                    _money(item["avg_pnl_usd"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Recent loss rows",
            "",
            "| market_start_utc | slug | label | decision | model_side | contrarian | prob_up | entry | edge | pnl_usd | ret_1m | ret_5m | pm_gap |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["recent_losses"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["market_start_time"].isoformat(),
                    row["slug"],
                    row["label"],
                    row["decision"],
                    row["model_side"],
                    str(row["contrarian_to_model"]),
                    f"{row['forecast_prob_up']:.3f}",
                    f"{row['entry_price']:.3f}",
                    f"{row['edge']:.3f}",
                    _money(row["pnl_usd"]),
                    f"{row['return_1m']:.6f}",
                    f"{row['return_5m']:.6f}",
                    f"{row['polymarket_prob_gap']:.3f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This report diagnoses forward paper trades only. It does not approve strategy changes, enable real trading or submit orders.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_recent_loss_diagnostics_report(
    output_path: Path = DEFAULT_RECENT_LOSS_REPORT,
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
    feature_cache_path: Path = DEFAULT_FEATURE_CACHE,
    recent_trade_count: int = 12,
    min_slice_trades: int = 3,
) -> dict[str, Any]:
    report = build_recent_loss_diagnostics_report(
        forward_ledger_path=forward_ledger_path,
        feature_cache_path=feature_cache_path,
        recent_trade_count=recent_trade_count,
        min_slice_trades=min_slice_trades,
    )
    output_path.write_text(render_recent_loss_diagnostics_markdown(report), encoding="utf-8")
    return report


def _categorical_slices(
    rows: tuple[TradeDiagnosticRow, ...],
    bucket_fn: Callable[[TradeDiagnosticRow], str],
) -> list[dict[str, Any]]:
    buckets: dict[str, list[TradeDiagnosticRow]] = {}
    for row in rows:
        buckets.setdefault(bucket_fn(row), []).append(row)
    return [
        _summarize_slice(bucket, tuple(bucket_rows))
        for bucket, bucket_rows in sorted(buckets.items())
    ]


def _summarize_slice(bucket: str, rows: tuple[TradeDiagnosticRow, ...]) -> dict[str, Any]:
    wins = sum(1 for row in rows if row.won)
    total_pnl = sum(row.pnl_usd for row in rows)
    return {
        "bucket": bucket,
        "trades": len(rows),
        "wins": wins,
        "losses": len(rows) - wins,
        "win_rate": wins / len(rows) if rows else 0.0,
        "total_pnl_usd": total_pnl,
        "avg_pnl_usd": total_pnl / len(rows) if rows else 0.0,
        "avg_edge": sum(row.edge for row in rows) / len(rows) if rows else 0.0,
        "avg_entry_price": sum(row.entry_price for row in rows) / len(rows) if rows else 0.0,
    }


def _market_start_time(slug: str) -> datetime:
    return datetime.fromtimestamp(int(slug.rsplit("-", 1)[-1]), tz=timezone.utc)


def _feature_float(features: dict[str, str], key: str) -> float:
    value = features.get(key, "")
    return float(value) if value != "" else 0.0


def _win_rate(rows: tuple[TradeDiagnosticRow, ...]) -> float:
    return sum(1 for row in rows if row.won) / len(rows) if rows else 0.0


def _find_slice(
    slices: dict[str, list[dict[str, Any]]],
    dimension: str,
    bucket: str,
) -> dict[str, Any] | None:
    for entry in slices.get(dimension, []):
        if entry["bucket"] == bucket:
            return entry
    return None


def _confidence_bucket(confidence: float) -> str:
    if confidence < 0.70:
        return "0.65-0.70"
    if confidence < 0.80:
        return "0.70-0.80"
    return "0.80-1.00"


def _edge_bucket(edge: float) -> str:
    if edge < 0.06:
        return "0.03-0.06"
    if edge < 0.09:
        return "0.06-0.09"
    return "0.09+"


def _entry_price_bucket(entry_price: float) -> str:
    if entry_price <= 0.20:
        return "<=0.20"
    if entry_price <= 0.40:
        return "0.20-0.40"
    if entry_price <= 0.60:
        return "0.40-0.60"
    return "0.60+"


def _fill_delay_bucket(fill_delay_seconds: int) -> str:
    if fill_delay_seconds <= 0:
        return "0s"
    if fill_delay_seconds <= 10:
        return "1-10s"
    return "11-30s"


def _signed_bucket(value: float) -> str:
    if value > 0.0:
        return "positive"
    if value < 0.0:
        return "negative"
    return "flat"


def _momentum_alignment(decision: str, return_value: float) -> str:
    if return_value == 0.0:
        return "flat"
    if (decision == "UP" and return_value > 0.0) or (
        decision == "DOWN" and return_value < 0.0
    ):
        return "with_momentum"
    return "against_momentum"


def _market_gap_alignment(decision: str, polymarket_prob_gap: float) -> str:
    if polymarket_prob_gap == 0.0:
        return "flat"
    market_side = "UP" if polymarket_prob_gap > 0.0 else "DOWN"
    return "with_market_gap" if decision == market_side else "against_market_gap"


def _abs_return_5m_bucket(abs_return_5m: float) -> str:
    if abs_return_5m <= 0.0003:
        return "<=0.0003"
    if abs_return_5m <= 0.0008:
        return "0.0003-0.0008"
    return "0.0008+"


def _distance_bucket(abs_distance_bps: float) -> str:
    if abs_distance_bps <= 2.0:
        return "<=2bps"
    if abs_distance_bps <= 6.0:
        return "2-6bps"
    return "6bps+"


def _render_items(items: tuple[str, ...] | list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]


def _pct(value: float) -> str:
    return f"{value:.1%}"


def _money(value: float) -> str:
    return f"{value:.2f}"
