# Candidate Generation Report

## Target

- forward_win_rate_goal: 60%
- live_order_goal: canary_after_readiness_and_explicit_lee_authorization

## Current forward state

- forward_evaluations: 303
- forward_trades: 49
- forward_win_rate: 42.9%
- forward_total_pnl_usd: -25.74

## Diagnostic flags

- recent_win_rate_below_full_forward_set
- recent_hit_rate_too_weak_for_canary
- recent_contrarian_trades_underperform

## Proposed next candidates

| candidate_id | filter_kind | action | source | trades | win_rate | pnl |
|---|---:|---:|---:|---:|---:|---:|
| avoid_trade_against_1m_momentum | avoid_trade_against_1m_momentum | collect_prospective_evidence | trade_vs_1m_momentum=against_momentum | 4 | 0.0% | -42.27 |

## Next commands

- `python -m btc5m_bot.strategy_candidate_cli compare --candidate-id avoid_trade_against_1m_momentum`

## Boundary

This report proposes prospective candidates only. It does not promote parameters, enable live trading or submit orders.
