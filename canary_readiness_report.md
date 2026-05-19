# Canary Readiness Report

## Status

- ready: False

## Blockers

- forward_pnl_not_positive
- forward_win_rate_below_canary_floor
- no_candidate_review_ready
- no_candidate_passed_change_quality

## Warnings

- candidate_evidence_still_collecting

## Core metrics

- forward_evaluations: 303
- forward_trades: 49
- forward_win_rate: 0.42857142857142855
- forward_total_pnl_usd: -25.741933118800908
- guardrail_stage: change_review_ready
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 0}
- candidate_count: 8
- active_candidate_count: 1
- review_ready_candidates: []
- quality_passed_candidates: []
- collecting_candidates: ['avoid_trade_against_1m_momentum_v2']
- accepted_attempts: 1
- rejected_attempts: 2

## Candidate evidence

### avoid_low_momentum_near_barrier

- filter_kind: avoid_low_momentum_near_barrier
- status: rejected
- active: False
- stage: review_ready
- change_quality_passed: False
- change_blockers: ['candidate_pnl_not_positive']
- eligible_windows: 84
- divergent_windows: 22
- delta_pnl_usd: 4.243557377049179
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### avoid_mid_abs_return_5m

- filter_kind: avoid_mid_abs_return_5m
- status: rejected
- active: False
- stage: review_ready
- change_quality_passed: False
- change_blockers: ['candidate_pnl_not_positive']
- eligible_windows: 84
- divergent_windows: 28
- delta_pnl_usd: 20.710364535266972
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### avoid_mid_distance_to_barrier_2_6bps

- filter_kind: avoid_mid_distance_to_barrier_bps
- status: rejected
- active: False
- stage: review_ready
- change_quality_passed: False
- change_blockers: ['candidate_pnl_not_positive']
- eligible_windows: 84
- divergent_windows: 33
- delta_pnl_usd: 15.670000000000002
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### avoid_trade_against_1m_momentum

- filter_kind: avoid_trade_against_1m_momentum
- status: rejected
- active: False
- stage: collecting
- change_quality_passed: False
- change_blockers: ['candidate_evidence_not_review_ready', 'insufficient_candidate_trades']
- eligible_windows: 84
- divergent_windows: 9
- delta_pnl_usd: 55.089
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 1}

### avoid_trade_against_1m_momentum_v2

- filter_kind: avoid_trade_against_1m_momentum
- status: registered
- active: True
- stage: collecting
- change_quality_passed: False
- change_blockers: ['candidate_evidence_not_review_ready', 'delta_pnl_not_positive', 'candidate_pnl_not_positive', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- eligible_windows: 0
- divergent_windows: 0
- delta_pnl_usd: 0
- next_review_gap: {'eligible_windows_needed': 30, 'divergent_windows_needed': 10}

### avoid_trade_against_5m_momentum

- filter_kind: avoid_trade_against_5m_momentum
- status: rejected
- active: False
- stage: review_ready
- change_quality_passed: False
- change_blockers: ['candidate_pnl_not_positive', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- eligible_windows: 84
- divergent_windows: 11
- delta_pnl_usd: 21.79012140712141
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### confidence_070

- filter_kind: none
- status: rejected
- active: False
- stage: review_ready
- change_quality_passed: False
- change_blockers: ['candidate_pnl_not_positive']
- eligible_windows: 84
- divergent_windows: 11
- delta_pnl_usd: 12.512999999999998
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### edge_008

- filter_kind: none
- status: rejected
- active: False
- stage: collecting
- change_quality_passed: False
- change_blockers: ['candidate_evidence_not_review_ready', 'candidate_pnl_not_positive']
- eligible_windows: 84
- divergent_windows: 8
- delta_pnl_usd: 31.486878048780486
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 2}
