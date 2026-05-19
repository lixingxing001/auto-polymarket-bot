# Candidate Change Review Report

## Decision

- status: DEFER_CHANGE
- selected_candidate_id: avoid_mid_abs_return_5m
- change_allowed: False

## Blockers

- guardrail_stage_review_only

## Warnings

- selected_candidate_win_rate_below_canary_floor

## Guardrail snapshot

- stage: review_only
- review_ready: True
- change_review_ready: False
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 12}

## Forward snapshot

- evaluations: 135
- traded_rows: 18
- win_rate: 0.4444444444444444
- total_pnl_usd: 53.66933580337976

## Candidate reviews

### avoid_mid_abs_return_5m

- filter_kind: avoid_mid_abs_return_5m
- review_ready: True
- change_quality_passed: True
- blockers: []
- warnings: ['candidate_win_rate_below_half']
- active_trades: 20
- candidate_trades: 13
- candidate_win_rate: 0.46153846153846156
- trade_retention: 0.65
- active_total_pnl_usd: 51.687649600693554
- candidate_total_pnl_usd: 71.99641128007795
- delta_pnl_usd: 20.308761679384396

### avoid_low_momentum_near_barrier

- filter_kind: avoid_low_momentum_near_barrier
- review_ready: True
- change_quality_passed: True
- blockers: []
- warnings: ['candidate_win_rate_below_half']
- active_trades: 20
- candidate_trades: 17
- candidate_win_rate: 0.47058823529411764
- trade_retention: 0.85
- active_total_pnl_usd: 51.687649600693554
- candidate_total_pnl_usd: 63.19980646343865
- delta_pnl_usd: 11.512156862745094

### edge_008

- filter_kind: none
- review_ready: True
- change_quality_passed: False
- blockers: ['delta_pnl_not_positive', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- warnings: ['candidate_win_rate_below_half', 'candidate_win_rate_below_active']
- active_trades: 20
- candidate_trades: 9
- candidate_win_rate: 0.4444444444444444
- trade_retention: 0.45
- active_total_pnl_usd: 51.687649600693554
- candidate_total_pnl_usd: 10.970457015500969
- delta_pnl_usd: -40.717192585192585

## Boundary

This report can approve only a manual freeze review. It does not enable live trading and it does not submit orders.
