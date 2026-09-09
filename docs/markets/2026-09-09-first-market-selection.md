# First Robinhood testnet market selection

| Field | Value |
|---|---|
| Status | Read-only qualification passed; PLTR/WETH later accepted for offline planning only |
| Snapshot | Block `116408992`, `2026-09-09T19:13:50Z` |
| Technical recommendation | PLTR/WETH, fee `3000`, tick spacing `60`, no hook |
| Candidate PoolId | `0xd600fd2ff936078114b72a01d3c6d31d449b7af12c24c82fb61efb7bf9c613ae` |
| Checks | `79` passed, `0` failed |
| Transactions authorized | None |

## 1. Outcome

All five Robinhood faucet Stock Tokens passed the same pinned-block eligibility
gate. Each token had the expected proxy runtime and registry wiring, was not
paused, had no scheduled multiplier change, was held by both test accounts,
and produced an uninitialized no-hook V4 PoolId with no existing Panoptic
factory mapping.

PLTR is the recommended first sandbox asset because its contract address is the
only qualified Stock Token address lower than the testnet WETH address. Uniswap
V4 requires currencies in ascending address order, so this gives the intuitive
orientation:

```text
currency0 = PLTR Stock Token
currency1 = WETH
```

This is an implementation-safety preference, not an investment opinion. It
reduces accidental inversion in price math, SDK adapters, charts, copy, and
collateral reporting. Ticker popularity, market capitalization, and real-world
investment merit were not considered.

The recommendation was not itself an owner decision. The owner later accepted
the exact candidate, synthetic-price class, and second-actor roles for offline
planning only. The exposure remains a separate proposal and no transaction is
authorized. See the
[offline genesis design](./2026-09-09-pltr-weth-offline-genesis-design.md).

## 2. Where this fits in the architecture

Market genesis connects the already deployed shared Panoptic stack to one
specific V4 liquidity venue. It creates no new Stock Token and changes no
issuer controls.

```mermaid
flowchart LR
    RH[Robinhood faucet and Stock registry] --> ST[PLTR test Stock Token]
    ST --> PK[Exact no-hook PoolKey]
    W[Testnet WETH] --> PK
    PK --> PM[Candidate V4 PoolManager]
    PM --> LP[Bounded V4 liquidity position]
    PM --> SFPM[Deployed Panoptic SFPM V4]
    SFPM --> PF[Deployed PanopticFactoryV4]
    PF --> MK[Future per-market PanopticPool]
    PF --> C0[Future PLTR CollateralTracker]
    PF --> C1[Future WETH CollateralTracker]
    RE[Deployed RiskEngine] --> MK
```

The boxes labelled “future” do not exist yet. The PoolManager, SFPM, factory,
and RiskEngine boxes are live and identity-checked. The PoolKey is derived but
uninitialized.

## 3. The exact PoolKey rule

A V4 pool is identified by five fields, not by a ticker pair:

```text
PoolKey = (
  currency0,
  currency1,
  fee,
  tickSpacing,
  hooks
)

PoolId = keccak256(abi.encode(PoolKey))
```

Changing token order, fee, tick spacing, or hook address changes the PoolId.
There is no later “attach a hook” operation: a hook change means a different
pool. The first sandbox therefore retains the core-tested candidate of fee
`3000`, tick spacing `60`, and `hooks = address(0)` until the owner explicitly
accepts that complete key.

The derived PLTR key is:

| Field | Value |
|---|---|
| `currency0` | PLTR `0x1FBE1a0e43594b3455993B5dE5Fd0A7A266298d0` |
| `currency1` | WETH `0x33e4191705c386532ba27cBF171Db86919200B94` |
| `fee` | `3000` = 0.30% |
| `tickSpacing` | `60` |
| `hooks` | `0x0000000000000000000000000000000000000000` |
| `PoolId` | `0xd600fd2ff936078114b72a01d3c6d31d449b7af12c24c82fb61efb7bf9c613ae` |

## 4. Candidate comparison

Every row uses the same fee, tick spacing, no-hook policy, and WETH address.
`slot0.sqrtPriceX96 == 0` is the observed uninitialized state.

| Stock Token | Stock is `currency0` | PoolId | V4 initialized | Panoptic market | Eligible |
|---|---:|---|---:|---|---:|
| AMZN | no | `0xe9f5eb0c...c50887b8` | no | none | yes |
| AMD | no | `0x5164b26e...ad32fe8a` | no | none | yes |
| TSLA | no | `0x199971df...88cbfa8e` | no | none | yes |
| PLTR | yes | `0xd600fd2f...f9c613ae` | no | none | yes |
| NFLX | no | `0x0d5f0b76...7988095f` | no | none | yes |

The complete addresses, PoolKeys, PoolIds, state, and blockers are in the
[market-selection manifest](../../manifests/markets/robinhood-testnet-market-selection-2026-09-09.json).

## 5. What the qualifier proves

The read-only qualifier pins the head block before reading state and fails if a
response cannot be decoded. Its `79` passing assertions cover:

- chain ID `46630` and a canonical snapshot block hash;
- six candidate V4 infrastructure runtime identities;
- PoolManager owner and fee controller plus PositionManager-to-PoolManager
  wiring;
