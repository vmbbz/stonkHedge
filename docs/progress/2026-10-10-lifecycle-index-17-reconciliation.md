# Robinhood lifecycle index-17 reconciliation

| Field | Verified value |
|---|---|
| Reconciliation date | 2026-10-10 |
| Network | Robinhood Chain Testnet (`46630`) |
| Public lifecycle prefix | Indexes `0..17` complete |
| Last canonical transaction | `0x2bca41b0d5a9b460b6ae68634bffff91a8b37cb435d9092b465ce32e64af22ba` |
| Last action | Buyer approves exactly `0.00025 WETH` to the WETH collateral tracker |
| Next unexecuted action | Index `18`: buyer deposits exactly `0.00025 WETH` |
| Public option state | No writer or buyer option leg has been opened |

This note closes a documentation gap discovered while preparing public milestone
copy. The earlier continuation progress manifest stopped at index `16`, but the
live buyer nonce and explorer history showed one later canonical transaction.
The transaction was reconciled byte-for-byte against ordinal `17` of the
receipt-bound continuation candidate.

The machine-readable companion is
[`robinhood-testnet-pltr-weth-lifecycle-index-17-reconciliation-2026-10-10.json`](../../manifests/markets/robinhood-testnet-pltr-weth-lifecycle-index-17-reconciliation-2026-10-10.json).

> **Truth boundary:** this is a valueless testnet approval, not a collateral
> deposit, option position, equity transaction, mainnet release, or invitation
> to trade.

## Canonical receipt

- Sender: `0x6719E877C05b2d6c28aBceA405fC033FEeF5750f`
- Sender nonce: `3`
- Target: Robinhood testnet WETH at
  `0x33e4191705c386532ba27cBF171Db86919200B94`
- Decoded call: `approve(0x48d0e86df893b6032ebe9f14ac0eaa23a7949867,
  250000000000000)`
- Calldata hash:
  `0x103ed5e3e804a8c730f83f270cc99078e73e4e57317d5e4c7a7dc19b4cc9e053`
- Receipt status: `1`
- Block: `121897519`
- Block timestamp: `2026-09-20T03:24:06Z`
- Explorer:
  `https://explorer.testnet.chain.robinhood.com/tx/0x2bca41b0d5a9b460b6ae68634bffff91a8b37cb435d9092b465ce32e64af22ba`

The receipt emitted an ERC-20 `Approval` from the buyer to the WETH collateral
tracker for exactly `250000000000000` raw WETH. A fresh read-only call on
2026-10-10 returned that same allowance.

## Current read-only anchors

The same reconciliation observed:

- deployer nonce `16`;
- writer nonce `27`;
- buyer nonce `4`;
- buyer WETH balance `300000000000000` raw;
- buyer WETH allowance to tracker1 `250000000000000` raw;
- PanopticFactoryV4 runtime length `20,702` bytes;
- SemiFungiblePositionManagerV4 runtime length `23,608` bytes;
- market PanopticPool clone runtime length `306` bytes; and
- both collateral tracker clone runtimes at `181` bytes.

These observations establish continued contract presence and the exact
index-17 approval state. They do not independently re-prove every historical
wiring assertion.

## Updated public accounting

The deployment and first-market genesis remain 29 project-signed transactions:
16 direct shared deployments and 13 market-genesis transactions. The lifecycle
now has 18 canonical transactions, indexed `0..17`.

The lifecycle prefix has therefore completed:

1. bounded funding and permission setup;
2. one tiny PLTR-to-WETH swap and one tiny WETH-to-PLTR swap;
3. writer PLTR and WETH collateral deposits;
4. buyer PLTR collateral deposit; and
5. buyer WETH approval for the still-unexecuted deposit.

Index `18` and all later option, premium-observation, close, cleanup, and
withdrawal actions remain unexecuted. The old swap deadline and Permit2 expiry
have elapsed. Any continuation requires a new state-derived plan, fresh clocks,
exact-head simulation, explicit authorization, one-transaction execution, and
post-receipt verification.
