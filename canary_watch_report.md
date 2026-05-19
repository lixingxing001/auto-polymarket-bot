# Canary Watch Report

- checked_at: 2026-05-19T10:12:56.840152+00:00
- ready: False
- next_action: inspect_blockers

## Readiness

- blockers: ['forward_win_rate_below_canary_floor', 'no_candidate_passed_change_quality']
- warnings: ['candidate_evidence_still_collecting']
- forward_evaluations: 224
- forward_trades: 32
- forward_win_rate: 0.4375
- forward_total_pnl_usd: 43.46473031776175
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 0}

## Preflight

- status: BLOCKED
- real_adapter_review_allowed: False
- blockers: ['forward_win_rate_below_canary_floor', 'no_candidate_passed_change_quality', 'canary_authorization_packet_not_ready', 'lee_authorization_env_missing', 'isolated_wallet_confirmation_missing', 'canary_funding_cap_missing']

## Candidate change review

- status: DEFER_CHANGE
- selected_candidate_id: none
- change_allowed: False
- blockers: ['no_candidate_passed_change_quality']
- warnings: []

## Candidate evidence progress

- next_review_candidate_id: confidence_070
- review_ready_candidates: ['confidence_070']
- change_quality_passed_candidates: []
- needs_divergent_windows: ['avoid_trade_against_1m_momentum', 'avoid_trade_against_5m_momentum']
- waiting_for_first_divergence: []

## Boundary

This watchdog refreshes reports only. It does not submit orders and it does not read private keys.
