# Canary Readiness Report

## Status

- ready: False

## Blockers

- forward_win_rate_below_canary_floor

## Warnings

- candidate_evidence_still_collecting

## Core metrics

- forward_evaluations: 199
- forward_trades: 30
- forward_win_rate: 0.43333333333333335
- forward_total_pnl_usd: 48.098698059697234
- guardrail_stage: change_review_ready
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 0}
- candidate_count: 5
- review_ready_candidates: ['avoid_low_momentum_near_barrier', 'avoid_mid_abs_return_5m', 'edge_008']
- collecting_candidates: ['avoid_mid_distance_to_barrier_2_6bps', 'confidence_070']
- accepted_attempts: 1
- rejected_attempts: 2

## Candidate evidence

### avoid_low_momentum_near_barrier

- filter_kind: avoid_low_momentum_near_barrier
- stage: review_ready
- eligible_windows: 87
- divergent_windows: 27
- delta_pnl_usd: 0.0
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### avoid_mid_abs_return_5m

- filter_kind: avoid_mid_abs_return_5m
- stage: review_ready
- eligible_windows: 87
- divergent_windows: 34
- delta_pnl_usd: -13.560555555555553
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### avoid_mid_distance_to_barrier_2_6bps

- filter_kind: avoid_mid_distance_to_barrier_bps
- stage: collecting
- eligible_windows: 0
- divergent_windows: 0
- delta_pnl_usd: 0
- next_review_gap: {'eligible_windows_needed': 30, 'divergent_windows_needed': 10}

### confidence_070

- filter_kind: none
- stage: collecting
- eligible_windows: 21
- divergent_windows: 3
- delta_pnl_usd: 2.6511818181818203
- next_review_gap: {'eligible_windows_needed': 9, 'divergent_windows_needed': 7}

### edge_008

- filter_kind: none
- stage: review_ready
- eligible_windows: 87
- divergent_windows: 10
- delta_pnl_usd: -44.75317094017093
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}
