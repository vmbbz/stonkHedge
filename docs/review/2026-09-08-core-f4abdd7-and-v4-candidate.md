# Independent review gate: core `f4abdd7` and Robinhood V4 candidate

## Purpose and hard boundary

This runbook gives the second contributor an independent, reproducible review
of the exact Panoptic core candidate and the external Uniswap V4 infrastructure
proposed for the first valueless stonkHedge sandbox on Robinhood Chain testnet.

Completing this review does **not** authorize a deployment. During this gate:

- do not open, copy, import, or inspect any private key or `.env` file;
- do not fund the deployer as part of a test command;
- do not regenerate nonce-derived deployment artifacts;
- do not sign or broadcast a transaction; and
- do not treat the historical nonce-0 simulation as a live deployment input.

The review ends with two separate decisions: `CORE_ACCEPT` or `CORE_REJECT`, and
`V4_CANDIDATE_ACCEPT_FOR_VALUELESS_TESTNET` or `V4_CANDIDATE_REJECT`. A pass in
one lane cannot compensate for a failure or blocker in the other.

## What the obstacles mean

There is no evidence that the deployer key, Robinhood testnet, or any public
stonkHedge deployment has been compromised. No stonkHedge contract has been
deployed and the preparation and simulation tools do not read keys or broadcast.
The word "unsupported" must be split into three different facts:

| Boundary | Current meaning | Effect on stonkHedge |
|---|---|---|
| Robinhood Chain EVM support | Robinhood documents chain `46630` as EVM-compatible, with standard JSON-RPC and ETH for gas. | Solidity, Foundry, ordinary CREATE, calls, and receipts use normal Ethereum tooling. Individual token pause/blocklist rules still apply. |
| Panoptic release infrastructure | Panoptic's canonical sub-zero CREATE3 singleton has no runtime on chain `46630`; upstream release salts and Safe batches cannot be replayed there as-is. | We lose the upstream vanity/stable-address and Safe-batch path. We do not lose Panoptic bytecode compatibility. |
| Uniswap deployment provenance | Uniswap's repository publishes a Robinhood **mainnet** (`4663`) deployment page. We found no official `46630` registry page. Identical-address V4 contracts exist on testnet and have been bytecode-qualified, but remain a non-official candidate. | Reuse avoids deploying V4 infrastructure, but the team must explicitly accept its owner/control and provenance risk for a valueless testnet only. The UI must not call it an official Uniswap testnet deployment. |

The earlier red test was a normal test-driven-development checkpoint: the new
preparer did not exist yet, so the test failed for the intended reason. That
transient red run is not a separate commit. The auditable state is the exact
green candidate at `f4abdd7...`, its tests, and its parent diff. Do not count a
description of the red run as independent evidence.

