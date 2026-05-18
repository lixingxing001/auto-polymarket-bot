# Execution Health Report

## Summary

- intent_events: 2
- created_intents: 1
- terminal_intents: 1
- attempts: 2
- accepted_attempts: 0
- rejected_attempts: 2
- actionable_signals: 0
- order_send_allowed: 0

## Diagnosis

- paper_signal_not_actionable
- no_attempts_accepted
- guardrail_stage_collecting

## Top blockers

### Paper reasons

- too_late: 1

### Safety reasons

- insufficient_forward_evaluations: 3
- insufficient_forward_trades: 3
- live_trading_disabled: 3
- strategy_guardrail_stage_collecting: 3

### Attempt reasons

- no_actionable_order: 2

## Forward gate

- evaluations: 28
- trades: 2
- wins: 2
- losses: 0
- win_rate: 1.0
- total_pnl_usd: 12.423176470588238
- guardrail_stage: collecting
- next_review_gap: {'evaluations_needed': 2, 'trades_needed': 8}
- next_change_review_gap: {'evaluations_needed': 72, 'trades_needed': 28}

## Interpretation

The execution layer is currently doing its job: it records why orders do not progress. The next improvement should be based on the largest blocker, not on gut feel.
