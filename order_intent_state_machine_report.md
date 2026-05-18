# Order Intent State Machine Report

## Purpose

This step adds an auditable order lifecycle before any real execution path exists. Every live execution CLI run now creates an order intent, records state transitions and writes execution attempts separately.

## Added components

- `src/btc5m_bot/order_intent.py`
  - order intent model
  - intent event model
  - valid transition guard
  - CSV audit writer
- `src/btc5m_bot/live_execution.py`
  - now builds an intent flow after paper dry-run and execution preflight
  - writes both execution attempts and intent events
- `src/btc5m_bot/live_execution_cli.py`
  - added `--intent-event-log`
- `tests/test_order_intent.py`
  - created, blocked, rejected and mock submitted transitions
  - invalid transition rejection
  - CSV audit writer
- `tests/test_live_execution.py`
  - added live execution integration test with mocked dry-run input

## State model

```text
created
  -> no_actionable_order
  -> safety_blocked
  -> adapter_rejected
  -> mock_submitted
```

The state machine only allows terminal transitions from `created` for now. That is deliberate: until reconciliation exists, a submitted mock order must not silently mutate into a filled or settled state.

## Real CLI check

Command:

```powershell
$env:PYTHONPATH="src"; python -m btc5m_bot.live_execution_cli --attempt-log data\live_execution_attempts.csv --intent-event-log data\order_intent_events.csv
```

Observed result:

```text
intent.status: no_actionable_order
attempt.accepted: False
attempt.status: rejected
attempt.reason: no_actionable_order
safety reasons:
  live_trading_disabled
  strategy_guardrail_stage_collecting
  insufficient_forward_evaluations
  insufficient_forward_trades
safety warnings:
  no_proposed_order
```

Current evidence gate at the time of the CLI run:

```text
forward_evaluations: 28
forward_trades: 2
forward_total_pnl_usd: 12.423176470588238
guardrail_stage: collecting
next_change_review_gap:
  evaluations_needed: 72
  trades_needed: 28
```

## Verification

```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
```

Result:

```text
Ran 67 tests: OK
```

## Mentor note

This is plumbing, but it is not cosmetic. Without an intent state machine, live execution becomes a pile of side effects. With it, every skipped trade and every mock submission has a durable reason, which is the raw material for later improving filters, sizing and eventually model selection.
