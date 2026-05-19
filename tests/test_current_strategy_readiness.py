import csv
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from btc5m_bot.active_strategy import ActiveStrategyState, write_active_strategy_state
from btc5m_bot.current_strategy_readiness import (
    CurrentStrategyReadinessPolicy,
    build_current_strategy_readiness_report,
)


class CurrentStrategyReadinessTests(unittest.TestCase):
    def test_counts_only_current_strategy_rows(self) -> None:
        activated_at = datetime(2026, 5, 19, 14, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            ledger = base / "forward.csv"
            state_path = base / "state.json"
            write_active_strategy_state(state_path, _state(activated_at))
            _write_forward_rows(
                ledger,
                [
                    _row(
                        slug="current-win",
                        source="candidate",
                        activated_at=activated_at.isoformat(),
                        pnl="1.0",
                    ),
                    _row(
                        slug="current-loss",
                        source="candidate",
                        activated_at=activated_at.isoformat(),
                        pnl="-1.0",
                    ),
                    _row(
                        slug="baseline-win",
                        source="baseline",
                        activated_at="",
                        pnl="10.0",
                    ),
                ],
            )

            report = build_current_strategy_readiness_report(
                forward_ledger_path=ledger,
                strategy_state_path=state_path,
                policy=CurrentStrategyReadinessPolicy(
                    min_evaluations=2,
                    min_trades=2,
                    min_win_rate=0.5,
                    min_total_pnl_usd=-1.0,
                ),
            )

        metrics = report["readiness"]["metrics"]
        self.assertEqual(metrics["current_strategy_evaluations"], 2)
        self.assertEqual(metrics["current_strategy_trades"], 2)
        self.assertEqual(metrics["current_strategy_win_rate"], 0.5)
        self.assertEqual(metrics["current_strategy_total_pnl_usd"], 0.0)

    def test_requires_current_strategy_trade_floor(self) -> None:
        activated_at = datetime(2026, 5, 19, 14, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            ledger = base / "forward.csv"
            state_path = base / "state.json"
            write_active_strategy_state(state_path, _state(activated_at))
            _write_forward_rows(
                ledger,
                [
                    _row(
                        slug="current-win",
                        source="candidate",
                        activated_at=activated_at.isoformat(),
                        pnl="1.0",
                    ),
                ],
            )

            report = build_current_strategy_readiness_report(
                forward_ledger_path=ledger,
                strategy_state_path=state_path,
                policy=CurrentStrategyReadinessPolicy(min_evaluations=1, min_trades=2),
            )

        self.assertIn(
            "insufficient_current_strategy_trades",
            report["readiness"]["blockers"],
        )


def _state(activated_at: datetime) -> ActiveStrategyState:
    return ActiveStrategyState(
        mode="paper",
        source_candidate_id="candidate",
        description="Candidate",
        rationale="Test",
        activated_at=activated_at,
        live_trading_enabled=False,
        min_confidence=0.65,
        min_edge=0.03,
        stake_usd=10.0,
        max_fill_delay_seconds=30,
    )


def _row(
    slug: str,
    source: str,
    activated_at: str,
    pnl: str,
) -> dict[str, str]:
    return {
        "slug": slug,
        "label": "UP",
        "forecast_prob_up": "0.7",
        "decision": "UP",
        "reason": "traded",
        "entry_price": "0.4",
        "edge": "0.1",
        "pnl_usd": pnl,
        "fill_delay_seconds": "1",
        "market_end_time": "2026-05-19T14:05:00+00:00",
        "active_strategy_source_candidate_id": source,
        "active_strategy_filter_kind": "none",
        "active_strategy_activated_at": activated_at,
    }


def _write_forward_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
