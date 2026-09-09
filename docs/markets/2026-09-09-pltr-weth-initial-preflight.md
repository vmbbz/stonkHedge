# PLTR/WETH initial market preflight

| Field | Value |
|---|---|
| Status | Read-only initial preflight passed; local fork rehearsal and exposure acceptance remain required |
| Chain | Robinhood Chain testnet `46630` |
| Pinned block | `116478616` |
| Block hash | `0xbc1efcf5cf57918e156a5bd39a44bc9b3465141d362c2bf67309750298ed2ca4` |
| Block timestamp | `2026-09-09T21:55:53Z` |
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
- PositionManager `nextTokenId()` was readable and returned `3732`; and
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
| Preflight evidence file | `8eefef3bf19407dfa3b2fef38857dc0a41395fea869bb500abd6108168c0210f` |

The evidence-file hash is an external review checksum; it is not embedded in
the file itself.

## Why this is not an execution plan

The committed plan intentionally contains null nonces and historical
rehearsal deadlines. Every authorization flag is false. The exact exposure
proposal—wrapping `0.004 ETH`, permitting at most `2 PLTR` and `0.002 WETH`,
minting `138450781996976174` liquidity between ticks `-81120` and `-57060`,
and using Panoptic factory salt `0`—has not been accepted for public execution.

The current blockers are therefore independent of the green preflight:

1. no accepted exact exposure;
2. no successful exact-head positive and negative fork rehearsal;
3. no fresh execution timestamps or nonce-bound execution plan;
4. no market-specific one-step operator; and
5. no hash-bound signing or broadcast authorization.

## Fork-rehearsal boundary

The first attempt to launch a local Anvil fork at the older accepted block
`116408992` did not establish a loopback listener, so it produced no rehearsal
evidence and is not counted as a pass. The committed calldata cannot simply be
replayed at a current timestamp because its historical deadlines are meant to
fail closed.

The next safe implementation round is a separate, explicitly fork-only
rehearsal artifact pinned to a fresh head and fresh local rehearsal clock. It
must preserve the accepted PoolKey and proposed exposure, keep every public
authorization false, run only against loopback Anvil, and leave the committed
offline plan unchanged. Only after the positive transition sequence and
negative cases pass should the owner decide whether to accept the exact
exposure for a separately generated public-execution candidate.

## Memory aid: READ

- **R — Read only:** preflight observes state; it does not create state.
- **E — Exact head:** every dependent fact belongs to one block and hash.
- **A — Authorization absent:** green checks do not grant signing permission.
- **D — Drift blocks:** changed code, balances, PoolKey, nonce, or occupancy stops the lane.
