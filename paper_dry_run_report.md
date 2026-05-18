# Paper Execution Dry-Run Report

## Purpose

This step connects the paper signal path to the execution safety preflight. The dry-run path now shows whether a paper signal would survive the same safety gate that a future live adapter must use.

## Added components

- `src/btc5m_bot/paper_dry_run.py`
  - converts actionable paper signals into `ProposedOrder`
  - runs execution safety preflight using forward and execution ledgers
  - writes structured dry-run CSV rows
  - separates `actionable_signal` from `order_send_allowed`
- `src/btc5m_bot/paper_dry_run_cli.py`
  - one-shot paper dry-run entrypoint
- `src/btc5m_bot/paper_loop.py`
  - added `--execution-dry-run`
  - writes dry-run rows to `data/paper_dry_runs.csv` by default
- `src/btc5m_bot/risk.py`
  - added `min_confidence` to align paper decisions with frozen strategy parameters

## Important fix found by dry-run

The first real dry-run exposed a mismatch: the paper risk layer allowed a positive-edge low-confidence UP signal, while execution safety rejected it via `confidence_below_minimum`.

Fix applied:

```text
RiskConfig.min_confidence = 0.65
RiskManager returns HOLD with reason low_confidence when max(prob_up, prob_down) is below the threshold.
```

This keeps the paper signal path closer to the active execution research path.

## Real dry-run checks

Command:

```powershell
$env:PYTHONPATH="src"; python -m btc5m_bot.paper_dry_run_cli --output data\paper_dry_runs.csv
```

Observed result after alignment:

```text
decision: HOLD
reason: low_confidence
actionable_signal: False
order_send_allowed: False
blocking reasons:
  live_trading_disabled
  strategy_guardrail_stage_collecting
  insufficient_forward_evaluations
  insufficient_forward_trades
warning:
  no_proposed_order
```

Paper loop integration check:

```powershell
$env:PYTHONPATH="src"; python -m btc5m_bot.paper_loop --execution-dry-run --iterations 1 --output data\paper_dry_runs_loop.csv
```

Observed result:

```text
decision: HOLD
reason: too_late
actionable_signal: False
order_send_allowed: False
```

## Current evidence gate

```text
forward_evaluations: 17
forward_trades: 1
guardrail_stage: collecting
next_change_review_gap:
  evaluations_needed: 83
  trades_needed: 29
```

## Verification

```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
```

Result:

```text
Ran 53 tests: OK
```

## Mentor note

The dry-run did useful work immediately: it caught a policy mismatch before any live adapter existed. This is the reason execution plumbing should be built before adding exchange credentials. Credentials would have hidden the bug behind urgency.
