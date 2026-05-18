import unittest
from datetime import datetime, timezone

from btc5m_bot.polymarket import Btc5mMarket
from btc5m_bot.ws_snapshot_recorder import (
    MutableOrderBook,
    apply_market_event,
    books_are_ready,
    parse_ws_messages,
    snapshot_row_from_books,
    subscription_message,
    top_of_book_signature,
)


class WebSocketSnapshotRecorderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.market = Btc5mMarket(
            slug="btc-updown-5m-1",
            title="BTC Up or Down",
            condition_id="c",
            end_time=datetime(2026, 5, 18, 15, 5, tzinfo=timezone.utc),
            up_token_id="up",
            down_token_id="down",
            accepting_orders=True,
        )
        self.books = {
            "up": MutableOrderBook("up"),
            "down": MutableOrderBook("down"),
        }

    def test_subscription_message_enables_custom_features(self) -> None:
        message = subscription_message(self.market)
        self.assertIn('"assets_ids": ["up", "down"]', message)
        self.assertIn('"custom_feature_enabled": true', message)

    def test_parse_ws_messages_handles_initial_book_batch(self) -> None:
        messages = parse_ws_messages(
            '[{"event_type":"book","asset_id":"up"},{"event_type":"book","asset_id":"down"}]'
        )
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["asset_id"], "up")

    def test_book_and_price_change_events_update_state(self) -> None:
        changed = apply_market_event(
            self.books,
            {
                "event_type": "book",
                "asset_id": "up",
                "bids": [{"price": "0.48", "size": "10"}],
                "asks": [{"price": "0.52", "size": "20"}],
            },
        )
        self.assertTrue(changed)
        self.assertFalse(books_are_ready(self.market, self.books))

        apply_market_event(
            self.books,
            {
                "event_type": "book",
                "asset_id": "down",
                "bids": [{"price": "0.47", "size": "15"}],
                "asks": [{"price": "0.53", "size": "25"}],
            },
        )
        self.assertTrue(books_are_ready(self.market, self.books))

        apply_market_event(
            self.books,
            {
                "event_type": "price_change",
                "price_changes": [
                    {
                        "asset_id": "up",
                        "price": "0.52",
                        "size": "0",
                        "side": "SELL",
                    },
                    {
                        "asset_id": "up",
                        "price": "0.51",
                        "size": "30",
                        "side": "SELL",
                    },
                ],
            },
        )

        self.assertNotIn(0.52, self.books["up"].asks)
        self.assertEqual(self.books["up"].asks[0.51], 30.0)

    def test_snapshot_row_from_books_uses_best_levels(self) -> None:
        apply_market_event(
            self.books,
            {
                "event_type": "book",
                "asset_id": "up",
                "bids": [{"price": "0.49", "size": "10"}],
                "asks": [{"price": "0.51", "size": "20"}],
            },
        )
        apply_market_event(
            self.books,
            {
                "event_type": "book",
                "asset_id": "down",
                "bids": [{"price": "0.48", "size": "11"}],
                "asks": [{"price": "0.52", "size": "21"}],
            },
        )

        row = snapshot_row_from_books(
            market=self.market,
            books=self.books,
            captured_at=datetime(2026, 5, 18, 15, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(row["up_best_bid"], 0.49)
        self.assertEqual(row["up_best_ask"], 0.51)
        self.assertEqual(row["down_best_bid_size"], 11.0)
        self.assertEqual(row["down_best_ask_size"], 21.0)

    def test_top_of_book_signature_ignores_non_best_levels(self) -> None:
        apply_market_event(
            self.books,
            {
                "event_type": "book",
                "asset_id": "up",
                "bids": [
                    {"price": "0.49", "size": "10"},
                    {"price": "0.40", "size": "50"},
                ],
                "asks": [
                    {"price": "0.51", "size": "20"},
                    {"price": "0.60", "size": "60"},
                ],
            },
        )
        apply_market_event(
            self.books,
            {
                "event_type": "book",
                "asset_id": "down",
                "bids": [{"price": "0.48", "size": "11"}],
                "asks": [{"price": "0.52", "size": "21"}],
            },
        )
        before = top_of_book_signature(self.market, self.books)

        apply_market_event(
            self.books,
            {
                "event_type": "price_change",
                "price_changes": [
                    {
                        "asset_id": "up",
                        "price": "0.40",
                        "size": "70",
                        "side": "BUY",
                    }
                ],
            },
        )

        self.assertEqual(before, top_of_book_signature(self.market, self.books))
