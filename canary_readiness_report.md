# Canary Readiness Report

## Status

- ready: False

## Blockers

- guardrail_stage_collecting
- insufficient_forward_evaluations
- insufficient_forward_trades
- no_candidate_review_ready
- no_mock_submit_seen

## Warnings

- candidate_evidence_still_collecting

## Core metrics

- forward_evaluations: 28
- forward_trades: 2
- forward_win_rate: 1.0
- forward_total_pnl_usd: 12.423176470588238
- guardrail_stage: collecting
- next_change_review_gap: {'evaluations_needed': 72, 'trades_needed': 28}
- candidate_count: 3
- review_ready_candidates: []
- collecting_candidates: ['avoid_low_momentum_near_barrier', 'avoid_mid_abs_return_5m', 'edge_008']
- accepted_attempts: 0
- rejected_attempts: 2

## Candidate evidence

### avoid_low_momentum_near_barrier

- filter_kind: avoid_low_momentum_near_barrier
- stage: collecting
- eligible_windows: 18
- divergent_windows: 3
- delta_pnl_usd: -9.264843137254903
- next_review_gap: {'eligible_windows_needed': 12, 'divergent_windows_needed': 7}

### avoid_mid_abs_return_5m

- filter_kind: avoid_mid_abs_return_5m
- stage: collecting
- eligible_windows: 0
- divergent_windows: 0
- delta_pnl_usd: 0
- next_review_gap: {'eligible_windows_needed': 30, 'divergent_windows_needed': 10}

### edge_008

- filter_kind: none
- stage: collecting
- eligible_windows: 5
- divergent_windows: 0
- delta_pnl_usd: 0.0
- next_review_gap: {'eligible_windows_needed': 25, 'divergent_windows_needed': 10}
