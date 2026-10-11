# StonkHedge multichain product boundary

**Status:** implemented product split; not a claim of identical deployment

**Networks:** Robinhood Chain testnet (`46630`) and BNB Smart Chain mainnet (`56`)

StonkHedge is one product and evidence system with two isolated chain lanes. It
is not one protocol deployment copied to two networks. The shared layer is the
interface, research, risk language, fail-closed validation, and proof discipline.
Every contract address, asset balance, nonce, allowance, authorization, and
transaction receipt remains specific to its own chain.

## Current support matrix

| Property | Robinhood Chain testnet | BNB Smart Chain mainnet |
|---|---|---|
| Chain ID | `46630` | `56` |
| Current purpose | Panoptic perpetual-options mechanism test | Issuer-aware tokenized-stock comparison and bounded route rehearsal |
| Assets in the demonstrated path | Faucet PLTR and test WETH | External Ondo `NVDAon`, bStocks `NVDAB`, and BSC USDT |
| StonkHedge deployments | `19` | `0` |
| StonkHedge public transactions | Canonical deployment, market-genesis, and lifecycle receipts | `0` |
| Execution state | One-transaction-at-a-time testnet lifecycle through index `17` | Live API data, fixed `5.10 USDT` quote, and unsigned simulation only |
| Value boundary | Valueless synthetic mechanism test | Mainnet data is real, but StonkHedge does not sign, broadcast, or spend |
| Primary evidence | Explorer receipts, runtime identity, wiring, and reconciled post-state | Fresh API observations, selectors, calldata hashes, and simulation statuses |

## What is shared

- the StonkHedge product identity and browser interface;
- schema validation, decoded-intent review, bounded exposure, and fail-closed
  behavior;
- public evidence conventions and explicit labels for observed versus planned
  state; and
- the requirement for a fresh review and authorization before any state-changing
  action.

## What is never shared implicitly

- deployed addresses or bytecode;
- PoolKeys, market IDs, token addresses, decimals, or issuer assumptions;
- wallets, nonces, balances, approvals, deadlines, or signatures;
- Robinhood transaction authorizations; or
- a claim that a simulation is a deployment, trade, or successful settlement.

There is no StonkHedge bridge between the two lanes. BSC token representations
are not treated as the same instruments as Robinhood Stock Tokens, even when
they reference the same traditional company.

## Architecture by lane

### Robinhood: deployed options mechanism test

The Robinhood lane contains the deployed Panoptic, Uniswap V4, collateral, and
market graph documented in the
[Robinhood testnet system architecture](./robinhood-testnet-system.md). Its
contract atlas and transaction trail are generated from reconciled manifests.
The public lifecycle deliberately stops between calls and requires fresh state,
nonce, receipt, and post-state verification.

### BSC: issuer and route safety lens

The BSC lane uses server-held Binance Web3 API credentials to resolve external
issuer representations, normalize per-share prices, obtain a fixed exact-input
quote, compile fresh approval and swap calls, and simulate those calls unsigned.
The browser receives non-executable proof fields, never credentials or raw
calldata. See the [BNB Gap Guardian architecture](./bnb-gap-guardian.md).

## Forward deployment strategy

1. Keep the current BSC hackathon release simulation-only and deploy only the
   web/API surface, with credentials held as encrypted server variables.
2. Treat any BSC wallet confirmation path as a new security boundary. It must
   bind chain, account, receiver, asset, amount, quote expiry, calldata hash,
   decoded approval, and post-receipt state before broadcast can be considered.
3. Decide separately whether BSC needs StonkHedge-owned contracts. The current
   comparison and simulation product does not require them.
4. If a BSC options deployment is proposed later, qualify compatible liquidity,
   oracle, issuer, and protocol infrastructure from scratch. Do not reuse
   Robinhood addresses, salts, manifests, or authorizations.
5. Preserve one public progress surface, but tag every artifact with network,
   proof type, and execution status.

## Website interpretation

The website's **BSC Gap** section and BSC chain card describe BSC mainnet API
and simulation evidence. The **RH architecture**, **RH contracts**, and
**RH transactions** sections describe Robinhood Chain testnet state only. The
timeline is cross-chain, and each milestone must identify its own evidence
type. This separation is an acceptance requirement, not editorial decoration.
