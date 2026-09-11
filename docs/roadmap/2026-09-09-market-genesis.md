# Robinhood testnet market-genesis plan

| Field | Value |
|---|---|
| Status | Public genesis complete; unsigned two-actor lifecycle replay passes `25/25` positive calls plus `4/4` required order/safety reverts; external-state cases, withdrawals, role review, and any public lifecycle remain |
| Authorization | Genesis authorization consumed and closed at continuation index `8`; no swap, collateral, option, other-market, or mainnet transaction is authorized |
| Target checkpoint | `robinhood-testnet-sandbox-0` |
| Estimated remaining focused engineering time | 2–5 hours for external-state cases, withdrawal continuation, fresh execution planning, review, and checkpoint evidence, excluding faucet, RPC, or authorization delays |

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

### Current progress: public genesis complete, lifecycle still gated

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
was at nonce `4`; the exact pool remained uninitialized, active liquidity and
NFT balance remained zero, and the Panoptic factory mapping remained empty.

A new nine-transaction continuation for nonces `4..12` refreshed PLTR's
time-bound Permit2 permission, completed the remaining intents, and used a
four-hour liquidity deadline plus six-hour Permit2 expirations. All nine calls
first passed exact-checkpoint replay. Its separate authorization bound the
exact plan, operator, replay report, actor, maximum index, clock policy, and
exclusions. Public execution then completed all nine calls one at a time:
PoolKey initialization, bounded liquidity NFT `3903`, four explicit allowance
revocations, and deterministic Panoptic market registration.

At final reference block `117093052`, the actor is at nonce `13`; all ERC-20
and Permit2 allowances are zero; LP NFT `3903` still holds liquidity
`138450781996976174`; factory mapping points to PanopticPool
`0x042c0d9c497d62a85b3410f2773cfa748d18e586`; both CollateralTrackers are
deployed and wired; and SFPM market ID `16897827167146926` is nonzero. The
genesis authorization is consumed. See the
[selection record](../markets/2026-09-09-first-market-selection.md),
[offline genesis design](../markets/2026-09-09-pltr-weth-offline-genesis-design.md),
the [initial preflight record](../markets/2026-09-09-pltr-weth-initial-preflight.md),
the [fork-rehearsal record](../markets/2026-09-10-pltr-weth-fork-rehearsal.md),
the [execution-candidate/operator record](../markets/2026-09-10-pltr-weth-execution-candidate-and-operator.md),
the [canonical public-genesis and continuation record](../markets/2026-09-10-pltr-weth-public-continuation.md),
the [machine-readable continuation candidate](../../manifests/markets/robinhood-testnet-pltr-weth-continuation-candidate-2026-09-10.json),
and the [final public-genesis manifest](../../manifests/markets/robinhood-testnet-pltr-weth-public-genesis-2026-09-11.json).

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
- continuation indexes `0–8`: canonical public receipts and exact terminal
  post-state, including zero allowances and receipt-derived NFT `3903`;
- predicted PanopticPool and both CollateralTrackers: deployed with non-empty
  code and exact immutable wiring;
- `PoolDeployed`, factory mapping, factory NFT ownership, RiskEngine, PoolManager,
  and nonzero SFPM market ID: reconciled; and
- current stop: public nonce `13`, genesis authorization consumed, no public
  swap/collateral/option transaction authorized.

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

### 5.2 Broader lifecycle rehearsal is now the next gate

Fork a fresh Robinhood testnet head containing the registered PLTR/WETH market
into local Anvil and impersonate only the exact planned public accounts. Do not
recreate genesis. Requalify it, then rehearse a new bounded lifecycle plan with
its own approvals, deadlines, decoded intents, exposure limits, cleanup, and
terminal state.

At minimum the rehearsal must cover:

1. reverify Stock Token health, the exact PoolKey, LP NFT `3903`, active
   liquidity, factory mapping, clone runtimes, ownership, and wiring;
2. assign distinct writer and buyer/test-user roles and freeze each account's
   balances and maximum exposure;
3. execute a very small swap in both directions and reconcile price, tick,
   token, and PoolManager deltas;
4. grant only the exact collateral approvals required by each tracker;
5. deposit tiny, bounded collateral from two distinct accounts and reconcile
   ERC-4626 shares/assets;
6. open the minimum matched writer/buyer legs supported by those balances;
7. observe premium movement after controlled swaps or time progression;
8. close both positions and withdraw recoverable collateral;
9. revoke every temporary allowance; and
10. verify solvency, position IDs, balances, shares/assets, pool state, and all
    residuals against a scale-appropriate public-test budget.

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

Current position in the diagram: the original execution loop stopped safely,
then the exact partial-state continuation completed all nine authorized calls.
Full market reconciliation and the public-genesis evidence commit are complete.
The next transaction, if any, belongs to a new two-actor lifecycle plan; none
is authorized by the genesis artifacts.

```mermaid
flowchart LR
    A[Requalify registered market] --> B[Freeze two actor roles and caps]
    B --> C[Build unsigned lifecycle plan]
    C --> D[Exact-head fork replay and negative cases]
    D --> E[Review exact hashes and exposure]
    E --> F[Separate lifecycle authorization]
    F --> G[One public transaction]
    G --> H[Wait and reconcile]
    H --> I{More authorized steps?}
    I -- yes --> G
    I -- no --> J[Close, withdraw, revoke, final replay]
    J --> K[Checkpoint C evidence]
```

## 7. Checkpoint C acceptance

Public genesis satisfies the selected-asset, PoolKey, price, transaction,
liquidity, `PoolDeployed`, mapping, ownership, runtime, and wiring portions
below. **Checkpoint C does not yet pass**, because the public two-actor swap,
collateral, option, premium, solvency, close, withdrawal, residual, and
fresh-machine replay evidence remains outstanding.

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

Hours `0–8` are evidenced by the current artifacts. The project is now at the
two-actor lifecycle planning boundary; elapsed clock time may still be
dominated by faucet limits, human authorization, or the testnet RPC's short
state-retention window rather than implementation work.

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
