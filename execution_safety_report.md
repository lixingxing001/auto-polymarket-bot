# Execution Safety Report

## Purpose

This layer is a pre-order safety gate for any future live execution path. It evaluates strategy readiness, account level circuit breakers and proposed order quality before an order can be sent.

## Added components

- `src/btc5m_bot/execution_safety.py`
  - global live-trading switch
  - forward evidence gate
  - guardrail stage gate
  - daily loss and trade count circuit breakers
  - consecutive loss circuit breaker
  - duplicate exposure detection
  - order price, stake, edge, confidence, liquidity and time-to-close checks
- `src/btc5m_bot/execution_safety_cli.py`
  - prints full preflight state
  - supports global status checks
  - supports proposed order dry-run checks
- `tests/test_execution_safety.py`
  - covers disabled live switch
  - covers collecting-stage rejection
  - covers duplicate and oversized order rejection
  - covers allowed path when all gates pass in a controlled fixture

## Current live-readiness result

Command:

```powershell
$env:PYTHONPATH="src"; python -m btc5m_bot.execution_safety_cli
```

Current assessment:

```text
allowed: False
reasons:
  live_trading_disabled
  strategy_guardrail_stage_collecting
  insufficient_forward_evaluations
  insufficient_forward_trades
warnings:
  no_proposed_order
```

Current forward ledger snapshot:

```text
forward_evaluations: 14
forward_trades: 1
forward_total_pnl_usd: 3.158333333333334
guardrail_stage: collecting
next_change_review_gap:
  evaluations_needed: 86
  trades_needed: 29
```

A safe-looking demo order was also blocked after enabling the runtime live switch, because strategy evidence remains insufficient:

```powershell
$env:PYTHONPATH="src"; python -m btc5m_bot.execution_safety_cli --enable-live-trading --slug btc-updown-demo --outcome UP --price 0.55 --stake-usd 8 --edge 0.08 --probability 0.72 --available-liquidity-usd 100 --seconds-to-close 120
```

Result:

```text
allowed: False
reasons:
  strategy_guardrail_stage_collecting
  insufficient_forward_evaluations
  insufficient_forward_trades
```

## Verification

```powershell
$env:PYTHONPATH="src"; python -m unittest tests.test_execution_safety -v
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
```

Result:

```text
Ran 5 execution safety tests: OK
Ran 47 total tests: OK
```

## Mentor note

The safety layer deliberately refuses live trading today. A high win-rate slice or a single profitable forward trade has no authority to bypass execution risk. The minimum bar is still forward evidence, frozen parameters, order-level capacity checks and circuit breakers all passing together.


