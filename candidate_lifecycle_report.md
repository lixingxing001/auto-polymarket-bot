# Candidate Lifecycle Report

## Executive decision

- next_action: keep_canary_blocked_and_collect_or_replace_candidates
- guardrail_stage: change_review_ready
- forward_trades: 49
- forward_win_rate: 42.9%
- forward_total_pnl_usd: -25.74
- change_review_status: DEFER_CHANGE
- change_allowed: False
- selected_candidate_id: none

## Lifecycle buckets

### PROMOTION_READY

- none

### REVIEW_READY

- none

### COLLECTING

- avoid_trade_against_1m_momentum_v2

### REJECT_RECOMMENDED

- none

### REJECTED

- avoid_low_momentum_near_barrier
- avoid_mid_abs_return_5m
- avoid_mid_distance_to_barrier_2_6bps
- avoid_trade_against_1m_momentum
- avoid_trade_against_5m_momentum
- confidence_070
- edge_008

## Candidate details

| candidate_id | status | lifecycle | action | review_ready | delta_pnl | candidate_trades | candidate_win_rate | blockers | rationale |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| avoid_trade_against_1m_momentum_v2 | registered | COLLECTING | collect_more_forward_evidence | False | 0.00 | 0 | 0.0% | candidate_evidence_not_review_ready, delta_pnl_not_positive, candidate_pnl_not_positive, insufficient_candidate_trades, candidate_trade_retention_too_low | needs_more_evidence:eligible_windows=30,divergent_windows=10 |
| avoid_trade_against_1m_momentum | rejected | REJECTED | keep_excluded_from_change_review | False | 55.09 | 9 | 66.7% | candidate_evidence_not_review_ready, insufficient_candidate_trades | candidate_status_not_active |
| edge_008 | rejected | REJECTED | keep_excluded_from_change_review | False | 31.49 | 10 | 50.0% | candidate_evidence_not_review_ready, candidate_pnl_not_positive | candidate_status_not_active |
| avoid_trade_against_5m_momentum | rejected | REJECTED | keep_excluded_from_change_review | True | 21.79 | 7 | 42.9% | candidate_pnl_not_positive, insufficient_candidate_trades, candidate_trade_retention_too_low | candidate_status_not_active |
| avoid_mid_abs_return_5m | rejected | REJECTED | keep_excluded_from_change_review | True | 20.71 | 12 | 33.3% | candidate_pnl_not_positive | candidate_status_not_active |
| avoid_mid_distance_to_barrier_2_6bps | rejected | REJECTED | keep_excluded_from_change_review | True | 15.67 | 15 | 40.0% | candidate_pnl_not_positive | candidate_status_not_active |
| confidence_070 | rejected | REJECTED | keep_excluded_from_change_review | True | 12.51 | 13 | 46.2% | candidate_pnl_not_positive | candidate_status_not_active |
| avoid_low_momentum_near_barrier | rejected | REJECTED | keep_excluded_from_change_review | True | 4.24 | 16 | 37.5% | candidate_pnl_not_positive | candidate_status_not_active |

## Boundary

This report manages candidate evidence only. It does not freeze parameters, enable live trading or submit orders.