Primary Robinhood references are its
[network configuration](https://docs.robinhood.com/chain/connecting/),
[contract-deployment guide](https://docs.robinhood.com/chain/deploy-smart-contracts/),
and [public-testnet announcement](https://robinhood.com/us/en/newsroom/robinhood-chain-launches-public-testnet/).

The direct-CREATE fallback deliberately changes only deployment operations:

- all 16 addresses are derived from the public sender and consecutive nonces;
- linked libraries, metadata pointers, and constructor arguments are rebuilt
  against those predicted addresses;
- one successful receipt and expected runtime must be confirmed before sending
  the next transaction; and
- any mined failure or unrelated sender transaction consumes a nonce and
  invalidates the remaining plan.

This avoids pretending that absent CREATE3 infrastructure exists. Its cost is
greater operational coupling to one EOA, no atomic Safe batch, and full artifact
regeneration after any nonce change. The current deployer is also the temporary
guardian and treasurer in the simulation; those roles are acceptable only for
the bounded, valueless sandbox and must be separated before a public alpha.

## Exact review inputs

| Input | Immutable value |
|---|---|
| Panoptic upstream base | `d65310d6cfbaadb6910fa9446cc59c6541060749` |
| Runtime-headroom change | `b0deb9f846dc15d890d96afdfd939c1091faeab9` |
| Direct-deployment candidate | `f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d` |
| Product evidence commit | `e177f07e4128dd6dd38ab63775d198458dd76efd` |
| Simulated public sender | `0xCa60c8eF6934f8a97c6a503C4e3a46e87F5b08bD` |
| Historical plan SHA-256 | `b1e354db53ecfd89042492a7ab18efb4dba909c31e8af67d5cff6de41579dd42` |
| Target chain | Robinhood Chain testnet, chain ID `46630` |

The historical plan is evidence that an exact-sender fork rehearsal worked. It
is not an artifact the reviewer should reconstruct now and it expires when the
sender's pending nonce or any dependency changes.

## Part A: review the core candidate

### A1. Use a clean, exact checkout

Use a separate review directory or a clean existing checkout. Clone recursive
submodules and detach at the exact candidate so a moving branch cannot change
what is reviewed:

```powershell
git clone --recurse-submodules https://github.com/vmbbz/panoptic-v2-core.git panoptic-v2-core-review
Set-Location .\panoptic-v2-core-review
git fetch origin --prune --tags
git switch --detach f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d
git submodule update --init --recursive
git status --short
git rev-parse HEAD
git merge-base --is-ancestor d65310d6cfbaadb6910fa9446cc59c6541060749 HEAD
git diff --check d65310d6cfbaadb6910fa9446cc59c6541060749..HEAD
```

Expected: status is empty, `HEAD` is the full `f4abdd7...` SHA, the ancestry
command exits `0`, and `git diff --check` prints nothing. Stop on any mismatch.

Review the two commits independently:

```powershell
git show --stat --oneline b0deb9f846dc15d890d96afdfd939c1091faeab9
git show --stat --oneline f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d
git diff d65310d6cfbaadb6910fa9446cc59c6541060749..b0deb9f846dc15d890d96afdfd939c1091faeab9
git diff b0deb9f846dc15d890d96afdfd939c1091faeab9..f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d
```

The first commit should touch only the release-size/Multicall surface and its
tests/documentation. The second should touch only the direct-deployment scripts,
unit tests, and deployment instructions. Unexpected files are a rejection.

### A2. Review the runtime-headroom change

For `b0deb9f...`, confirm all of the following in code rather than trusting the
reported byte count:

- `Multicall.multicall` remains payable and executes each requested call by
  `delegatecall`, preserving the caller, value, ordering, and dynamic results;
- a failed child call reverts the whole batch with the exact original revert
  bytes rather than partial success or a replacement error;
- the assembly memory layout cannot overlap the result array or corrupt the free
  memory pointer;
- the ERC-2771 calldata-appending caveat and Solady attribution remain visible;
- the optimizer change to `1` is limited to `PanopticPoolV2` in both exact V3
  and V4 release configs; and
- the size gate checks the exact linked release build, applies a 256-byte logic
  runtime margin under EIP-170, checks EIP-3860 initcode, and runs in CI.

Run the exact size and focused regression lanes:

```powershell
bun run .\metadata\compiler.js
python -B .\script\check_release_sizes.py .\build-config-v4.json --margin 256
python -B .\script\check_release_sizes.py .\build-config-v3.json --margin 256

$env:FOUNDRY_PROFILE = 'ci_test'
forge test --match-path 'test/foundry/base/Multicall.t.sol' -vv
forge test --match-path 'test/foundry/core/PanopticFactory.t.sol' -vv
forge test --match-path 'test/foundry/core/PanopticPool.t.sol' -vv
forge test --match-path 'test/foundry/core/SemiFungiblePositionManager.t.sol' -vv
forge test --match-path 'test/foundry/core/RiskEngine/*.t.sol' -vv
Remove-Item Env:\FOUNDRY_PROFILE
```

Expected evidence from the pinned candidate is: both size lanes pass;
`PanopticPoolV2` runtime is 24,275 bytes with 301 bytes of raw EIP-170 headroom;
and the focused V4 lanes have no failures. One inherited SFPM test contains an
unconditional skip in source, so do not report that unexecuted test as a pass.

### A3. Review the direct-deployment tools

Read these four files in full:

- `script/prepare_direct_deployment.py`
- `script/simulate_direct_deployment.py`
- `script/tests/test_prepare_direct_deployment.py`
- `script/tests/test_simulate_direct_deployment.py`

Confirm that the preparer accepts only files plus public configuration, invokes
local build/address/hash tooling, and has no RPC URL, private-key, signing, or
broadcast input. Confirm that the simulator:

- accepts only `http://localhost` or loopback IP RPC URLs;
- requires the RPC client to identify as Anvil before mutating fork state;
- locally impersonates and funds only the public sender on the disposable fork;
- checks chain ID, starting nonce, ordered CREATE address, receipt success,
  non-empty runtime, final nonce, and the plan hash;
- bounds receipt polling; and
- rejects a transaction gas limit at or above 2^24.

Run the unit suite:

```powershell
python -B -m unittest discover -s .\script\tests -p 'test_*direct_deployment.py' -v
```

Expected: 11 tests pass. This is offline/unit evidence. Do not start Anvil and do
not create new deployment artifacts during this review gate; the exact fork
simulation is already recorded in the product evidence lane below.

### A4. Core acceptance decision

Record `CORE_ACCEPT` only if the checkout, diff, size gates, focused contract
tests, direct-deployment tests, and manual code review all pass. Otherwise record
`CORE_REJECT` with exact file/line findings, failing command, and output. A tool
installation or RPC problem is `BLOCKED`, never a pass.

## Part B: review the candidate V4 infrastructure

### B1. Pin the product evidence

Use a second clean checkout and detach at the immutable evidence commit:

```powershell
git clone https://github.com/vmbbz/stonkHedge.git stonkHedge-evidence-review
Set-Location .\stonkHedge-evidence-review
git fetch origin --prune --tags
git switch --detach e177f07e4128dd6dd38ab63775d198458dd76efd
git status --short
git rev-parse HEAD
git diff --check HEAD^
Get-Content .\manifests\chains\robinhood-testnet-46630.json -Raw | ConvertFrom-Json | Out-Null
Get-Content .\manifests\deployments\robinhood-testnet-direct-preflight-2026-09-08.json -Raw | ConvertFrom-Json | Out-Null
```

Expected: empty status, exact `e177f07...` SHA, no whitespace errors, and both
JSON files parse. Read both manifests plus:

- `docs/chain/2026-09-08-robinhood-testnet-qualification.md`
- `docs/deployment/2026-09-08-direct-deployment-simulation.md`
- `scripts/verify-robinhood-testnet.ps1`

### B2. Reproduce the read-only verifier

This command performs only public RPC reads and intentionally skips the funding
gate. It neither needs nor reads a wallet key:

```powershell
pwsh -File .\scripts\verify-robinhood-testnet.ps1 -SkipFundingGate
```

Expected if public state has not drifted: exit `0`; all identity, runtime-hash,
owner, wiring, Stock Token, pause, multiplier, WETH, and test-USDC checks pass;
the deployer funding line is `SKIPPED`. Any identity or state mismatch is
`V4_CANDIDATE_REJECT`, not a reason to edit the manifest to current values.

Then run the strict mode to prove that deployment is still blocked before
funding:

```powershell
pwsh -File .\scripts\verify-robinhood-testnet.ps1
```

Expected before the faucet step: non-zero exit because deployer funding is
`BLOCKED`, while preceding dependency checks still pass. A strict pass would
mean the funding state changed and must be investigated before regenerating any
nonce-derived artifact.

### B3. Independently spot-check the critical V4 controls

Do not rely only on our verifier. Run independent calls against chain `46630`:

```powershell
$rpc = 'https://rpc.testnet.chain.robinhood.com'
$poolManager = '0x8366a39CC670B4001A1121B8F6A443A643e40951'
$positionManager = '0x58daec3116aae6D93017bAAea7749052E8a04fA7'

cast chain-id --rpc-url $rpc
cast codehash $poolManager --rpc-url $rpc
cast call $poolManager 'owner()(address)' --rpc-url $rpc
cast call $poolManager 'protocolFeeController()(address)' --rpc-url $rpc
cast codehash $positionManager --rpc-url $rpc
cast call $positionManager 'poolManager()(address)' --rpc-url $rpc
```

Expected:

| Check | Expected value |
|---|---|
| Chain ID | `46630` |
| PoolManager code hash | `0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626` |
| PoolManager owner | `0x9701fb0aDe1E269c8f64Ec0C7b3cfADB31A13A52` |
| Protocol fee controller | zero address |
| PositionManager code hash | `0xf3a0edb689229fa4bf135a728f2ec2eb4a2fbee2e41e3e74ffadb7b4c56e8a6d` |
| PositionManager's PoolManager | exact PoolManager above |

The owner currently has no runtime code. That proves only that it is an EOA at
the observed block; it does not prove who controls it. Owner and fee-controller
authority are the main residual external-control risk. For a valueless sandbox,
the reviewer may explicitly accept that risk only while the verifier fails
closed on drift and the UI labels the infrastructure non-official.

### B4. Check provenance without upgrading it into an endorsement

Use the primary Uniswap deployment repository to confirm that the PoolManager,
PositionManager, Quoter, StateView, Permit2, and UniversalRouter addresses are
published for Robinhood mainnet chain `4663`:

<https://github.com/Uniswap/contracts/blob/main/deployments/4663.md>

The candidate testnet PoolManager runtime hash also matches the recorded
official mainnet runtime hash. This is strong bytecode-equivalence evidence, but
it is not an official chain-`46630` listing and not proof of current owner
identity. The EqualFi chain-`46630` manifest is a reproducibility/discovery lead,
not the authority:

<https://github.com/EqualFiLabs/statics/blob/master/deployments/robinhood-chain-testnet-46630.json>

If Uniswap later publishes an official `46630` entry, open a separate manifest
update and compare it; do not silently change this historical review.

### B5. V4 acceptance decision

Record `V4_CANDIDATE_ACCEPT_FOR_VALUELESS_TESTNET` only if all current hashes,
wiring, control values, Stock Token health checks, and primary-source address
comparisons pass, and the reviewer accepts the explicitly non-official status.
Acceptance is limited to the valueless sandbox. Reject on any drift, unexpected
proxy/control path, unexplained source mismatch, or inability to reproduce the
checks. Rejection means deploying a separately reviewed minimal V4 stack or
waiting for an official testnet deployment; it does not invalidate Robinhood
Chain compatibility or the Panoptic core work.

## Part C: official faucet without the deployer key in the browser

Use only Robinhood's official testnet faucet:

<https://faucet.testnet.chain.robinhood.com/>

The faucet Stock Tokens are testnet-only integration assets. They are not real
equity claims and successful receipt does not imply unrestricted transferability;
the reviewed registry, pause, blocklist, and multiplier checks remain mandatory.

Do not import the deployer private key into a browser wallet you do not control.
The faucet's interface may change, so use this decision tree:

1. If the official page provides a plain recipient-address field, paste only
   the public deployer address
   `0xCa60c8eF6934f8a97c6a503C4e3a46e87F5b08bD`, confirm chain `46630`, and request
   bounded test ETH and test Stock Tokens.
2. If the page requires wallet connection or a signature, do not use the
   uncontrolled browser wallet. Use a fresh test-only browser profile and wallet
   that you control, or ask the friend to use a fresh wallet they control. Never
   share a seed phrase or private key.
3. Keep that fresh wallet as the second test actor. From its normal wallet UI,
   send a tiny native-ETH probe and the smallest transferable amount of one Stock
   Token to the public deployer address. Verify both receipts before sending any
   additional bounded test amount. Never send real ETH or real assets.
4. Record only public actor addresses and transaction hashes. Do not paste a
   key, seed phrase, keystore, or `.env` content into an issue, chat, terminal
   history, or review report.

Robinhood documents ETH as the native gas token for testnet. A faucet claim to a
controlled second actor followed by ordinary transfers does not alter the
deployer nonce until the deployer itself sends a transaction. Nevertheless,
after funding, re-read the deployer's pending nonce and all dependency state.
Do not infer that it is still zero.

After the browser transfer, either contributor can verify public balances with
no key:

```powershell
$rpc = 'https://rpc.testnet.chain.robinhood.com'
$deployer = '0xCa60c8eF6934f8a97c6a503C4e3a46e87F5b08bD'
$stock = '<EXACT_STOCK_TOKEN_ADDRESS_FROM_THE_REVIEWED_MANIFEST>'

cast balance $deployer --rpc-url $rpc
cast call $stock 'balanceOf(address)(uint256)' $deployer --rpc-url $rpc
pwsh -File .\scripts\verify-robinhood-testnet.ps1
```

Funding is complete only when strict verification passes and the second actor
retains enough test ETH and the selected Stock Token for the two-actor lifecycle.
Faucet success alone is not proof that the correct address received usable
assets.

## Review report template

Copy this into the pull request or a new review record. Do not edit the evidence
manifests merely to record approval.

```text
Reviewer:
UTC timestamp:

CORE_REVIEW: CORE_ACCEPT | CORE_REJECT | BLOCKED
Core SHA: f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d
Clean checkout and ancestry:
Diff review findings:
V4 size gate:
V3 size gate:
Focused Foundry results:
Direct-deployment unit results:
Residual core risks accepted/rejected:

V4_REVIEW: V4_CANDIDATE_ACCEPT_FOR_VALUELESS_TESTNET | V4_CANDIDATE_REJECT | BLOCKED
Product evidence SHA: e177f07e4128dd6dd38ab63775d198458dd76efd
Observed block number/hash:
Verifier -SkipFundingGate result:
Strict verifier result:
Independent PoolManager code hash/owner/fee-controller:
Independent PositionManager code hash/wiring:
Provenance findings:
Residual external-control risks accepted/rejected:

NONCE_REGENERATION_GATE: GO | NO_GO
Reason:
```

`NONCE_REGENERATION_GATE` remains `NO_GO` unless both review decisions are
accepted and strict funding verification passes. Only then may the operator
read the current pending nonce, regenerate every derived address/config/bundle/
plan, rerun the exact fork simulation, and request a separate broadcast review.
