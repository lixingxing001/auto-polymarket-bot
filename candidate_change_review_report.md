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

- evaluations: 303
- traded_rows: 49
- win_rate: 0.42857142857142855
- total_pnl_usd: -25.741933118800908

## Candidate reviews

### avoid_trade_against_1m_momentum_v2

- filter_kind: avoid_trade_against_1m_momentum
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

## Excluded candidates

| candidate_id | status | reason |
|---|---:|---:|
| avoid_low_momentum_near_barrier | rejected | candidate_status_not_active |
| avoid_mid_abs_return_5m | rejected | candidate_status_not_active |
| avoid_mid_distance_to_barrier_2_6bps | rejected | candidate_status_not_active |
| avoid_trade_against_1m_momentum | rejected | candidate_status_not_active |
| avoid_trade_against_5m_momentum | rejected | candidate_status_not_active |
| confidence_070 | rejected | candidate_status_not_active |
| edge_008 | rejected | candidate_status_not_active |

## Boundary

This report can approve only a manual freeze review. It does not enable live trading and it does not submit orders.
