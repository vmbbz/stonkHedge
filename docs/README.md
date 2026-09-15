# StonkHedge documentation map

This directory is the source-of-truth documentation set for the StonkHedge
testnet project. The Markdown is intentionally organized so it can later move
into Docusaurus without rewriting the technical content. Docusaurus is a
publishing layer, not a substitute for accurate manifests and runbooks.

## Current milestone

The 16-contract shared Panoptic V4 stack is deployed and reconciled on
Robinhood Chain testnet. PLTR/WETH public genesis completed four bounded setup
transactions and then stopped before pool initialization when the original
mint deadline became too short. A nonce-`4..12` continuation passed a fresh
nine-call exact-head replay and received a separate hash-bound authorization.
All nine continuation calls are now canonical: they initialized the PoolKey,
minted bounded V4 liquidity NFT `3903`, zeroed both allowance layers, and
deployed and registered the predicted PanopticPool and two CollateralTrackers.
Public genesis is complete and its authorization is closed. A new unsigned
three-account lifecycle proposal has since passed all `25/25` ordered calls on an
exact loopback fork, including collateral, matched short/long positions,
premium observation, buyer-first close, and allowance cleanup. This was not a
public execution: four required transaction-order reverts also pass. The next
verifier now fails closed on runtime/wiring drift, issuer controls, stale
balances, elevated allowances, and swap-output shortfalls, and a separate
offline withdrawal preparer binds fresh post-close `maxWithdraw` values.
The dedicated third unprivileged buyer is now funded, and the fresh exact-head
replay also passed `4/4` bounded state-derived withdrawals while keeping every
residual below `2e12` raw units. A new public preflight then proved both actor
states unchanged at block `120109926`. The dual-sender execution candidate
binds writer nonces `13..30`, buyer nonces `0..6`, short-lived deadlines, exact
calldata, and both-account nonce vectors. Its one-step operator passed `25/25`
calls on the exact-head fork, including receipt/state reconciliation and
premium movement. Independent review and a separate hash-bound authorization
still remain. Public swaps, collateral, options, withdrawals, and the
application are not live yet.

Start with:

1. [`progress/2026-09-15-lifecycle-execution-preparation.md`](./progress/2026-09-15-lifecycle-execution-preparation.md)
   for the current dual-sender nonce/deadline candidate, one-step operator,
   25-call exact-fork replay, and authorization boundary;
2. [`progress/2026-09-14-three-account-lifecycle-rehearsal.md`](./progress/2026-09-14-three-account-lifecycle-rehearsal.md)
   for the three-account lifecycle, withdrawal, failure-analysis, and evidence
   ledger;
3. [`progress/2026-09-11-public-genesis-milestone.md`](./progress/2026-09-11-public-genesis-milestone.md)
   for the complete public achievement, contract and transaction ledgers,
   ordering rationale, communications facts, and next boundary;
4. [`architecture/robinhood-testnet-system.md`](./architecture/robinhood-testnet-system.md)
   for the system, component, trust-boundary, and evidence overview;
5. [`deployment/2026-09-09-direct-deployment-public-progress.md`](./deployment/2026-09-09-direct-deployment-public-progress.md)
   for the public transaction record; and
6. [`roadmap/2026-09-09-market-genesis.md`](./roadmap/2026-09-09-market-genesis.md)
   for the next gated implementation phase.

For the proposed Solana track, read the
[perpetual-options feasibility and integration study](./research/2026-09-15-solana-perpetual-options-feasibility.md).
It concludes that a Solana-native prototype investigation is technically
plausible and warranted, while end-to-end feasibility remains unproven. It does
not authorize implementation, deployment, asset listing, or real-value access.

The current lifecycle design and exact-fork evidence are in
[`markets/2026-09-11-pltr-weth-two-actor-lifecycle-design.md`](./markets/2026-09-11-pltr-weth-two-actor-lifecycle-design.md).
The follow-on [lifecycle safety and withdrawal boundary](./markets/2026-09-12-lifecycle-safety-and-withdrawal-boundary.md)
records the hard third-account decision, strengthened fail-closed verifier,
state-derived four-call withdrawal design, and fresh-head replay gate.

