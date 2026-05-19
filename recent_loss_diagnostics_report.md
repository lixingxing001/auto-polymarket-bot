# Recent Loss Diagnostics Report

## Status

- forward_evaluations: 303
- forward_trades: 49
- forward_win_rate: 42.9%
- forward_total_pnl_usd: -25.74
- recent_trades: 12
- recent_win_rate: 41.7%
- recent_total_pnl_usd: -51.46
- tail_loss_streak: 0

## Diagnostic flags

- recent_win_rate_below_full_forward_set
- recent_hit_rate_too_weak_for_canary
- recent_contrarian_trades_underperform

## Full trade structure

- all_trades: 49
- all_wins: 21
- all_losses: 28
- all_win_rate: 42.9%
- all_total_pnl_usd: -25.74
- contrarian_trades: 26
- contrarian_win_rate: 15.4%
- contrarian_total_pnl_usd: -55.45
- aligned_trades: 23
- aligned_win_rate: 73.9%
- aligned_total_pnl_usd: 29.71

## PnL concentration

- positive_pnl_usd: 268.01
- negative_pnl_usd: -293.75
- largest_win_pnl_usd: 51.91
- largest_win_share_of_positive_pnl: 19.4%
- top_three_win_share_of_positive_pnl: 52.9%
- largest_loss_pnl_usd: -10.63

## Worst recent slices

| dimension | bucket | trades | win_rate | total_pnl_usd | avg_pnl_usd |
|---|---:|---:|---:|---:|---:|
| model_trade_alignment | contrarian | 4 | 0.0% | -42.27 | -10.57 |
| trade_vs_1m_momentum | against_momentum | 4 | 0.0% | -42.27 | -10.57 |
| return_5m_direction | positive | 5 | 20.0% | -36.15 | -7.23 |
| decision_side | DOWN | 4 | 25.0% | -29.73 | -7.43 |
| model_side | DOWN | 4 | 25.0% | -29.70 | -7.42 |
| return_1m_direction | negative | 4 | 25.0% | -29.70 | -7.42 |
| abs_return_5m | 0.0008+ | 6 | 33.3% | -36.36 | -6.06 |
| abs_return_5m | 0.0003-0.0008 | 3 | 33.3% | -17.79 | -5.93 |
| edge | 0.03-0.06 | 3 | 33.3% | -17.24 | -5.75 |
| trade_vs_5m_momentum | with_momentum | 5 | 40.0% | -23.58 | -4.72 |

## Recent loss rows

| market_start_utc | slug | label | decision | model_side | contrarian | prob_up | entry | edge | pnl_usd | ret_1m | ret_5m | pm_gap |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-05-19T12:15:00+00:00 | btc-updown-5m-1779192900 | UP | DOWN | UP | True | 0.664 | 0.260 | 0.063 | -10.52 | 0.000416 | 0.000691 | 0.010 |
| 2026-05-19T13:05:00+00:00 | btc-updown-5m-1779195900 | DOWN | UP | DOWN | True | 0.332 | 0.260 | 0.059 | -10.52 | -0.001137 | -0.001297 | 0.240 |
| 2026-05-19T13:15:00+00:00 | btc-updown-5m-1779196500 | DOWN | UP | UP | False | 0.731 | 0.670 | 0.045 | -10.23 | 0.000252 | 0.000202 | 0.270 |
| 2026-05-19T14:25:00+00:00 | btc-updown-5m-1779200700 | UP | DOWN | DOWN | False | 0.226 | 0.660 | 0.098 | -10.24 | -0.000805 | -0.000950 | -0.055 |
| 2026-05-19T14:45:00+00:00 | btc-updown-5m-1779201900 | DOWN | UP | DOWN | True | 0.216 | 0.140 | 0.068 | -10.60 | -0.000770 | -0.000719 | -0.150 |
| 2026-05-19T15:15:00+00:00 | btc-updown-5m-1779203700 | DOWN | UP | UP | False | 0.909 | 0.790 | 0.108 | -10.15 | 0.000983 | 0.001846 | 0.130 |
| 2026-05-19T15:30:00+00:00 | btc-updown-5m-1779204600 | UP | DOWN | UP | True | 0.792 | 0.100 | 0.102 | -10.63 | 0.000955 | 0.001967 | -0.090 |

## Boundary

This report diagnoses forward paper trades only. It does not approve strategy changes, enable real trading or submit orders.
