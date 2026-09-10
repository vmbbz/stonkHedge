# Robinhood testnet market-genesis plan

| Field | Value |
|---|---|
| Status | Continuation indexes `0–3` canonical; exact PoolKey initialized and bounded liquidity NFT `3903` minted; cleanup and Panoptic registration remain |
| Authorization | Exact continuation indexes `0..8` only, one transaction per invocation; swaps, collateral, options, every other market, and mainnet remain excluded |
| Target checkpoint | `robinhood-testnet-sandbox-0` |
| Estimated remaining focused engineering time | 3–6 hours to public genesis, excluding faucet, RPC, or review delays |

## 1. Objective

Convert the verified shared Panoptic deployment into exactly one functioning,
valueless Robinhood testnet market:

```text
one qualified Stock Token
        + testnet WETH
        + exact no-hook Uniswap V4 PoolKey
        + bounded two-sided liquidity
        + deployed PanopticPool and two CollateralTrackers
        + two-actor collateral and lifecycle evidence
```

This phase completes Hour 24 and Checkpoint C in `plan.md`. It does not add
mainnet support, custom hooks, vaults, multiple markets, autonomous trading, or
real-value claims.

### Current progress: four setup transactions public, continuation proven locally

At block `116408992`, the repository qualifier passed `79/79` checks across
chain identity, external and Panoptic runtimes, Stock Token controls, both
accounts, five candidate PoolIds, and factory mappings. All five candidates are
eligible. PLTR/WETH was recommended because PLTR is the only eligible Stock
Token that sorts as `currency0` against WETH. The owner has now accepted that
exact PoolKey, a synthetic mechanism-test price class, and the second actor's
roles for offline planning only. The repository has generated the unsigned
design and its fresh strict initial preflight passed at block `116510322`: the full
qualification passed `79/79` and all `17/17` plan-specific starting-state
checks passed. A loopback-only fork of that exact head then passed all twelve
genesis transitions and four snapshot-isolated negative cases. The Anvil state
was discarded. The owner subsequently accepted the exact synthetic price,
range, liquidity, wrap, token caps, salt, and second-actor roles for execution
planning only. A final canonical snapshot at block `116968208` passed `79/79`
plus `17/17`; the offline generator bound nonce `0`, a shared PositionManager
counter floor of `3893`, and new deadlines into a twelve-transaction candidate.
The hardened one-step operator then passed all `12/12` ordered invocations on
the exact fork. The actual LP NFT ID is derived from the mint receipt and must
be supplied for every later step; it is never assumed to be reserved by the
shared counter.

The actor subsequently executed original indexes `0–3`: wrap `0.004` test ETH,
approve exactly `2 PLTR` and `0.002 WETH` to Permit2 at the ERC-20 layer, and
approve exactly `2 PLTR` from Permit2 to PositionManager. Each receipt was
reconciled before proceeding. Execution then stopped before original index `4`
because the one-hour mint deadline had become operationally unsafe. The actor
is at nonce `4`; the exact pool remains uninitialized, active liquidity and NFT
balance remain zero, and the Panoptic factory mapping remains empty.

A new nine-transaction continuation for nonces `4..12` refreshes PLTR's
time-bound Permit2 permission, completes the remaining intents, and uses a
four-hour liquidity deadline plus six-hour Permit2 expirations. All nine calls
passed exact-checkpoint replay and end with zero allowances, the bounded LP
NFT, and the registered Panoptic market. Its separately recorded authorization
binds the exact plan, operator, replay report, actor, maximum index, clock
policy, and exclusions. Public continuation indexes `0–3` then refreshed both
bounded Permit2 permissions, initialized the exact PoolKey, and minted
liquidity NFT `3903`. The next action is the four-step allowance cleanup; the
Panoptic market remains unregistered. See the
[selection record](../markets/2026-09-09-first-market-selection.md),
[offline genesis design](../markets/2026-09-09-pltr-weth-offline-genesis-design.md),
the [initial preflight record](../markets/2026-09-09-pltr-weth-initial-preflight.md),
the [fork-rehearsal record](../markets/2026-09-10-pltr-weth-fork-rehearsal.md),
the [execution-candidate/operator record](../markets/2026-09-10-pltr-weth-execution-candidate-and-operator.md),
the [partial public-genesis and continuation record](../markets/2026-09-10-pltr-weth-public-continuation.md),
and [machine-readable continuation candidate](../../manifests/markets/robinhood-testnet-pltr-weth-continuation-candidate-2026-09-10.json).

