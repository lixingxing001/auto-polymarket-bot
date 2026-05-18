from __future__ import annotations

import csv
from pathlib import Path

from .models import TradeDecision
from .paper import settle_binary_trade
from .polymarket import PolymarketPublicClient, resolved_outcome_from_event


def reconcile_paper_signals(
    input_path: Path,
    output_path: Path,
    polymarket: PolymarketPublicClient | None = None,
) -> dict:
    polymarket = polymarket or PolymarketPublicClient()
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    with input_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    output_rows: list[dict] = []
    settled = 0
    pending = 0

    for row in rows:
        outcome = None
        try:
            event = polymarket.get_event_by_slug(row["slug"])
            outcome = resolved_outcome_from_event(event)
        except Exception:  # noqa: BLE001
            outcome = None

        if outcome is None:
            pending += 1
            continue

        settled += 1
        decision = TradeDecision(
            side=row["decision"],
            expected_edge=float(row.get("edge") or 0.0),
            size_usd=float(row.get("size_usd") or 0.0),
            reason=row.get("reason", ""),
        )
        entry_price = 0.0
        if decision.side == "UP":
            entry_price = float(row["up_ask"])
        elif decision.side == "DOWN":
            entry_price = float(row["down_ask"])

        pnl_usd = settle_binary_trade(
            decision=decision,
            outcome=outcome.upper(),
            entry_price=entry_price or 1.0,
        )
        output_rows.append(
            {
                **row,
                "resolved_outcome": outcome.upper(),
                "won": decision.side == outcome.upper() if decision.side != "HOLD" else "",
                "pnl_usd": round(pnl_usd, 8),
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(output_rows[0].keys()) if output_rows else [
        "timestamp",
        "slug",
        "decision",
        "resolved_outcome",
        "won",
        "pnl_usd",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    traded_rows = [row for row in output_rows if row["decision"] != "HOLD"]
    wins = sum(1 for row in traded_rows if row["won"] is True)
    total_pnl = sum(float(row["pnl_usd"]) for row in traded_rows)

    return {
        "input_rows": len(rows),
        "settled_rows": settled,
        "pending_rows": pending,
        "traded_rows": len(traded_rows),
        "wins": wins,
        "win_rate": wins / len(traded_rows) if traded_rows else 0.0,
        "total_pnl_usd": total_pnl,
    }
