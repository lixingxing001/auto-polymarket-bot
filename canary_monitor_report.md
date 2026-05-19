# Canary Monitor Report

- checked_at: 2026-05-19T07:57:32.021460+00:00
- ready: False
- next_action: inspect_blockers
- readiness_report_path: canary_readiness_report.md

## Blockers

- forward_win_rate_below_canary_floor
- no_candidate_passed_change_quality

## Warnings

- candidate_evidence_still_collecting

## Evidence gap

- forward_evaluations: 203
- forward_trades: 30
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 0}
- review_ready_candidates: ['avoid_low_momentum_near_barrier', 'avoid_mid_abs_return_5m', 'edge_008']
- collecting_candidates: ['avoid_mid_distance_to_barrier_2_6bps', 'confidence_070']
