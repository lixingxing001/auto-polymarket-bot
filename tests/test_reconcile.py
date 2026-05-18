import csv
import tempfile
import unittest
from pathlib import Path

from btc5m_bot.reconcile import reconcile_paper_signals


class FakePolymarketClient:
    def get_event_by_slug(self, slug: str) -> dict:
        return {
            "markets": [
                {
                    "closed": True,
                    "outcomes": "[\"Up\", \"Down\"]",
                    "outcomePrices": "[\"1\", \"0\"]",
                }
            ]
        }


class ReconcileTests(unittest.TestCase):
    def test_reconcile_paper_signals_writes_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "signals.csv"
            output_path = Path(tmp) / "results.csv"
            with input_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "timestamp",
                        "slug",
                        "decision",
                        "edge",
                        "size_usd",
                        "reason",
                        "up_ask",
                        "down_ask",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "timestamp": "x",
                        "slug": "s",
                        "decision": "UP",
                        "edge": "0.1",
                        "size_usd": "10",
                        "reason": "edge_passed",
                        "up_ask": "0.5",
                        "down_ask": "0.5",
                    }
                )

            summary = reconcile_paper_signals(
                input_path=input_path,
                output_path=output_path,
                polymarket=FakePolymarketClient(),
            )
            with output_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(summary["settled_rows"], 1)
        self.assertEqual(summary["wins"], 1)
        self.assertEqual(rows[0]["resolved_outcome"], "UP")


if __name__ == "__main__":
    unittest.main()
