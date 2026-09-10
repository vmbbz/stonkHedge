# Checkpoint A baseline report — 2026-09-08

## Outcome

The three intended repositories and pinned source commits exist, the Panoptic core's recursive submodules are now initialized, and the unchanged core compiles. Bun and the deterministic metadata prerequisite are installed, the V4 release builder succeeds, and the pinned-block Factory, PanopticPool, SFPM, and RiskEngine baseline suites pass. Checkpoint A is **not green yet**: the exact release artifact's `PanopticPoolV2` exceeds EIP-170 and the standalone SDK checkout cannot resolve its private workspace dependency. The product worktree also contains the owner's pre-existing untracked `buildl.md`; that unrelated file is preserved as a hygiene warning, not treated as a protocol blocker.

No inherited protocol behavior was changed. No key was read or printed. No contract was deployed.

The machine-readable source of truth for this snapshot is [`../../manifests/baseline/2026-09-08.json`](../../manifests/baseline/2026-09-08.json).

## Feedback attachment reconciliation

The supplied `pasted-text.txt` contains an earlier 634-line copy of the StonkHedge build plan. It does not contain a separately labeled Grok critique or attributable feedback passages. It was therefore not used to overwrite the newer approved plan or to invent quotations.

The durable, non-duplicative challenge points that a critical long-term review should retain are now explicit in `plan.md` Section 10.2: architecture alternatives, liquidity ownership, issuer/infrastructure dependency, user evidence, economic viability, governance/escape, assurance depth, distribution/jurisdiction, and scope discipline. If the actual Grok response is supplied later, each point should be mapped to that section with its source and disposition.

## Repository topology

| Repository | Branch | Pinned commit | Result |
|---|---|---|---|
| Product | `main` | contains planning baseline `66061ce504cdf81e860e29d82c744f5df7067887` | `KNOWN DIRTY`: untracked `buildl.md` is preserved and excluded from the checkpoint |
| Core fork | `feature/equity-options-base` | exact `d65310d6cfbaadb6910fa9446cc59c6541060749` | `PASS`: clean tracked tree and 48 recursive submodules initialized |
| SDK fork | `feature/equity-options-base` | exact `aa971d1f9ea5836546cd5266bcbfb94138ef4f57` | `PASS`: clean tree; build readiness is separately blocked |

Both derived repositories have the expected `origin` fork and fetch-only `upstream` remote. Their feature branches track the corresponding `origin` feature branch.

## Captured toolchain

| Tool | Version/result |
|---|---|
| Windows | `Microsoft Windows NT 10.0.26200.0` |
| PowerShell | `7.5.2` |
| Git | `2.47.0.windows.1` |
| Node | `22.15.0` |
| npm | `11.6.2` |
| pnpm | `10.30.2` |
| Python | `3.11.9` |
| Forge/Cast/Anvil | `1.8.1`, commit `982849d3140c01fd3b72905759581a132df7aa98` |
| Bun | `1.4.2`, revision `744846f84` |
| Standalone solc | not installed; Foundry fetched `0.8.24`, `0.8.26`, and `0.8.36` as selected by source pragmas |

## Executed evidence

### Core dependency initialization

Command:

```powershell
git submodule update --init --recursive
```

Result: `PASS`. Forty-eight recursive entries are initialized at the gitlinks reachable from `d65310d6`. The normalized status snapshot has SHA-256 `bfe1f59bc28e8743032d541dbc981713a096fdad3a4b0876bad5b83714525b01`.

### Unchanged core build

Command, with build artifacts kept outside all repositories:

```powershell
forge build --out "$env:TEMP\stonkhedge-core-baseline-20260908\out" --cache-path "$env:TEMP\stonkhedge-core-baseline-20260908\cache"
```

Result: `PASS` with inherited warnings. Foundry reported more than 256 compiler warnings, including future-keyword/deprecation warnings, and warned that nine direct dependencies are absent from `foundry.lock`. The baseline is compilable, but the warning and dependency-lock debt must remain visible.

### Default-profile size check

Command:

```powershell
forge build --out "$env:TEMP\stonkhedge-core-baseline-20260908\out-production" --cache-path "$env:TEMP\stonkhedge-core-baseline-20260908\cache-production" --sizes --skip test
```

Result: `FAIL`. The report still compiled some test support files, but it exposed a production-relevant result: `PanopticPoolV2` is `24,658` runtime bytes, `82` bytes above EIP-170's `24,576`-byte limit in the default Foundry profile. Other primary V4 values included `RiskEngine` `22,789`, `SemiFungiblePositionManagerV4` `19,085`, `PanopticFactoryV4` `16,024`, and `CollateralTrackerV2` `17,337` bytes.

That first default-profile result was not used alone to justify a source change. The exact release-config build below establishes the real blocker.

### Metadata and release-config preflight

Commands:

```powershell
bun run ./metadata/compiler.js
python -c "import eth_abi; print(eth_abi.__version__)"
python build_release.py --dry-run build-config-v4.json
```

Result: `PASS`. Bun `1.4.2` generated the ignored `metadata/out/MetadataPackage.json`; `eth_abi` `5.2.0` is available; and the V4 dry run resolved seven data contracts plus nine logic contracts without writes. The configured optimizer runs include `399` for `PanopticPoolV2`, rather than the default profile's `200`, so the exact release build remains the deciding size gate.

### Exact V4 release build and size boundary

Command:

```powershell
python build_release.py build-config-v4.json "$env:TEMP\stonkhedge-core-baseline-20260908\deployment-info-v4.json"
```

