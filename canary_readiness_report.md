# Canary Readiness Report

## Status

- ready: False

## Blockers

- guardrail_stage_review_only
- insufficient_forward_trades
- forward_win_rate_below_canary_floor

## Warnings

- candidate_evidence_still_collecting

## Core metrics

- forward_evaluations: 180
- forward_trades: 26
- forward_win_rate: 0.38461538461538464
- forward_total_pnl_usd: 40.23726449326367
- guardrail_stage: review_only
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 4}
- candidate_count: 4
- review_ready_candidates: ['avoid_low_momentum_near_barrier', 'avoid_mid_abs_return_5m', 'edge_008']
- collecting_candidates: ['confidence_070']
- accepted_attempts: 1
- rejected_attempts: 2

## Candidate evidence

### avoid_low_momentum_near_barrier

- filter_kind: avoid_low_momentum_near_barrier
- stage: review_ready
- eligible_windows: 87
- divergent_windows: 28
- delta_pnl_usd: -14.344373134328357
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### avoid_mid_abs_return_5m

- filter_kind: avoid_mid_abs_return_5m
- stage: review_ready
- eligible_windows: 87
- divergent_windows: 33
- delta_pnl_usd: -16.384314176245212
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### confidence_070

- filter_kind: none
- stage: collecting
- eligible_windows: 2
- divergent_windows: 0
- delta_pnl_usd: 0.0
- next_review_gap: {'eligible_windows_needed': 28, 'divergent_windows_needed': 10}

### edge_008

- filter_kind: none
- stage: review_ready
- eligible_windows: 87
- divergent_windows: 10
- delta_pnl_usd: -62.70368731057357
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}
