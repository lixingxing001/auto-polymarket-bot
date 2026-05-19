# Canary Readiness Report

## Status

- ready: False

## Blockers

- forward_win_rate_below_canary_floor
- no_candidate_review_ready
- no_candidate_passed_change_quality

## Warnings

- candidate_evidence_still_collecting

## Core metrics

- forward_evaluations: 204
- forward_trades: 30
- forward_win_rate: 0.43333333333333335
- forward_total_pnl_usd: 48.098698059697234
- guardrail_stage: change_review_ready
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 0}
- candidate_count: 7
- active_candidate_count: 4
- review_ready_candidates: []
- quality_passed_candidates: []
- collecting_candidates: ['avoid_mid_distance_to_barrier_2_6bps', 'avoid_trade_against_1m_momentum', 'avoid_trade_against_5m_momentum', 'confidence_070']
- accepted_attempts: 1
- rejected_attempts: 2

## Candidate evidence

### avoid_low_momentum_near_barrier

- filter_kind: avoid_low_momentum_near_barrier
- status: rejected
- active: False
- stage: review_ready
- change_quality_passed: False
- change_blockers: ['delta_pnl_not_positive']
- eligible_windows: 87
- divergent_windows: 27
- delta_pnl_usd: 0.0
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### avoid_mid_abs_return_5m

- filter_kind: avoid_mid_abs_return_5m
- status: rejected
- active: False
- stage: review_ready
- change_quality_passed: False
- change_blockers: ['delta_pnl_not_positive']
- eligible_windows: 87
- divergent_windows: 33
- delta_pnl_usd: -13.560555555555553
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### avoid_mid_distance_to_barrier_2_6bps

- filter_kind: avoid_mid_distance_to_barrier_bps
- status: registered
- active: True
- stage: collecting
- change_quality_passed: False
- change_blockers: ['candidate_evidence_not_review_ready', 'delta_pnl_not_positive', 'candidate_pnl_not_positive', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- eligible_windows: 5
- divergent_windows: 2
- delta_pnl_usd: 0.0
- next_review_gap: {'eligible_windows_needed': 25, 'divergent_windows_needed': 8}

### avoid_trade_against_1m_momentum

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
- status: registered
- active: True
- stage: collecting
- change_quality_passed: False
- change_blockers: ['candidate_evidence_not_review_ready', 'delta_pnl_not_positive', 'candidate_pnl_not_positive', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- eligible_windows: 0
- divergent_windows: 0
- delta_pnl_usd: 0
- next_review_gap: {'eligible_windows_needed': 30, 'divergent_windows_needed': 10}

### confidence_070

- filter_kind: none
- status: registered
- active: True
- stage: collecting
- change_quality_passed: False
- change_blockers: ['candidate_evidence_not_review_ready', 'insufficient_candidate_trades']
- eligible_windows: 26
- divergent_windows: 4
- delta_pnl_usd: 2.6511818181818203
- next_review_gap: {'eligible_windows_needed': 4, 'divergent_windows_needed': 6}

### edge_008

- filter_kind: none
- status: rejected
- active: False
- stage: review_ready
- change_quality_passed: False
- change_blockers: ['delta_pnl_not_positive', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- eligible_windows: 87
- divergent_windows: 10
- delta_pnl_usd: -44.75317094017093
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}
