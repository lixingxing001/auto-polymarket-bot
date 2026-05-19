# Canary Preflight Report

## Status

- status: BLOCKED
- real_adapter_review_allowed: False
- next_action: collect_more_forward_evidence

## Blockers

- guardrail_stage_review_only
- insufficient_forward_trades
- forward_win_rate_below_canary_floor
- canary_authorization_packet_not_ready
- lee_authorization_env_missing
- isolated_wallet_confirmation_missing
- canary_funding_cap_missing

## Warnings

- candidate_evidence_still_collecting
- no_live_execution_ledger_entries

## Metrics

- readiness_ready: False
- authorization_status: NOT_READY
- kill_switch_active: False
- real_adapter_unlock_allowed: False
- forward_evaluations: 180
- forward_trades: 26
- forward_total_pnl_usd: 40.23726449326367
- review_ready_candidates: ['avoid_low_momentum_near_barrier', 'avoid_mid_abs_return_5m', 'edge_008']

## Boundary

This report is a preflight summary only. It does not read private keys and it does not submit orders.
