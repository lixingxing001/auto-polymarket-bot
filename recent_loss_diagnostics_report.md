# Recent Loss Diagnostics Report

## Status

- forward_evaluations: 204
- forward_trades: 30
- forward_win_rate: 43.3%
- forward_total_pnl_usd: 48.10
- recent_trades: 12
- recent_win_rate: 41.7%
- recent_total_pnl_usd: -5.57
- tail_loss_streak: 0

## Diagnostic flags

- recent_win_rate_below_full_forward_set
- recent_hit_rate_too_weak_for_canary
- recent_contrarian_trades_underperform

## Full trade structure

- all_trades: 30
- all_wins: 13
- all_losses: 17
- all_win_rate: 43.3%
- all_total_pnl_usd: 48.10
- contrarian_trades: 18
- contrarian_win_rate: 22.2%
- contrarian_total_pnl_usd: 28.96
- aligned_trades: 12
- aligned_win_rate: 75.0%
- aligned_total_pnl_usd: 19.13

## PnL concentration

- positive_pnl_usd: 226.81
- negative_pnl_usd: -178.72
- largest_win_pnl_usd: 51.91
- largest_win_share_of_positive_pnl: 22.9%
- top_three_win_share_of_positive_pnl: 62.6%
- largest_loss_pnl_usd: -10.60

## Worst recent slices

| dimension | bucket | trades | win_rate | total_pnl_usd | avg_pnl_usd |
|---|---:|---:|---:|---:|---:|
| model_trade_alignment | contrarian | 7 | 14.3% | -18.39 | -2.63 |
| trade_vs_1m_momentum | against_momentum | 7 | 14.3% | -18.39 | -2.63 |
| trade_vs_5m_momentum | against_momentum | 6 | 16.7% | -48.10 | -8.02 |
| confidence | 0.65-0.70 | 5 | 20.0% | -34.01 | -6.80 |
| entry_price | <=0.20 | 5 | 20.0% | 2.66 | 0.53 |
| edge | 0.09+ | 4 | 25.0% | -23.87 | -5.97 |
| distance_to_barrier_bps | 6bps+ | 4 | 25.0% | 13.23 | 3.31 |
| abs_return_5m | 0.0003-0.0008 | 4 | 25.0% | 13.56 | 3.39 |
| return_5m_direction | positive | 9 | 33.3% | -45.43 | -5.05 |
| decision_side | DOWN | 9 | 33.3% | -8.24 | -0.92 |

## Recent loss rows

| market_start_utc | slug | label | decision | model_side | contrarian | prob_up | entry | edge | pnl_usd | ret_1m | ret_5m | pm_gap |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-05-19T02:20:00+00:00 | btc-updown-5m-1779157200 | UP | DOWN | UP | True | 0.666 | 0.250 | 0.071 | -10.53 | 0.000598 | 0.001243 | 0.010 |
| 2026-05-19T02:25:00+00:00 | btc-updown-5m-1779157500 | DOWN | UP | DOWN | True | 0.313 | 0.180 | 0.123 | -10.57 | -0.000725 | 0.001450 | -0.040 |
| 2026-05-19T03:00:00+00:00 | btc-updown-5m-1779159600 | UP | DOWN | DOWN | False | 0.316 | 0.630 | 0.037 | -10.26 | -0.000324 | -0.000573 | -0.165 |
| 2026-05-19T04:30:00+00:00 | btc-updown-5m-1779165000 | UP | DOWN | UP | True | 0.714 | 0.180 | 0.095 | -10.57 | 0.000552 | 0.000625 | 0.120 |
| 2026-05-19T04:35:00+00:00 | btc-updown-5m-1779165300 | UP | DOWN | UP | True | 0.786 | 0.160 | 0.045 | -10.59 | 0.000726 | 0.001080 | -0.025 |
| 2026-05-19T04:40:00+00:00 | btc-updown-5m-1779165600 | UP | DOWN | UP | True | 0.728 | 0.160 | 0.102 | -10.59 | 0.000739 | 0.000423 | -0.070 |
| 2026-05-19T07:05:00+00:00 | btc-updown-5m-1779174300 | UP | DOWN | UP | True | 0.663 | 0.260 | 0.063 | -10.52 | 0.000315 | 0.000180 | 0.050 |

## Boundary

This report diagnoses forward paper trades only. It does not approve strategy changes, enable real trading or submit orders.
