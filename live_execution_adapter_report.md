# Live Execution Adapter Report

## Purpose

This step adds a live execution interface without enabling real order placement. The code now has a controlled boundary where future live execution must pass through paper dry-run, execution safety and an adapter.

## Added components

- `src/btc5m_bot/live_execution.py`
  - `ExecutionAdapter` protocol
  - `DisabledLiveExecutionAdapter`
  - `MockExecutionAdapter`
  - `submit_preflighted_order`
  - attempt audit CSV writer
- `src/btc5m_bot/live_execution_cli.py`
  - one-shot execution attempt CLI
  - default adapter is `disabled`
- `tests/test_live_execution.py`
  - disabled adapter rejection
  - mock adapter acceptance under controlled allowed preflight
  - safety failure rejection before adapter submission
  - no actionable order rejection
  - audit row writing

## Safety design

Execution is now split into three gates:

```text
paper signal -> paper dry-run -> execution safety -> execution adapter
```

The default adapter rejects by construction. The mock adapter is available for tests and future state-machine work. There is no real Polymarket signing or order submission path in this step.

## Real CLI check

Command:

```powershell
$env:PYTHONPATH="src"; python -m btc5m_bot.live_execution_cli --attempt-log data\live_execution_attempts.csv
```

Observed result:

```text
adapter: disabled
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

Current forward gate at the time of the CLI run:

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
Ran 59 tests: OK
```

## Mentor note

The adapter boundary is useful because it prevents credentials from becoming the architecture. The next useful layer is an order intent state machine and reconciliation log, still under mock execution, so every future live order has an auditable lifecycle before any private key enters the system.
