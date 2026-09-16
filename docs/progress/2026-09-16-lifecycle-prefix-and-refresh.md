# PLTR/WETH public lifecycle prefix and safe clock refresh

| Field | Value |
|---|---|
| Network | Robinhood Chain Testnet (`46630`) |
| Publicly completed prefix | Original indexes `0..4` |
| Value-moving swaps completed | None |
| Refreshed public reference | Block `120177489`, hash `0x5d0103524cad072f2506fa596a186f906ad45801dbb11414ee5ed680eaf6df90` |
| Refreshed execution start | Index `5` |
| Remaining calls | `22` |
| Exact-head replay | `22/22` passed |
| Signing or broadcast under refreshed plan | None |

## 1. Outcome

StonkHedge safely completed the funding and bounded-permission prefix of the
first public PLTR/WETH options lifecycle. The operator verified every receipt
and stopped after each transaction. Before the first swap, the remaining clock
was compared with the later premium-observation swaps. The original candidate
could no longer finish while retaining its mandatory 30-minute deadline
margin, so execution stopped before any swap, collateral deposit, or option
position.

The resulting partial state is recoverable and intentionally bounded:

```text
buyer wrap complete
  -> writer ERC-20 swap allowances exact
  -> writer Permit2 router allowances exact and expiring
  -> STOP before first swap
  -> bind five receipts + live state
  -> insert two exact Permit2 renewals
  -> refresh four swap deadlines
  -> exact-head replay remaining 22 calls
  -> STOP before new authorization
```

This is not a failed lifecycle. It is the designed fail-closed response to a
short execution window.

## 2. Canonical public prefix

| Index | Sender nonce | Purpose | Public transaction |
|---:|---:|---|---|
| 0 | Buyer `0` | Wrap exactly `0.0003 ETH` into WETH | `0x73efa85dd1ee329847cc2f5618c940bda9747d73d910a6d5c523bfb9eb6c068f` |
| 1 | Writer `13` | Approve exactly `0.002 PLTR` to Permit2 | `0xe0d48363dc520f59f0b75aff779571b362c256d0690841a6284d09432a2abd11` |
| 2 | Writer `14` | Approve exactly `0.000002 WETH` to Permit2 | `0x06a16a46d1f36e1a84be07f4737f18c36a34cc74b4e54717d0af811c0e638387` |
| 3 | Writer `15` | Grant UniversalRouter the exact PLTR Permit2 allowance | `0x6fac923657f13afc339661927df201c0a821922bde76f2009454f4207126f334` |
| 4 | Writer `16` | Grant UniversalRouter the exact WETH Permit2 allowance | `0x01594e06fe274584c20e4a3432d5ed48ff29205ac0a558468ec1522481d7eb6f` |

All five receipts succeeded. The live continuation state is writer nonce `17`,
buyer nonce `1`, buyer WETH `0.0003`, zero open option legs, zero collateral
shares, unchanged V4 pool state, and the exact two-layer writer allowances.

### Why this order matters

The buyer must hold bounded WETH before later collateral funding. Each ERC-20
approval establishes the maximum token amount Permit2 may pull. Each Permit2
approval then narrows that same amount to UniversalRouter and gives it a finite
expiry. A swap cannot precede either layer. Stopping after index `4` therefore
left no partially executed trade or Panoptic position.

## 3. Why the original candidate was retired

The original swap deadline was `2026-09-16T01:13:38Z`. At the index-`5`
preflight only `3,481` seconds remained. Although that single swap still met
the 30-minute rule, the plan also required deadline-bearing swaps at original
indexes `17` and `18`. Completing twelve intervening one-transaction review
gates before those swaps was no longer credible.

Continuing would have optimized for one more green receipt instead of a safely
finishable lifecycle. StonkHedge retired the remaining authorization before
the first value-moving swap.

## 4. Refreshed continuation architecture

