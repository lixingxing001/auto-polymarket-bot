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

- forward_evaluations: 141
- forward_trades: 20
- forward_win_rate: 0.4
- forward_total_pnl_usd: 32.570335803379756
- guardrail_stage: review_only
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 10}
- candidate_count: 3
- review_ready_candidates: ['avoid_low_momentum_near_barrier', 'avoid_mid_abs_return_5m']
- collecting_candidates: ['edge_008']
- accepted_attempts: 1
- rejected_attempts: 2

## Candidate evidence

### avoid_low_momentum_near_barrier

- filter_kind: avoid_low_momentum_near_barrier
- stage: review_ready
- eligible_windows: 87
- divergent_windows: 25
- delta_pnl_usd: 1.1551568627451019
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### avoid_mid_abs_return_5m

- filter_kind: avoid_mid_abs_return_5m
- stage: review_ready
- eligible_windows: 87
- divergent_windows: 28
- delta_pnl_usd: 9.755761679384406
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 0}

### edge_008

- filter_kind: none
- stage: collecting
- eligible_windows: 87
- divergent_windows: 8
- delta_pnl_usd: -9.666192585192583
- next_review_gap: {'eligible_windows_needed': 0, 'divergent_windows_needed': 2}
