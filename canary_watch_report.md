# Canary Watch Report

- checked_at: 2026-05-19T02:51:18.795772+00:00
- ready: False
- next_action: collect_more_forward_evidence

## Readiness

- blockers: ['guardrail_stage_review_only', 'insufficient_forward_trades', 'forward_win_rate_below_canary_floor']
- warnings: ['candidate_evidence_still_collecting']
- forward_evaluations: 141
- forward_trades: 20
- forward_win_rate: 0.4
- forward_total_pnl_usd: 32.570335803379756
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 10}

## Preflight

- status: BLOCKED
- real_adapter_review_allowed: False
- blockers: ['guardrail_stage_review_only', 'insufficient_forward_trades', 'forward_win_rate_below_canary_floor', 'canary_authorization_packet_not_ready', 'lee_authorization_env_missing', 'isolated_wallet_confirmation_missing', 'canary_funding_cap_missing']

## Candidate change review

- status: DEFER_CHANGE
- selected_candidate_id: avoid_mid_abs_return_5m
- change_allowed: False
- blockers: ['guardrail_stage_review_only']
- warnings: ['selected_candidate_win_rate_below_canary_floor']

## Boundary

This watchdog refreshes reports only. It does not submit orders and it does not read private keys.
