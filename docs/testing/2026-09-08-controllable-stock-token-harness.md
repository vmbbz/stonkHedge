# Controllable Stock Token and local Panoptic lifecycle evidence — 2026-09-08

## Outcome

The Hours 10–16 local Stock Token/quote/Panoptic checkpoint is implemented and
pushed on branch
`feat/stock-token-compatibility-harness`. The latest evidence commit is
`cfaf42c29b5c59304540e2a31e24daee4d977797`, built on residual-reconciliation
commit `ec3278b3871b92f7d3440cd792097c4e9d7e7cd9`, two-actor commit
`d90788202f622388a5bda1a9db32515662aea2af`, initial lifecycle commit
`e6646eb6a259a6152d770090e63ec61ecc67ed09`, and standalone token commit
`159dabdd09a8b1168b23aa732fec9cb562a3f22b`.

This is a local test double, not Robinhood issuer code, a synthetic equity, or
a deployable public asset. It lives only under `test/foundry/mocks/`; no local
fixture address is permitted in a chain-`46630` manifest. The local quote token
is an ERC-20 test stand-in named `lWETH`; it is not production WETH.

## Red-to-green evidence

The first focused test run failed because
`test/foundry/mocks/ControllableStockToken.sol` did not exist. That was the
intended red boundary. The minimum implementation was then added and the same
focused suite completed with `16 passed, 0 failed, 0 skipped`, including 30 fuzz
runs for scaled-view rounding.

Reproduce from `C:\dev-shared\stonkHedge-core`:

```powershell
git switch --detach cfaf42c29b5c59304540e2a31e24daee4d977797
$env:FOUNDRY_PROFILE = "ci_test"
forge test --match-path test/foundry/mocks/ControllableStockToken.t.sol --fuzz-runs 30
forge fmt --check test/foundry/integration/StockTokenPanopticFixture.sol test/foundry/integration/StockTokenPanopticLifecycle.t.sol
forge test --match-path test/foundry/integration/StockTokenPanopticLifecycle.t.sol --fuzz-runs 30
forge test --match-path test/foundry/core/PanopticFactory.t.sol
forge test --match-path test/foundry/core/PanopticPool.t.sol
forge test --match-path test/foundry/base/Multicall.t.sol
python -m unittest discover -s script/tests -p "test_*direct_deployment.py"
Remove-Item Env:\FOUNDRY_PROFILE
pwsh -NoProfile -File .\script\local\verify-local-stock-panoptic.ps1
```

Observed results:

| Check | Result |
|---|---|
| Controllable-token focused suite | `16 passed, 0 failed, 0 skipped` |
| Fuzz multiplier/rounding cases | `30` runs |
| Local Stock/quote Panoptic lifecycle | `14 passed, 0 failed, 0 skipped` |
| Inherited Panoptic factory | `7 passed, 0 failed, 0 skipped` |
| Inherited PanopticPool | `72 passed, 0 failed, 0 skipped` |
| Scoped formatting | passed for both new integration files |
| Inherited Multicall regression | `4 passed, 0 failed, 0 skipped` |
| Direct-deployment Python tests | `11 passed` |
| Clean loopback-Anvil replay | `33` transactions and `33` successful receipts |
| Independent post-state verifier | `LOCAL_STOCK_PANOPTIC_VERIFY_PASS` at committed core SHA `cfaf42c...` |
| Unsafe RPC refusal and artifact cleanup | passed |

Inherited Solar preprocessor warnings about duplicate `stdMath` declarations
remain visible during compilation and inherited compiler warnings remain in the
large PanopticPool suite. Repository-wide `forge fmt --check` also reports
pre-existing formatting drift in untouched upstream contracts, so the recorded
format gate is intentionally scoped to the two new integration files. None of
these inherited warnings was hidden or mass-reformatted.

## Implemented behavior

The harness provides separate registry admin, pauser, blocker, minter, burner,
and multiplier roles. It exercises:

