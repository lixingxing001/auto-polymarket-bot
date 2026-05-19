# Recent Loss Diagnostics Report

## Status

- forward_evaluations: 180
- forward_trades: 26
- forward_win_rate: 38.5%
- forward_total_pnl_usd: 40.24
- recent_trades: 12
- recent_win_rate: 33.3%
- recent_total_pnl_usd: 62.65
- tail_loss_streak: 3

## Diagnostic flags

- recent_win_rate_below_full_forward_set
- recent_hit_rate_too_weak_for_canary
- positive_pnl_concentrated_in_top_winners
- active_tail_loss_streak
- recent_contrarian_trades_underperform

## Full trade structure

- all_trades: 26
- all_wins: 10
- all_losses: 16
- all_win_rate: 38.5%
- all_total_pnl_usd: 40.24
- contrarian_trades: 17
- contrarian_win_rate: 23.5%
- contrarian_total_pnl_usd: 39.48
- aligned_trades: 9
- aligned_win_rate: 66.7%
- aligned_total_pnl_usd: 0.75

## PnL concentration

- positive_pnl_usd: 208.43
- negative_pnl_usd: -168.20
- largest_win_pnl_usd: 51.91
- largest_win_share_of_positive_pnl: 24.9%
- top_three_win_share_of_positive_pnl: 68.1%
- largest_loss_pnl_usd: -10.60

## Worst recent slices

| dimension | bucket | trades | win_rate | total_pnl_usd | avg_pnl_usd |
|---|---:|---:|---:|---:|---:|
| confidence | 0.65-0.70 | 5 | 0.0% | -52.17 | -10.43 |
| distance_to_barrier_bps | 2-6bps | 4 | 0.0% | -41.89 | -10.47 |
| market_gap_alignment | with_market_gap | 5 | 20.0% | -37.02 | -7.40 |
| trade_vs_5m_momentum | with_momentum | 5 | 20.0% | 3.34 | 0.67 |
| return_5m_direction | positive | 8 | 25.0% | -6.52 | -0.82 |
| abs_return_5m | 0.0003-0.0008 | 4 | 25.0% | 13.56 | 3.39 |
| edge | 0.06-0.09 | 4 | 25.0% | 13.64 | 3.41 |
| edge | 0.09+ | 4 | 25.0% | 20.18 | 5.04 |
| model_side | UP | 8 | 25.0% | 33.81 | 4.23 |
| return_1m_direction | positive | 8 | 25.0% | 33.81 | 4.23 |

## Recent loss rows

| market_start_utc | slug | label | decision | model_side | contrarian | prob_up | entry | edge | pnl_usd | ret_1m | ret_5m | pm_gap |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-05-19T01:35:00+00:00 | btc-updown-5m-1779154500 | DOWN | UP | UP | False | 0.679 | 0.600 | 0.062 | -10.28 | 0.000152 | 0.002468 | 0.055 |
| 2026-05-19T02:05:00+00:00 | btc-updown-5m-1779156300 | UP | DOWN | UP | True | 0.663 | 0.240 | 0.084 | -10.53 | 0.000445 | -0.000824 | 0.090 |
| 2026-05-19T02:20:00+00:00 | btc-updown-5m-1779157200 | UP | DOWN | UP | True | 0.666 | 0.250 | 0.071 | -10.53 | 0.000598 | 0.001243 | 0.010 |
| 2026-05-19T02:25:00+00:00 | btc-updown-5m-1779157500 | DOWN | UP | DOWN | True | 0.313 | 0.180 | 0.123 | -10.57 | -0.000725 | 0.001450 | -0.040 |
| 2026-05-19T03:00:00+00:00 | btc-updown-5m-1779159600 | UP | DOWN | DOWN | False | 0.316 | 0.630 | 0.037 | -10.26 | -0.000324 | -0.000573 | -0.165 |
| 2026-05-19T04:30:00+00:00 | btc-updown-5m-1779165000 | UP | DOWN | UP | True | 0.714 | 0.180 | 0.095 | -10.57 | 0.000552 | 0.000625 | 0.120 |
| 2026-05-19T04:35:00+00:00 | btc-updown-5m-1779165300 | UP | DOWN | UP | True | 0.786 | 0.160 | 0.045 | -10.59 | 0.000726 | 0.001080 | -0.025 |
| 2026-05-19T04:40:00+00:00 | btc-updown-5m-1779165600 | UP | DOWN | UP | True | 0.728 | 0.160 | 0.102 | -10.59 | 0.000739 | 0.000423 | -0.070 |

## Boundary

This report diagnoses forward paper trades only. It does not approve strategy changes, enable real trading or submit orders.
