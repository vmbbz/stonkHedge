# Robinhood direct-deployment public progress — 2026-09-09

## Current state

The authorized Robinhood Chain testnet direct-CREATE sequence is in progress
and stopped safely after transaction index `0`. Exactly one of the 16 approved
zero-value CREATE transactions has been broadcast.

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

## Continuation gate

A read-only index-1 operator preflight passed at block `116062791`:

- deployer pending nonce: `1`;
- prior deployments verified: `1`;
- remaining predicted addresses verified empty: `15`;
- deployer balance: `0.00994218257` test ETH;
- next expected address: `0xb1820CEE1BE8b9eDdC382eE83304efBe5ceD0019`; and
- next gas estimate: `5,127,186`, below the plan gas limit of `16,711,680`.

No index-1 transaction was signed or broadcast during that preflight. The
sequence remains governed by the approved one-transaction/wait/verify/stop
policy. Pool initialization, liquidity provision, and market registration are
still outside this authorization.
