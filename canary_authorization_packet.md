# Canary Authorization Packet

## Status

- status: NOT_READY

## Blockers

- guardrail_stage_collecting
- insufficient_forward_evaluations
- insufficient_forward_trades
- no_candidate_review_ready

## Warnings

- candidate_evidence_still_collecting

## Canary envelope

- max_order_stake_usd: 1.0
- max_daily_loss_usd: 3.0
- max_daily_trades: 3
- max_open_exposures: 1
- max_consecutive_losses: 2
- canary_duration_hours: 24
- funding_cap_usdc: 10.0

## Operator checklist

- [ ] Confirm canary readiness report is ready true
- [ ] Confirm kill switch report is active false
- [ ] Fund isolated wallet with at most 10.0 USDC
- [ ] Keep private key out of git, reports and logs
- [ ] Set max order stake to 1.0 USDC
- [ ] Set daily loss cap to 3.0 USDC
- [ ] Run mock execution smoke before any canary attempt
- [ ] Manually authorize canary in this thread before enabling real adapter

## Readiness snapshot

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

## Kill switch snapshot

# Canary Kill Switch Report

- active: False
- kill_switch_file: data\CANARY_KILL_SWITCH
- ledger_path: data\live_execution_ledger.csv

## Reasons

- none

## Warnings

- no_live_execution_ledger_entries

## Metrics

- daily_trade_count: 0
- daily_realized_pnl_usd: 0
- consecutive_losses: 0
- open_exposures: 0
- max_daily_loss_usd: 3.0
- max_consecutive_losses: 2
- max_daily_trades: 3
- max_open_exposures: 1
- max_order_stake_usd: 1.0

## Hard rule

A real canary attempt requires Lee authorization and no `data\CANARY_KILL_SWITCH` file present. This packet never contains private keys.
