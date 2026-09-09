# Owner clean-room reproduction: core `f4abdd7` and Robinhood V4 candidate

## Outcome

At `2026-09-09T00:06:55Z`, the owner/Codex clean-room reproduction accepted
core commit `f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d` and accepted the existing
Robinhood Chain testnet V4 stack for a strictly valueless testnet only. The
frozen product evidence commit was
`e177f07e4128dd6dd38ab63775d198458dd76efd`.

This is not represented as an independent-human review. The owner explicitly
chose to continue with a separate clean-room checkout while the invited
contributor remained unavailable. That is an owner-approved testnet-only
process waiver, not an audit, endorsement, mainnet approval, or permission to
handle real value.

Decision record:

```text
OWNER_CORE_REPRODUCTION: ACCEPT
OWNER_V4_REPRODUCTION: ACCEPT_FOR_VALUELESS_TESTNET
INDEPENDENT_HUMAN_REVIEW: NOT_SATISFIED; MAY ARRIVE LATER AS DEFENCE_IN_DEPTH
NONCE_REGENERATION_GATE: GO_FOR_OFFLINE_ARTIFACT_REGENERATION_ONLY
PUBLIC_BROADCAST_GATE: NO_GO_PENDING_SECOND_ACTOR_AND_FRESH_ARTIFACT_REVIEW
```

No private key, `.env` value, signing operation, nonce-changing transaction, or
public broadcast was used during this reproduction.

## Clean-room checkouts

The review was performed outside both working repositories under
`C:\dev-shared\stonkHedge-review`:

- `panoptic-v2-core-review` was detached at exact core SHA `f4abdd7...`;
- `stonkHedge-evidence-review` was detached at exact evidence SHA `e177f07...`;
- upstream base `d65310d6cfbaadb6910fa9446cc59c6541060749` was confirmed as an
  ancestor of the core candidate;
- all 48 recursive core submodule gitlinks matched their recorded commits; and
- both review worktrees were clean before testing.

Windows long-path support had to be enabled in the review clones to finish the
deep recursive submodule checkout. One submodule interrupted by the initial
timeout was fetched and checked out at its recorded gitlink, then `git fsck`
passed. This changed local Git configuration only, not reviewed source.

## Core evidence

The candidate changes were reviewed as two bounded commits. Runtime-headroom
commit `b0deb9f846dc15d890d96afdfd939c1091faeab9` changes the shared Multicall,
release size tooling/configuration, CI gate, tests, and deployment instructions.
Commit `f4abdd7...` adds the offline direct-CREATE preparer, loopback-only Anvil
simulator, tests, and runbook.

Manual review confirmed:

- the Multicall assembly is a faithful adaptation of the vendored Solady
  implementation and retains the vendored MIT license attribution;
- the intended Panoptic `payable` behavior, exact revert bubbling, result
  ordering, dynamic return data, sender/value behavior, and transaction rollback
  are covered by focused tests;
- the release size checker builds the exact configured paths, optimizer runs,
  link addresses, and constructor arguments before enforcing EIP-170 and
  EIP-3860;
- the preparer accepts no RPC URL, private key, signer, or broadcast option and
  emits only ordered `CREATE` artifacts; and
- the simulator accepts only credential-free loopback HTTP URLs, rejects a
  non-Anvil client before mutation, impersonates the public sender locally,
  applies a gas limit below `2^24`, validates receipts/created addresses/runtime,
  and verifies the final nonce.

Reproduced gates:

| Gate | Result |
|---|---|
| Metadata compiler | PASS |
| V4 exact release size gate, 256-byte policy margin | PASS |
| V3 exact release size gate, 256-byte policy margin | PASS |
| Direct-deployment Python tests | 11 passed, 0 failed |
| Multicall Foundry tests | 4 passed, 0 failed |
| PanopticFactory V4 Foundry tests | 7 passed, 0 failed |
| PanopticPool V4 Foundry tests | 72 passed, 0 failed |
| SFPM V4 Foundry tests | 37 passed, 0 failed, 1 pre-existing explicit skip |
| RiskEngine V4 Foundry tests | 117 passed, 0 failed |

The tightest configured logic runtime remains `PanopticPoolV2` at 24,275 bytes,
with 301 bytes of raw EIP-170 headroom. That is only 45 bytes beyond the required
256-byte policy margin, so this pass applies only to the exact source, compiler,
metadata, optimizer, links, and constructor configuration reviewed here.

## Robinhood testnet and V4 evidence

All three committed JSON manifests parsed successfully. The checked-in verifier
first passed with only the funding decision skipped, then passed separately in
strict mode. The strict run observed head `115884813`, block hash
`0xb1fdcbcb663691f056068ad2cffb61fbcdffec7617e841dd29925df582cd6948`,
and timestamp `2026-09-09T00:01:14Z`.

