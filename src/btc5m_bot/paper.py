from .models import TradeDecision


def settle_binary_trade(decision: TradeDecision, outcome: str, entry_price: float) -> float:
    """
    Return PnL in USD for a paper trade that buys binary shares.
    """
    if decision.side == "HOLD":
        return 0.0

    shares = decision.size_usd / entry_price
    gross_payout = shares if decision.side == outcome else 0.0
    return gross_payout - decision.size_usd
