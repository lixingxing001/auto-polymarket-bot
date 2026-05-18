# Canary Runbook

## Current status

Canary is not authorized. The system can run data collection, forward evaluation, mock execution smoke tests, readiness reports and authorization packet generation. Real order submission remains unavailable.

## Required gates before canary

1. `python -m btc5m_bot.canary_readiness_cli` returns `ready: True`.
2. `python -m btc5m_bot.canary_kill_switch_cli` returns `active: False`.
3. `python -m btc5m_bot.mock_execution_smoke_cli` produces `mock_submitted`.
4. `python -m btc5m_bot.real_adapter_gate_cli` has no blockers after Lee sets explicit authorization environment variables.
5. Lee manually confirms canary in this thread.

## Canary envelope

- Maximum order stake: 1 USDC
- Maximum wallet funding: 10 USDC
- Maximum daily loss: 3 USDC
- Maximum daily trades: 3
- Maximum open exposure: 1
- Maximum consecutive losses: 2
- Duration: 24 hours before review

## Manual kill switch

Create this file to halt canary eligibility:

```powershell
New-Item -ItemType File data\CANARY_KILL_SWITCH
```

Remove it only after reviewing `canary_kill_switch_report.md`.

## Authorization environment variables

These are only gate confirmations. They must never contain private keys.

```powershell
$env:LEE_CANARY_AUTHORIZED="I_ACCEPT_CANARY_RISK"
$env:CANARY_WALLET_ISOLATED="YES"
$env:CANARY_MAX_FUNDING_USDC="10"
```

## Private key rule

Private keys must stay outside git, reports and logs. If a real adapter is ever implemented, it must read a key from an external secret path or wallet service after Lee explicitly approves that design.

## Wake-up behavior

The scheduled monitor may prepare updated readiness and authorization reports. It must not request keys, print keys or submit real orders.
