# Canary Monitor Report

- checked_at: 2026-05-19T10:12:56.823635+00:00
- ready: False
- next_action: inspect_blockers
- readiness_report_path: canary_readiness_report.md

## Blockers

- forward_win_rate_below_canary_floor
- no_candidate_passed_change_quality

## Warnings

- candidate_evidence_still_collecting

## Evidence gap

- forward_evaluations: 224
- forward_trades: 32
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 0}
- review_ready_candidates: ['confidence_070']
- collecting_candidates: ['avoid_mid_distance_to_barrier_2_6bps', 'avoid_trade_against_1m_momentum', 'avoid_trade_against_5m_momentum']
