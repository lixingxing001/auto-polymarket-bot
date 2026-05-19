# Canary Watch Report

- checked_at: 2026-05-19T08:16:34.728027+00:00
- ready: False
- next_action: wait_for_candidate_evidence_or_register_new_candidate

## Readiness

- blockers: ['forward_win_rate_below_canary_floor', 'no_candidate_review_ready', 'no_candidate_passed_change_quality']
- warnings: ['candidate_evidence_still_collecting']
- forward_evaluations: 206
- forward_trades: 30
- forward_win_rate: 0.43333333333333335
- forward_total_pnl_usd: 48.098698059697234
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 0}

## Preflight

- status: BLOCKED
- real_adapter_review_allowed: False
- blockers: ['forward_win_rate_below_canary_floor', 'no_candidate_review_ready', 'no_candidate_passed_change_quality', 'canary_authorization_packet_not_ready', 'lee_authorization_env_missing', 'isolated_wallet_confirmation_missing', 'canary_funding_cap_missing']

## Candidate change review

- status: DEFER_CHANGE
- selected_candidate_id: none
- change_allowed: False
- blockers: ['no_candidate_passed_change_quality']
- warnings: []

## Candidate evidence progress

- next_review_candidate_id: avoid_mid_distance_to_barrier_2_6bps
- review_ready_candidates: []
- change_quality_passed_candidates: []
- needs_divergent_windows: ['avoid_mid_distance_to_barrier_2_6bps', 'confidence_070']
- waiting_for_first_divergence: ['avoid_trade_against_1m_momentum', 'avoid_trade_against_5m_momentum']

## Boundary

This watchdog refreshes reports only. It does not submit orders and it does not read private keys.