- Stock registry, Stock implementation, and WETH runtime identities;
- WETH symbol and decimals;
- all 16 deployed Panoptic runtime identities;
- registry pause and beacon implementation state;
- both account types, gas balances, and Stock-registry block state;
- all five token proxy identities, symbol/name/decimals, registry wiring, pause
  state, multiplier state, and both Stock Token balances;
- all five derived PoolIds remaining uninitialized; and
- all five exact PoolKey/RiskEngine factory mappings remaining empty.

The RPC interface permits only:

```text
eth_chainId
eth_blockNumber
eth_getBlockByNumber
eth_getCode
eth_call
eth_getBalance
eth_getTransactionCount
```

Any attempt to use `eth_sendTransaction`, `eth_sendRawTransaction`, signing, or
wallet RPC methods is rejected before network access. The tool has no keystore
or private-key parameters.

## 6. Account and exposure boundary

At the recorded block:

| Account | Native balance | WETH | Each Stock Token | Intended boundary |
|---|---:|---:|---:|---|
| Deployer `0xCa60...08bD` | `0.00928600103 ETH` | `0` | `5` | Shared-stack admin; not the default LP |
| Second actor `0x04D5...6d6f` | `0.01 ETH` | `0` | `5` | Default test user and LP candidate |

No account can provide Stock/WETH liquidity in the observed state because both
hold zero WETH. Wrapping ETH is itself a transaction and is not authorized.
The plan must also reserve enough native ETH for gas rather than treating the
whole faucet balance as liquidity.

Using the second actor as the LP and eventual market-NFT recipient keeps the
temporary guardian/treasurer deployer separate from ordinary market activity.
That role split is now encoded in the offline plan. It is still not authorized
for a public transaction.

## 7. Later decision status

### 7.1 Asset and complete key

The owner accepted PLTR/WETH with fee `3000`, tick spacing `60`, and hooks zero
for offline planning. This does not authorize initialization.

### 7.2 Initial price

The local lifecycle used `sqrtPriceX96 = 2^96`, which means a raw-unit 1:1
ratio. It was not copied silently to public testnet. The owner accepted a
synthetic mechanism-test price class for offline planning, and the generator
records:

- which human-readable direction is displayed;
- decimal normalization;
- price in both directions;
- target tick and tick-spacing rounding;
- exact `sqrtPriceX96` rounding;
- source and timestamp if reference-derived; and
- maximum tolerated drift before initialization.

The resulting offline target is `0.001` test WETH per PLTR with exact
`sqrtPriceX96 = 2505414483750479311864138015` and tick `-69082`. It must never
be displayed as a live PLTR equity quote, and exact exposure still needs a
separate decision.

### 7.3 Maximum exposure and liquidity shape

The unsigned plan proposes caps of `0.004 ETH` wrapped, `2 PLTR` and `0.002
WETH` for liquidity, a `-81120` to `-57060` range, and explicit allowance
cleanup. These are calculated review inputs, not accepted exposure or
broadcast authority.

### 7.4 Roles and ownership

The owner accepted the second actor as pool initializer, LP and V4 NFT owner,
Panoptic market deployer, and factory-NFT recipient for offline planning. The
later two-user collateral/trade roles are not part of this genesis plan. One
person controlling two keys gives functional separation, not independent
review.

## 8. Memory aid: PAIRS

Use **PAIRS** before every market-genesis rehearsal or public step:

- **P — Pin** the chain ID, block, code identities, and exact input hashes.
- **A — Assess** issuer pause/block/multiplier state and both account balances.
- **I — Identify** the full PoolKey, sorted currencies, PoolId, price, and role.
- **R — Reject** drift, initialized pools, existing markets, excessive
  allowances, stale deadlines, or undecodable RPC responses.
- **S — Separate** technical recommendation, owner acceptance, simulation,
  authorization, one-step execution, and post-state reconciliation.

The shorter transaction reminder is **plan → simulate → authorize → one step →
reconcile → stop**.

## 9. Reproduce the evidence

Prerequisites are Python with `eth-abi` and `eth-utils`, plus Foundry `cast` on
`PATH`. From the product repository:

```powershell
python -m pip install -r .\requirements-market-tools.txt
python -m unittest discover -s .\scripts\tests -p "test_*.py" -v
python .\scripts\qualify_robinhood_market.py --transport cast --block 116408992
```

Omit `--block` to take and pin a fresh head. The script defaults to `cast`
because that is also the transport used by the strict repository verifier.
The alternative `--transport urllib` remains available but fails closed on TLS
certificate errors.

The snapshot is historical evidence, not a forever-valid preflight. Rerun at a
fresh head immediately before plan freezing and again before every eventual
state-changing step.

## 10. Next engineering gate

The offline market-plan generator, exact price/tick calculator, bounded
liquidity calculator, acceptance manifest, and unsigned plan are now complete.
The next code artifact is the strict market verifier, followed by a fresh-head
fork rehearsal. Only a separately reviewed execution plan and authorization
may later permit one public transaction at a time.

Until then, there is no permission to wrap ETH, approve tokens, initialize the
pool, add liquidity, swap, deploy the Panoptic market, deposit collateral, or
trade.