Result: `PASS` for compilation of all seven metadata contracts and nine logic contracts. The temporary 591,489-byte bundle has SHA-256 `88fdf3d23ac0eca77927623782a873b838341cbedc62c45860fde999667f7339`. It uses the upstream mainnet-oriented external addresses and is compile evidence only—not a Robinhood testnet manifest or deployable approval.

An exact standalone size build with Solidity `0.8.28`, optimizer-runs `399`, and the release library links reports `PanopticPoolV2` at `24,869` runtime bytes: `293` bytes over EIP-170. The upstream optimizer search produced:

| Search | Result |
|---|---|
| Current `399` runs | `24,869` bytes; over by `293` |
| Maximum zero-margin fit | `133` runs; exactly `24,576` bytes; no headroom |
| Smallest `1` run | `24,501` bytes; only `75` bytes headroom |
| Required 256-byte safety margin | no optimizer-only solution |

Deployment remains `BLOCKED`. Do not change the release config to `133` and deploy at the exact limit. First add an automated size regression targeting at most `24,320` bytes, then make the smallest behavior-preserving source reduction and rerun the 233-pass baseline plus deployment verification.

### Focused V4 tests

All suites used `FOUNDRY_PROFILE=ci_test`, which pins the inherited fork block at `18963715`.

| Suite | Result |
|---|---|
| `test/foundry/core/PanopticFactory.t.sol` | `PASS`: 7 passed, 0 failed, 0 skipped |
| `test/foundry/core/PanopticPool.t.sol` | `PASS`: 72 passed, 0 failed, 0 skipped |
| `test/foundry/core/SemiFungiblePositionManager.t.sol` | `PASS`: 37 passed, 0 failed, 1 skipped |
| `test/foundry/core/RiskEngine/*.t.sol` | `PASS`: 117 passed, 0 failed, 0 skipped across 10 suites |

The combined focused baseline is 233 passed, 0 failed, and 1 skipped. The SFPM skip is inherited `test_removedLiquidityOverflow`; it remains visible and needs an upstream rationale before StonkHedge relies on that edge case. The suites also emit inherited compiler and deprecated-cheatcode warnings. Passing baseline tests prove reproducibility at the pinned commit, not Stock Token compatibility or StonkHedge safety.

### SDK install preflight

Command:

```powershell
pnpm install --lockfile=false --ignore-scripts
```

Result: `BLOCKED` with `ERR_PNPM_WORKSPACE_PKG_NOT_FOUND`. The synced standalone SDK repository declares `@panoptic-eng/deployments@workspace:*`, while its tree contains neither that workspace package nor a lockfile/workspace definition. A public npm registry lookup returns `E404`; comments in the checked-in build configuration explicitly identify the package as internal and unpublished. The Panoptic Labs public GitHub organization contains no deployments repository. The failed preflight left the SDK tree clean.

Do not work around this with an unpinned ad hoc package. First inspect the source monorepo commit named by the SDK sync commit, then choose and document one reproducible repair:

1. obtain access to the complete pinned private monorepo/workspace named by SDK sync commit `976165ae69fa2595213e856df035a90c8c6a64a0`; or
2. make the public standalone SDK genuinely self-contained by reconstructing the exact compatible deployments module from an authorized source, removing the private workspace dependency, and committing a lockfile and parity tests.

Do not fabricate chain deployments or silently drop the affected HypoVault exports merely to make installation green.

The public registry does contain a self-contained `@panoptic-eng/sdk@1.0.49` artifact matching the source checkout's package version. Its registry integrity is `sha512-JRx+t3NPVwp70XwdtUto6I11Eq5NI61VVyWEmXXnEnUURXi64VxVJIL0oj4rICdq3I4tZFhkcAWm3P2WWdLbvg==`, and its public dependency list does not include the private deployments workspace. The first sandbox will pin that exact package and put StonkHedge-specific adapters in the product repo; source-fork publication remains blocked until parity is reproducible.

### License record audit

Result: `PASS` for evidence collection and `BLOCKED` for production permission. At Ethereum block `25932700`, both ENS child names referenced by the pinned BUSL license had zero owner and resolver, and the parent resolver did not support wildcard resolution. No Additional Use Grant or alternative change date is available. See [`panoptic-license-2026-09-08.md`](./panoptic-license-2026-09-08.md). StonkHedge proceeds only as a bounded, valueless, non-monetized non-production testnet project; production and mainnet remain separately blocked.

### Baseline verifier

From the product repository:

```powershell
pwsh -File .\scripts\verify-baseline.ps1
```

The verifier checks paths, commits, branch names, remotes, required files, recursive submodule initialization, clean worktrees, and recorded gates. It exits non-zero for `FAIL` or `BLOCKED`. During an intentional editing session, `-AllowDirty` may be used only to test the other checks; it prints worktree checks as `SKIPPED` and does not convert recorded blockers into passes.

## Recovery order

1. Add a red release-size regression capped at `24,320` bytes, make the smallest reviewed `PanopticPoolV2` source reduction, and rerun all focused V4 lanes; the exact release build is currently `293` bytes over EIP-170.
2. Reconstruct the SDK's intended workspace from its source monorepo or make the standalone package reproducible with an exact compatible deployments dependency and lockfile.
3. Run the focused V4 factory, pool, SFPM, and RiskEngine lanes and record exact counts.
4. Re-audit and archive the mutable ENS license records immediately before the bounded public-testnet launch; obtain written permission or qualified advice before any production-like public operation.
5. Re-run this verifier and update each manifest gate only with new evidence. Strict mode will continue to report the unrelated `buildl.md` until the owner chooses its disposition; do not mix it into protocol commits.

Checkpoint A must remain visibly incomplete until these results are either `PASS` or accepted as narrowly scoped blockers that do not affect the next local-only action.
