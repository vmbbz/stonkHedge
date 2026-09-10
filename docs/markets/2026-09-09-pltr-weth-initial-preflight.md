# PLTR/WETH initial market preflight

| Field | Value |
|---|---|
| Status | Read-only initial preflight passed and exact-head fork rehearsal completed; exposure acceptance remains required |
| Chain | Robinhood Chain testnet `46630` |
| Pinned block | `116510322` |
| Block hash | `0x7e2f9ad36e849939324d92c992bddc8a8e5dd96071047044cc95602994812e74` |
| Block timestamp | `2026-09-09T23:06:06Z` |
| Shared qualification | `79/79` passed |
| Plan-specific pre-state | `17/17` passed |
| Public execution | Not ready and not authorized |

## What this checkpoint proves

The strict verifier consumed the committed unsigned PLTR/WETH plan, regenerated
it from its hash-bound inputs, required full equality across all twelve
transaction intents, ran the complete market
qualifier at one pinned canonical head, and then checked the exact starting
state required by transaction zero. The resulting
[machine-readable evidence](../../manifests/markets/robinhood-testnet-pltr-weth-initial-preflight-2026-09-09.json)
is bound to the verifier, plan, qualifier, chain, deployment, and actor files by
SHA-256.

The pass proves that, at the pinned block:

- chain ID, V4 dependencies, shared Panoptic contracts, Stock infrastructure,
  and all five faucet assets still matched the recorded identities;
- the exact PLTR/WETH PoolKey remained eligible, uninitialized, and had zero
  active liquidity;
- the Panoptic factory mapping remained zero;
- the second actor was unblocked, had confirmed and pending nonce `0`, and held
  enough faucet assets for the proposed caps and reserves;
- the actor started with zero WETH and zero PLTR/WETH allowances at both the
  ERC-20-to-Permit2 and Permit2-to-PositionManager layers;
- PositionManager `nextTokenId()` was readable and returned `3740`; and
- the predicted PanopticPool and both CollateralTracker addresses had no code.

This is a pre-state snapshot, not a state transition. Nothing was wrapped or
approved, the V4 pool was not initialized, no liquidity NFT was minted, and no
Panoptic market was registered.

## Fail-closed design

The verifier has no private-key, keystore, signing, serialization, or broadcast
path. Its RPC allowlist contains only chain identity, block, code, balance,
nonce, and `eth_call` reads. Any malformed artifact, source-hash drift, RPC
failure, wrong chain, changed runtime, changed PoolKey, nonzero market state,
nonce gap, unexpected allowance, insufficient reserve, or occupied predicted
address changes the result to `BLOCKED`.

Run it from the product repository with:

```powershell
python -B .\scripts\verify_robinhood_market_plan.py `
  --transport cast `
  --output .\manifests\markets\robinhood-testnet-pltr-weth-initial-preflight-2026-09-09.json
```

The evidence used here records:

| Artifact | SHA-256 |
|---|---|
| Offline plan file | `889eb501f7b20c4ae2f352ce878c76c4f18bbf1b2438027c5c9a7b876e006417` |
| Strict verifier | `30200c330a7f42209073cbbabe481cf6f8321c1745813b8689c8280f4a65157d` |
| Complete qualifier | `71a1f9d995a4c11efd98cfb4fcc58af7a4eca3837b51276f3e9f0d10b475e228` |
| Preflight evidence file | `d9d06889b2e4c73d0c741a6fdc4585b1880f1522c2b0f3a43640f0802a14c098` |

The evidence-file hash is an external review checksum; it is not embedded in
the file itself.

## Why this is not an execution plan

The committed plan intentionally contains null nonces and historical
rehearsal deadlines. Every authorization flag is false. The exact exposure
proposal—wrapping `0.004 ETH`, permitting at most `2 PLTR` and `0.002 WETH`,
minting `138450781996976174` liquidity between ticks `-81120` and `-57060`,
and using Panoptic factory salt `0`—has not been accepted for public execution.

At the time of this preflight, the blockers were independent of its green
result:

1. no accepted exact exposure;
2. no fresh execution timestamps or nonce-bound execution plan;
3. no market-specific one-step operator; and
4. no hash-bound signing or broadcast authorization.

Later on 2026-09-10, the owner accepted the exact exposure for execution
planning only, and a fresh nonce/deadline-bound candidate plus one-step
operator replay completed. Public authorization remains absent. See the
[execution-candidate/operator record](./2026-09-10-pltr-weth-execution-candidate-and-operator.md).

## Fork-rehearsal follow-on

The committed calldata cannot simply be replayed at a current timestamp because
its historical deadlines are meant to fail closed. A separate fork transformer
therefore refreshed only the local Permit2 expirations and PositionManager
deadline while preserving the exact accepted mechanism and all false public
authorization flags.

That exact-head rehearsal has now passed all twelve positive transitions and
four snapshot-isolated negative cases. Read the
[full fork-rehearsal record](./2026-09-10-pltr-weth-fork-rehearsal.md). Its
Anvil state was discarded, so this preflight remains a public pre-state
snapshot rather than evidence of a public pool. The later planning acceptance
and operator rehearsal do not retroactively authorize this historical plan or
any public transaction.

## Memory aid: READ

- **R — Read only:** preflight observes state; it does not create state.
- **E — Exact head:** every dependent fact belongs to one block and hash.
- **A — Authorization absent:** green checks do not grant signing permission.
- **D — Drift blocks:** changed code, balances, PoolKey, nonce, or occupancy stops the lane.
