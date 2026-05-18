# Real Adapter Gate Report

- unlock_allowed: False
- authorization_packet_status: NOT_READY
- kill_switch_active: False

## Blockers

- canary_authorization_packet_not_ready
- lee_authorization_env_missing
- isolated_wallet_confirmation_missing
- canary_funding_cap_missing

## Warnings

- none

## Metrics

- authorization_status: NOT_READY
- authorization_blocker_count: 4
- kill_switch_active: False
- lee_authorization_env: LEE_CANARY_AUTHORIZED
- isolated_wallet_env: CANARY_WALLET_ISOLATED
- max_funding_env: CANARY_MAX_FUNDING_USDC
- parsed_funding_usdc: None
- max_funding_usdc: 10.0

## Boundary

This gate only controls whether real adapter development may proceed. It does not submit orders and it does not read private keys.