Strict mode reconfirmed every recorded runtime size/hash and critical state for:

- PoolManager, PositionManager, Quoter, StateView, UniversalRouter, and Permit2;
- PoolManager owner `0x9701fb0aDe1E269c8f64Ec0C7b3cfADB31A13A52`, its zero-byte
  runtime, and zero protocol-fee controller;
- PositionManager's exact PoolManager wiring;
- the Stock registry/beacon, its implementation, global pause state, and the
  deployer's block status;
- all five Stock Token proxies, symbols/names, 18 decimals, pause flags,
  multipliers, and registry link; and
- WETH and faucet-style test USDC identity.

The strict funding result was:

| Account state | Observed value |
|---|---:|
| Deployer pending nonce | `0` |
| Native balance | `10000000000000000` wei (`0.01` ETH) |
| AMZN balance | `5000000000000000000` raw units (`5`) |
| AMD balance | `5000000000000000000` raw units (`5`) |
| TSLA balance | `5000000000000000000` raw units (`5`) |
| PLTR balance | `5000000000000000000` raw units (`5`) |
| NFLX balance | `5000000000000000000` raw units (`5`) |

Independent `cast` calls, separate from the verifier, reproduced chain ID
`46630`, PoolManager code hash/owner/zero fee controller, PositionManager code
hash, and PositionManager-to-PoolManager wiring.

Current primary-source comparison was also repeated:

- Robinhood documents testnet chain ID `46630`, the testnet explorer, and the
  rate-limited public RPC used for this review;
- Robinhood describes Stock Tokens on the public testnet as testnet-only assets
  for integration testing; and
- Uniswap's official Robinhood mainnet (`4663`) deployment record lists the same
  PoolManager, PositionManager, V4 Quoter, StateView, UniversalRouter, and
  Permit2 addresses.

There is still no official Uniswap `deployments/46630.md`. The EqualFiLabs
chain-`46630` manifest remains a useful source-pinned reproducibility lead, but
it is not upgraded here into Uniswap authority or endorsement.

## Findings and accepted residual risks

1. **External V4 control — accepted only for valueless testnet.** The candidate
   PoolManager owner is an EOA whose real-world controller is not established.
   The owner can change control state after a verifier pass. Recheck immediately
   before deployment and market operations, fail closed on drift, and label the
   stack non-official in the UI.
2. **Upgradeable Stock Tokens — accepted only for valueless testnet.** The five
   assets share an externally controlled registry/beacon and implementation.
   Pause, block, multiplier, implementation, or administrative behavior can
   change independently of stonkHedge.
3. **Tight bytecode margin — accepted for this exact build.** `PanopticPoolV2`
   has 301 bytes of raw headroom. Any code/config/toolchain change invalidates
   this measurement and requires a fresh exact size gate.
4. **Simulation-report hash hardening — low severity, follow-up required.** The
   simulator records each plan-supplied `initcodeHash` without independently
   recomputing it. It still executes the embedded initcode and binds the report
   to a SHA-256 hash of the complete plan, so the reviewed exact-plan simulation
   remains meaningful. Recompute and compare each initcode hash before relying
   on this field in a production-grade operator workflow.
5. **Public RPC reliability — operational warning.** Robinhood labels the public
   endpoint rate-limited and not recommended for production. The two verifier
   runs took approximately 192 and 126 seconds. Use a reviewed provider endpoint
   for immediate deployment operations and retain the public endpoint as an
   independent comparison.

## Next controlled step

Offline artifact regeneration may now start from a fresh pending nonce read.
Regenerate every predicted address, direct config, release bundle, and plan;
then rerun the exact size gate and fresh Anvil-fork simulation. Do not reuse the
historical nonce-0 hashes merely because the live nonce is currently still zero.

Before the first public transaction:

1. create a separately controlled, password-protected test-actor keystore
   without printing or storing an unencrypted key;
2. fund that public address through Robinhood's faucet and verify its ETH and
   Stock Token balances;
3. repeat the strict infrastructure/deployer verifier;
4. review the regenerated artifact hashes and simulation report; and
5. run a separate broadcast checklist that sends one transaction at a time and
   stops on the first failed or mismatched receipt.

The invited contributor's eventual review should still be retained as
defence-in-depth. Any rejection or material mismatch reopens this decision and
returns both regeneration and broadcast to `NO_GO`.

## Sources

- Robinhood network configuration: <https://docs.robinhood.com/chain/connecting/>
- Robinhood public testnet announcement: <https://robinhood.com/us/en/newsroom/robinhood-chain-launches-public-testnet/>
- Uniswap official Robinhood mainnet deployment record: <https://github.com/Uniswap/contracts/blob/main/deployments/4663.md>
- Non-authoritative EqualFiLabs reproducibility lead: <https://github.com/EqualFiLabs/statics/blob/master/deployments/robinhood-chain-testnet-46630.json>
