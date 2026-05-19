# Candidate Change Review Report

## Decision

- status: DEFER_CHANGE
- selected_candidate_id: none
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

- evaluations: 224
- traded_rows: 32
- win_rate: 0.4375
- total_pnl_usd: 43.46473031776175

## Candidate reviews

### confidence_070

- filter_kind: none
- review_ready: True
- change_quality_passed: False
- blockers: ['insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- warnings: []
- active_trades: 8
- candidate_trades: 2
- candidate_win_rate: 1.0
- trade_retention: 0.25
- active_total_pnl_usd: -1.2455019174374051
- candidate_total_pnl_usd: 10.512615384615383
- delta_pnl_usd: 11.758117302052788

### avoid_mid_distance_to_barrier_2_6bps

- filter_kind: avoid_mid_distance_to_barrier_bps
- review_ready: False
- change_quality_passed: False
- blockers: ['candidate_evidence_not_review_ready', 'insufficient_candidate_trades']
- warnings: []
- active_trades: 3
- candidate_trades: 2
- candidate_win_rate: 1.0
- trade_retention: 0.6666666666666666
- active_total_pnl_usd: 1.2290645161290321
- candidate_total_pnl_usd: 11.726064516129032
- delta_pnl_usd: 10.497

### avoid_trade_against_1m_momentum

- filter_kind: avoid_trade_against_1m_momentum
- review_ready: False
- change_quality_passed: False
- blockers: ['candidate_evidence_not_review_ready', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- warnings: []
- active_trades: 3
- candidate_trades: 1
- candidate_win_rate: 1.0
- trade_retention: 0.3333333333333333
- active_total_pnl_usd: 1.2290645161290321
- candidate_total_pnl_usd: 5.863032258064516
- delta_pnl_usd: 4.633967741935484

### avoid_trade_against_5m_momentum

- filter_kind: avoid_trade_against_5m_momentum
- review_ready: False
- change_quality_passed: False
- blockers: ['candidate_evidence_not_review_ready', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- warnings: []
- active_trades: 3
- candidate_trades: 1
- candidate_win_rate: 1.0
- trade_retention: 0.3333333333333333
- active_total_pnl_usd: 1.2290645161290321
- candidate_total_pnl_usd: 5.863032258064516
- delta_pnl_usd: 4.633967741935484

## Excluded candidates

| candidate_id | status | reason |
|---|---:|---:|
| avoid_low_momentum_near_barrier | rejected | candidate_status_not_active |
| avoid_mid_abs_return_5m | rejected | candidate_status_not_active |
| edge_008 | rejected | candidate_status_not_active |

## Boundary

This report can approve only a manual freeze review. It does not enable live trading and it does not submit orders.
