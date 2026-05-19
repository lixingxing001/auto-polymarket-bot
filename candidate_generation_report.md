# Candidate Generation Report

## Target

- forward_win_rate_goal: 60%
- live_order_goal: canary_after_readiness_and_explicit_lee_authorization

## Current forward state

- forward_evaluations: 204
- forward_trades: 30
- forward_win_rate: 43.3%
- forward_total_pnl_usd: 48.10

## Diagnostic flags

- recent_win_rate_below_full_forward_set
- recent_hit_rate_too_weak_for_canary
- recent_contrarian_trades_underperform

## Proposed next candidates

| candidate_id | filter_kind | action | source | trades | win_rate | pnl |
|---|---:|---:|---:|---:|---:|---:|
| avoid_trade_against_1m_momentum | avoid_trade_against_1m_momentum | collect_prospective_evidence | trade_vs_1m_momentum=against_momentum | 7 | 14.3% | -18.39 |
| avoid_trade_against_5m_momentum | avoid_trade_against_5m_momentum | collect_prospective_evidence | trade_vs_5m_momentum=against_momentum | 6 | 16.7% | -48.10 |
| confidence_070 | none | collect_prospective_evidence | confidence=0.65-0.70 | 5 | 20.0% | -34.01 |

## Next commands

- `python -m btc5m_bot.strategy_candidate_cli compare --candidate-id avoid_trade_against_1m_momentum`
- `python -m btc5m_bot.strategy_candidate_cli compare --candidate-id avoid_trade_against_5m_momentum`
- `python -m btc5m_bot.strategy_candidate_cli compare --candidate-id confidence_070`

## Boundary

This report proposes prospective candidates only. It does not promote parameters, enable live trading or submit orders.
