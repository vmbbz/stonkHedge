# Receipt-bound lifecycle continuation after index 7

| Field | Value |
|---|---|
| Network | Robinhood Chain Testnet (`46630`) |
| Market | PLTR/WETH, 0.30% fee, tick spacing 60, zero hooks |
| Status | Public prefix `0..14` verified; both writer collateral deposits passed, then execution stopped before buyer collateral approval |
| Writer | `0x04D5A0f57Cb2e110faC9703024888cd4562B6d6f` |
| Buyer | `0x6719E877C05b2d6c28aBceA405fC033FEeF5750f` |
| Public continuation start | Index `8`; writer nonce `20`, buyer nonce `1` |

## 1. Outcome

The first prefix-bound refresh executed three public calls after the original
five-call prefix:

| Index | Result | Transaction |
|---:|---|---|
| 5 | Renewed the remaining PLTR Permit2-to-router allowance without transferring assets | `0xa0b800c1c1f75258a288c36bf2eca91c280f987d71cf42f3b03ce0578db696d0` |
| 6 | Renewed the remaining WETH Permit2-to-router allowance without transferring assets | `0x9dcf9a40cf1cc3b3cacb6f87889c0b1e5bdf3654c3dfc90094b1b6cd0ec2d1fa` |
| 7 | Swapped exactly `0.001 PLTR` for `0.000000996773015596 WETH` | `0xd2d2783b10d9fcd1c2595cd4cc7c9a000acd56824c3311c8f1b888b5cc9ed5b2` |

The expired predecessor's attempted index `8` reverse swap never reached the keystore prompt. The
operator rejected it during read-only preflight because the mandatory
30-minute swap-deadline margin was exhausted. There is no index-`8` receipt or
evidence file, the writer nonce remains `20`, and index `7` is the last
canonical lifecycle transaction in that predecessor plan.

This is a successful fail-closed outcome, not a failed or partially submitted
transaction.