The refreshed plan keeps original indexes `0..4` byte-for-byte as historical
prefix evidence and resumes at index `5`. Two new calls renew the existing
router allowances without increasing either amount:

| Refreshed index | Writer nonce | Operation |
|---:|---:|---|
| 5 | 17 | Renew exact `0.002 PLTR` Permit2 allowance |
| 6 | 18 | Renew exact `0.000002 WETH` Permit2 allowance |

The original remaining calls then shift by two indexes. The four swaps are now
indexes `7`, `8`, `19`, and `20`; buyer-first and writer-second closes are
indexes `21` and `22`; allowance cleanup is indexes `23..26`.

The refresh does not increase wrap, swap, collateral, or option exposure. It
only replaces time-bound Permit2 expirations and UniversalRouter deadlines.

## 5. New clocks and nonce streams

| Boundary | Value |
|---|---|
| Reference time | `2026-09-16T00:28:47Z` |
| Swap deadline | `2026-09-16T04:28:47Z` |
| Permit2 expiry | `2026-09-16T06:28:47Z` |
| Continuation start nonces | Writer `17`, buyer `1` |
| Terminal nonces after replay | Writer `33`, buyer `7` |
| Minimum margin at refreshed index 5 | 2 hours |
| Minimum margin at every swap | 30 minutes |

These clocks belong only to this candidate. They are not standing authority.
If the execution-start margin expires, the live state must be recaptured and
the continuation regenerated and replayed again.

## 6. Exact-head replay

Anvil forked the exact public reference block and impersonated only the two
committed ordinary-user accounts. It loaded no wallet and had no public
submission path.

| Check | Result |
|---|---|
| Starting partial state | Matched completed prefix `0..4` |
| Remaining calls | `22/22` passed |
| Premium observation | Changed after the controlled swaps |
| Terminal option legs | Writer `0`, buyer `0` |
| Terminal allowances | ERC-20 and Permit2 amounts zero |
| Total local gas | `3,566,496` |
| Largest local call | Refreshed index `17`, `607,881` gas |
| Public mutation during replay | None |

## 7. Hash ledger

| Artifact | SHA-256 or canonical body hash |
|---|---|
| Refresh preflight body | `30d343cedeaa5d1562ea65b0e12a8b1f126caf47f9fee739630d8c94cbc4e05e` |
| Refresh preflight file | `2f940cee051c22ae4561eae65bca28a23719b8f1e76d73c9add244cb7fbe83e3` |
| Refresh candidate body | `b97bd784e43e2e4e9495c39294ee87f892eb9c132449d34de7a42709bcf390cf` |
| Refresh candidate file | `6ad14f4f8f4c341d3dcb477f06b523d6d380510c6e955c46460b7b31a6d347c3` |
| One-step operator | `d908b07b6b83638aeaea56811e827a221861bfc199db60b5818a2bfa29ab8eb3` |
| Exact-fork simulation runner | `364990fc7bb213a832d0cf6c158512ebcc9ba72385d9b6fde49ebdcfc16290e6` |
| Refresh simulation report | `048bbc06ffbeaa24a5ed632c076beb045396e10c75ab06e172338f388e7cec74` |

The refreshed plan deterministically regenerates from the prior candidate and
the public prefix preflight. The operator rejects attempts to execute indexes
below the refreshed start, changes to the 27-entry historical-plus-continuation
sequence, nonce-chain drift, altered calldata, or a mismatched report.

## 8. Remaining boundary

No refreshed transaction is authorized yet. The next gate is a new explicit
authorization binding:

- the refreshed plan body and file hashes;
- the updated operator and simulation-report hashes;
- both ordinary-user addresses;
- minimum index `5` and maximum index `26`;
- the new swap deadline and Permit2 expiry; and
- `ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH`.

Withdrawals, other markets, administration, deployments, mainnet, and any
transaction after a nonce, state, hash, or time mismatch remain excluded.
