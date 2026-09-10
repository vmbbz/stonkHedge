# Faucet funding and Robinhood mainnet Safe readiness — 2026-09-08

## Outcome

The official Robinhood Chain testnet faucet successfully funded the public
StonkHedge deployer without requiring its private key in a browser. Transaction
[`0x4ad5005f8f19e454a2a4b0bbe111f3f5ead57a15b146023f87000b3c18e47d98`](https://explorer.testnet.chain.robinhood.com/tx/0x4ad5005f8f19e454a2a4b0bbe111f3f5ead57a15b146023f87000b3c18e47d98)
succeeded at block `115750101`, timestamp `2026-09-08T19:07:49Z`.

The deployer now has `0.01` test ETH and `5` each of AMZN, AMD, TSLA, PLTR,
and NFLX. Its pending nonce remains `0`: receiving faucet assets does not consume
the recipient's nonce. A later strict verifier run passed at block `115756898`,
hash `0x8d7f902d4969c72ecb1196dc69118d8a679089e11a3a600b4cbfd998431bb49d`,
timestamp `2026-09-08T19:22:39Z`.

This clears the deployer's funding gate. It does not clear the second-actor,
independent-review, exact-artifact regeneration, or broadcast gates. No private
key was read, no deployer-signed transaction was made, and no StonkHedge
contract was deployed.

## Receipt and resulting balances

| Evidence | Verified value |
|---|---|
| Chain | Robinhood Chain testnet, `46630` |
| Receipt status | `1` / success |
| Block | `115750101` |
| Block hash | `0x9ff10ea22ff3c0396d6f205895c24536a1032b37b43662dbd34269a416b38c14` |
| Faucet distributor | `0x8762f93772c663c6a88ba50900bd5381df2717be` |
| Recipient | `0xCa60c8eF6934f8a97c6a503C4e3a46e87F5b08bD` |
| Native balance | `10000000000000000` wei (`0.01` ETH) |
| Each Stock Token balance | `5000000000000000000` raw units (`5`, at 18 decimals) |
| Pending deployer nonce | `0` |

The receipt emitted standard ERC-20 `Transfer` events from the zero address to
the deployer for all five reviewed Stock Token addresses. It also emitted each
token's `TransferWithScaledUI` event. Current raw and UI amounts are equal because
the verified multiplier is `1e18`.

## Full strict verification

The checked-in verifier completed in 130.7 seconds against Robinhood's
rate-limited public RPC and exited `0` with no failed or blocked assertions:

```powershell
pwsh -File .\scripts\verify-robinhood-testnet.ps1
```

It reconfirmed the candidate V4 runtime hashes, PoolManager owner and zero fee
controller, PositionManager wiring, Stock Token proxy/registry/implementation
identity, pause and multiplier state, WETH/test-USDC identity, deployer block
status, nonce, and funded balances. The long duration is an operational warning:
immediate pre-broadcast verification should use a reviewed provider RPC or a
future bounded-concurrency verifier, while retaining the public RPC as an
independent comparison.

## Does the testnet direct-CREATE path create a mainnet problem?

No. The direct-CREATE fallback is specific to chain `46630`, where Panoptic's
canonical sub-zero CREATE3 contract is absent. Robinhood mainnet chain `4663`
has the canonical CREATE3 contract at
`0x000000000000b361194cfe6312EE3210d53C15AA`: at block `57933888`, its runtime
was 10,812 bytes with code hash
`0xb7cfc5d258769f50c9fdc05c39485a86dbd23a0c984824d2c522e3e8d5dbcfb7`.

Robinhood mainnet and testnet also both contain the canonical Safe v1.4.1
contracts needed for on-chain multisig execution and MultiSend batching. Their
runtime hashes match the official `safe-global/safe-deployments` registry. The
sanitized values are pinned in
[`../../manifests/chains/robinhood-mainnet-deployment-prerequisites-4663.json`](../../manifests/chains/robinhood-mainnet-deployment-prerequisites-4663.json):

| Contract | Canonical address |
|---|---|
| Safe L2 singleton | `0x29fcB43b46531BcA003ddC8FCB67FFE91900C762` |
| Safe singleton | `0x41675C099F32341bf84BFc5382aF534df5C7461a` |
| Safe proxy factory | `0x4e1DCf7AD4e460CfD30791CCC4F9c8a4f820ec67` |
| MultiSend | `0x38869bf66a61cF6bDB996A6aE40D5853Fd43B526` |
| MultiSendCallOnly | `0x9641d764fc13c8B624c04430C7356C1C7C8102e2` |

Therefore Robinhood's EVM can execute a Safe batch. Hosted Safe Wallet and
Transaction Service availability is a separate convenience layer and was not
established by this audit. A reviewed deployment can still construct, simulate,
sign, and execute Safe transactions against the on-chain contracts without
claiming hosted-service support.

One Panoptic-specific mainnet prerequisite remains. The current upstream salts
embed Panoptic's Ethereum Safe address
`0x82bf455e9ebd6a541ef10b683de1edcaf05ce7a1` as the CREATE3 mint recipient. That
3-of-5 Safe exists on Ethereum but is currently absent on both Robinhood chains.
Having Safe and CREATE3 contracts available does not let StonkHedge impersonate
Panoptic's owners or reuse their release authorization.

A future Robinhood mainnet plan must choose one explicitly reviewed route:

1. Panoptic deploys/controls its corresponding Safe and performs an official
   release on chain `4663`.
2. StonkHedge creates its own reviewed multisig, mines fresh salts bound to that
   Safe, rebuilds and audits every address/artifact, then uses CREATE3 and Safe
   batches.
3. A separate mainnet deployment method is designed and audited.

Testnet direct CREATE neither prevents nor silently decides that mainnet choice.
Mainnet also remains blocked on licensing, legal eligibility, protocol audit,
governance, operations, and real-value risk—not merely deployment mechanics.

## Current execution boundary

Independent review is allowed to run concurrently with local implementation.
It is not required for specifications, unit/fuzz/invariant tests, local Anvil
work, SDK adapters, UI scaffolding, monitoring, or refreshed fork simulations.

It remains a hard prerequisite before the first public transaction that embeds
or calls the non-official V4 candidate as a trusted dependency. That includes
public Panoptic deployment, pool initialization, liquidity, approvals, and
market registration. This keeps the review consequential without making the
team idle.