The first live, read-only market qualification passed at block `116408992`.
Read the [first-market selection record](./markets/2026-09-09-first-market-selection.md)
for the five exact PoolIds and the
[offline PLTR/WETH genesis design](./markets/2026-09-09-pltr-weth-offline-genesis-design.md)
for the accepted planning boundary, synthetic price, proposed exposure,
architecture, transaction sequence, and ZERO memory aid. The subsequent
[strict initial preflight](./markets/2026-09-09-pltr-weth-initial-preflight.md)
passed `79/79` shared checks and `17/17` exact-plan checks at block `116510322`.
The [exact-head fork rehearsal](./markets/2026-09-10-pltr-weth-fork-rehearsal.md)
then passed `12/12` local transitions and `4/4` expected reverts. Its local
state was discarded. The [execution candidate and one-step operator record](./markets/2026-09-10-pltr-weth-execution-candidate-and-operator.md)
   documents the final `12/12` operator replay at canonical block `116968208`,
   including nonce/deadline binding, receipt-derived LP NFT identity, full
   evidence validation, and the original public non-mutation proof. The
   [partial public-genesis and continuation record](./markets/2026-09-10-pltr-weth-public-continuation.md)
   records the safe deadline stop and all nine canonical continuation receipts.
   The [final public-genesis manifest](../manifests/markets/robinhood-testnet-pltr-weth-public-genesis-2026-09-11.json)
   consolidates every public genesis transaction, the registered market graph,
   terminal zero-allowance state, and the still-excluded lifecycle actions.

## Documentation by audience

| Audience | Read first | Then use |
|---|---|---|
| New contributor | Architecture overview and repository `CONTRIBUTING.md` | Baselines, test evidence, and the relevant roadmap checkpoint |
| Protocol reviewer | Core/candidate review record | Runtime-headroom evidence, deployment simulation, and final public manifest |
| Chain operator | Final public progress record | Strict verifier, authorization manifest, and the next-phase runbook |
| Product/SDK developer | Architecture overview | Controllable-token specification and local lifecycle evidence |
| Security/legal reviewer | Architecture trust boundaries | License record, issuer-control findings, open blockers, and decision log in `plan.md` |

## Directory responsibilities

| Directory | Responsibility |
|---|---|
| `architecture/` | Evergreen component, data-flow, ownership, and trust-boundary explanations |
| `baseline/` | Immutable build, test, licensing, and release-size checkpoints |
| `chain/` | External chain, token, and infrastructure qualification |
| `deployment/` | Simulations, approvals, operator design, receipts, and reconciliation |
| `markets/` | Asset selection, exact PoolKeys, price policy, market genesis, and lifecycle evidence |
| `progress/` | Public milestone ledgers, communications facts, and proof-backed build-in-public records |
| `research/` | Time-stamped feasibility, ecosystem, and comparative design studies that do not authorize implementation or deployment |
| `review/` | Human or explicitly labelled owner-reproduced review evidence |
| `roadmap/` | Forward-looking checkpoint plans that do not themselves authorize transactions |
| `specs/` | Behavioral requirements and acceptance matrices |
| `testing/` | Reproduction commands and observed test evidence |

Machine-readable facts belong in `../manifests/`. Narrative documents should
link to those manifests rather than silently duplicating mutable values.

The [build-in-public site architecture](./architecture/build-in-public-site.md)
explains how the visual dashboard imports those manifests, validates editorial
entries, degrades without WebGL, and publishes after a main-branch merge.

## Source-of-truth order

When records disagree, use this order and investigate the drift:

1. canonical on-chain state at an explicitly recorded block;
2. the reconciled public deployment manifest;
3. hash-bound simulation, operator, and authorization artifacts;
4. chain-qualification and test manifests;
5. narrative documentation and `plan.md`;
6. chat transcripts or screenshots.

A receipt proves only that a transaction executed. Deployment acceptance also
requires expected sender/nonce/input, created address, runtime identity,
constructor wiring, and post-state.

## Future Docusaurus information architecture

Do not scaffold Docusaurus during the market-deployment work. After deployment
and acceptance documents stabilize, migrate this source material into:

```text
docs site
├── start-here
│   ├── project status
│   ├── testnet quickstart
│   └── limitations and terminology
├── concepts
│   ├── Stock Tokens and issuer controls
│   ├── Uniswap V4 PoolKey
│   ├── Panoptic perpetual options
│   └── collateral, premium, and solvency
├── architecture
│   ├── system overview
│   ├── contracts and data flow
│   ├── trust boundaries
│   └── repository topology
├── developers
│   ├── local environment
│   ├── SDK adapters and golden vectors
│   ├── tests and fork simulation
│   └── contributing
├── operators
│   ├── chain manifests
│   ├── deployment and verification
│   ├── monitoring and safe mode
│   └── incident and unwind runbooks
├── security-and-risk
│   ├── threat model
│   ├── issuer and oracle failure modes
│   ├── audit status
│   └── licensing and legal boundaries
└── reference
    ├── addresses and releases
    ├── transaction history
    ├── decisions
    └── glossary
```

The eventual site should generate address and transaction tables from validated
manifests. Hand-copied deployment facts should fail CI if they drift.

## Publishing gate

Build the documentation site only after all intended testnet deployment rounds
are complete and the following are true:

- public manifests and contract addresses are stable;
- the first market has a clean-checkout reproduction and first-user run;
- navigation and terminology have been reviewed;
- secret scanning and link checking pass;
- testnet/mainnet and deployed/planned labels are unambiguous; and
- automated manifest-to-reference generation has an owner.
