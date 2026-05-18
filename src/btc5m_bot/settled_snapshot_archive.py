from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .polymarket import PolymarketPublicClient, resolved_outcome_from_event


@dataclass(frozen=True)
class SettledSnapshotWindow:
    slug: str
    condition_id: str
    title: str
    market_end_time: datetime
    resolved_outcome: str
    snapshot_count: int
    first_captured_at: datetime
    last_captured_at: datetime
    min_up_best_ask: float
    max_up_best_ask: float
    min_down_best_ask: float
    max_down_best_ask: float


def load_snapshot_rows(path: Path) -> dict[str, list[dict[str, str]]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["slug"], []).append(row)
    return grouped


def load_archived_windows(path: Path) -> dict[str, SettledSnapshotWindow]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {
        row["slug"]: SettledSnapshotWindow(
            slug=row["slug"],
            condition_id=row["condition_id"],
            title=row["title"],
            market_end_time=datetime.fromisoformat(row["market_end_time"]),
            resolved_outcome=row["resolved_outcome"],
            snapshot_count=int(row["snapshot_count"]),
            first_captured_at=datetime.fromisoformat(row["first_captured_at"]),
            last_captured_at=datetime.fromisoformat(row["last_captured_at"]),
            min_up_best_ask=float(row["min_up_best_ask"]),
            max_up_best_ask=float(row["max_up_best_ask"]),
            min_down_best_ask=float(row["min_down_best_ask"]),
            max_down_best_ask=float(row["max_down_best_ask"]),
        )
        for row in rows
    }


def archive_settled_snapshot_windows(
    snapshot_path: Path,
    archive_path: Path,
    polymarket: PolymarketPublicClient | None = None,
    now: datetime | None = None,
) -> dict:
    polymarket = polymarket or PolymarketPublicClient()
    now = now or datetime.now(timezone.utc)
    grouped_rows = load_snapshot_rows(snapshot_path)
    archived = load_archived_windows(archive_path)
    new_windows: list[SettledSnapshotWindow] = []
    pending_not_ended = 0
    pending_unresolved = 0

    for slug, rows in grouped_rows.items():
        if slug in archived:
            continue

        ordered = sorted(rows, key=lambda row: row["captured_at"])
        market_end_time = datetime.fromisoformat(ordered[0]["market_end_time"])
        if market_end_time > now:
            pending_not_ended += 1
            continue

        try:
            event = polymarket.get_event_by_slug(slug)
            outcome = resolved_outcome_from_event(event)
        except Exception:  # noqa: BLE001
            outcome = None
        if outcome is None:
            pending_unresolved += 1
            continue

        up_asks = [float(row["up_best_ask"]) for row in ordered if row["up_best_ask"] != ""]
        down_asks = [float(row["down_best_ask"]) for row in ordered if row["down_best_ask"] != ""]
        if not up_asks or not down_asks:
            continue

        new_windows.append(
            SettledSnapshotWindow(
                slug=slug,
                condition_id=ordered[0]["condition_id"],
                title=ordered[0]["title"],
                market_end_time=market_end_time,
                resolved_outcome=outcome.upper(),
                snapshot_count=len(ordered),
                first_captured_at=datetime.fromisoformat(ordered[0]["captured_at"]),
                last_captured_at=datetime.fromisoformat(ordered[-1]["captured_at"]),
                min_up_best_ask=min(up_asks),
                max_up_best_ask=max(up_asks),
                min_down_best_ask=min(down_asks),
                max_down_best_ask=max(down_asks),
            )
        )

    merged = {
        **archived,
        **{window.slug: window for window in new_windows},
    }
    write_archived_windows(
        archive_path,
        tuple(sorted(merged.values(), key=lambda window: window.market_end_time)),
    )
    return {
        "snapshot_windows": len(grouped_rows),
        "existing_archived_windows": len(archived),
        "newly_archived_windows": len(new_windows),
        "total_archived_windows": len(merged),
        "pending_not_ended": pending_not_ended,
        "pending_unresolved": pending_unresolved,
    }


def write_archived_windows(path: Path, windows: tuple[SettledSnapshotWindow, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(SettledSnapshotWindow.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for window in windows:
            writer.writerow(
                {
                    **window.__dict__,
                    "market_end_time": window.market_end_time.isoformat(),
                    "first_captured_at": window.first_captured_at.isoformat(),
                    "last_captured_at": window.last_captured_at.isoformat(),
                }
            )
