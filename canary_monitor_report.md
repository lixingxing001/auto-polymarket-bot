# Canary Monitor Report

- checked_at: 2026-05-19T02:51:18.790470+00:00
- ready: False
- next_action: collect_more_forward_evidence
- readiness_report_path: canary_readiness_report.md

## Blockers

- guardrail_stage_review_only
- insufficient_forward_trades
- forward_win_rate_below_canary_floor

## Warnings

- candidate_evidence_still_collecting

## Evidence gap

- forward_evaluations: 141
- forward_trades: 20
- next_change_review_gap: {'evaluations_needed': 0, 'trades_needed': 10}
- review_ready_candidates: ['avoid_low_momentum_near_barrier', 'avoid_mid_abs_return_5m']
- collecting_candidates: ['edge_008']
