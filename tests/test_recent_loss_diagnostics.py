import unittest
from datetime import timezone

from btc5m_bot.recent_loss_diagnostics import (
    build_diagnostic_flags,
    build_slice_diagnostics,
    build_trade_diagnostic_rows,
    count_tail_losses,
    find_worst_slices,
    render_recent_loss_diagnostics_markdown,
    summarize_profit_concentration,
    summarize_trade_rows,
)
from btc5m_bot.strategy_guardrails import summarize_forward_ledger


class RecentLossDiagnosticsTests(unittest.TestCase):
    def test_build_rows_marks_model_contrarian_trade(self) -> None:
        rows = build_trade_diagnostic_rows(
            [
                _forward_row(
                    slug="btc-updown-5m-1779165300",
                    label="UP",
                    decision="DOWN",
                    forecast_prob_up="0.78",
                    entry_price="0.16",
                    edge="0.045",
                    pnl_usd="-10.58",
                )
            ],
            {
                "btc-updown-5m-1779165300": {
                    "return_1m": "0.0007",
                    "return_5m": "0.0010",
                    "realized_vol_5m": "0.0004",
                    "distance_to_barrier_bps": "7.2",
                    "range_1m_bps": "3.0",
                    "range_5m_bps": "11.8",
                    "polymarket_prob_gap": "-0.025",
                }
            },
        )

        self.assertEqual(rows[0].market_start_time.tzinfo, timezone.utc)
        self.assertEqual(rows[0].model_side, "UP")
        self.assertTrue(rows[0].contrarian_to_model)
        self.assertFalse(rows[0].won)

    def test_recent_slice_flags_surface_weak_contrarian_cluster(self) -> None:
        rows = build_trade_diagnostic_rows(
            [
                _forward_row("btc-updown-5m-1779164400", "DOWN", "DOWN", "0.75", "0.18", "0.05", "44.0"),
                _forward_row("btc-updown-5m-1779164700", "UP", "UP", "0.72", "0.30", "0.04", "23.0"),
                _forward_row("btc-updown-5m-1779165000", "UP", "DOWN", "0.71", "0.18", "0.09", "-10.5"),
                _forward_row("btc-updown-5m-1779165300", "UP", "DOWN", "0.78", "0.16", "0.04", "-10.6"),
                _forward_row("btc-updown-5m-1779165600", "UP", "DOWN", "0.73", "0.16", "0.10", "-10.6"),
                _forward_row("btc-updown-5m-1779165900", "UP", "DOWN", "0.74", "0.17", "0.08", "-10.5"),
            ],
            {
                "btc-updown-5m-1779164400": _feature_row("-0.0005", "0.01"),
                "btc-updown-5m-1779164700": _feature_row("0.0004", "0.05"),
                "btc-updown-5m-1779165000": _feature_row("0.0006", "0.12"),
                "btc-updown-5m-1779165300": _feature_row("0.0010", "-0.03"),
                "btc-updown-5m-1779165600": _feature_row("0.0004", "-0.07"),
                "btc-updown-5m-1779165900": _feature_row("0.0005", "-0.05"),
            },
        )

        slices = build_slice_diagnostics(rows)
        worst = find_worst_slices(slices, min_trades=3)
        flags = build_diagnostic_flags(rows, rows, slices)

        self.assertEqual(count_tail_losses(rows), 4)
        self.assertIn("recent_hit_rate_too_weak_for_canary", flags)
        self.assertIn("recent_contrarian_trades_underperform", flags)
        self.assertIn(
            ("model_trade_alignment", "contrarian"),
            {(item["dimension"], item["bucket"]) for item in worst},
        )

    def test_render_markdown_contains_core_numbers(self) -> None:
        forward_rows = [
            _forward_row("btc-updown-5m-1779164400", "DOWN", "DOWN", "0.75", "0.18", "0.05", "44.0"),
            _forward_row("btc-updown-5m-1779165000", "UP", "DOWN", "0.71", "0.18", "0.09", "-10.5"),
            _forward_row("btc-updown-5m-1779165300", "UP", "DOWN", "0.78", "0.16", "0.04", "-10.6"),
        ]
        rows = build_trade_diagnostic_rows(
            forward_rows,
            {
                "btc-updown-5m-1779164400": _feature_row("-0.0005", "0.01"),
                "btc-updown-5m-1779165000": _feature_row("0.0006", "0.12"),
                "btc-updown-5m-1779165300": _feature_row("0.0010", "-0.03"),
            },
        )
        slices = build_slice_diagnostics(rows)
        report = {
            "ledger_summary": summarize_forward_ledger(forward_rows).__dict__,
            "all_trades": summarize_trade_rows(rows),
            "recent_trades": summarize_trade_rows(rows),
            "profit_concentration": summarize_profit_concentration(rows),
            "tail_loss_streak": count_tail_losses(rows),
            "recent_loss_count": 2,
            "recent_losses": [row.__dict__ for row in rows if not row.won],
            "slices": slices,
            "worst_slices": find_worst_slices(slices, min_trades=2),
            "flags": build_diagnostic_flags(rows, rows, slices),
            "config": {},
        }

        markdown = render_recent_loss_diagnostics_markdown(report)

        self.assertIn("# Recent Loss Diagnostics Report", markdown)
        self.assertIn("forward_trades: 3", markdown)
        self.assertIn("Recent loss rows", markdown)
        self.assertIn("model_trade_alignment", markdown)


def _forward_row(
    slug: str,
    label: str,
    decision: str,
    forecast_prob_up: str,
    entry_price: str,
    edge: str,
    pnl_usd: str,
) -> dict[str, str]:
    return {
        "slug": slug,
        "label": label,
        "forecast_prob_up": forecast_prob_up,
        "decision": decision,
        "reason": "traded",
        "entry_price": entry_price,
        "edge": edge,
        "pnl_usd": pnl_usd,
        "fill_delay_seconds": "0",
    }


def _feature_row(return_5m: str, polymarket_prob_gap: str) -> dict[str, str]:
    return {
        "return_1m": return_5m,
        "return_5m": return_5m,
        "realized_vol_5m": "0.0004",
        "distance_to_barrier_bps": "5.0",
        "range_1m_bps": "3.0",
        "range_5m_bps": "10.0",
        "polymarket_prob_gap": polymarket_prob_gap,
    }


if __name__ == "__main__":
    unittest.main()
