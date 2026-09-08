# Controllable Stock Token and local Panoptic lifecycle evidence — 2026-09-08

## Outcome

The standalone Hours 10–11 compatibility harness and the first local
Stock/quote Panoptic lifecycle are implemented and pushed on branch
`feat/stock-token-compatibility-harness`. The latest evidence commit is
`e6646eb6a259a6152d770090e63ec61ecc67ed09`, built on the standalone token
commit `159dabdd09a8b1168b23aa732fec9cb562a3f22b`.

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
git switch --detach e6646eb6a259a6152d770090e63ec61ecc67ed09
$env:FOUNDRY_PROFILE = "ci_test"
forge test --match-path test/foundry/mocks/ControllableStockToken.t.sol --fuzz-runs 30
forge fmt --check test/foundry/integration/StockTokenPanopticFixture.sol test/foundry/integration/StockTokenPanopticLifecycle.t.sol
forge test --match-path test/foundry/integration/StockTokenPanopticLifecycle.t.sol --fuzz-runs 30
forge test --match-path test/foundry/core/PanopticFactory.t.sol
forge test --match-path test/foundry/core/PanopticPool.t.sol
forge test --match-path test/foundry/base/Multicall.t.sol
python -m unittest discover -s script/tests -p "test_*direct_deployment.py"
Remove-Item Env:\FOUNDRY_PROFILE
```

Observed results:

| Check | Result |
|---|---|
| Controllable-token focused suite | `16 passed, 0 failed, 0 skipped` |
| Fuzz multiplier/rounding cases | `30` runs |
| Local Stock/quote Panoptic lifecycle | `11 passed, 0 failed, 0 skipped` |
| Inherited Panoptic factory | `7 passed, 0 failed, 0 skipped` |
| Inherited PanopticPool | `72 passed, 0 failed, 0 skipped` |
| Scoped formatting | passed for both new integration files |
| Inherited Multicall regression | `4 passed, 0 failed, 0 skipped` |
| Direct-deployment Python tests | `11 passed` |

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
- the UI multiplier changes scaled views but not Panoptic's raw-unit collateral
  accounting;
- token or registry pause and a blocked PoolManager reject affected deposits
  atomically and recover after the restriction is lifted;
- an option already open at pause can close using PoolManager internal balances,
  while stock withdrawal and external stock-involving swaps stay blocked; and
- forced administrative burn of Stock Tokens held by PoolManager reduces the
  raw on-chain reserve without updating CollateralTracker's cached deposited
  assets.

The last two findings require explicit product controls. A pause is not a simple
all-functions-off state: the UI must distinguish internal option close from
underlying withdrawal. The monitor must compare raw PoolManager reserves with
protocol accounting and fail closed on an unexplained issuer burn/deficit.

## Remaining Checkpoint B work

The fixture uses one option actor and an ERC-20 quote stand-in. It has not yet
proven a separately controlled long/short pair, forced liquidation under issuer
restrictions, a clean standalone Anvil replay, or the local independent
verifier. These remain the next test layer; this evidence does not claim Hours
15–16 or Checkpoint B complete.

This local work may continue while the independent review runs. The review of
core `f4abdd7...` and the candidate V4 stack remains a hard gate before any
public transaction trusts those dependencies. Later test-only commits on top do
not change the exact review target unless they modify its deployment/runtime
files.

Machine-readable evidence is in
[`../../manifests/testing/controllable-stock-token-harness-2026-09-08.json`](../../manifests/testing/controllable-stock-token-harness-2026-09-08.json).
