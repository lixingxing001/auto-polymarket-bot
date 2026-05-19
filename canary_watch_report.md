# Canary Watch Report

- checked_at: 2026-05-19T06:02:01.659892+00:00
- ready: False
- next_action: collect_more_forward_evidence

## Readiness

- blockers: ['guardrail_stage_review_only', 'insufficient_forward_trades', 'forward_win_rate_below_canary_floor']
- warnings: ['candidate_evidence_still_collecting']
- forward_evaluations: 180
- forward_trades: 26
- forward_win_rate: 0.38461538461538464
- forward_total_pnl_usd: 40.23726449326367
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 4}

## Preflight

- status: BLOCKED
- real_adapter_review_allowed: False
- blockers: ['guardrail_stage_review_only', 'insufficient_forward_trades', 'forward_win_rate_below_canary_floor', 'canary_authorization_packet_not_ready', 'lee_authorization_env_missing', 'isolated_wallet_confirmation_missing', 'canary_funding_cap_missing']

## Candidate change review

- status: DEFER_CHANGE
- selected_candidate_id: avoid_low_momentum_near_barrier
- change_allowed: False
- blockers: ['guardrail_stage_review_only', 'no_candidate_passed_change_quality']
- warnings: []

## Boundary

This watchdog refreshes reports only. It does not submit orders and it does not read private keys.
