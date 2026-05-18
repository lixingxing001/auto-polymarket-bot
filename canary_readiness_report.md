# Canary Readiness Report

## Status

- ready: False

## Blockers

- guardrail_stage_collecting
- insufficient_forward_evaluations
- insufficient_forward_trades
- no_candidate_review_ready

## Warnings

- candidate_evidence_still_collecting

## Core metrics

- forward_evaluations: 31
- forward_trades: 2
- forward_win_rate: 1.0
- forward_total_pnl_usd: 12.423176470588238
- guardrail_stage: collecting
- next_change_review_gap: {'evaluations_needed': 69, 'trades_needed': 28}
- candidate_count: 3
- review_ready_candidates: []
- collecting_candidates: ['avoid_low_momentum_near_barrier', 'avoid_mid_abs_return_5m', 'edge_008']
- accepted_attempts: 1
- rejected_attempts: 2

## Candidate evidence

### avoid_low_momentum_near_barrier

- filter_kind: avoid_low_momentum_near_barrier
- stage: collecting
- eligible_windows: 21
- divergent_windows: 4
- delta_pnl_usd: -9.264843137254903
- next_review_gap: {'eligible_windows_needed': 9, 'divergent_windows_needed': 6}

### avoid_mid_abs_return_5m

- filter_kind: avoid_mid_abs_return_5m
- stage: collecting
- eligible_windows: 19
- divergent_windows: 1
- delta_pnl_usd: 0.0
- next_review_gap: {'eligible_windows_needed': 11, 'divergent_windows_needed': 9}

### edge_008

- filter_kind: none
- stage: collecting
- eligible_windows: 24
- divergent_windows: 1
- delta_pnl_usd: 10.553
- next_review_gap: {'eligible_windows_needed': 6, 'divergent_windows_needed': 9}