## 2. Entry gates already complete

- shared Panoptic V4 deployment: 16 of 16 contracts reconciled;
- exact deployed runtime identities: 16 of 16 pass;
- constructor/wiring assertions: 11 of 11 pass;
- strict chain, V4 dependency, Stock Token, WETH, and account verifier: pass;
- two encrypted testnet keystores exist outside the repository;
- both public accounts received bounded faucet ETH and all five Stock Tokens;
- local pool/liquidity/market/position lifecycle: pass at `cfaf42c...`;
- deterministic twelve-step unsigned market-genesis plan: complete;
- fresh public preflight: `79/79` shared plus `17/17` exact-plan checks;
- exact-head genesis rehearsal: `12/12` transitions plus `4/4` required
  reverts;
- exact owner exposure acceptance for execution planning only;
- fresh nonce/deadline-bound execution candidate: complete; and
- finalized one-step operator replay: `12/12` ordered calls with full state
  reconciliation and no public send;
- original public indexes `0–3`: canonical and independently reconciled;
- frozen partial state: actor nonce `4`, bounded setup balances/permissions,
  uninitialized pool, zero liquidity/NFT balance, and empty factory mapping;
- nonce-`4..12` continuation plan: complete; and
- continuation operator replay: `9/9` ordered calls from the exact partial
  state, with full cleanup and no continuation public send; and
- continuation authorization: exact hashes, actor, indexes `0..8`, four-hour
  liquidity deadline, six-hour Permit2 expiry, and unchanged exclusions bound;
- continuation indexes `0–3`: canonical public receipts, exact initialized
  pool state, active liquidity, and receipt-derived NFT `3903`; and
- current stop: public nonce `8`, residual allowances bounded exactly as
  planned, factory mapping still empty.

## 3. Decisions and calculations for the transaction plan

### 3.1 Select one Stock Token by evidence

Do not choose by ticker popularity. Re-read all five candidates and select one
only after recording:

- proxy, registry/beacon, and implementation identity;
- symbol, decimals, pause/block status, multiplier, and scheduled update;
- deployer and test-actor balances;
- exact token ordering against WETH;
- whether the proposed PoolKey is currently uninitialized; and
- any available reference-price source and its limitations.

The result should be a small machine-readable asset-selection manifest. Every
other Stock Token remains out of scope for Checkpoint C.

Current result: all five passed; the owner accepted the exact PLTR/WETH
fee-`3000`, spacing-`60`, no-hook candidate for offline planning only.

### 3.2 Freeze the complete PoolKey

Record and hash:

- `currency0` and `currency1` in ascending address order;
- fee;
- tick spacing;
- `hooks = address(0)`;
- derived PoolId; and
- proof that this exact PoolId is uninitialized immediately before execution.

The local `3,000` fee and `60` tick spacing are the tested starting candidate.
They are not public defaults until the asset-selection review accepts them.

### 3.3 Define a test-only initial price policy

Do not copy the local 1:1 `sqrtPriceX96 = 2^96` silently. The chosen value must
state whether it is:

- a deliberately synthetic mechanism-test price;
- derived from a qualified test feed; or
- derived from a timestamped external reference solely for valueless testing.

Record token orientation, decimal normalization, human-readable price in both
directions, tick, `sqrtPriceX96`, rounding method, source timestamp, and maximum
accepted deviation. The UI must not present a synthetic initialization price as
a live equity quote.

### 3.4 Define bounded liquidity and account roles

The balances are faucet-sized. Specify exact maximum amounts before any
approval:

- ETH to wrap;
- WETH and Stock Token to place into V4;
- slippage and deadline limits;
- amount reserved for collateral and swaps;
- amount reserved for gas; and
- which account receives the factory NFT and determines the Panoptic market
  CREATE3 salt.

The second actor should be the default LP/user. Using the deployer for market
deployment or a second trading role requires an explicit rationale because it
also holds guardian and treasurer authority.

