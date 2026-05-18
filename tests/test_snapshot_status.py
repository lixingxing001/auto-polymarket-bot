import csv
import tempfile
import unittest
from pathlib import Path

from btc5m_bot.snapshot_status import read_snapshot_status


class SnapshotStatusTests(unittest.TestCase):
    def test_read_snapshot_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snapshots.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["captured_at", "slug", "seconds_to_close"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "captured_at": "2026-05-18T10:00:00+00:00",
                        "slug": "a",
                        "seconds_to_close": "240",
                    }
                )
                writer.writerow(
                    {
                        "captured_at": "2026-05-18T10:00:05+00:00",
                        "slug": "b",
                        "seconds_to_close": "235",
                    }
                )
            status = read_snapshot_status(path)
        self.assertEqual(status["snapshot_rows"], 2)
        self.assertEqual(status["window_count"], 2)
        self.assertEqual(status["latest_slug"], "b")


if __name__ == "__main__":
    unittest.main()
