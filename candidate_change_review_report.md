# Candidate Change Review Report

## Decision

- status: DEFER_CHANGE
- selected_candidate_id: avoid_low_momentum_near_barrier
- change_allowed: False

## Blockers

- guardrail_stage_review_only
- no_candidate_passed_change_quality

## Warnings

- none

## Guardrail snapshot

- stage: review_only
- review_ready: True
- change_review_ready: False
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 4}

## Forward snapshot

- evaluations: 180
- traded_rows: 26
- win_rate: 0.38461538461538464
- total_pnl_usd: 40.23726449326367

## Candidate reviews

### avoid_low_momentum_near_barrier

- filter_kind: avoid_low_momentum_near_barrier
- review_ready: True
- change_quality_passed: False
- blockers: ['delta_pnl_not_positive']
- warnings: ['candidate_win_rate_below_half', 'candidate_win_rate_below_active']
- active_trades: 18
- candidate_trades: 16
- candidate_win_rate: 0.25
- trade_retention: 0.8888888888888888
- active_total_pnl_usd: 53.94724286612913
- candidate_total_pnl_usd: 39.60286973180077
- delta_pnl_usd: -14.344373134328357

### avoid_mid_abs_return_5m

- filter_kind: avoid_mid_abs_return_5m
- review_ready: True
- change_quality_passed: False
- blockers: ['delta_pnl_not_positive']
- warnings: ['candidate_win_rate_below_half']
- active_trades: 18
- candidate_trades: 11
- candidate_win_rate: 0.36363636363636365
- trade_retention: 0.6111111111111112
- active_total_pnl_usd: 53.94724286612913
- candidate_total_pnl_usd: 37.56292868988392
- delta_pnl_usd: -16.384314176245212

### edge_008

- filter_kind: none
- review_ready: True
- change_quality_passed: False
- blockers: ['delta_pnl_not_positive', 'candidate_pnl_not_positive', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- warnings: ['candidate_win_rate_below_half', 'candidate_win_rate_below_active']
- active_trades: 18
- candidate_trades: 8
- candidate_win_rate: 0.25
- trade_retention: 0.4444444444444444
- active_total_pnl_usd: 53.94724286612913
- candidate_total_pnl_usd: -8.756444444444442
- delta_pnl_usd: -62.70368731057357

### confidence_070

- filter_kind: none
- review_ready: False
- change_quality_passed: False
- blockers: ['candidate_evidence_not_review_ready', 'delta_pnl_not_positive', 'candidate_pnl_not_positive', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- warnings: ['candidate_win_rate_below_half']
- active_trades: 0
- candidate_trades: 0
- candidate_win_rate: 0.0
- trade_retention: 0.0
- active_total_pnl_usd: 0.0
- candidate_total_pnl_usd: 0.0
- delta_pnl_usd: 0.0

## Boundary

This report can approve only a manual freeze review. It does not enable live trading and it does not submit orders.