## 4. Tooling built before broadcasting

All three genesis-tooling items below are now implemented and tested. They
remain documented as requirements because any replacement must preserve these
boundaries.

### 4.1 Offline market-plan generator

Add a product-repository tool that accepts reviewed public inputs and emits an
unsigned, deterministic plan. It must have no private-key, keystore-password,
signing, or broadcast capability.

The output must bind:

- chain ID and RPC identity;
- selected Stock Token, WETH, candidate V4 contracts, PanopticFactoryV4,
  SFPM, RiskEngine, and account addresses;
- PoolKey, PoolId, initial price, ticks, salt, and predicted market/tracker
  addresses where derivable;
- every transaction target, value, calldata hash, allowance, amount, deadline,
  and expected post-state;
- source, manifest, and tool hashes; and
- explicit maximum native/token exposure.

### 4.2 Read-only market verifier

Before signing, and again after every state transition, verify:

- chain ID and latest block identity;
- all existing external and Panoptic runtime hashes;
- Stock Token health and account balances;
- exact PoolKey/PoolId initialization state;
- current allowances and token ordering;
- PoolManager slot/tick/liquidity state;
- factory mapping and expected clone emptiness before market registration;
- post-registration SFPM pool ID, PanopticPool wiring, both tracker assets, and
  RiskEngine; and
- post-deposit shares/assets, open positions, premium, solvency, and close
  state.

RPC failure, stale state, or an undecodable response is `BLOCKED`, never pass.

### 4.3 Separate one-step operator

The market-specific operator is complete and passed twelve ordered invocations
on an exact fork. It deliberately does not reuse the CREATE transaction model:
market actions have recipients, values, allowances, deadlines, and richer
postconditions.

The operator must:

- bind a reviewed market-plan hash and authorization hash;
- accept one explicitly selected transaction only;
- show account, target, value, token maximums, and decoded intent before the
  password prompt;
- run the strict verifier and step-specific preflight immediately before
  signing;
- reject unlimited approval unless the reviewed plan explicitly justifies it;
- reconcile the receipt and exact post-state; and
- stop before the next transaction.

## 5. Fork rehearsal

### 5.1 Completed genesis subset

The exact-head rehearsal at block `116510322` completed the state-creation
subset needed before the owner accepted the exact exposure for execution
planning. The final operator rehearsal at block `116968208` repeated the full
positive sequence through the actual one-step interface:

1. bounded ETH wrapping;
2. exact two-layer PLTR/WETH permissions;
3. exact PoolKey initialization;
4. bounded two-sided liquidity and actor-owned NFT;
5. complete permission revocation;
6. deterministic Panoptic market and tracker deployment; and
7. event, mapping, runtime, ownership, immutable-wiring, delta, and SFPM
   reconciliation.

Duplicate initialization, expired liquidity, occupied CREATE3 proxy, and
duplicate Panoptic registration all reverted inside restored snapshots. The
[full evidence record](../markets/2026-09-10-pltr-weth-fork-rehearsal.md)
explains the loopback-only architecture and why no public state changed.

### 5.2 Broader lifecycle rehearsal still required

Fork a fresh Robinhood testnet head into local Anvil and impersonate only the
exact planned public accounts. Rehearse the final transaction order, including
all approvals and deadlines.

At minimum the rehearsal must cover:

1. wrap only the bounded ETH amount;
2. grant the exact token/Permit2/PositionManager permissions required by the
   chosen liquidity path;
3. initialize the exact no-hook PoolKey;
4. add bounded two-sided liquidity;
5. execute a small swap in both directions and reconcile deltas;
6. call `PanopticFactoryV4.deployNewPool` with the reviewed caller and salt;
7. reconcile `PoolDeployed`, factory mapping, SFPM pool ID, PanopticPool, and
   both CollateralTrackers;
8. approve and deposit tiny collateral from two distinct accounts;
9. open the minimum matched writer/buyer legs supported by the public balance;
10. observe premium movement after controlled swaps or time progression;
11. close positions and withdraw recoverable collateral; and
12. verify all balances and residuals against a scale-appropriate public-test
    budget.

Across genesis and the later lifecycle, the fork suite must exercise at least
these negative paths:

