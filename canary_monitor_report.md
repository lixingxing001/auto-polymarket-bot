# Canary Monitor Report

- checked_at: 2026-05-19T16:44:42.052579+00:00
- ready: False
- next_action: wait_for_candidate_evidence_or_register_new_candidate
- readiness_report_path: canary_readiness_report.md

## Blockers

- forward_pnl_not_positive
- forward_win_rate_below_canary_floor
- no_candidate_review_ready
- no_candidate_passed_change_quality

## Warnings

- candidate_evidence_still_collecting

## Evidence gap

- forward_evaluations: 303
- forward_trades: 49
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 0}
- review_ready_candidates: []
- collecting_candidates: ['avoid_trade_against_1m_momentum_v2']