- raw ERC-20 conservation and `TransferWithScaledUI` emission;
- non-rebasing ERC-8056 current/pending multiplier behavior at the exact
  activation boundary;
- global and per-token pauses;
- blocked sender, receiver, spender, and permit behavior;
- holder burn and role-gated administrative burn;
- atomic failure with unchanged state; and
- recovery after unpause/unblock.

The implementation deliberately prevents a blocked spender from bypassing the
registry with an infinite allowance. A permit to a blocked spender reverts
without consuming the permit nonce. Administrative burn may bypass the holder
blocklist to model issuer cancellation, but it cannot bypass global or token
pause.

## Local Panoptic lifecycle evidence

The first lifecycle layer uses the inherited `PoolManager`, `V4RouterSimple`,
`SemiFungiblePositionManagerV4`, `PanopticFactoryV4`, `RiskEngine`,
`PanopticPoolV2`, and `CollateralTrackerV2` paths. It proves:

- a no-hook pool initializes with full-range liquidity and swaps in both
  directions with reconciled balances and tick movement;
- factory-deployed Panoptic market, risk engine, SFPM, PoolManager, collateral
  trackers, and underlying tokens reconcile;
- an actor deposits both assets, opens an in-range short, accrues observable
  premium after swaps, closes, and withdraws stock collateral;
- distinct short and long actors deposit, open matched positions in the same
  range, both accrue premium, and both close with their position counts cleared;
- the matched close leaves no open Panoptic/SFPM position and keeps AMM dust,
  credited-share asset value, and PoolManager-claim deviation below a strict
  `2e12` raw-unit local-test budget;
- the UI multiplier changes scaled views but not Panoptic's raw-unit collateral
  accounting;
- token or registry pause and a blocked PoolManager reject affected deposits
  atomically and recover after the restriction is lifted;
- an option already open at pause can close using PoolManager internal balances,
  while stock withdrawal and external stock-involving swaps stay blocked; and
- liquidation of an intentionally insolvent account needs an underlying Stock
  Token transfer from the liquidator, so pause blocks it atomically; liquidator
  shares and the victim position remain unchanged until unpause permits the
  liquidation; and
- forced administrative burn of Stock Tokens held by PoolManager reduces the
  raw on-chain reserve without updating CollateralTracker's cached deposited
  assets.

These findings require explicit product controls. A pause is not a simple
all-functions-off state: the UI must distinguish owner close from withdrawal
and liquidation, and warn that liquidation liveness is lost until transfers
resume. The monitor must compare raw PoolManager reserves with protocol
accounting and fail closed on an unexplained issuer burn/deficit.

## Checkpoint B boundary and next work

The fixture uses distinct option actors and an ERC-20 quote stand-in. Insolvency
for the liquidation case is induced with a Foundry-only collateral-share edit;
the test proves liquidation behavior after insolvency, not a natural route to
insolvency. The clean Anvil replay uses one random, unlocked local operator; the
separate Foundry suite proves the distinct long/short actor behavior.

Local Checkpoint B is complete. Its verifier rejects non-loopback endpoints,
requires a fresh nonce-zero chain-`31337` Anvil account, validates all 33
receipts, derives the final receipt contract from the sender nonce, checks live
runtime/wiring/closed-position state, independently recomputes the residual
budget, stops Anvil, and removes ignored replay artifacts. The `2e12` cap is
`0.000002` token at 18 decimals; the committed-SHA replay observed AMM residuals
of `0` and `1` raw units, zero credited-asset residual, and claim deviations of
`531` and `32` raw units.

This local checkpoint does not approve a public deployment. The review of core
`f4abdd7...` and the candidate V4 stack, second-actor public funding, fresh
pending-nonce regeneration, exact-sender fork simulation, and separate
broadcast approval remain hard gates. Later local test-only commits on top do
not change the exact `f4abdd7...` review target unless they modify its
deployment/runtime files.

Machine-readable evidence is in
[`../../manifests/testing/controllable-stock-token-harness-2026-09-08.json`](../../manifests/testing/controllable-stock-token-harness-2026-09-08.json).
