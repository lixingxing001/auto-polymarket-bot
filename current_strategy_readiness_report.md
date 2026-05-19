# Current Strategy Readiness Report

## Status

- ready: False
- source_candidate_id: baseline
- filter_kind: none
- activated_at: 2026-05-19T15:22:57.038131+00:00
- live_trading_enabled: False

## Blockers

- insufficient_current_strategy_evaluations
- insufficient_current_strategy_trades

## Warnings

- legacy_forward_rows_without_strategy_version

## Metrics

- evaluations: 2
- trades: 1
- wins: 1
- losses: 0
- win_rate: 1.0
- total_pnl_usd: 5.373
- avg_pnl_usd: 5.373
- hold_reasons: {'low_confidence': 1}
- first_market_end_time: 2026-05-19T16:30:00+00:00
- latest_market_end_time: 2026-05-19T16:35:00+00:00
- legacy_rows_without_strategy_version: 301

## Policy

- min_evaluations: 30
- min_trades: 30
- min_win_rate: 0.55
- min_total_pnl_usd: 0.0

## Boundary

This report evaluates the current paper strategy only. It does not enable live trading and it does not submit orders.
