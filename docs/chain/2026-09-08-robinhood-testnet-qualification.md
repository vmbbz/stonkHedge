# Robinhood testnet read-only qualification — 2026-09-08

## Outcome

Chain `46630`, five issuer-shaped test Stock Token proxies, test WETH, and an existing Uniswap v4 candidate stack are live and internally consistent. Reusing the candidate stack can remove the planned PoolManager/periphery deployment transactions from the fastest sandbox path.

The qualification is intentionally bounded: Uniswap's official deployment repository does not list chain `46630`, so the testnet stack is recorded as **reusable candidate infrastructure, not an official Uniswap deployment**. A second contributor must reproduce this report before its addresses become deployment inputs.

No private key was read or printed and no transaction was signed or broadcast. The public deployer `0xCa60c8eF6934f8a97c6a503C4e3a46e87F5b08bD` had nonce `0`, zero test ETH, and zero of all five Stock Tokens. Faucet funding therefore remains `BLOCKED`.

The machine-readable evidence is [`../../manifests/chains/robinhood-testnet-46630.json`](../../manifests/chains/robinhood-testnet-46630.json), and the executable drift check is [`../../scripts/verify-robinhood-testnet.ps1`](../../scripts/verify-robinhood-testnet.ps1).

## Evidence window

Most pinned state was read at block `115636679`, hash `0x18f11247efe58b3c909446f08ed28798ac79a6a89f844c514654dc807c6c5871`, timestamp `2026-09-08T14:54:53Z`. The public RPC lacked two historical trie nodes while reading code hashes. Those hashes were re-read at current block `115639902`, hash `0x0443f9395c2185d2e7221894be5777c189458dce4853dee2d7bdd384385009a4`, timestamp `2026-09-08T15:03:05Z`. The verifier deliberately checks latest state so any later drift fails closed.

## Candidate v4 stack

| Contract | Address | Runtime bytes | Runtime code hash |
|---|---|---:|---|
| PoolManager | `0x8366a39CC670B4001A1121B8F6A443A643e40951` | 24,009 | `0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626` |
| PositionManager | `0x58daec3116aae6D93017bAAea7749052E8a04fA7` | 23,877 | `0xf3a0edb689229fa4bf135a728f2ec2eb4a2fbee2e41e3e74ffadb7b4c56e8a6d` |
| Quoter | `0x8Dc178eFB8111BB0973Dd9d722ebeFF267c98F94` | 6,118 | `0xd707b1da8cb165e5ea35a3b4450d971eb562ec171e23492aa117036b78a868f6` |
| StateView | `0xF3334192D15450CdD385c8B70e03f9A6bD9E673b` | 3,531 | `0x7d9c591e0956fd89d98feb4ffcfe8bf1f7a62bd485edd979fa21d104b49878a6` |
| UniversalRouter | `0x8876789976dEcBfCbBbe364623C63652db8C0904` | 24,546 | `0xfdd90802f39ce5fc8bac4c2f1b3ac7bac530fd17ff46b0630f1bd00f1e14082f` |
| Permit2 | `0x000000000022D473030F116dDEE9F6B43aC78BA3` | 9,152 | `0x0117e0ed818bc3f2a8729ffc336c837e63e965f04b473047b39b35ad86aac259` |

The PoolManager runtime hash also matches the official Robinhood mainnet PoolManager at the same deterministic address. Testnet-specific control state is different: owner `0x9701fb0aDe1E269c8f64Ec0C7b3cfADB31A13A52` is an EOA, while `protocolFeeController()` is zero. PositionManager's `poolManager()` returns the expected candidate PoolManager. These controls and wiring are verifier gates, not merely documentation.

## Test assets

All five Stock addresses contain the same 283-byte beacon-proxy runtime hash and resolve through registry/beacon `0x1dF3cA0fD30ED5eeb09eB01938f4E9c5196E6Ca5` to shared implementation `0xBd14156E05c6AF28ad39aA53a2AB8eB9CDf657DA`. The registry is not globally paused and does not block the deployer. Every token reported:

- the expected symbol and 18 decimals;
- `paused() == false` and `tokenPaused() == false`;
- current and pending UI multipliers of `1e18`;
- `effectiveAt() == 0`, so no multiplier transition was scheduled; and
- a zero deployer balance.

| Symbol | Address |
|---|---|
| AMZN | `0x5884aD2f920c162CFBbACc88C9C51AA75eC09E02` |
| AMD | `0x71178BAc73cBeb415514eB542a8995b82669778d` |
| TSLA | `0xC9f9c86933092BbbfFF3CCb4b105A4A94bf3Bd4E` |
| PLTR | `0x1FBE1a0e43594b3455993B5dE5Fd0A7A266298d0` |
| NFLX | `0x3b8262A63d25f0477c4DDE23F83cfe22Cb768C93` |

Test WETH `0x33e4191705c386532ba27cBF171Db86919200B94` is an 18-decimal WETH contract. Faucet-style test USDC `0xbf4479C07Dc6fdc6dAa764A0ccA06969e894275F` is also 18 decimals and is not Circle USDC.

## Reproduce

Read-only qualification, allowing the known funding blocker:

```powershell
pwsh -File .\scripts\verify-robinhood-testnet.ps1 -SkipFundingGate
```

Deployment preflight, which must remain non-zero until both ETH and at least one Stock Token are present:

```powershell
pwsh -File .\scripts\verify-robinhood-testnet.ps1
```

Passing either command validates current public chain state only. Core review, infrastructure review, exact-sender simulation, a second actor, and a bounded transaction manifest are separate gates.

## Source classification

- Robinhood's official network documentation establishes chain identity and RPC/explorer endpoints.
- Robinhood's testnet announcement establishes the purpose of the test Stock Tokens.
- Uniswap's official Robinhood mainnet deployment record establishes the mainnet PoolManager address and provenance.
- EqualFiLabs' public testnet manifest supplies a reproducibility lead for the non-official testnet stack and pins Uniswap source commits; stonkHedge independently re-read every consumed runtime hash and critical control value.

This evidence supports reuse for a valueless sandbox after review. It does not establish issuer partnership, Uniswap endorsement, audit coverage, mainnet rights, or safe handling of real value.
