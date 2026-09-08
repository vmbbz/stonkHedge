# Checkpoint B runtime-headroom report — 2026-09-08

## Outcome

The release-size blocker recorded at Checkpoint A is resolved in the pushed core-fork candidate `b0deb9f846dc15d890d96afdfd939c1091faeab9` on `fix/pool-runtime-headroom`. Exact V3 and V4 release configurations now enforce a 256-byte EIP-170 margin and pass. The largest contract, `PanopticPoolV2`, is 24,275 runtime bytes, leaving 301 bytes of raw headroom and passing the project margin by 45 bytes.

This is a review candidate, not permission to deploy. No private key was read or printed, no transaction was broadcast, and no stonkHedge contract has been deployed. Independent review, Robinhood chain/address qualification, an exact-sender simulation, and faucet funding remain required.

The machine-readable source of truth is [`../../manifests/baseline/2026-09-08.json`](../../manifests/baseline/2026-09-08.json). Checkpoint A remains as the immutable red-baseline narrative in [`2026-09-08-checkpoint-a.md`](./2026-09-08-checkpoint-a.md).

## Pinned repositories

| Repository | Branch | Commit | State |
|---|---|---|---|
| Product | `main` | contains baseline `66061ce504cdf81e860e29d82c744f5df7067887` | user-owned untracked `buildl.md` preserved |
| Core fork | `fix/pool-runtime-headroom` | `b0deb9f846dc15d890d96afdfd939c1091faeab9` | pushed to `vmbbz/panoptic-v2-core` |
| SDK fork | `feature/equity-options-base` | `aa971d1f9ea5836546cd5266bcbfb94138ef4f57` | unchanged and clean |

The core candidate is based directly on upstream `d65310d6cfbaadb6910fa9446cc59c6541060749`. Its 48 recursive submodules remain initialized at the recorded gitlinks.

## Red-to-green size evidence

All `PanopticPoolV2` measurements use Solidity `0.8.28` with the exact release library links.

| State | Optimizer runs | Runtime bytes | Raw EIP-170 headroom | Result against 256-byte margin |
|---|---:|---:|---:|---:|
| Upstream release baseline | 399 | 24,869 | -293 | fail by 549 bytes |
| Optimizer-only experiment | 1 | 24,501 | 75 | fail by 181 bytes |
| Checkpoint B candidate | 1 | 24,275 | 301 | pass by 45 bytes |

The final reduction combines optimizer-runs `1` for the pool in both release configs with a behavior-preserving assembly implementation of `Multicall.multicall`. The implementation retains the payable ABI, delegatecall caller/value context, ordered dynamic return data, and exact revert bubbling. Its source records the vendored Solady attribution and the ERC-2771 calldata-appending caveat.

The new size checker derives artifacts through the repository's release optimizer and fails if any selected runtime exceeds `24,576 - 256` bytes or if any initcode exceeds EIP-3860. CI runs the checker for both `build-config-v3.json` and `build-config-v4.json`.

## Exact release size gates

Both V3 and V4 configurations pass the 256-byte runtime-margin gate for every configured logic contract. The V4 values are:

| Contract | Runtime bytes |
|---|---:|
| `PanopticMath` | 3,217 |
| `InteractionHelper` | 7,020 |
| `CollateralTrackerV2` | 21,338 |
| `Guardian` | 5,562 |
| `BuilderFactory` | 3,744 |
| `RiskEngine` | 22,483 |
| `SemiFungiblePositionManagerV4` | 23,608 |
| `PanopticPoolV2` | 24,275 |
| `PanopticFactoryV4` | 20,702 |

The corresponding V3-specific values are `SemiFungiblePositionManager` 23,386 bytes and `PanopticFactory` 20,140 bytes; shared contracts have the same values shown above. `PanopticPoolV2` initcode is 24,488 bytes, below the EIP-3860 limit.

The exact V4 release builder completed all nine configured logic contracts. Its temporary 588,815-byte JSON bundle had SHA-256 `f8981c6da71068e26d7ed3eabb59682d4826133aa5a0bb7949dbe91fc0c846c6`; it was removed after hashing and was never a Robinhood deployment manifest.

## Regression evidence

All inherited suites used `FOUNDRY_PROFILE=ci_test` and the repository's pinned fork block.

| Lane | Executed result |
|---|---|
| V4 Factory | 7 passed, 0 failed |
| V4 PanopticPool | 72 passed, 0 failed |
| V4 SFPM | 38 passed, 0 failed |
| V4 RiskEngine | 117 passed, 0 failed across 10 suites |
| New focused Multicall | 4 passed, 0 failed |
| Inherited PanopticPool multicall range | 3 passed, 0 failed |

The four focused tests cover empty output, ordered and dynamic results, caller propagation, `msg.value`, exact revert bytes, and atomic rollback. The inherited 234-test core total has zero failures. One additional inherited SFPM test still contains an unconditional `vm.skip(true)` in source; it is not counted as an executed pass and remains review debt.

Inherited compiler/deprecation warnings and missing `foundry.lock` dependency warnings also remain visible. Green focused tests establish evidence for this narrow diff; they do not prove issuer-token compatibility, economic safety, or an independent audit.

## SDK lane disposition

The SDK source fork still cannot install standalone because its synced package refers to unpublished `@panoptic-eng/deployments@workspace:*`. That remains a future source-contribution gate. It does not block the first sandbox, which is pinned to self-contained public package `@panoptic-eng/sdk@1.0.49` and registry integrity `sha512-JRx+t3NPVwp70XwdtUto6I11Eq5NI61VVyWEmXXnEnUURXi64VxVJIL0oj4rICdq3I4tZFhkcAWm3P2WWdLbvg==`; stonkHedge-specific adapters belong in the product repository until the source lane is reproducible.

## Next gates

1. A second contributor reviews the complete core diff and records approval or actionable objections.
2. Re-query Robinhood chain `46630`; qualify PoolManager/periphery and candidate Stock Token addresses by runtime code, roles, decimals, pause state, multiplier state, and provenance.
3. Build a chain-specific, zero-secret deployment manifest and simulate every transaction with the exact public deployer address.
4. Fund the deployer and a distinct test actor through the official faucet, then re-read balances.
5. Broadcast only the reviewed, simulated, manifest-listed testnet transactions and record receipts plus post-state.
