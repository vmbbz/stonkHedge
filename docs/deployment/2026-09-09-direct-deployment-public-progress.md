# Robinhood direct-deployment public progress — 2026-09-09

## Current state

The authorized Robinhood Chain testnet direct-CREATE sequence is in progress
and stopped safely after transaction index `2`. Exactly three of the 16
approved zero-value CREATE transactions have been broadcast.

The machine-readable checkpoint is
[`../../manifests/deployments/robinhood-testnet-direct-public-progress-2026-09-09.json`](../../manifests/deployments/robinhood-testnet-direct-public-progress-2026-09-09.json).

## Transaction 0 evidence

| Item | Verified value |
|---|---|
| Plan SHA-256 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Label | `dataContracts[0]` |
| Nonce | `0` |
| Transaction | [`0xbf6ad4dd...4fda9e`](https://explorer.testnet.chain.robinhood.com/tx/0xbf6ad4ddcf9a22f584f53de5053186a2d9e5ab93eecbfb0847633ab1ac4fda9e) |
| Receipt | success (`status = 1`) |
| Block | `116058458` |
| Created address | `0x05449292522e3FCCD58dB4f947A94BD083d5e13d` |
| Gas used | `5,781,743` |
| Runtime length | `24,439` bytes |
| Runtime code hash | `0xdd0ec57b873af7e553fbd9404281da95203e426929ecb3dfb419bbcbcd87aa7f` |
| External operator evidence SHA-256 | `21996edbaa19301942a8738f92ad141cb9927ec96590c5ef8f67f95977a09201` |

The receipt was queried independently after the operator returned. The runtime
was then fetched again from the expected address and matched the frozen runtime
length and hash.

## Transaction 1 evidence

| Item | Verified value |
|---|---|
| Plan SHA-256 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Label | `dataContracts[1]` |
| Nonce | `1` |
| Transaction | [`0x2faa5abd...6c2050`](https://explorer.testnet.chain.robinhood.com/tx/0x2faa5abd65568cf95a5439e86bc312fab2586a6f287c29a2d77fb2c32f6c2050) |
| Receipt | success (`status = 1`) |
| Block | `116067257` |
| Created address | `0xb1820CEE1BE8b9eDdC382eE83304efBe5ceD0019` |
| Gas used | `5,016,221` |
| Runtime length | `20,669` bytes |
| Runtime code hash | `0x97d0d1afc82d4dba1ebaabd94ef9cdc7e38789cf81a410565d2502634c446615` |
| External operator evidence SHA-256 | `53b872a07ef9f85b3144e7b92af77970525f993e7f58124b0e29c5b68b44078f` |

The transaction-1 receipt and deployed runtime were independently fetched from
the public RPC after the operator stopped, with exact matches to the frozen
plan and simulation evidence.

## Transaction 2 evidence

| Item | Verified value |
|---|---|
| Plan SHA-256 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Label | `dataContracts[2]` |
| Nonce | `2` |
| Transaction | [`0x122f1406...dce1dcd`](https://explorer.testnet.chain.robinhood.com/tx/0x122f14060ca93053445646b08260b0290400c45e4fa76e6925c634e59dce1dcd) |
| Receipt | success (`status = 1`) |
| Block | `116071445` |
| Created address | `0xa318218fEA30EA64c223A1c8E96551c68B007656` |
| Gas used | `5,034,762` |
| Runtime length | `20,141` bytes |
| Runtime code hash | `0x3027b6042e96eabda4468d04a6366f717c3546f2e106b51b5b490574529e7097` |
| External operator evidence SHA-256 | `c0acc47ec082f1c876ed71f5f9de4522db7cf4925e5f5269884399f56676ffe1` |

The transaction-2 receipt and runtime were independently re-read from the
public RPC and matched the frozen plan exactly.

## Continuation gate

A read-only index-3 operator preflight passed at block `116072305`:

- deployer pending nonce: `3`;
- prior deployments verified: `3`;
- remaining predicted addresses verified empty: `13`;
- deployer balance: `0.00984167274` test ETH;
- next expected address: `0xbAD75CD571AeE30644aBe85Da20B6Fa527106c5d`; and
- next gas estimate: `4,423,644`, below the plan gas limit of `16,711,680`.

No index-3 transaction was signed or broadcast during that preflight. The
sequence remains governed by the approved one-transaction/wait/verify/stop
policy. Pool initialization, liquidity provision, and market registration are
still outside this authorization.
