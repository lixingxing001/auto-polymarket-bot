# Canary Monitor Report

- checked_at: 2026-05-18T17:26:17.013747+00:00
- ready: False
- next_action: collect_more_forward_evidence
- readiness_report_path: canary_readiness_report.md

## Blockers

- guardrail_stage_collecting
- insufficient_forward_evaluations
- insufficient_forward_trades
- no_candidate_review_ready

## Warnings

- candidate_evidence_still_collecting

## Evidence gap

- forward_evaluations: 28
- forward_trades: 2
- next_change_review_gap: {'evaluations_needed': 72, 'trades_needed': 28}
- review_ready_candidates: []
- collecting_candidates: ['avoid_low_momentum_near_barrier', 'avoid_mid_abs_return_5m', 'edge_008']
