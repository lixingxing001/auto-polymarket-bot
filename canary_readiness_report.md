# Canary Readiness Report

## Status

- ready: False

## Blockers

- forward_win_rate_below_canary_floor
- no_candidate_passed_change_quality

## Warnings

- candidate_evidence_still_collecting

## Core metrics

- forward_evaluations: 224
- forward_trades: 32
- forward_win_rate: 0.4375
- forward_total_pnl_usd: 43.46473031776175
- guardrail_stage: change_review_ready
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 0}
- candidate_count: 7
- active_candidate_count: 4
- review_ready_candidates: ['confidence_070']
- quality_passed_candidates: []
- collecting_candidates: ['avoid_mid_distance_to_barrier_2_6bps', 'avoid_trade_against_1m_momentum', 'avoid_trade_against_5m_momentum']
- accepted_attempts: 1
- rejected_attempts: 2

## Candidate evidence

### avoid_low_momentum_near_barrier

- filter_kind: avoid_low_momentum_near_barrier
- status: rejected
- active: False
- stage: review_ready
- change_quality_passed: True
- change_blockers: []
- eligible_windows: 82
- divergent_windows: 32
- delta_pnl_usd: 4.472967741935484
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### avoid_mid_abs_return_5m

- filter_kind: avoid_mid_abs_return_5m
- status: rejected
- active: False
- stage: review_ready
- change_quality_passed: False
- change_blockers: ['delta_pnl_not_positive', 'candidate_pnl_not_positive', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- eligible_windows: 82
- divergent_windows: 43
- delta_pnl_usd: -4.45362007168459
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### avoid_mid_distance_to_barrier_2_6bps

- filter_kind: avoid_mid_distance_to_barrier_bps
- status: registered
- active: True
- stage: collecting
- change_quality_passed: False
- change_blockers: ['candidate_evidence_not_review_ready', 'insufficient_candidate_trades']
- eligible_windows: 25
- divergent_windows: 13
- delta_pnl_usd: 10.497
- next_review_gap: {'eligible_windows_needed': 5, 'divergent_windows_needed': 0}

### avoid_trade_against_1m_momentum

- filter_kind: avoid_trade_against_1m_momentum
- status: registered
- active: True
- stage: collecting
- change_quality_passed: False
- change_blockers: ['candidate_evidence_not_review_ready', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- eligible_windows: 20
- divergent_windows: 2
- delta_pnl_usd: 4.633967741935484
- next_review_gap: {'eligible_windows_needed': 10, 'divergent_windows_needed': 8}

### avoid_trade_against_5m_momentum

- filter_kind: avoid_trade_against_5m_momentum
- status: registered
- active: True
- stage: collecting
- change_quality_passed: False
- change_blockers: ['candidate_evidence_not_review_ready', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- eligible_windows: 20
- divergent_windows: 2
- delta_pnl_usd: 4.633967741935484
- next_review_gap: {'eligible_windows_needed': 10, 'divergent_windows_needed': 8}

### confidence_070

- filter_kind: none
- status: registered
- active: True
- stage: review_ready
- change_quality_passed: False
- change_blockers: ['insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- eligible_windows: 46
- divergent_windows: 10
- delta_pnl_usd: 11.758117302052788
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### edge_008

- filter_kind: none
- status: rejected
- active: False
- stage: collecting
- change_quality_passed: False
- change_blockers: ['candidate_evidence_not_review_ready', 'delta_pnl_not_positive', 'candidate_pnl_not_positive', 'insufficient_candidate_trades', 'candidate_trade_retention_too_low']
- eligible_windows: 82
- divergent_windows: 9
- delta_pnl_usd: -25.358235456299973
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 1}
