# Canary Readiness Report

## Status

- ready: False

## Blockers

- guardrail_stage_review_only
- insufficient_forward_trades
- forward_win_rate_below_canary_floor

## Warnings

- none

## Core metrics

- forward_evaluations: 135
- forward_trades: 18
- forward_win_rate: 0.4444444444444444
- forward_total_pnl_usd: 53.66933580337976
- guardrail_stage: review_only
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 12}
- candidate_count: 3
- review_ready_candidates: ['avoid_low_momentum_near_barrier', 'avoid_mid_abs_return_5m', 'edge_008']
- collecting_candidates: []
- accepted_attempts: 1
- rejected_attempts: 2

## Candidate evidence

### avoid_low_momentum_near_barrier

- filter_kind: avoid_low_momentum_near_barrier
- stage: review_ready
- eligible_windows: 87
- divergent_windows: 25
- delta_pnl_usd: 11.512156862745094
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### avoid_mid_abs_return_5m

- filter_kind: avoid_mid_abs_return_5m
- stage: review_ready
- eligible_windows: 87
- divergent_windows: 30
- delta_pnl_usd: 20.308761679384396
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### edge_008

- filter_kind: none
- stage: review_ready
- eligible_windows: 87
- divergent_windows: 11
- delta_pnl_usd: -40.717192585192585
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}
