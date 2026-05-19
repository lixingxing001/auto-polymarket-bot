# Candidate Evidence Progress Report

## Status

- generated_at: 2026-05-19T10:12:56.839664+00:00
- active_candidate_count: 4
- all_candidate_count: 7
- next_review_candidate_id: confidence_070
- review_ready_candidates: ['confidence_070']
- change_quality_passed_candidates: []
- waiting_for_first_divergence: []
- needs_divergent_windows: ['avoid_trade_against_1m_momentum', 'avoid_trade_against_5m_momentum']

## Active candidates

| candidate_id | blocker | eligible | divergent | eligible_gap | divergent_gap | eta_minutes | eta_confidence | delta_pnl | win_rate | next_action |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| confidence_070 | review_ready_quality_failed | 46 | 10 | 0 | 0 | 0 | ready | 11.76 | 100.0% | reject_or_redesign_candidate |
| avoid_mid_distance_to_barrier_2_6bps | needs_eligible_windows | 25 | 13 | 5 | 0 | 25 | observed_rate | 10.50 | 100.0% | wait_for_more_settled_windows |
| avoid_trade_against_1m_momentum | needs_divergent_windows | 20 | 2 | 10 | 8 | 400 | observed_rate | 4.63 | 100.0% | wait_for_more_divergent_windows |
| avoid_trade_against_5m_momentum | needs_divergent_windows | 20 | 2 | 10 | 8 | 400 | observed_rate | 4.63 | 100.0% | wait_for_more_divergent_windows |

## Inactive candidates

- avoid_low_momentum_near_barrier: status=rejected, delta_pnl=4.47
- avoid_mid_abs_return_5m: status=rejected, delta_pnl=-4.45
- edge_008: status=rejected, delta_pnl=-25.36

## Boundary

This report estimates evidence maturity only. It does not approve strategy changes, enable live trading or submit orders.
