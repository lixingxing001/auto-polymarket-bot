# Candidate Autopilot Report

- generated_at: 2026-05-19T16:44:41.597057+00:00
- enabled: True
- action: NOOP
- selected_candidate_id: none
- blockers: ['no_promotion_ready_candidate']
- promotion_ready_candidates: []
- active_strategy_degradation: none
- rejected_candidate_id: none

## Active Paper Strategy

- strategy_state_path: data\active_strategy_state.json
- source_candidate_id: baseline
- filter_kind: none
- min_confidence: 0.65
- min_edge: 0.03
- live_trading_enabled: False

## Change Decision

- status: DEFER_CHANGE
- change_allowed: False
- selected_candidate_id: none
- blockers: ['no_candidate_passed_change_quality']

## Boundary

This autopilot can update only the paper active strategy state. It does not enable live trading, read private keys or submit orders.
