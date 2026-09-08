# Controllable Stock Token test-double specification

## Scope

This is the Hour 9 specification for a local-only test double that exercises
the issuer-controlled behaviors stonkHedge must survive before using a Robinhood
faucet Stock Token publicly. It is not issuer code, a synthetic equity, a faucet,
or a production token. It must never be deployed or presented as a Robinhood
Stock Token.

The public integration lane always uses Robinhood's exact chain-`46630` token
addresses. The test double exists because ordinary users cannot trigger issuer
mint/burn, pause, blocklist, or corporate-action schedules on those shared
contracts, while those states materially affect an options protocol.

## Observed compatibility surface

The double should match only the externally observed interfaces needed by the
tests:

- ERC-20 with 18 decimals: `balanceOf`, `totalSupply`, `transfer`, `approve`,
  `allowance`, and `transferFrom`;
- EIP-2612 permit surface where inherited integration paths consume it;
- ERC-8056 views/events: `uiMultiplier`, `newUIMultiplier`, `effectiveAt`,
  `balanceOfUI`, `totalSupplyUI`, `UIMultiplierUpdated`, and
  `TransferWithScaledUI`;
- token-level `pause`, `unpause`, `paused`, and `tokenPaused` behavior;
- registry-level global pause and address block/unblock behavior;
- controlled `mint`, holder/authorized `burn`, and administrative burn; and
- metadata getters/update behavior only where the integration reads them.

Robinhood documents that Stock Tokens are standard transferable ERC-20s and
non-rebasing ERC-8056 assets. A multiplier changes UI-adjusted share exposure,
not raw `balanceOf` or `totalSupply`. The local double must preserve that exact
separation.

## Minimal architecture

Use two deliberately small test contracts:

1. `ControllableStockRegistry` owns global pause, blocklist, and narrowly scoped
   role checks.
2. `ControllableStockToken` owns ERC-20 balances/allowances, token pause,
   multiplier scheduling, and controlled supply operations while consulting the
   registry.

Use constructor deployment for the test double unless proxy behavior itself is
under test. Beacon upgrade machinery is not needed for the first compatibility
matrix and would inflate the trusted surface. Keep admin roles as separate test
addresses for registry admin, pauser, minter, multiplier operator, and burner;
do not silently grant every role to the test deployer.

## Required behavior

### ERC-20 and restrictions

- Successful transfer and `transferFrom` change raw balances and emit both
  `Transfer` and `TransferWithScaledUI` using the effective multiplier.
- Zero-value transfers follow standard ERC-20 behavior but still pass through
  pause/block policy.
- Global pause, token pause, blocked sender, or blocked recipient reject
  transfer, mint, burn, deposit, withdrawal, and protocol settlement paths in a
  deterministic way.
- Approval and permit policy under pause/block must be explicit in tests rather
  than assumed from transfer behavior.
- Failed restricted operations leave balances, supply, allowances, protocol
  positions, and accounting accumulators unchanged.

### Supply controls

- Only the minter role can mint.
- Holder burn and privileged burn are separate code paths.
- Administrative burn can model issuer-forced cancellation from a holder, but
  must emit the standard burn transfer and scaled event.
- No test helper may mint or rewrite balances without exercising the public
  role-checked surface after initial fixture setup.

### ERC-8056 multiplier

- Initial current and pending multiplier are `1e18`; `effectiveAt` is zero.
- Scheduling a positive multiplier records the pending value/time and emits the
  expected update event semantics.
- Before `effectiveAt`, raw and UI views use the old effective multiplier.
- At and after `effectiveAt`, UI views use the new multiplier while raw balances
  and total supply remain bit-for-bit unchanged.
- Test values include increase, decrease, rounding-down dust, very small raw
  balances, near-boundary timestamps, repeated schedules, and invalid zero or
  overflow-producing inputs.
- Tests must prove the application never multiplies a Chainlink price by the
  token multiplier a second time; Robinhood documents its stock price feeds as
  already incorporating corporate actions.

## Red-test matrix for Hour 10 and Hour 11

| ID | Scenario | Required assertion |
|---|---|---|
| STK-001 | ordinary transfer | raw conservation; both transfer events agree at multiplier `1e18` |
| STK-002 | transfer after multiplier activation | raw conservation; scaled event/UI view use new multiplier |
| STK-003 | scheduled multiplier before boundary | old multiplier remains effective |
| STK-004 | scheduled multiplier at boundary | new multiplier becomes effective exactly once |
| STK-005 | fractional scaling | UI amount rounds down predictably; no raw balance mutation |
| STK-006 | global pause | direct transfer and Panoptic token movement fail atomically |
| STK-007 | token pause | only the selected token fails; unrelated token remains usable |
| STK-008 | blocked sender | transfer/deposit/open path fails without accounting drift |
| STK-009 | blocked receiver/protocol | transfer/deposit/withdraw/settlement behavior is explicit |
| STK-010 | forced administrative burn | holder supply falls; protocol solvency response is measured |
| STK-011 | unauthorized admin action | every privileged entry point reverts with unchanged state |
| STK-012 | permit/allowance under restriction | policy is reproduced and failed spend is atomic |
| STK-013 | pause during open position | close/liquidation/unwind failure is classified, not hidden |
| STK-014 | unpause recovery | permitted lifecycle resumes without phantom balances |
| STK-015 | repeated schedule | replacement/cancellation policy matches the implemented model |
| STK-016 | fuzz raw amount × multiplier | no overflow; raw conservation; documented rounding bound |

The Panoptic integration assertions must cover the full lifecycle: approve,
deposit, create/register market, open, premium settlement, close/liquidate, and
withdraw. It is insufficient to test only standalone ERC-20 transfers.

## Explicit differences from issuer contracts

The implementation and its test names must label these deviations:

- local roles are controlled by test actors rather than Robinhood/RHJ systems;
- local mint/burn is available solely to construct deterministic scenarios;
- no legal claim, custody, redemption, jurisdiction, KYB, RFQ, or primary-market
  behavior is modeled;
- no production oracle is bundled into the token; and
- proxy/beacon upgrade behavior is tested separately only if an integration
  failure requires it.

## Acceptance gate

Hour 9 is complete when this specification is committed. Hours 10–11 require a
red test first, the minimum implementation, deterministic tests, fuzz coverage,
and a manifest that labels the contracts `LOCAL_TEST_DOUBLE_ONLY`. No address
from the local fixture may enter a chain-`46630` deployment manifest.
