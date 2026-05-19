# Candidate Evidence Progress Report

## Status

- generated_at: 2026-05-19T08:16:35.210295+00:00
- active_candidate_count: 4
- all_candidate_count: 7
- next_review_candidate_id: avoid_mid_distance_to_barrier_2_6bps
- review_ready_candidates: []
- change_quality_passed_candidates: []
- waiting_for_first_divergence: ['avoid_trade_against_1m_momentum', 'avoid_trade_against_5m_momentum']
- needs_divergent_windows: ['avoid_mid_distance_to_barrier_2_6bps', 'confidence_070']

## Active candidates

| candidate_id | blocker | eligible | divergent | eligible_gap | divergent_gap | eta_minutes | eta_confidence | delta_pnl | win_rate | next_action |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| avoid_mid_distance_to_barrier_2_6bps | needs_divergent_windows | 5 | 2 | 25 | 8 | 125 | thin_sample | 0.00 | 0.0% | wait_for_more_divergent_windows |
| confidence_070 | needs_divergent_windows | 26 | 4 | 4 | 6 | 195 | observed_rate | 2.65 | 100.0% | wait_for_more_divergent_windows |
| avoid_trade_against_1m_momentum | waiting_for_first_divergence | 0 | 0 | 30 | 10 | unknown | unknown_until_divergence_observed | 0.00 | 0.0% | wait_for_divergent_decision |
| avoid_trade_against_5m_momentum | waiting_for_first_divergence | 0 | 0 | 30 | 10 | unknown | unknown_until_divergence_observed | 0.00 | 0.0% | wait_for_divergent_decision |

## Inactive candidates

- avoid_low_momentum_near_barrier: status=rejected, delta_pnl=0.00
- avoid_mid_abs_return_5m: status=rejected, delta_pnl=-13.56
- edge_008: status=rejected, delta_pnl=-44.75

## Boundary

This report estimates evidence maturity only. It does not approve strategy changes, enable live trading or submit orders.
