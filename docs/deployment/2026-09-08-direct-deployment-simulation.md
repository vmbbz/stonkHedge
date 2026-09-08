# Robinhood testnet direct-deployment simulation — 2026-09-08

## Outcome

The exact 16-contract Panoptic V4 deployment sequence for public deployer
`0xCa60c8eF6934f8a97c6a503C4e3a46e87F5b08bD` passed on a fresh Anvil fork of
Robinhood Chain testnet. All CREATE addresses matched, all receipts succeeded,
all deployed runtimes were non-empty, final nonce was `16`, and 11
post-deployment constructor/wiring assertions passed.

No private key was read, no deployer transaction was signed or broadcast, and no
stonkHedge contract exists on the public testnet. The official faucet later
funded the deployer without consuming its nonce, as documented in
[`2026-09-08-faucet-and-mainnet-safe-readiness.md`](./2026-09-08-faucet-and-mainnet-safe-readiness.md).
Public broadcast remains blocked on a second actor, independent core and
candidate-infrastructure review, and a fresh exact-artifact review.

The sanitized machine-readable evidence is
[`../../manifests/deployments/robinhood-testnet-direct-preflight-2026-09-08.json`](../../manifests/deployments/robinhood-testnet-direct-preflight-2026-09-08.json).

## Why direct CREATE is required

The upstream Panoptic release process uses a Safe and the canonical sub-zero
CREATE3 deployer at `0x000000000000b361194cfe6312EE3210d53C15AA`. That address
has no code on chain `46630`. Reusing upstream salts or Safe batches would
therefore create false address expectations.

Core commit `f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d` instead:

- derives ordinary CREATE addresses from the public sender and live nonce;
- rebuilds metadata pointers, linked libraries, and constructor arguments for
  those addresses through the inherited release builder;
- emits a validated, ordered, zero-value transaction plan without accepting an
  RPC URL, key, or broadcast flag; and
- simulates only against an HTTP loopback Anvil client, refusing external RPCs
  and non-Anvil clients before state mutation.

The implementation is pushed at
[`vmbbz/panoptic-v2-core@feat/robinhood-testnet-direct-deployment`](https://github.com/vmbbz/panoptic-v2-core/tree/feat/robinhood-testnet-direct-deployment).

## Exact evidence

| Gate | Result |
|---|---|
| Direct-deployment unit tests | 11 passed, 0 failed |
| Exact V4 release build | 7 metadata + 9 logic contracts built |
| EIP-170/EIP-3860 size gate | Passed with required 256-byte logic-runtime margin |
| Exact plan | 16 CREATE transactions, nonce 0–15 |
| Plan SHA-256 | `b1e354db53ecfd89042492a7ab18efb4dba909c31e8af67d5cff6de41579dd42` |
| Fresh Anvil-fork deployment | 16 successful receipts; final nonce 16 |
| Largest deployment | `PanopticFactoryV4`, 10,749,128 gas |
| Post-deployment wiring | 11 passed, 0 failed |

The tightest logic runtime is `PanopticPoolV2` at 24,275 bytes, leaving 301
bytes under EIP-170. The largest logic initcode is `PanopticFactoryV4` at 40,654
bytes, leaving 8,498 bytes under EIP-3860. Metadata data contract 5 deploys to a
24,482-byte runtime, 94 bytes below EIP-170; it is deterministic static data,
not executable protocol logic, and its exact deployment passed on the target
chain fork.

The final wiring assertions verified:

- guardian admin and treasurer equal the explicit temporary testnet role;
- BuilderFactory owner equals PanopticGuardian;
- RiskEngine points to the expected guardian and BuilderFactory;
- both RiskEngine cross buffers are `10,000,000` and `vegoid()` is `8`;
- PanopticPoolV2 points to the planned V4 SFPM; and
- the factory exposes the expected NFT name and symbol.

## Problems found and fixed during proof

Three failures were resolved rather than hidden:

1. Windows rejected large initcode passed to `cast keccak` on the command line.
   The planner now streams it through standard input and has a 40,000-byte
   regression test.
2. An immediate receipt read returned `null` while Anvil was mining. The guarded
   simulator now polls with a bound and distinguishes pending from revert.
3. Anvil inherited an impractically large automatic CREATE gas value. The
   runbook starts the fork with an explicit 30,000,000 block limit and sends each
   transaction with `0xff0000` gas, below 2^24. The simulator rejects a supplied
   gas limit at or above 2^24.

## Fresh public preflight

At public block `115718190`, hash
`0xbfdbef350a9ac84b34817197eec0f0d2535beb895b97e406d735760769402fff`,
timestamp `2026-09-08T18:01:02Z`:

- RPC chain ID was `46630`;
- deployer pending nonce was `0` and native balance was `0`;
- canonical CREATE3 deployer runtime was empty; and
- all 16 predicted direct-CREATE addresses had empty code.

This observation expires as soon as public state changes. Repeat it immediately
before any authorized broadcast.

## Stop/go boundary

The next public action is not “run deploy.” It is:

1. friend follows the [independent review gate](../review/2026-09-08-core-f4abdd7-and-v4-candidate.md) and separately accepts core `f4abdd7...` and the non-official candidate V4 stack;
2. a distinct second actor obtains bounded faucet ETH and Stock Tokens; the deployer funding leg is complete;
3. strict `scripts/verify-robinhood-testnet.ps1` passes;
4. artifacts are regenerated from the then-current pending nonce;
5. the exact regenerated plan passes a fresh fork simulation; and
6. a separately reviewed operator sends one transaction, waits for and verifies
   its receipt/runtime, then advances to the next.

A mined failed CREATE consumes its nonce. Stop immediately after any failure;
never skip ahead through the plan.
