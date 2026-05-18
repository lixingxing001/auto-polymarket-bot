import csv
import tempfile
import unittest
from pathlib import Path

from btc5m_bot.paper_loop import append_signal


class PaperLoopTests(unittest.TestCase):
    def test_append_signal_writes_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "signals.csv"
            append_signal(
                path,
                {
                    "timestamp": "2026-05-18T10:00:00+00:00",
                    "slug": "btc-updown-5m-1",
                    "decision": "HOLD",
                    "reason": "edge_too_small",
                    "features": {"return_1m": 0.0},
                },
            )
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["decision"], "HOLD")
        self.assertIn("return_1m", rows[0]["features_json"])


if __name__ == "__main__":
    unittest.main()
