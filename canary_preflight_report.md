# Canary Preflight Report

## Status

- status: BLOCKED
- real_adapter_review_allowed: False
- next_action: collect_more_forward_evidence

## Blockers

- guardrail_stage_collecting
- insufficient_forward_evaluations
- insufficient_forward_trades
- no_candidate_review_ready
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
- forward_evaluations: 31
- forward_trades: 2
- forward_total_pnl_usd: 12.423176470588238
- review_ready_candidates: []

## Boundary

This report is a preflight summary only. It does not read private keys and it does not submit orders.