The receipt-bound replacement was then separately authorized. Its index `8`
renewed only the exact remaining `0.001 PLTR` Permit2 allowance and mined
successfully as transaction
[`0x13df...e77f`](https://explorer.testnet.chain.robinhood.com/tx/0x13df2d9fc83d2796c4e85ea5716e70604506c83de7f8fbc78f8e1fa46409e77f)
in block `121820023`. The receipt status is `1`, gas used is `42,000`, the
writer nonce advanced from `20` to `21`, the buyer nonce remained `1`, and the
operator stopped before index `9`.

Index `9` then renewed only the exact remaining `0.000002 WETH` Permit2
allowance. Transaction
[`0x068c...3f95`](https://explorer.testnet.chain.robinhood.com/tx/0x068c593886dd268d977bec8d8027f763545c16d33d3cf1cd32749edb395a3f95)
mined successfully in block `121822865`. The receipt status is `1`, gas used
is `38,969`, the writer nonce advanced from `21` to `22`, the buyer nonce
remained `1`, and both Permit2 allowances now have the exact amounts and
expiry committed by the authorization. The operator stopped before the first
remaining swap at index `10`.

Index `10` then spent exactly `0.000001 WETH` and received
`0.000997226984392005 PLTR`, exceeding the committed minimum output of
`0.0008 PLTR`. Transaction
[`0xf6c0...a524`](https://explorer.testnet.chain.robinhood.com/tx/0xf6c064b17f2e279b1f3f8a404929ddf836d09453d144fe5fd3c7d2f22fc2a524)
mined successfully in block `121826821` and used `188,093` gas. Independent
reads confirm the writer nonce advanced from `22` to `23`, both WETH
allowances fell by exactly the input to `0.000001 WETH`, active liquidity was
unchanged, and the pool tick moved from `-69086` to `-69082`. The operator
stopped before any collateral approval.

Index `11` approved exactly `0.5 PLTR` from the writer to collateral tracker0.
Transaction
[`0x78a6...c7e5`](https://explorer.testnet.chain.robinhood.com/tx/0x78a6058909060b41148fc5c600b30ad594a9b6bf75a8c79dbec0bbe9bf24c7e5)
mined successfully in block `121832461` and used `68,739` gas. Independent
reads confirm the writer nonce advanced from `23` to `24`, both token balances
were unchanged, and the allowance equals exactly `0.5 PLTR`. The operator
stopped before the corresponding collateral deposit.

Index `12` deposited exactly `0.5 PLTR` into collateral tracker0 for the
writer. Transaction
[`0x0415...688f`](https://explorer.testnet.chain.robinhood.com/tx/0x041588abab2ce9dce2a3e14a820c27be81f9e5aafd273e4a32a8e1593b83688f)
mined successfully in block `121836639` and used `198,601` gas. Independent
reads reconcile the full `0.5 PLTR` wallet debit, `500000000000000000000000`
tracker shares, `0.5 PLTR` credited assets and `maxWithdraw`, zero residual
tracker0 allowance, and writer nonce `25`. The WETH balance was unchanged.

Index `13` approved exactly `0.0005 WETH` from the writer to collateral
tracker1. Transaction
[`0xeb1e...dfca`](https://explorer.testnet.chain.robinhood.com/tx/0xeb1ece5b5f1d63b2eb36ce50db38c9a2cadef89a9f7ee0e414039e37fb3edfca)
mined successfully in block `121843623` and used `52,659` gas. Independent
reads confirm the writer nonce advanced from `25` to `26`, the buyer nonce
remained `1`, both writer token balances were unchanged, and the allowance is
exactly `0.0005 WETH`. The operator stopped before the corresponding tracker1
deposit.

Index `14` deposited exactly `0.0005 WETH` into collateral tracker1 for the
writer. Transaction
[`0x801b...8af1`](https://explorer.testnet.chain.robinhood.com/tx/0x801bf16e8764211f8f309de0506955aa45d2cccca8a4bed38431c161b88a8af1)
mined successfully in block `121846768` and used `166,336` gas. Independent
reads reconcile the exact wallet debit, `500000000000000000000` tracker1
shares, `0.0005 WETH` credited assets and `maxWithdraw`, zero residual
tracker1 allowance, writer nonce `27`, and buyer nonce `1`. The PLTR balance
was unchanged.

## 2. Why a second continuation is necessary

The four-hour clock was safe for automated execution but did not match the
actual human one-transaction/review cadence. Reusing or editing the expired
candidate would break its calldata hashes, nonce chain, simulation binding,
and authorization.

The replacement therefore treats transactions `0..7` as immutable history:

```mermaid
flowchart LR
    A[Receipts 0..4] --> B[Renewals 5 and 6]
    B --> C[PLTR to WETH swap 7]
    C --> D[Receipt-bound public checkpoint]
    D --> E[Exact remaining approvals]
    E --> F[Remaining lifecycle 8..28]
    F --> G[Exact-head fork replay]
    G --> H[Separate owner authorization]
```

The read-only qualifier revalidated all eight public receipts, calldata
hashes, senders, nonces, destinations, values, deployed runtimes, wiring,
issuer controls, balances, allowances, pool state, and both confirmed and
pending nonce streams at block `121787328`.

## 3. Exposure is derived from remaining calls

The new planner does not restore the original swap budget. It sums only the
unexecuted exact-input swaps and requires the live ERC-20 and Permit2 amounts
to equal those totals:

| Token | Original total budget | Already consumed | Exact remaining renewal |
|---|---:|---:|---:|
| PLTR | `0.002` | `0.001` | `0.001` |
| WETH | `0.000002` | `0` | `0.000002` |

The renewal transactions change only Permit2 expiry metadata and preserve the
same UniversalRouter spender. They do not transfer tokens. All router and
ERC-20 allowance amounts return to zero at the end of the replay.

## 4. Remaining ordered sequence

| Index | Sender nonce | Purpose |
|---:|---:|---|
| 8 | Writer `20` | **Complete:** renewed exact remaining PLTR Permit2 allowance |
| 9 | Writer `21` | **Complete:** renewed exact remaining WETH Permit2 allowance |
| 10 | Writer `22` | **Complete:** swapped exact `0.000001 WETH` for `0.000997226984392005 PLTR` |
| 11 | Writer `23` | **Complete:** approved exact `0.5 PLTR` collateral to tracker0 |
| 12 | Writer `24` | **Complete:** deposited exact `0.5 PLTR` collateral into tracker0 |
| 13 | Writer `25` | **Complete:** approved exact `0.0005 WETH` collateral to tracker1 |
| 14 | Writer `26` | **Complete:** deposited exact `0.0005 WETH` collateral into tracker1 |
| 15–18 | Buyer `1–4` | Approve and deposit exact PLTR/WETH collateral |
| 19 | Writer `27` | Open the bounded in-range short call |
| 20 | Buyer `5` | Open the smaller matched long call |
| 21–22 | Writer `28–29` | Drive and observe bounded premium movement |
| 23 | Buyer `6` | Close the matched long first |
| 24 | Writer `30` | Close the short after its counterparty |
| 25–26 | Writer `31–32` | Revoke both Permit2 router allowances |
| 27–28 | Writer `33–34` | Clear both ERC-20 allowances to Permit2 |

The terminal nonce vector is writer `35`, buyer `7`.

## 5. Explicit clock-policy change

The replacement candidate proposes a seven-day swap deadline and eight-day
Permit2 expiry solely for this faucet-sized testnet lifecycle:

| Boundary | UTC |
|---|---|
| Reference block time | `2026-09-19T18:59:13Z` |
| Swap deadline | `2026-09-26T18:59:13Z` |
| Permit2 expiry | `2026-09-27T18:59:13Z` |
| Minimum margin when index 8 begins | Six days |
| Minimum margin at each swap | 30 minutes |

This longer window reduces repeated clock regeneration but increases the time
the exact remaining test-token allowances can be used by the committed
UniversalRouter. It is not inherited authority: the owner must explicitly
accept these timestamps and the two exact remaining amounts in a new
hash-bound authorization. Mainnet and every other market remain excluded.

## 6. Exact-head replay

Anvil forked the exact public reference block, impersonated only the committed
writer and buyer, loaded no wallet, signed nothing, and had no public
submission path.

| Check | Result |
|---|---|
| Starting public prefix | `0..7` matched |
| Remaining calls | `21/21` passed |
| Premium observation | Changed after the two controlled swaps |
| Terminal option legs | Writer `0`, buyer `0` |
| Terminal ERC-20 allowance amounts | PLTR `0`, WETH `0` |
| Terminal Permit2 allowance amounts | PLTR `0`, WETH `0` |
| Total local gas | `3,402,569` |
| Largest local call | Index `19`, writer short open, `607,881` gas |
| Public mutation during replay | None |

The disposable fork was stopped after the report was written.

## 7. Hash ledger

| Artifact | SHA-256 or canonical body hash |
|---|---|
| Continuation preflight body | `3c1a24b5faab3a656de65c52b84d03a5bf0c374f08b9ad1b3f41b9d7a6c087ee` |
| Continuation preflight file | `78b43454035ca0300ad5729f942a16583226f46014c3750f0bbac97147e47d95` |
| Continuation candidate body | `cd8cdfb5fd01dc9cdfa6fc3a12c8b9e4010cb3529036df96c919c4f4b0871428` |
| Continuation candidate file | `2a93225456d3365cd3bdc7588072977f88ffa1fb4fd1f8a68326181f47c4ac1b` |
| Receipt-bound qualifier | `8f74eb3b66573abc4280c17434291c8432b72cc393e9d002c118568450b11835` |
| Continuation planner | `86cca6d988457e17dc485d7384cb61b58824bb1938d3529e394db656bea24b73` |
| One-step operator | `73e0451aa99e60ed104ef75450560643ae8d0de08e3c41f39d6e5805d20a7caf` |
| Exact-fork simulation runner | `364990fc7bb213a832d0cf6c158512ebcc9ba72385d9b6fde49ebdcfc16290e6` |
| Continuation simulation report | `72bf0a44324976ae187dc9d36b650249971defc48fbf5dc8ade78e4d515453d3` |

## 8. Public authorization boundary

The owner authorization recorded on `2026-09-19` binds all of the following
exactly:

- candidate body and file hashes;
- current operator and simulation-report hashes;
- writer and buyer addresses;
- minimum index `8` and maximum index `28`;
- the exact remaining PLTR/WETH approval amounts;
- the seven-day swap and eight-day Permit2 timestamps; and
- `ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH`.

It excludes increased exposure, prefix re-execution, withdrawals, other
markets, issuer/factory administration, deployments, mainnet, and continued
execution after any nonce, state, hash, or time-window mismatch.

Authorization of the range does not permit unattended execution. Indexes `8`
through `14` have completed; the next gate is a fresh read-only preflight for
index `15`, one encrypted-keystore prompt, receipt verification, post-state
verification, and another unconditional stop.
