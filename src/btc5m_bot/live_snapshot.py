from datetime import datetime, timezone

from .polymarket import PolymarketPublicClient


def main() -> None:
    client = PolymarketPublicClient()
    market = client.find_live_btc_5m_market()
    quote = client.quote_for_market(market)
    now = datetime.now(timezone.utc)
    seconds_to_close = max(0, int((market.end_time - now).total_seconds()))

    print(
        {
            "slug": market.slug,
            "title": market.title,
            "seconds_to_close": seconds_to_close,
            "up_ask": quote.up_ask,
            "down_ask": quote.down_ask,
            "up_liquidity_usd": round(quote.up_liquidity_usd, 2),
            "down_liquidity_usd": round(quote.down_liquidity_usd, 2),
        }
    )


if __name__ == "__main__":
    main()
