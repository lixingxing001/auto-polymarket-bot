# Candidate Change Review Report

## Decision

- status: DEFER_CHANGE
- selected_candidate_id: avoid_low_momentum_near_barrier
- change_allowed: False

## Blockers

- no_candidate_passed_change_quality

## Warnings

- none

## Guardrail snapshot

- stage: change_review_ready
- review_ready: True
- change_review_ready: True
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 0}

## Forward snapshot

- evaluations: 199
- traded_rows: 30
- win_rate: 0.43333333333333335
- total_pnl_usd: 48.098698059697234

## Candidate reviews

### avoid_low_momentum_near_barrier

- filter_kind: avoid_low_momentum_near_barrier
- review_ready: True
- change_quality_passed: False
- blockers: ['delta_pnl_not_positive']
- warnings: ['candidate_win_rate_below_half']
- active_trades: 16
- candidate_trades: 16
- candidate_win_rate: 0.375
- trade_retention: 1.0
- active_total_pnl_usd: 55.585544677544675
- candidate_total_pnl_usd: 55.585544677544675
- delta_pnl_usd: 0.0

### avoid_mid_abs_return_5m

- filter_kind: avoid_mid_abs_return_5m
- review_ready: True
- change_quality_passed: False
- blockers: ['delta_pnl_not_positive']
- warnings: ['candidate_win_rate_below_half']
- active_trades: 16
- candidate_trades: 12
- candidate_win_rate: 0.4166666666666667
- trade_retention: 0.75
- active_total_pnl_usd: 55.585544677544675
- candidate_total_pnl_usd: 42.02498912198912
- delta_pnl_usd: -13.560555555555553

### edge_008

- filter_kind: none
- review_ready: True
- change_quality_passed: False
- blockers: ['delta_pnl_not_positive', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- warnings: ['candidate_win_rate_below_half', 'candidate_win_rate_below_active']
- active_trades: 16
- candidate_trades: 6
- candidate_win_rate: 0.3333333333333333
- trade_retention: 0.375
- active_total_pnl_usd: 55.585544677544675
- candidate_total_pnl_usd: 10.83237373737374
- delta_pnl_usd: -44.75317094017093

### confidence_070

- filter_kind: none
- review_ready: False
- change_quality_passed: False
- blockers: ['candidate_evidence_not_review_ready', 'insufficient_candidate_trades']
- warnings: []
- active_trades: 4
- candidate_trades: 2
- candidate_win_rate: 1.0
- trade_retention: 0.5
- active_total_pnl_usd: 7.861433566433563
- candidate_total_pnl_usd: 10.512615384615383
- delta_pnl_usd: 2.6511818181818203

### avoid_mid_distance_to_barrier_2_6bps

- filter_kind: avoid_mid_distance_to_barrier_bps
- review_ready: False
- change_quality_passed: False
- blockers: ['candidate_evidence_not_review_ready', 'delta_pnl_not_positive', 'candidate_pnl_not_positive', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- warnings: ['candidate_win_rate_below_half']
- active_trades: 0
- candidate_trades: 0
- candidate_win_rate: 0.0
- trade_retention: 0.0
- active_total_pnl_usd: 0
- candidate_total_pnl_usd: 0
- delta_pnl_usd: 0

## Boundary

This report can approve only a manual freeze review. It does not enable live trading and it does not submit orders.
