# Canary Preflight Report

## Status

- status: BLOCKED
- real_adapter_review_allowed: False
- next_action: collect_more_forward_evidence

## Blockers

- forward_win_rate_below_canary_floor
- no_candidate_passed_change_quality
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
- forward_evaluations: 224
- forward_trades: 32
- forward_total_pnl_usd: 43.46473031776175
- review_ready_candidates: ['confidence_070']

## Boundary

This report is a preflight summary only. It does not read private keys and it does not submit orders.