- wrong chain, PoolKey, token order, hook, fee, or tick spacing;
- already initialized pool or occupied predicted market address;
- stale/paused/blocked/multiplier-changed Stock Token;
- allowance above the plan maximum;
- expired deadline or excess slippage;
- incorrect sender or salt;
- strict verifier or runtime drift; and
- receipt success with unexpected event or post-state.

## 6. Proposed execution gates

```mermaid
flowchart TD
    A[Fresh asset and infrastructure qualification] --> B{One Stock/WETH design accepted?}
    B -- no --> X[BLOCKED: no transaction]
    B -- yes --> C[Generate unsigned deterministic plan]
    C --> D[Independent or explicitly labelled owner reproduction]
    D --> E[Exact-head genesis fork rehearsal: PASS]
    E --> F{Exact exposure accepted?}
    F -- no --> X
    F -- yes --> G[Fresh execution plan and one-step operator]
    G --> H[Fresh verify and fork replay]
    H --> I[Separate explicit authorization]
    I --> J[Execute one transaction]
    J --> K[Reconcile receipt and post-state]
    K --> L{More authorized steps?}
    L -- yes --> J
    L -- no --> M[Full market reconciliation]
    M --> N[Commit public genesis evidence]
```

The previous authorization ended at shared-deployment transaction index `15`.
It explicitly excluded every action in this plan. No wording in this roadmap is
authorization to broadcast.

Current position in the diagram: the original execution loop completed four
transactions and stopped safely before the deadline became unsafe. The
partial-state continuation then completed indexes `0–3`; the exact PoolKey and
liquidity NFT `3903` are public. The next action is only continuation index `4`
to begin allowance cleanup, followed by full reconciliation and another stop.

## 7. Checkpoint C acceptance

Checkpoint C passes only when the committed public manifest contains:

- exact selected asset and full PoolKey;
- PoolId and initial-price derivation;
- all transaction hashes and canonical block identities;
- liquidity position identity, ranges, amounts, and token deltas;
- bidirectional swap evidence;
- `PoolDeployed` event and factory mapping;
- PanopticPool, both trackers, RiskEngine, SFPM, and PoolManager wiring;
- two-actor deposits and position IDs;
- premium, solvency, close, withdrawal, and residual evidence;
- strict-verifier output and a fresh-machine read-only replay;
- explicit failures/skips; and
- a statement that assets are valueless testnet assets and the stack is not
  audited, issuer-endorsed, or mainnet-ready.

Only then may the repository tag `robinhood-testnet-sandbox-0`.

## 8. Suggested focused-hour order

Hours `0–5` are evidenced by the current artifacts. The project is at the
review/final-regeneration boundary; elapsed clock time may be dominated by the
testnet RPC's short state-retention window rather than implementation work.

| Hours | Work | Exit gate |
|---:|---|---|
| 0–1 | Fresh asset, balance, PoolKey, and infrastructure qualification | One reviewed design or explicit block |
| 1–3 | Offline planner plus red/green unit tests | Deterministic unsigned plan and decoded intent |
| 3–5 | Read-only verifier and exact-head fork lifecycle | Positive and negative rehearsal evidence |
| 5–6 | Review, artifact freeze, and separate authorization | Exact hashes and maximum exposure approved |
| 6–8 | One-step-at-a-time public initialization, liquidity, and market registration | Every receipt and post-state reconciled |
| 8–10 | Two-actor lifecycle, clean replay, docs, and checkpoint commit | Checkpoint C pass or honest blocked report |

## 9. Work immediately after Checkpoint C

Do not expand to a second ticker. Build the first-user path:

1. product-local adapters around exact `@panoptic-eng/sdk@1.0.49`;
2. Solidity-to-TypeScript golden vectors for PoolKey and TokenId encoding;
3. read-only market state, collateral, premium, and solvency views;
4. simulation-first protective-put transaction construction;
5. wallet rejection/pending/replacement/failure UX;
6. independent Stock Token/V4/Panoptic health monitoring; and
7. a clean-wallet first-user acceptance run.

Docusaurus should wait until the intended deployment rounds and acceptance
evidence are complete. The Markdown source should stabilize first; the site can
then present it without obscuring what is live versus planned.
