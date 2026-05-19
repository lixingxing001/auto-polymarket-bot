# Candidate Change Review Report

## Decision

- status: DEFER_CHANGE
- selected_candidate_id: avoid_mid_abs_return_5m
- change_allowed: False

## Blockers

- guardrail_stage_review_only

## Warnings

- selected_candidate_win_rate_below_canary_floor

## Guardrail snapshot

- stage: review_only
- review_ready: True
- change_review_ready: False
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 10}

## Forward snapshot

- evaluations: 141
- traded_rows: 20
- win_rate: 0.4
- total_pnl_usd: 32.570335803379756

## Candidate reviews

### avoid_mid_abs_return_5m

- filter_kind: avoid_mid_abs_return_5m
- review_ready: True
- change_quality_passed: True
- blockers: []
- warnings: ['candidate_win_rate_below_half', 'candidate_win_rate_below_active']
- active_trades: 19
- candidate_trades: 13
- candidate_win_rate: 0.46153846153846156
- trade_retention: 0.6842105263157895
- active_total_pnl_usd: 61.72964960069355
- candidate_total_pnl_usd: 71.48541128007795
- delta_pnl_usd: 9.755761679384406

### avoid_low_momentum_near_barrier

- filter_kind: avoid_low_momentum_near_barrier
- review_ready: True
- change_quality_passed: True
- blockers: []
- warnings: ['candidate_win_rate_below_half', 'candidate_win_rate_below_active']
- active_trades: 19
- candidate_trades: 17
- candidate_win_rate: 0.47058823529411764
- trade_retention: 0.8947368421052632
- active_total_pnl_usd: 61.72964960069355
- candidate_total_pnl_usd: 62.88480646343865
- delta_pnl_usd: 1.1551568627451019

### edge_008

- filter_kind: none
- review_ready: False
- change_quality_passed: False
- blockers: ['candidate_evidence_not_review_ready', 'delta_pnl_not_positive']
- warnings: ['candidate_win_rate_below_half', 'candidate_win_rate_below_active']
- active_trades: 19
- candidate_trades: 11
- candidate_win_rate: 0.45454545454545453
- trade_retention: 0.5789473684210527
- active_total_pnl_usd: 61.72964960069355
- candidate_total_pnl_usd: 52.063457015500965
- delta_pnl_usd: -9.666192585192583

## Boundary

This report can approve only a manual freeze review. It does not enable live trading and it does not submit orders.
