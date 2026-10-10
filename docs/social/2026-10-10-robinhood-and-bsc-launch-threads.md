# StonkHedge Robinhood and BSC public-update threads

These are copy-ready X drafts. They intentionally contain no repository link.
Post the Robinhood thread first, then the BSC hackathon thread. Preserve the
truth boundaries: Robinhood is testnet-only, the public lifecycle is complete
through index `17`, and StonkHedge has not deployed a contract or broadcast a
trade on BSC mainnet.

## Thread 1 — Robinhood Chain Testnet milestone

### 1/10

StonkHedge is deployed on Robinhood Chain Testnet (chain 46630): a Panoptic-style options stack for testing tokenized-stock markets, starting with PLTR/WETH. We deployed 16 shared contracts and 3 market-specific clones. 🧵

### 2/10

What works: a PLTR/WETH Uniswap V4 pool was initialized, bounded two-sided liquidity was minted as NFT #3903, and a Panoptic market with two collateral trackers was registered. The starting price is synthetic test data—not a PLTR market quote.

### 3/10

Core contracts:

Factory 0x96C3291C9b0C34b007893326ee9dcA534BfcFa0c

SFPM 0x86ef420fD3e27c3Ac896c479B19b6A840b97Bee1

RiskEngine 0x3Ad134ff173dFA0a892B4116A65B76B818218585

Guardian 0x4620fCf531A72EC24af9325dD1Fa476A59Bd7b9e

### 4/10

Shared logic:

BuilderFactory 0xAa1Cc5922f41C93d09CeCbE80373B63D96cC027B

Pool ref 0xfBA5b34cb1471605d82BBF395F244Fa41148b155

Collateral ref 0x41119aAd1c69dba3934D0A061d312A52B06B27DF

Math 0x45bb5b5719bB2B6cf516BE7C063B4D318890D3e7

### 5/10

Market graph:

Helper 0xDCf9936b330D6957CaD463f850D1F2B6F1eABc3A

PLTR/WETH pool 0x042c0d9c497d62a85b3410f2773cfa748d18e586

PLTR tracker 0x2146295437da444638a4cf80900a9e2d3b1315de

WETH tracker 0x48d0e86df893b6032ebe9f14ac0eaa23a7949867

### 6/10

Factory metadata stores 0–3:

0x05449292522e3FCCD58dB4f947A94BD083d5e13d

0xb1820CEE1BE8b9eDdC382eE83304efBe5ceD0019

0xa318218fEA30EA64c223A1c8E96551c68B007656

0xbAD75CD571AeE30644aBe85Da20B6Fa527106c5d

### 7/10

Factory metadata stores 4–6:

0x1F6f1daab8b0d9605D7A880bD738aEe6Fd764107

0xB1D560De10Fb3733d7A5dFefED0388A2435fdaBA

0x19E58B3113579A02c2C266e1be0049766F333338

These seven stores hold renderer bytes; they are not seven protocol engines.

### 8/10

Deployment + market genesis used 29 verified project-signed transactions. The public lifecycle then completed indexes 0–17: two bounded PLTR↔WETH swaps, writer PLTR/WETH collateral deposits, buyer PLTR deposit, then exact buyer WETH approval.

### 9/10

Current boundary: index 18—the buyer's WETH collateral deposit—was not executed. No public option leg has been opened. Every step is testnet-only, nonce/state bound, one transaction at a time, and stopped on mismatch.

### 10/10

Inspect the anchors on Robinhood's explorer:

Factory: https://explorer.testnet.chain.robinhood.com/address/0x96C3291C9b0C34b007893326ee9dcA534BfcFa0c

Market: https://explorer.testnet.chain.robinhood.com/address/0x042c0d9c497d62a85b3410f2773cfa748d18e586

Mechanism evidence—not an equity quote or mainnet launch.

### Suggested media

- Post 1: `public/media/stonkhedge-testnet-hero.jpg`
- Post 2 or 8: `public/media/stonkhedge-progress.mp4`

## Thread 2 — BSC / BNB Hack build announcement

### 1/7

Next for StonkHedge: BSC mainnet. We are building Gap Guardian for the @BNBChain Tokenized Stocks Hackathon—a live, issuer-aware safety layer for comparing and rehearsing tokenized-stock spot routes before anyone signs. 🧵 #BNBHack #RWA

### 2/7

Live BSC assets integrated—these are issuer/token contracts, not StonkHedge deployments:

Ondo NVDAon 0xa9ee28c80f960b889dfbd1902055218cba016f75

bStocks NVDAB 0x02fca66c1d1afb4e2a7884261eb00f63598a7436

USDT 0x55d398326f99059ff775485246999027b3197955

### 3/7

The problem: tokenized stocks trade on-chain while the underlying market can be closed or changing session. Different issuers also use different token-to-share ratios. A raw token price comparison can therefore be dangerously misleading.

### 4/7

Gap Guardian resolves both NVDA representations through Binance Web3 APIs, normalizes each to per-share value, and exposes freshness, session status, issuer gap, reference data, attestation support, pauses, and route identity.

### 5/7

The transaction lens is deliberately bounded to exactly 5.10 USDT. It binds chain 56, token pair, amount, receiver, vendor, quote, expiry, output, approval target, and 0.5% slippage—then simulates approval and swap without returning executable calldata.

### 6/7

Current proof: live discovery and quotes work. Exact approval simulation returned SUCCESS; the unfunded sender's swap returned FAILED for insufficient USDT, so StonkHedge returned BLOCKED. No wallet, private key, signature, or broadcast was involved.

### 7/7

Truth boundary: no StonkHedge-owned contract or completed trade exists on BSC yet. Next milestones are the public demo and a separately reviewed small-amount spot proof. The goal is simple: make tokenized-stock uncertainty visible before execution. #TokenizedStocks

### Suggested media

- Post 1: `docs/hackathons/evidence/2026-10-10/01-live-comparison-desktop.png`
- Post 5: `docs/hackathons/evidence/2026-10-10/02-live-quote-desktop.png`
- Post 6: `docs/hackathons/evidence/2026-10-10/03-live-simulation-desktop.png`

## Posting checks

- Do not say “Robinhood mainnet”; this is Robinhood Chain Testnet.
- Do not say the synthetic PLTR/WETH price is a stock quote.
- Do not say lifecycle index `18` or an option position is complete.
- Do not describe the seven metadata stores as independent protocol engines.
- Do not claim the source implementations are explorer-verified; runtime
  identities and wiring were reconciled, while explorer source publication was
  still pending in the recorded verification inventory.
- Do not call the BSC issuer contracts StonkHedge deployments.
- Do not claim a BSC transaction, wallet connection, signature, or broadcast.
- Open every explorer link in a signed-out window before posting.
- Keep the repository URL out of both threads, as requested.
