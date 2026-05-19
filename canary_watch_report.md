# Canary Watch Report

- checked_at: 2026-05-19T16:44:42.061990+00:00
- ready: False
- next_action: wait_for_candidate_evidence_or_register_new_candidate

## Readiness

- blockers: ['forward_pnl_not_positive', 'forward_win_rate_below_canary_floor', 'no_candidate_review_ready', 'no_candidate_passed_change_quality']
- warnings: ['candidate_evidence_still_collecting']
- forward_evaluations: 303
- forward_trades: 49
- forward_win_rate: 0.42857142857142855
- forward_total_pnl_usd: -25.741933118800908
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 0}

## Current strategy readiness

- ready: False
- blockers: ['insufficient_current_strategy_evaluations', 'insufficient_current_strategy_trades']
- source_candidate_id: baseline
- evaluations: 2
- trades: 1
- win_rate: 1.0
- total_pnl_usd: 5.373

## Preflight

- status: BLOCKED
- real_adapter_review_allowed: False
- blockers: ['forward_pnl_not_positive', 'forward_win_rate_below_canary_floor', 'no_candidate_review_ready', 'no_candidate_passed_change_quality', 'canary_authorization_packet_not_ready', 'lee_authorization_env_missing', 'isolated_wallet_confirmation_missing', 'canary_funding_cap_missing']

## Candidate change review

- status: DEFER_CHANGE
- selected_candidate_id: none
- change_allowed: False
- blockers: ['no_candidate_passed_change_quality']
- warnings: []

## Candidate evidence progress

- next_review_candidate_id: avoid_trade_against_1m_momentum_v2
- review_ready_candidates: []
- change_quality_passed_candidates: []
- needs_divergent_windows: []
- waiting_for_first_divergence: ['avoid_trade_against_1m_momentum_v2']

## Boundary

This watchdog refreshes reports only. It does not submit orders and it does not read private keys.
