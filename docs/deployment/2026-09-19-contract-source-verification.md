# Robinhood testnet contract source-verification runbook

**Status:** runtime identity passed; Blockscout source publication pending

**Network:** Robinhood Chain testnet (`46630`)

**Source commit:** Panoptic core `f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d`

**Safety boundary:** this record prepares commands; it does not submit source,
sign a transaction, or broadcast anything.

## What “verified” means here

There are two different proofs, and both matter:

1. **Deployment/runtime verification** proves that the code currently at an
   address has the exact byte length and Keccak-256 hash recorded at deployment.
   This already passes for all 19 StonkHedge/Panoptic addresses in scope.
2. **Explorer source verification** asks Blockscout to reproduce the deployment
   bytecode from a compiler input and then publish the matching source, ABI,
   compiler settings, linked libraries, and constructor arguments. This has not
   yet been submitted for the nine source implementations.

A green explorer badge is therefore useful, but it does not replace constructor
wiring, ownership, clone-argument, receipt, or post-state checks.

The machine-readable snapshot is
[`robinhood-testnet-contract-verification-inventory-2026-09-19.json`](../../manifests/deployments/robinhood-testnet-contract-verification-inventory-2026-09-19.json).

The committed audit is pinned to block `121795958`, block hash
`0x0cff5ef2948232834738591825a11a755046c02c27ef22d60ed38d04936c3dd7`,
and timestamp `2026-09-19T19:32:22Z`. It recorded:

- inventory body SHA-256
  `a98eda2e196a84a6efa8b3b9d395705d0c48de2b67c62ba79c344faf147073c8`;
- inventory file SHA-256
  `7fa59999fedc29d9438b90dc96ee0c88dda0bfc94372f475fca92d6d327b6e08`;
- preparer SHA-256
  `055d30c17d7966d9cab2259d3e629c1b90ee3da54e15a8d347cc4aa3f7720619`;
- `19/19` live runtime identity matches;
- `0/9` source implementations currently source-verified on Blockscout; and
- zero source submissions attempted.

## The three verification classes

| Class | Count | Correct treatment |
|---|---:|---|
| Metadata data stores | 7 | Raw bytecode-backed NFT metadata stores. Preserve their runtime hashes; there is no ordinary Solidity artifact to publish. |
| Source implementations | 9 | Recompile and submit the exact source, libraries, compiler settings, and constructor arguments to Blockscout. |
| PLTR/WETH market clones | 3 | Verify the implementation first, then associate the clone with that implementation and preserve its immutable-argument runtime hash. |

The source implementations are `PanopticMath`, `InteractionHelper`,
`CollateralTrackerV2`, `PanopticGuardian`, `BuilderFactory`, `RiskEngine`,
`SemiFungiblePositionManagerV4`, `PanopticPoolV2`, and
`PanopticFactoryV4`.

The two collateral contracts are already recognized by Blockscout as
`clone_with_immutable_arguments` instances of `CollateralTrackerV2`. The
PLTR/WETH PanopticPool runtime embeds `PanopticPoolV2` at
`0xfBA5…b155`, but Blockscout did not automatically classify that custom clone
at the audit block. That is an explorer presentation gap, not runtime drift.

## Exact build identity

Verification must run from a clean checkout at the exact deployed commit. The
preparer rejects any other commit or dirty worktree and binds:

- Solidity `0.8.28`;
- EVM target `cancun`;
- optimizer enabled, with each contract's original run count (`1` or
  `9,999,999`);
- `viaIR = false`;
- BUSL-1.1 source license;
- the exact linked library addresses;
- the exact direct-CREATE constructor arguments;
- direct-config SHA-256
  `728898b3f201e3c4421b00e9fcb2b7587796971e55fef73ac504a081da489cc0`;
- metadata-package SHA-256
  `c5d1b27e67ee4b62d865c240d428afc00115dc38a741988edcf1f2a22631b5f8`.

Do not verify from the newer working core branch merely because it contains
the deployment commit in its history. Use the clean review checkout pinned to
`f4abdd7...` so later harness files cannot enter the compiler input.

## Read-only audit

From the StonkHedge repository:

```powershell
python .\scripts\prepare_robinhood_contract_verification.py `
  --core-root C:\dev-shared\stonkHedge-review\panoptic-v2-core-review `
  --direct-config C:\dev-shared\stonkHedge-review\artifacts\robinhood-46630-20260909-owner\direct-config.json
```

This performs only `eth_chainId`, `eth_getBlockByNumber`, `eth_getCode`, and
Blockscout API reads. It contains no private-key, keystore, signing, transaction
serialization, or verification-submission path.

## Prepare one exact Foundry command

Robinhood's official deployment guide identifies Blockscout as the verifier,
testnet chain ID `46630`, the official RPC, and
`https://explorer.testnet.chain.robinhood.com/api/` as the testnet verifier
endpoint. The preparer fixes those values rather than accepting a different
chain or verifier by accident.

Generate and inspect one command at a time:

```powershell
python .\scripts\prepare_robinhood_contract_verification.py `
  --core-root C:\dev-shared\stonkHedge-review\panoptic-v2-core-review `
  --direct-config C:\dev-shared\stonkHedge-review\artifacts\robinhood-46630-20260909-owner\direct-config.json `
  --print-command PanopticMath
```

The output uses Robinhood's Blockscout endpoint and includes `--watch`. It is
printed for review and is **not executed**. Repeat with the other eight names.
Linked contracts must follow dependency order:

```text
PanopticMath
  -> InteractionHelper
     -> CollateralTrackerV2
  -> PanopticPoolV2
PanopticGuardian -> BuilderFactory -> RiskEngine
SemiFungiblePositionManagerV4
PanopticMath + all dependencies -> PanopticFactoryV4
```

`PanopticFactoryV4` carries a very large metadata constructor payload. Do not
copy it from chat, truncate it, or reconstruct it manually. Generate it from
the hash-bound metadata package through the preparer.

## Submission and acceptance sequence

Source publication is an external explorer write, so it remains a separate
owner-reviewed action even though it spends no gas and needs no wallet.

For each implementation:

1. rerun the read-only inventory and require `19/19` runtime identities;
2. print the exact command;
3. review address, contract path, optimizer runs, linked libraries, and
   constructor-argument presence;
4. explicitly approve source publication;
5. run only that one command from the clean core checkout;
6. wait for Blockscout to report success;
7. rerun the inventory and commit the changed explorer status;
8. stop on the first mismatch before continuing.

After the implementations are verified, confirm both collateral clone pages
resolve to `CollateralTrackerV2`. For the pool clone, use Blockscout's proxy or
implementation association only if it supports this custom immutable-argument
layout; never submit the clone as if it were the 24,275-byte implementation.

## What is outside this source-publication pass

`PoolManager`, `PositionManager`, `StateView`, `UniversalRouter`, `Permit2`,
WETH, the StockRegistry, and PLTR are external Robinhood/Uniswap/issuer
deployments. StonkHedge checks their live runtime identity and wiring, but does
not claim ownership of their source-verification records.

Likewise, source verification does not authorize lifecycle index `8`, any
collateral movement, options positions, withdrawals, deployments, or mainnet
activity.

Official reference: [Deploy smart contracts on Robinhood Chain](https://docs.robinhood.com/chain/deploy-smart-contracts).
