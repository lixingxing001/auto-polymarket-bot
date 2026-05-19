import csv
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from btc5m_bot.active_strategy import (
    active_strategy_state_from_candidate,
    load_active_strategy_state,
    write_active_strategy_state,
)
from btc5m_bot.candidate_autopilot import CandidateAutopilotPolicy, run_candidate_autopilot
from btc5m_bot.candidate_strategies import (
    CandidateStrategy,
    load_candidate_registry,
    write_candidate_registry,
)


class CandidateAutopilotTests(unittest.TestCase):
    def test_auto_promotes_paper_strategy_when_candidate_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            registry = base / "registry.csv"
            comparison_dir = base / "comparisons"
            ledger = base / "forward.csv"
            state_path = base / "state.json"
            comparison_dir.mkdir()
            write_candidate_registry(
                registry,
                (
                    CandidateStrategy(
                        candidate_id="good",
                        description="Good",
                        rationale="Test",
                        registered_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
                        eligible_after_market_end_time=datetime(
                            2026,
                            5,
                            19,
                            tzinfo=timezone.utc,
                        ),
                        min_confidence=0.65,
                        min_edge=0.03,
                        stake_usd=10.0,
                        max_fill_delay_seconds=30,
                        filter_kind="avoid_mid_distance_to_barrier_bps",
                        min_abs_distance_to_barrier_bps=2.0,
                        max_abs_distance_to_barrier_bps=6.0,
                    ),
                ),
            )
            _write_rows(
                comparison_dir / "good.csv",
                [
                    *[_avoid_active_loss_row() for _ in range(10)],
                    *[_candidate_win_row() for _ in range(20)],
                ],
            )
            _write_forward_ledger(ledger)

            report = run_candidate_autopilot(
                output_path=base / "autopilot.md",
                lifecycle_output_path=base / "lifecycle.md",
                strategy_state_path=state_path,
                forward_ledger_path=ledger,
                registry_path=registry,
                comparison_dir=comparison_dir,
                policy=CandidateAutopilotPolicy(enabled=True),
                now=datetime(2026, 5, 19, tzinfo=timezone.utc),
            )
            state = load_active_strategy_state(state_path)

        self.assertEqual(report["action"], "PAPER_STRATEGY_PROMOTED")
        self.assertEqual(state.source_candidate_id, "good")
        self.assertEqual(state.filter_kind, "avoid_mid_distance_to_barrier_bps")
        self.assertFalse(state.live_trading_enabled)

    def test_dry_run_does_not_write_strategy_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            registry = base / "registry.csv"
            comparison_dir = base / "comparisons"
            ledger = base / "forward.csv"
            state_path = base / "state.json"
            comparison_dir.mkdir()
            write_candidate_registry(
                registry,
                (
                    CandidateStrategy(
                        candidate_id="good",
                        description="Good",
                        rationale="Test",
                        registered_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
                        eligible_after_market_end_time=datetime(
                            2026,
                            5,
                            19,
                            tzinfo=timezone.utc,
                        ),
                        min_confidence=0.65,
                        min_edge=0.03,
                        stake_usd=10.0,
                        max_fill_delay_seconds=30,
                    ),
                ),
            )
            _write_rows(
                comparison_dir / "good.csv",
                [
                    *[_avoid_active_loss_row() for _ in range(10)],
                    *[_candidate_win_row() for _ in range(20)],
                ],
            )
            _write_forward_ledger(ledger)

            report = run_candidate_autopilot(
                output_path=base / "autopilot.md",
                lifecycle_output_path=base / "lifecycle.md",
                strategy_state_path=state_path,
                forward_ledger_path=ledger,
                registry_path=registry,
                comparison_dir=comparison_dir,
                policy=CandidateAutopilotPolicy(enabled=False),
            )

        self.assertEqual(report["action"], "DRY_RUN_PROMOTION_READY")
        self.assertFalse(state_path.exists())

    def test_demotes_degraded_active_strategy_to_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            registry = base / "registry.csv"
            comparison_dir = base / "comparisons"
            ledger = base / "forward.csv"
            state_path = base / "state.json"
            comparison_dir.mkdir()
            candidate = CandidateStrategy(
                candidate_id="bad",
                description="Bad",
                rationale="Test",
                registered_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
                eligible_after_market_end_time=datetime(
                    2026,
                    5,
                    19,
                    tzinfo=timezone.utc,
                ),
                min_confidence=0.65,
                min_edge=0.03,
                stake_usd=10.0,
                max_fill_delay_seconds=30,
            )
            write_candidate_registry(registry, (candidate,))
            write_active_strategy_state(
                state_path,
                active_strategy_state_from_candidate(
                    candidate,
                    now=datetime(2026, 5, 19, hour=1, tzinfo=timezone.utc),
                ),
            )
            _write_rows(
                comparison_dir / "bad.csv",
                [
                    *[_active_win_candidate_hold_row() for _ in range(10)],
                    *[_candidate_loss_row() for _ in range(20)],
                ],
            )
            _write_forward_ledger(ledger)

            report = run_candidate_autopilot(
                output_path=base / "autopilot.md",
                lifecycle_output_path=base / "lifecycle.md",
                strategy_state_path=state_path,
                forward_ledger_path=ledger,
                registry_path=registry,
                comparison_dir=comparison_dir,
                policy=CandidateAutopilotPolicy(enabled=True),
                now=datetime(2026, 5, 19, hour=2, tzinfo=timezone.utc),
            )
            state = load_active_strategy_state(state_path)
            updated_registry = load_candidate_registry(registry)

        self.assertEqual(report["action"], "PAPER_STRATEGY_DEMOTED_TO_BASELINE")
        self.assertEqual(report["rejected_candidate_id"], "bad")
        self.assertEqual(
            report["active_strategy_degradation"]["reason"],
            "active_candidate_failed_change_quality",
        )
        self.assertEqual(state.source_candidate_id, "baseline")
        self.assertFalse(state.live_trading_enabled)
        self.assertEqual(updated_registry["bad"].status, "rejected")


def _avoid_active_loss_row() -> dict[str, str]:
    return {
        "active_decision": "UP",
        "active_reason": "traded",
        "active_pnl_usd": "-1.0",
        "candidate_decision": "HOLD",
        "candidate_reason": "candidate_filter",
        "candidate_pnl_usd": "",
    }


def _candidate_win_row() -> dict[str, str]:
    return {
        "active_decision": "UP",
        "active_reason": "traded",
        "active_pnl_usd": "0.0",
        "candidate_decision": "UP",
        "candidate_reason": "traded",
        "candidate_pnl_usd": "1.0",
    }


def _active_win_candidate_hold_row() -> dict[str, str]:
    return {
        "active_decision": "UP",
        "active_reason": "traded",
        "active_pnl_usd": "1.0",
        "candidate_decision": "HOLD",
        "candidate_reason": "candidate_filter",
        "candidate_pnl_usd": "",
    }


def _candidate_loss_row() -> dict[str, str]:
    return {
        "active_decision": "UP",
        "active_reason": "traded",
        "active_pnl_usd": "0.0",
        "candidate_decision": "UP",
        "candidate_reason": "traded",
        "candidate_pnl_usd": "-1.0",
    }


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_forward_ledger(path: Path) -> None:
    fieldnames = ["reason", "pnl_usd", "edge"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index in range(100):
            writer.writerow(
                {
                    "reason": "traded" if index < 30 else "low_confidence",
                    "pnl_usd": "1.0" if index < 30 else "",
                    "edge": "0.1" if index < 30 else "",
                }
            )


if __name__ == "__main__":
    unittest.main()
