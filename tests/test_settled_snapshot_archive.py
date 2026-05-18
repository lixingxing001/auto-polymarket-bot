import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from btc5m_bot.settled_snapshot_archive import archive_settled_snapshot_windows


class FakePolymarketClient:
    def get_event_by_slug(self, slug: str) -> dict:
        return {
            "markets": [
                {
                    "closed": True,
                    "outcomes": '["Up", "Down"]',
                    "outcomePrices": '["1", "0"]',
                }
            ]
        }


class SettledSnapshotArchiveTests(unittest.TestCase):
    def test_archive_settled_snapshot_windows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snapshot_path = Path(tmp) / "snapshots.csv"
            archive_path = Path(tmp) / "archive.csv"
            snapshot_path.write_text(
                "\n".join(
                    [
                        "captured_at,slug,condition_id,title,market_end_time,seconds_to_close,up_token_id,down_token_id,up_best_bid,up_best_bid_size,up_best_ask,up_best_ask_size,down_best_bid,down_best_bid_size,down_best_ask,down_best_ask_size",
                        "2026-05-18T14:30:01+00:00,s1,c1,t,2026-05-18T14:35:00+00:00,299,u,d,0.49,10,0.51,20,0.48,11,0.52,21",
                        "2026-05-18T14:30:02+00:00,s1,c1,t,2026-05-18T14:35:00+00:00,298,u,d,0.50,12,0.53,22,0.47,13,0.54,23",
                    ]
                ),
                encoding="utf-8",
            )
            summary = archive_settled_snapshot_windows(
                snapshot_path=snapshot_path,
                archive_path=archive_path,
                polymarket=FakePolymarketClient(),
                now=datetime(2026, 5, 18, 14, 40, tzinfo=timezone.utc),
            )

            self.assertEqual(summary["newly_archived_windows"], 1)
            content = archive_path.read_text(encoding="utf-8")
            self.assertIn("s1", content)
            self.assertIn("UP", content)
