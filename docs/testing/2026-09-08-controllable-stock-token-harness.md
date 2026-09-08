# Controllable Stock Token harness evidence — 2026-09-08

## Outcome

The standalone Hours 10–11 compatibility harness is implemented and pushed in
the core fork at commit
`159dabdd09a8b1168b23aa732fec9cb562a3f22b` on branch
`feat/stock-token-compatibility-harness`.

This is a local test double, not Robinhood issuer code, a synthetic equity, or
a deployable public asset. It lives only under `test/foundry/mocks/`; no local
fixture address is permitted in a chain-`46630` manifest.

## Red-to-green evidence

The first focused test run failed because
`test/foundry/mocks/ControllableStockToken.sol` did not exist. That was the
intended red boundary. The minimum implementation was then added and the same
focused suite completed with `16 passed, 0 failed, 0 skipped`, including 30 fuzz
runs for scaled-view rounding.

Reproduce from `C:\dev-shared\stonkHedge-core`:

```powershell
git switch --detach 159dabdd09a8b1168b23aa732fec9cb562a3f22b
$env:FOUNDRY_PROFILE = "ci_test"
forge test --match-path test/foundry/mocks/ControllableStockToken.t.sol --fuzz-runs 30
forge fmt --check
forge test --match-path test/foundry/base/Multicall.t.sol
python -m unittest discover -s script/tests -p "test_*direct_deployment.py"
Remove-Item Env:\FOUNDRY_PROFILE
```

Observed results:

| Check | Result |
|---|---|
| Controllable-token focused suite | `16 passed, 0 failed, 0 skipped` |
| Fuzz multiplier/rounding cases | `30` runs |
| Formatting | `forge fmt --check` passed |
| Inherited Multicall regression | `4 passed, 0 failed, 0 skipped` |
| Direct-deployment Python tests | `11 passed` |

Inherited Solar preprocessor warnings about duplicate `stdMath` declarations
remain visible during compilation; they did not fail these focused checks and
were not suppressed.

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

## Remaining Hours 11–16 work

The standalone token model is green; the protocol lifecycle is not yet proven.
The next red tests must integrate the token with a local pinned Uniswap v4 and
Panoptic stack and measure deposit, market registration, open, premium,
close/liquidation, and withdrawal behavior under pause, block, multiplier, and
forced-burn transitions.

This local work may continue while the independent review runs. The review of
core `f4abdd7...` and the candidate V4 stack remains a hard gate before any
public transaction trusts those dependencies.

Machine-readable evidence is in
[`../../manifests/testing/controllable-stock-token-harness-2026-09-08.json`](../../manifests/testing/controllable-stock-token-harness-2026-09-08.json).
