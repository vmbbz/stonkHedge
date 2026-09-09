Hey are there any launchpads on solana and base with open source code? doing the stocks meta

=========================

**Yes — several launchpads on Solana and Base have open-source (or partially open-source/verified) code.** The “stocks meta” refers to the recent wave of tokenized equities (e.g., Coinbase B20 stocks on Base like NVDAc/AAPLc, xStocks on Solana) and meme/launch tokens that pair against or parody them.

### Solana
- **solana-labs/launchpad** (archived reference implementation): Trustless decentralized token distribution with flexible price discovery. Full Anchor program source on GitHub (now read-only).
- **IPFLOW-FUN/LAUNCHPAD**: Audited bonding-curve launchpad with token creation, whitelist (Merkle), migration to Raydium, and configurable params. Open-source (Apache-2.0).
- **stickpump/stick**: Production-oriented Solana launchpad focused on Pump.fun-style raises (timed SOL commitments, weighted allocation, Pump/PumpSwap routing). Includes Anchor program, Next.js frontend, keeper, and packages.
- **viainti/launchpad-for-solana**: Full open-source pump.fun-style platform using Meteora Dynamic Bonding Curve (DBC), with admin dashboard, rewards, AI whitepaper tools, etc. (MIT).
- Other notable ones: MetaDAO’s launchpad programs (futarchy-style ICOs, open on GitHub), various pump.fun clones/SDKs (e.g., community Pump SDKs, bonding-curve contracts), and frontend templates. Pump.fun itself is not fully open-source (program is public but proprietary), but many reverse-engineered/clone contracts and SDKs exist.

### Base
- **BasedPad (basedpadfun/bpad)**: Explicitly built for the stocks meta. Launches fixed-supply (1B) tokens as real Uniswap markets from block 1, with dedicated support for pairing against official Coinbase tokenized stocks (B20/RWA quotes like NVDA, AAPL, etc.) or curated crypto. 90/10 creator/platform fee split on LP fees, no bonding curve/migration in the core model. GitHub has docs, ABIs, partner API, and developer notes; contracts are verified on-chain. Multi-chain (also Arc, Robinhood Chain, HyperEVM).
- **CurvePad (Boomtoknlab/token-launchpad)**: Permissionless linear bonding-curve launchpad on Base mainnet. Fully open-source (Foundry contracts + frontend), no admin keys, 1% fee to creator. Deployed and verified.
- **BasePad (basepad.online)**: Virtual-liquidity bonding-curve style (pump.fun-like) with configurable tax. Claims open-source contracts built on OpenZeppelin, verified on Basescan.
- **openlaunch.lol**: Free, 0% platform fee, open-source verified contracts. One-tx token deploy + Uniswap v4 pool with liquidity locked forever (no owner/admin). Supports Base (and Robinhood Chain).
- Others: B20 Instant Launcher (GitHub contracts for instant B20 + Uniswap v4), various smaller/clone projects.

### Stocks meta notes
BasedPad is the clearest direct fit — it lets you launch tokens paired *against* real tokenized stocks on Base rather than just naming them after stocks. Solana has heavy real tokenized-stock volume (xStocks etc.), but pure open-source “stocks-meta” launchpads are less specialized than BasedPad. Most general bonding-curve/fair-launch tools work for stock-themed memes on either chain.

**Caveats**: Always verify the exact repo, license, audits, and on-chain verified source yourself. Many projects are small/unaudited; use at your own risk. Popular closed ones (Pump.fun, some Base social launchers like Zora/Clanker) dominate volume but don’t meet the open-source criterion. Check GitHub stars/activity and Basescan/Solscan verification for the latest.

================================


links and more info on basepad and openlaunch please...i need to find the best repo between the two and then improve it to now support more than base: robinhood, binance, ethereum, solana later mayve

=============================================



**Here’s the detailed breakdown with links.**

### 1. BasePad (basepad.online)
- **Website**: [https://www.basepad.online/](https://www.basepad.online/)
- **Model**: Virtual-liquidity bonding curve (pump.fun-style) on Base. Tokens launch with virtual ETH + token reserves (constant-product `x · y = k`). Configurable 0–5% tax (hard-capped, auto-routed to creator treasury). 1% protocol fee. Graduates at ~24 ETH raised → remaining tokens + ETH released to creator for DEX liquidity (Aerodrome/Uniswap v3).
- **Claims**: Open-source contracts (minimal, OpenZeppelin v5), verified on Basescan. No team allocations (100% supply starts on the curve). Sniper-resistant via virtual reserves.
- **Status**: Live on Base mainnet. FAQ notes a formal audit is recommended.
- **Repo / source**: No public full GitHub monorepo found for the complete frontend + contracts under “BasePad / basepad.online”. Contracts are claimed verified on Basescan — search the site or recent launch txs for factory addresses. (Note: there are older unrelated “BasePad” tokens and bounty projects with the same name.)

### 2. openlaunch.lol
- **Website**: [https://openlaunch.lol/](https://openlaunch.lol/)
- **Model**: One-transaction launch: deploy ERC-20 + open Uniswap v4 pool + lock **100% of supply as liquidity forever**. 0% platform fee. Creator chooses 0–3% trading fee → 100% to a named beneficiary or burned. No owner/admin keys. Liquidity position NFT sits in an ownerless locker.
- **Chains**: Already live on **Base + Robinhood Chain**.
- **Stats** (approx at time of check): ~140–175 launches, $600k+ volume, higher activity on Robinhood side in recent data.
- **Key verified contracts**:
  - Locker (same address on both chains): [0xcd1680D26922fcd9CabFbb8a56bA40C333fD842a](https://basescan.org/address/0xcd1680D26922fcd9CabFbb8a56bA40C333fD842a) (Base) / Robinhood Blockscout equivalent.
  - Site emphasizes “no fee address in the code” — verifiable on-chain.
- **Repo / source**: Site says “open source · verified contracts”. No single prominent public GitHub repo was immediately indexed under the exact name (many unrelated “OpenLaunch” projects exist for Product Hunt clones, Solana launchpads, AI tools, etc.). Source is primarily the verified on-chain contracts + the live site. Check the site’s `/rules#contracts` section for exact factory/locker addresses and verification links.

### Which is the better starting repo / base for multi-chain expansion?

**openlaunch.lol is clearly the stronger foundation for your goals.**

| Aspect                  | BasePad (basepad.online)              | openlaunch.lol                              | Winner for multi-chain |
|-------------------------|---------------------------------------|---------------------------------------------|------------------------|
| Current multi-chain     | Base only                             | Base + Robinhood already                    | openlaunch            |
| Openness / verifiability| Claims verified contracts             | Strong emphasis on 0-fee, ownerless, verified, no fee address | openlaunch            |
| Architecture            | Bonding curve + graduation            | Instant Uniswap v4 + permanent lock         | openlaunch (simpler, more portable) |
| Fee model               | Protocol takes 1% + tax to creator    | 0% platform, creator controls 0–3%          | openlaunch            |
| Stocks meta fit         | General fair launch                   | Already pairing with tokenized assets on Robinhood side | openlaunch            |
| Ease of forking/extending | Limited public full source            | Verified minimal contracts + already multi-chain | openlaunch            |

**Recommendation**: Start with **openlaunch.lol**. Its design (one-tx factory → Uniswap v4 pool + ownerless locker) is cleaner and already proves multi-chain (Base + Robinhood). Bonding-curve logic (BasePad style) is more chain-specific and harder to port cleanly.

### How to improve it for more chains (Robinhood already done, then Binance / Ethereum / Solana later)

1. **Fork / extract the verified contracts**
   Pull the factory, token, and locker source from Basescan / Robinhood explorer. They are minimal and OpenZeppelin-based → easy to audit and modify.

2. **Make it chain-agnostic**
   - Abstract the Uniswap v4 PoolManager + PositionManager addresses (they differ per chain).
   - Use a config file / constructor args for:
     - Chain ID
     - Native token / quote assets (ETH, WETH, USDG, BNB, etc.)
     - PoolManager, Permit2, etc.
   - Deploy the same bytecode (or near-identical) on each EVM chain via CREATE2 for vanity addresses if desired.

3. **Immediate next chains (EVM)**
   - **Ethereum mainnet**: Straightforward — same Uniswap v4 stack exists. Higher gas, so consider a slightly higher creator fee option or gas-optimized paths.
   - **BNB Chain (Binance)**: Uniswap v4 is rolling out / available via forks; or adapt to PancakeSwap v3/v4 style if pure v4 is limited. Same Solidity contracts work with minimal changes.
   - Robinhood is already supported — reuse that deployment pattern.

4. **Solana later**
   - Completely different runtime (no EVM). You would need a parallel implementation:
     - Use Meteora Dynamic Bonding Curve / DAMM, Raydium, or a custom Pump.fun-style program (many open-source clones exist).
     - Or keep the “instant lock 100% LP” philosophy with a Solana program that mints + seeds a Meteora/Raydium pool and burns the LP.
   - Frontend can stay unified (wagmi for EVM + Solana wallet-adapter).

5. **Practical improvement roadmap**
   - Add a multi-chain factory registry + chain selector in the UI.
   - Support more quote assets (tokenized stocks, stablecoins, native tokens).
   - Keep the 0% platform fee philosophy or make fees optional/configurable.
   - Open-source the full frontend + contracts under a clean MIT/Apache license on GitHub so others can contribute.
   - Add CREATE2 salt grinding for consistent addresses across chains.
   - Formal audit before mainnet on Ethereum/BNB.

**Bottom line**: Go with **openlaunch.lol** as the base. Its contracts are already multi-chain proven, minimal, and philosophy-aligned (free, locked, no admin). Extract the verified source, parameterize for new EVM chains first (Ethereum + BNB), then tackle Solana as a separate module.

If you want, I can help sketch the Solidity changes, frontend multi-chain setup, or search for the exact factory addresses / verified source on explorers. Just share any specific contract addresses you find on the sites.


========================================



how do people tokenise stocks, whats also a tokenized stock token is it a erc standard or what? is it transferrabel to wallets and smart contracts like any other token?


==============================================



**Tokenized stocks** (also called tokenized equities) are blockchain tokens that represent economic exposure to real publicly traded company shares (or ETFs). One token typically tracks one share (or a fraction) of stocks like Apple, Nvidia, Tesla, etc.

### How people / companies tokenize stocks

The process generally works like this:

1. **Acquisition & Custody**
   A regulated issuer (or its partner) buys the actual shares on traditional stock exchanges (NYSE/Nasdaq) through licensed brokers.
   Those shares are placed with a regulated custodian in a bankruptcy-remote structure (segregated so they can’t be mixed with the issuer’s other assets).

2. **Issuance / Minting**
   The issuer mints an equivalent number of blockchain tokens (usually 1:1).
   Example: 1 real Apple share → 1 AAPLc or AAPLx token.

3. **Trading & Settlement**
   Tokens trade 24/7 on crypto exchanges (CEX or DEX) and settle almost instantly on-chain.

4. **Corporate actions**
   Dividends, stock splits, etc. are handled by the issuer — often via a multiplier (so balances don’t need to be rewritten) or by reinvesting dividends into more shares/tokens.

5. **Redemption**
   Eligible (usually institutional) holders can redeem tokens for the underlying share value or (in some models) the actual shares. This arbitrage keeps the token price close to the real stock price.

**Three main models** exist today:

| Model | What you actually own | Backing | Examples | Typical rights |
|-------|-----------------------|---------|----------|---------------|
| **1:1 Backed Wrapper / Tracker Certificate** | Contractual claim / economic exposure | Real shares held by custodian | xStocks (Backed), most Ondo products, many others | Price exposure + dividends (often reinvested). Usually **no voting rights** |
| **Issuer-led native issuance** | Closer to actual share ownership | Shares recorded on-chain via transfer agent | Some Securitize / Figure products | Can include more shareholder rights |
| **Synthetic** | Derivative / price tracker | No real shares (or partial) | Perpetuals, pure synthetics | Pure price exposure only |

Most volume today uses the **1:1 backed wrapper** model.

### What standard is a tokenized stock token?

It is **not a special “stock token” standard** in most cases. The technical token is almost always a normal fungible token:

- **On Ethereum / Base / other EVM chains**: Standard **ERC-20** (or a lightweight extension of it).
  - Coinbase’s tokens on Base use **B20** — a Base-native extension of ERC-20 with built-in features for compliance (freeze/seize), multipliers for splits/dividends, roles, and supply controls. It remains fully ERC-20 compatible.
  - Robinhood Chain stock tokens are also described as standard ERC-20 (sometimes with ERC-8056 for scaled UI amounts).
  - Some more regulated security tokens use **ERC-1400** (or ERC-3643), which add transfer restrictions, partitions, and identity checks.

- **On Solana**: Standard **SPL Token** (or Token-2022 with extensions for metadata, transfer hooks, freeze authority, scaled UI amounts, etc.). xStocks are SPL tokens.

There is **no single universal “tokenized stock” token standard**. The legal wrapper and custody arrangement matter far more than the token standard itself.

### Are they transferable to wallets and smart contracts like any other token?

**Yes — in most current products they behave like normal tokens for secondary transfers.**

- You can send them to any compatible wallet (MetaMask, Phantom, Coinbase Wallet, hardware wallets, etc.).
- You can interact with smart contracts (approve, transfer, deposit into DEXes, lending protocols, etc.) exactly like USDC or any other ERC-20/SPL token.
- Many are deliberately designed to be DeFi-composable: usable as collateral, LP tokens, etc.

**Important caveats**:
- Some issuers retain freeze/seize/pause powers for legal/compliance reasons (court orders, sanctions, etc.).
- Primary minting/redemption is usually restricted (KYC, accredited/institutional only).
- Availability is often geo-restricted (many products exclude U.S. persons).
- You typically do **not** get full shareholder rights (voting, direct legal ownership of the share itself) with the most common wrapper models.
- The token price can trade at a small premium/discount to the real stock, especially outside market hours.

**In short**:
Technically, a tokenized stock is usually just a regular ERC-20 (or B20 extension) / SPL token that happens to be backed by (or tracks) a real share held in custody. Once issued, it moves around wallets and smart contracts like any other fungible token — that’s the whole point of putting it on-chain. The real complexity sits in the legal structure, custody, and regulatory compliance behind it, not in the token standard itself.



=========================================



Is there a platform thats doing options trading on the blockchain on any chain, and with open code also? also smart contracts.. then whats the best way to create or build such a platform that specializes in offering risk management tools for stonks or tokenized stocks in the form of call options and put options. OTC or there is some more cooler modern way thais was done before



=========================================

**Yes**, there are several platforms offering on-chain options trading (calls and puts) across different chains, and a number of them have open-source smart contracts or significant open components.

### Existing On-Chain Options Platforms (with Open Source / Smart Contracts)

Here are the most relevant ones:

| Protocol       | Chain(s)              | Style                          | Open Source?                  | Notes / Focus |
|----------------|-----------------------|--------------------------------|-------------------------------|---------------|
| **Panoptic**  | Ethereum (Uniswap v3) | Perpetual, oracle-free options | Yes (open-source)            | Built on Uniswap v3 concentrated liquidity. Instant settlement, no traditional expiry. Very composable. |
| **Derive** (formerly Lyra) | Own OP Stack L2      | CLOB + cross-margined options & perps | Core contracts public (GitHub: derivexyz) | Professional-grade, evolved from options AMM to orderbook. Strong liquidity. |
| **Aevo**      | Custom OP Stack L2   | Orderbook options + perps + OTC | Partial / settlement on-chain | High volume historically; off-chain matching + on-chain settlement. Also has strategies/vaults. |
| **Premia**    | Multi-EVM            | Peer-to-pool AMM (American-style) | Yes (GitHub: Premian-Labs/premia-contracts) | Buyers vs liquidity pools. |
| **Opyn**      | Ethereum             | Tokenized options + Squeeth   | Yes (historic Gamma protocol open) | One of the earliest. |
| **Hegic / Dopex / Rysk / Charm** | Various EVM     | Vaults / AMMs / peer-to-pool  | Many have public contracts   | Older generation; mixed activity levels. |
| **Others**    | Solana, Arbitrum, etc. | Various (binary, American, etc.) | Several smaller GitHub repos (e.g. Newton OTC-style, Pax-Options, Arbnomo binary) | Less mature or specialized. |

**Panoptic** and the older Opyn/Premia/Charm-style contracts are among the most fully open-source and composable. Derive and Aevo are more production-ready with deeper liquidity but lean toward hybrid (off-chain matching + on-chain settlement) models.

Very few (if any) currently specialize in **tokenized stocks / equities** options at scale — most focus on crypto underlyings (ETH, BTC, majors). This is still a relatively open niche.

### Best Ways to Build a Platform Specializing in Call/Put Options for Tokenized Stocks

You want risk-management tools (protective puts, covered calls, spreads, etc.) specifically for tokenized stocks (xStocks, Coinbase B20, Ondo, etc.).

**Modern “cooler” approaches (recommended over pure OTC):**

1. **Peer-to-Pool / AMM Options (easiest to bootstrap liquidity)**
   - Users buy options against a liquidity pool that underwrites them (like Premia, Hegic, early Lyra).
   - Pricing via Black-Scholes + dynamic IV or utilization-based models.
   - Pros: Instant liquidity, no need for matching counterparties.
   - Cons: LPs take inventory risk (need good hedging or risk parameters).
   - Good starting point: Fork Premia or similar open contracts and adapt pricing/oracles for equity underlyings.

2. **Orderbook / CLOB + RFQ (professional / institutional feel)**
   - On-chain or hybrid orderbook (Derive/Aevo style).
   - Support RFQ (request-for-quote) for larger/OTC-sized trades.
   - Pros: Better price discovery, portfolio margining, complex strategies.
   - Cons: Needs market makers and liquidity providers from day one.
   - Cooler modern twist: Hybrid — off-chain matching for speed + on-chain settlement + portfolio margin.

3. **Perpetual Options / Oracle-Free Models (most “crypto-native”)**
   - Panoptic-style: Options built on top of concentrated liquidity AMMs (Uniswap v3/v4 ranges). No traditional expiry.
   - Or power perpetuals / everlasting options.
   - Pros: Continuous, highly composable with DeFi, no expiry management.
   - Excellent for risk management because positions can stay open indefinitely.

4. **Structured Products / Vaults + Vanilla Options**
   - Offer ready-made risk tools (covered call vaults, put-selling strategies, collars) while also allowing vanilla call/put trading.
   - Users deposit tokenized stocks → vault sells options against them and returns yield + protection.
   - This is often the fastest path to product-market fit for “risk management tools.”

5. **True On-Chain OTC / Peer-to-Peer**
   - Customizable options (user sets strike, expiry, premium) listed on an on-chain orderbook or RFQ board (like older Newton).
   - Fully collateralized or partially collateralized with liquidation.
   - Still useful as a complement, especially for large or exotic trades on illiquid tokenized stocks.

### Recommended Architecture for a Tokenized-Stocks Options Platform

**Best practical path right now:**

- **Start with a hybrid peer-to-pool + RFQ model** on a cheap, fast chain that already has good tokenized stock liquidity (Base for Coinbase B20 stocks, Solana for xStocks, or a multi-chain approach).
- Use **open-source base**:
  - Premia / similar AMM contracts for the pool side.
  - Or Panoptic-style for perpetual options on top of existing Uniswap/Aerodrome pools of tokenized stocks.
  - Add an RFQ/OTC desk layer for bigger size.
- **Key technical pieces**:
  - Reliable oracles for the underlying tokenized stock price (Chainlink equity feeds + the token’s own multiplier for dividends/splits).
  - Robust collateral & margin system (support the tokenized stock itself + stables as collateral).
  - Cash-settled (easier) or physical settlement into the tokenized stock.
  - Portfolio margining and risk engine (Greeks, VaR, liquidation).
  - Compliance hooks if needed (transfer restrictions on the options tokens themselves).

**Cooler modern extras**:
- Perpetual options (no expiry management).
- Auto-compounding risk-management vaults (e.g., “protect my NVDA bag with puts while earning yield”).
- Composability: Let users use their option positions as collateral elsewhere or package them into structured products.
- AI/agent-friendly interfaces (RFQ via agents, automated hedging).

**OTC is still useful** as a liquidity backstop or for customized large trades, but pure OTC is less “cool” and harder to scale than AMM/orderbook hybrids. The most successful recent platforms moved from pure vaults or pure AMMs toward hybrid CLOB + RFQ + strategies.

Would you like recommendations on specific open-source repos to fork first, chain choice (Base vs Solana vs multi-chain), or a high-level smart-contract architecture outline?



=====================================



Which issuers can i build on top off?? ALSO CAN I BUILD ON THE CHEAPEST EG UNISWAP V4 LP HOOKS that are already deployed? can u provide repo and website links we can fork as base then refactor. i need a strategy too on the detailed build out and deployment and launch



======================================


**Here’s a clear, actionable answer.**

### 1. Which tokenized stock issuers can you build on top of?

These are the main ones with meaningful on-chain presence and liquidity (as of late 2026):

| Issuer              | Tokens / Brand     | Main Chains                  | Model                          | Best for building on          | Notes |
|---------------------|--------------------|------------------------------|--------------------------------|-------------------------------|-------|
| **Ondo Finance**   | Ondo Global Markets / Stocks | Ethereum, Solana, BNB, others | 1:1 backed claims             | High TVL, broad catalog      | Largest by value locked |
| **Backed Finance** | xStocks (AAPLx, NVDAx, etc.) | Solana (primary), Ethereum, multi | Tracker certificates 1:1     | Deepest secondary liquidity, DeFi-friendly | Acquired by Kraken |
| **Coinbase**       | B20 tokens (NVDAc, AAPLc, METAc, etc.) | **Base**                    | Beneficial interest in real shares | Native Base + B20 standard   | Strongest on Base, growing fast |
| **Dinari**         | dShares            | Arbitrum, Base, others       | More direct claim             | US-accessible path           | Expanding |
| **Binance**        | bStocks            | BNB Chain                    | 1:1 certificates              | High volume on BNB           | Exchange-integrated |
| **Robinhood**      | Stock Tokens       | Robinhood Chain              | Tokenized debt / exposure     | Already multi-chain friendly | Restricted rights |
| Others (smaller)   | Reality, Centrifuge, Backpack, Superstate, Securitize | Various                     | Mixed                         | Niche / experimental         | Lower liquidity |

**Practical recommendation**:
- Start on **Base** with **Coinbase B20** tokens (best native integration + growing pools on Aerodrome/Uniswap).
- Add **xStocks** (Solana or Ethereum) and **Ondo** for multi-chain reach.
Most are standard ERC-20 / SPL / B20, so they work as underlyings in options protocols as long as you have reliable price oracles (Chainlink equity feeds + any multiplier for dividends/splits).

### 2. Can you build on the cheapest option — already-deployed Uniswap v4 LP hooks?

**Yes — this is one of the smartest and cheapest paths.**

Uniswap v4’s hook system lets you attach custom logic (before/after swap, liquidity changes, etc.) to any pool. You can:
- Deploy your own hook that turns existing Uniswap v4 pools of tokenized stocks into options markets.
- Or build perpetual options / risk tools directly on top of the liquidity ranges (exactly what Panoptic does).

This is gas-efficient, leverages existing liquidity, and avoids reinventing an entire AMM.

**Key open resources**:
- Official Uniswap v4 hooks: https://github.com/Uniswap/v4-hooks-public
- Hook registry / examples: https://github.com/Uniswap/hooklist and community catalogs like https://github.com/CryptoGnome/v4hooks
- Specific options experiments: https://github.com/ivanvolov/v4-options (call/put using v4 + other hooks)

### 3. Best repos & websites to fork as a base

**Top recommendation (best fit for tokenized stocks + cheapest path):**

1. **Panoptic** (strongest starting point)
   - Website: https://panoptic.xyz/
   - Core contracts (v2, open-source): https://github.com/panoptic-labs/panoptic-v2-core
   - SDK: https://github.com/panoptic-labs/panoptic-sdk
   - Why: Perpetual, oracle-free options built directly on Uniswap v3/v4 concentrated liquidity. Perfect for turning existing tokenized-stock pools into call/put markets. Fully collateralized, composable, no traditional expiry. Already supports V4.

**Strong alternatives / complements**:
- Premia contracts: https://github.com/Premian-Labs/premia-contracts (peer-to-pool American-style options)
- Older but clean: Charm Options https://github.com/charmfinance/options-protocol or Opyn Gamma
- Uniswap v4 base + custom hooks: Official v4-hooks-public + any of the community limit-order / dynamic-fee / curve hooks

Fork **Panoptic v2-core** first — it already has the modular risk engine and V4 integrator. Then specialize the RiskEngine and factory for equity underlyings (B20 / xStocks / Ondo).

### 4. Detailed Build-Out, Deployment & Launch Strategy

**Phase 0 – Research & Setup (1–2 weeks)**
- Pick primary chain: **Base** (Coinbase B20 + cheap gas + Uniswap v4 live).
- Secondary: Solana (xStocks) or multi-EVM later.
- Audit existing pools for NVDAc, AAPLc, etc. on Base.
- Set up Foundry + viem/wagmi frontend stack.
- Legal note: Options on tokenized stocks may have securities implications depending on jurisdiction — consult counsel early (especially if offering to US persons).

**Phase 1 – Core Protocol (4–8 weeks)**
1. Fork Panoptic v2-core.
2. Adapt:
   - Factory to deploy options markets on existing Uniswap v4 pools of tokenized stocks.
   - RiskEngine parameters for equity volatility (higher than crypto in some cases, different corporate-action handling).
   - Oracles: Chainlink equity feeds + B20 multiplier reading.
   - Collateral: Accept the tokenized stock itself + USDC/ETH.
3. Add simple risk tools first: single-leg calls/puts, then covered-call vaults and protective-put strategies.
4. Write comprehensive tests (Foundry) + fuzzing for edge cases (splits, dividends, low liquidity).

**Phase 2 – Frontend & UX (parallel, 3–6 weeks)**
- Clean trading UI (position builder, Greeks, payoff diagrams).
- “Risk Management” dashboard: one-click protective puts, covered calls, collars on your stonk bag.
- Use Panoptic SDK as base and extend.

**Phase 3 – Security & Testnet (2–4 weeks)**
- Internal audit + public testnet on Base Sepolia.
- Incentivized bug bounty (Immunefi or Code4rena style).
- Formal verification on critical risk/margin math if possible.

**Phase 4 – Mainnet Deployment & Launch**
1. Deploy factory + risk engines on Base.
2. Seed initial markets on the deepest B20 pools (NVDA, AAPL, META, etc.).
3. Liquidity mining / points program for early LPs and traders.
4. Soft launch with limited strikes → full open.
5. Marketing: Target tokenized-stock holders on Base/Solana, Twitter/X, Discord, DeFi communities. Partner with launchpads or wallets that already show B20/xStocks.
6. Expand: Add more issuers, then Solana version or cross-chain messaging.

**Go-to-market tips**
- Position as “the risk layer for on-chain stocks” — protective tools first, speculation second.
- Offer both retail one-click strategies and advanced multi-leg trading.
- Keep fees low initially (or 0 for buyers) to bootstrap volume.
- Composability: Make option positions usable as collateral elsewhere.

**Cheapest path summary**:
Fork Panoptic → specialize for Uniswap v4 pools of Coinbase B20 / xStocks / Ondo → deploy on Base → launch focused risk-management products.

This leverages existing liquidity (no need to bootstrap a full orderbook from zero) and stays fully on-chain and open-source friendly.

Want me to expand any phase into a more granular task list, suggest specific contract changes, or help prioritize features for v1?


============================================



Awesome pick on Panoptic and uniswap v4 hooks. LETS dive into the Phase 1 - deeper into the actual build out details and which tools we are seeking to cover first, we can offer a variety to be rich out the gate in our tool offering...you had said::===============Phase 1 – Core Protocol (4–8 weeks)  Fork Panoptic v2-core.
Adapt:Factory to deploy options markets on existing Uniswap v4 pools of tokenized stocks.
RiskEngine parameters for equity volatility (higher than crypto in some cases, different corporate-action handling).
Oracles: Chainlink equity feeds + B20 multiplier reading.
Collateral: Accept the tokenized stock itself + USDC/ETH.Add simple risk tools first: single-leg calls/puts, then covered-call vaults and protective-put strategies.
Write comprehensive tests (Foundry) + fuzzing for edge cases (splits, dividends, low liquidity).==============i think this is my biggest work and what id like to start working on today now, give a more comprehensive and detailed startegy to document and execute covering all aspects and scopes..also does uniswap v4 hooks allow for a base sepolia testnet or we just have to go direct to main chain and maiinet?




==================================================



# stonkHedge build and Robinhood Chain testnet launch plan

**Planning baseline:** 2026-09-08
**Status:** The deployment-preparation slice is reproducible. Repository/toolchain/license baselines, 234 focused V4 tests, Multicall regressions, exact V3/V4 release-size gates, five healthy Stock Token proxies, and a reusable candidate Uniswap v4 testnet stack are captured. Core commit `f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d` includes the runtime-headroom fix and a guarded EOA direct-CREATE workflow. Fresh nonce-0 artifacts were rebuilt twice deterministically; the exact 16-contract plan passed a Robinhood-testnet Anvil-fork simulation with 16 successful receipts, final nonce `16`, 11 post-deployment wiring assertions, and the exact size gate. Robinhood faucet transactions funded both the deployer and separately controlled test actor with `0.01` test ETH and five units of each reviewed test Stock Token while both nonces remained `0`; the strict verifier passed afterward. Both actors now use separate encrypted Foundry keystores, and a file-based one-transaction operator passed unit, supplemental runtime-hash replay, negative authorization, and live read-only preflight gates. No stonkHedge contract has been deployed publicly. Broadcast remains blocked on owner review of the exact operator/artifact hashes and creation of a bound authorization manifest; execute-time strict and state checks remain automatic.
**Primary objective:** Deliver a reproducible Robinhood Chain testnet vertical slice for perpetual options and one-click equity hedging using Robinhood-provided, valueless test Stock Tokens, then harden it into a public testnet alpha.
**Primary pair for the vertical slice:** one faucet-distributed Robinhood test Stock Token / testnet WETH, selected after address and liquidity qualification. The deterministic local failure lane still uses a controllable ERC-8056 mock.
**Secondary compatibility lane:** Base Sepolia remains the B20/official test-USDC integration target; it is not the fastest route to an issuer-shaped public stock-token demo.
**Mainnet:** Explicitly out of scope until the licensing, issuer, legal, audit, economic-risk, and operational gates below are all cleared.

This section supersedes the earlier draft from line 410 onward. The material before this section is a research conversation, not an approved specification.

## 1. Verified facts and corrections to the earlier draft

### 1.1 Robinhood provides issuer-shaped test assets now

Robinhood Chain testnet is live at chain ID `46630` with public RPC `https://rpc.testnet.chain.robinhood.com`. Robinhood announced testnet-only Stock Tokens specifically for integration testing. A current RPC/explorer audit on 2026-09-08 found the following five 18-decimal test Stock Tokens deployed from one `StockFactory` proxy and sharing one verified `Stock` implementation:

| Test asset | Address |
|---|---|
| AMZN | `0x5884aD2f920c162CFBbACc88C9C51AA75eC09E02` |
| AMD | `0x71178BAc73cBeb415514eB542a8995b82669778d` |
| TSLA | `0xC9f9c86933092BbbfFF3CCb4b105A4A94bf3Bd4E` |
| PLTR | `0x1FBE1a0e43594b3455993B5dE5Fd0A7A266298d0` |
| NFLX | `0x3b8262A63d25f0477c4DDE23F83cfe22Cb768C93` |

The same testnet currently exposes test WETH at `0x33e4191705c386532ba27cBF171Db86919200B94` and a faucet-style 18-decimal test USDC at `0xbf4479C07Dc6fdc6dAa764A0ccA06969e894275F`. This USDC is **not** Circle's official Base Sepolia test USDC and must never be represented as such.

The verified test Stock implementation has the behavior stonkHedge needs to qualify: normal ERC-20 transfer/approval, ERC-8056-style current and scheduled multipliers, global/token pause, address blocking, role-gated mint/burn, and administrative burn. Testnet users obtain valueless assets through Robinhood's testnet faucet; faucet receipt addresses must be compared with the pinned table before the UI accepts them.

Sources:

- Testnet announcement: https://robinhood.com/us/en/newsroom/robinhood-chain-launches-public-testnet/
- Network/RPC documentation: https://docs.robinhood.com/chain/connecting/
- Testnet explorer: https://explorer.testnet.chain.robinhood.com/
- Verified shared Stock implementation: https://explorer.testnet.chain.robinhood.com/address/0xBd14156E05c6AF28ad39aA53a2AB8eB9CDf657DA?tab=contract
- Testnet faucet: https://faucet.testnet.chain.robinhood.com/

### 1.2 Robinhood mainnet is composable, but transferability is not universal eligibility

Robinhood Chain mainnet is live at chain ID `4663`. Robinhood's own documentation says its Stock Tokens are standard 18-decimal ERC-20s that can be held, transferred, and composed in compatible wallets and DeFi applications. The issuer is Robinhood Assets (Jersey) Limited (`RHJ`), and the tokens are debt securities providing economic exposure rather than legal or beneficial ownership of the referenced company shares.

That resolves two distinctions the earlier plan blurred:

1. **Secondary transfer/composability:** a holder can call ordinary ERC-20 operations and DeFi contracts can integrate the token, subject to the token not being paused and the sender, recipient, or spender not being blocked.
2. **Primary issuance/redemption and legal access:** only authorized, KYB-onboarded participants can mint/burn directly with RHJ, and offers, sales, or delivery remain jurisdiction-restricted. A permissionless chain does not make a regulated instrument legally available to every person.

Robinhood's canonical mainnet asset registry and `https://api.robinhood.com/rhj/assets` are address sources of truth; tickers and token names are not. Many Robinhood Chain projects create pools, vault shares, baskets, perps, or community tokens **using** RHJ Stock Tokens. They do not thereby become issuers of the underlying RHJ debt securities. Any independently issued security needs its own issuer, legal documents, custody/reserve evidence, transfer policy, oracle, and exact contract qualification.

At the 2026-09-08 planning audit, Robinhood's `/rhj/assets` API returned `194` active Stock Token/ETF deployments, all on chain `4663`. This is broad instrument issuance by RHJ, not evidence of 194 issuers. Vimen and ATLAS illustrate the application layer: they mint redeemable index/basket ERC-20s backed by deposits of existing RHJ Stock Tokens. HoodFactory illustrates another category: it launches ordinary community ERC-20s and can pair them with a Stock Token as the quote asset. Those projects issue their own basket/community tokens, not the underlying RHJ instrument.

Robinhood's current external-brand rules also require us to call its products “Stock Tokens” rather than “tokenized stocks” or “tokenized equities,” keep stonkHedge branding more prominent, and explicitly avoid suggesting endorsement. Generic architecture discussions may still describe the broader tokenized-asset category, but all public product copy must use Robinhood's approved terminology.

Sources:

- Stock Token overview and issuer disclosure: https://docs.robinhood.com/chain/stock-tokens/
- Integration and transfer model: https://docs.robinhood.com/chain/building-with-stock-tokens/
- Canonical contract registry: https://docs.robinhood.com/chain/contracts/
- Asset metadata API: https://docs.robinhood.com/chain/stock-token-apis/
- Live RHJ asset registry response: https://api.robinhood.com/rhj/assets
- Robinhood 2026 Form 10-Q issuer disclosure: https://investors.robinhood.com/static-files/8b6703a6-90f8-4697-b225-caf577e5720a
- Current ecosystem categories: https://docs.robinhood.com/chain/
- Vimen basket contracts: https://github.com/vimenprotocol/vimen
- ATLAS index protocol: https://www.atlasprotocolrh.com/
- HoodFactory launchpad contracts: https://github.com/HoodFactory/Hoodfactory
- Robinhood Chain terms and terminology: https://docs.robinhood.com/chain/terms-of-service/

### 1.3 Uniswap v4 availability changes the testnet deployment path

Uniswap's official repository records a complete v4 deployment on Robinhood Chain **mainnet**, including PoolManager `0x8366a39CC670B4001A1121B8F6A443A643e40951`. Robinhood also lists Uniswap as a public DEX. The official Uniswap deployment registry still does not contain a chain `46630` entry, so no testnet address may be labelled canonical or official from that registry alone.

The 2026-09-08 read-only qualification found an existing testnet v4 stack suitable for reuse. At block `115636679`, PoolManager `0x8366a39CC670B4001A1121B8F6A443A643e40951` had 24,009 bytes of runtime code with hash `0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626`—the exact runtime hash independently observed at Uniswap's official Robinhood mainnet PoolManager. Its owner is a testnet EOA, not the mainnet owner, and its protocol-fee controller is zero. The existing testnet PositionManager is immutably wired to that PoolManager, and the observed PositionManager, Quoter, StateView, UniversalRouter, Permit2, and WETH hashes match a public third-party reproducibility manifest pinned to Uniswap source commits.

This is **qualified candidate infrastructure**, not an official Uniswap testnet deployment or an endorsement of the third-party project. Reuse it for the first sandbox only while the checked-in verifier confirms chain ID, every runtime hash, PoolManager owner/fee-controller state, PositionManager wiring, and token health. A second contributor must review its provenance and manifest. If any check drifts or review rejects it, fall back to simulating and deploying stonkHedge-labelled test infrastructure. Reuse removes several deployment transactions and advances the sandbox clock without weakening fail-closed identity checks.

Base Sepolia still has official Uniswap v4 contracts and official Circle test USDC, so it remains a valuable second integration lane after the Robinhood Stock Token slice.

Sources:

- Uniswap Robinhood mainnet deployments: https://github.com/Uniswap/contracts/blob/main/deployments/4663.md
- Robinhood deploy guide: https://docs.robinhood.com/chain/deploy-smart-contracts/
- Base/Uniswap v4 deployments: https://developers.uniswap.org/docs/protocols/v4/deployments
- Circle test USDC addresses: https://developers.circle.com/stablecoins/usdc-contract-addresses

### 1.3.1 The Panoptic deployment path is direct CREATE, not upstream CREATE3

Panoptic's upstream release flow targets the canonical sub-zero CREATE3 deployer at `0x000000000000b361194cfe6312EE3210d53C15AA`. A fresh chain-`46630` read found no code at that address, so the upstream Safe batches cannot be replayed on Robinhood testnet. The fastest bounded route is an isolated EOA direct-CREATE sequence using the public deployer and its live nonce.

Core branch `feat/robinhood-testnet-direct-deployment` now provides an offline config/plan generator and a simulator that refuses non-loopback and non-Anvil RPCs. At commit `f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d`, the generated 16-transaction sequence passed on a fresh Anvil fork of Robinhood testnet. Every created address matched its prediction, the final nonce was `16`, the largest deployment used `10,749,128` gas under a `16,711,680` per-transaction cap, and 11 constructor-role/wiring assertions passed. The plan SHA-256 is `b1e354db53ecfd89042492a7ab18efb4dba909c31e8af67d5cff6de41579dd42`.

This is simulation evidence, not permission to broadcast. Direct CREATE makes nonce discipline critical: a mined failed deployment consumes its nonce and invalidates safe continuation. Public execution must recheck chain ID, pending nonce, predicted-address emptiness, dependency hashes, funding, and review, then send one transaction at a time and stop on the first mismatch. See `docs/deployment/2026-09-08-direct-deployment-simulation.md` and `manifests/deployments/robinhood-testnet-direct-preflight-2026-09-08.json`.

### 1.4 A Uniswap v4 hook cannot be attached after pool creation

The earlier statement that we can deploy a hook and attach it to an already-existing pool is wrong. A v4 pool is identified by its full `PoolKey`: `currency0`, `currency1`, `fee`, `tickSpacing`, and `hooks`. Changing the hook changes the pool ID. If a custom stonkHedge hook becomes necessary, we must initialize a new pool whose key contains the mined hook address and seed liquidity into that new pool.

Panoptic v2's current V4 architecture does **not** require its SFPM to be the pool's hook. `PanopticFactoryV4.deployNewPool` accepts an existing initialized `PoolKey`, checks it in PoolManager, and registers that pool with `SemiFungiblePositionManagerV4`. The upstream tests use `hooks = address(0)`. Therefore the cheapest Phase 1 route is:

1. Use the reviewed Robinhood-testnet PoolManager deployment recorded in the manifest.
2. Initialize a normal test-Stock-Token/WETH pool, initially with `hooks = address(0)`.
3. Deploy/register a Panoptic v2 stack over that pool.
4. Add a custom hook only if a separately documented requirement cannot be met by Panoptic, the guardian, SDK, or monitoring layer.

### 1.5 “Cash settlement” is not a small configuration change

Panoptic perpetual options are liquidity-range positions with streaming premia, burn/close, force-exercise, and liquidation mechanics. They are not conventional dated, cash-settled OCC-style contracts. A new expiry and cash-settlement subsystem would materially change the protocol and its security model. It is excluded from the first testnet vertical slice.

The first product should present familiar risk outcomes—protective put, covered call, collar—using Panoptic-native perpetual positions. Dated/cash-settled options become a separate future design only after market validation.

### 1.6 Chainlink is a reference/risk input, not an automatic replacement oracle

Panoptic describes itself as oracle-free because position pricing and premium accounting derive from Uniswap liquidity and internal tick observations. Robinhood documents a per-asset Chainlink feed on mainnet whose value already includes the token's corporate-action multiplier. Those feeds are valuable for:

- detecting AMM/reference-price divergence;
- monitoring feed freshness and market-session state;
- triggering or recommending conservative safe mode;
- validating corporate-action transitions; and
- frontend reference pricing.

They must not silently replace the inherited Panoptic oracle inside collateral math in Phase 1. Any such replacement would require a separate specification, manipulation/failure analysis, and full invariant review.

Testnet feed addresses must be independently verified; the mainnet guarantee must not be projected onto chain `46630`. Until an official feed exists for the chosen test asset, use a transparent test feed for mutable scenarios and read mainnet data only in non-broadcast fork tests.

### 1.7 ERC-8056 corporate actions affect risk even though raw AMM balances do not rebase

Robinhood Stock Tokens implement the same central accounting property we planned to test for B20: raw `balanceOf`, transfers, and AMM inventory remain unchanged while `uiMultiplier()` changes the share-equivalent display amount. The verified testnet implementation exposes `newUIMultiplier()` and `effectiveAt()` for scheduled changes. Base B20 remains a secondary compatibility target using related ERC-8056 semantics.

That means stonkHedge must model a dangerous transition window: the claim represented by one raw token can change at the effective timestamp, while the AMM's raw balances remain unchanged and its price moves only through trading/arbitrage. Phase 1 therefore needs:

- Robinhood test Stock Tokens for real public integration plus a controllable local mock for deterministic multiplier/admin scenarios;
- monitoring of `UIMultiplierUpdated`, pending/effective-time changes, pause, blocklist, administrative-burn, and other issuer-policy events;
- a documented pre-effective and post-effective safe-mode policy;
- tests for immediate emergency updates and scheduled updates; and
- no automatic unlock until price/oracle divergence and pool health recover.

References:

- Robinhood Stock Token integration: https://docs.robinhood.com/chain/building-with-stock-tokens/
- Standard library: https://github.com/base/base-std
- B20 overview: https://github.com/base/base-std/blob/main/docs/overview.md
- Asset/multiplier behavior: https://github.com/base/base-std/blob/main/docs/concepts/multipliers.md

### 1.8 Tokenized-stock availability is a product and compliance dependency

Robinhood now provides supported, valueless test Stock Tokens on its public testnet, so the earlier “wait for an issuer” premise is rejected. This authorizes technical integration testing only. Mainnet RHJ Stock Tokens remain regulated debt securities with jurisdiction and primary-market restrictions. Any mainnet asset must be allowlisted one contract address at a time after legal and technical qualification; ticker, name, explorer popularity, or a third-party project's claim is never sufficient identity evidence.

### 1.9 License gate: source-available does not equal unrestricted production use

The current `panoptic-v2-core` `LICENSE` is Business Source License 1.1. It points to `v2-license-grants.panoptic.eth`, sets a change date no later than 2028-03-01, and applies its terms to modifications and derivative works. Interfaces and some files have different licenses, while the SDK is MIT.

Actions allowed in this plan are limited to repository study, local development, tests, and a non-production testnet prototype, subject to final review of the live Additional Use Grant. Before branding, public production operation, monetization, or mainnet deployment:

- resolve and archive the current ENS Additional Use Grant and change-date record;
- obtain written legal interpretation or a commercial license if required;
- preserve upstream notices and per-file SPDX headers; and
- do not describe the core fork as MIT or unrestricted open source.

The Checkpoint A on-chain audit at Ethereum block `25932700` found that both exact ENS nodes named by the license—`v2-license-grants.panoptic.eth` and `v2-license-date.panoptic.eth`—have zero owner and zero resolver in the ENS registry. The `panoptic.eth` parent exists, but its configured resolver does not support ENSIP-10 wildcard resolution and contains no direct grant/date records for those child nodes. Therefore no Additional Use Grant or earlier change date is currently resolvable. The working interpretation is limited to the license text itself: local development, redistribution with notices, and a bounded valueless testnet used for testing are non-production; production operation, fees/monetization, or mainnet use remain blocked pending written licensor permission or qualified legal advice. See `docs/baseline/panoptic-license-2026-09-08.md` for reproducible evidence. This is a project gate, not legal advice.

## 2. Repositories and source-control model

The project deliberately uses three repositories so product code and upstream-derived protocol code stay reviewable.

| Purpose | GitHub repository | Local checkout | Pinned planning baseline |
|---|---|---|---|
| Product, docs, deployment manifests, later web app/indexer | https://github.com/vmbbz/stonkHedge | `C:\dev-shared\stonkHedge` | planning round 2 commit |
| Protocol fork | https://github.com/vmbbz/panoptic-v2-core | `C:\dev-shared\stonkHedge-core` | local Checkpoint B `cfaf42c29b5c59304540e2a31e24daee4d977797`, including residual reconciliation `ec3278b3871b92f7d3440cd792097c4e9d7e7cd9`, two-actor lifecycle `d90788202f622388a5bda1a9db32515662aea2af`, initial lifecycle `e6646eb6a259a6152d770090e63ec61ecc67ed09`, and standalone harness `159dabdd09a8b1168b23aa732fec9cb562a3f22b`, on direct-deployment candidate `f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d` and runtime fix `b0deb9f846dc15d890d96afdfd939c1091faeab9`, based on upstream `d65310d6cfbaadb6910fa9446cc59c6541060749` |
| SDK fork | https://github.com/vmbbz/panoptic-sdk | `C:\dev-shared\stonkHedge-sdk` | upstream `aa971d1f9ea5836546cd5266bcbfb94138ef4f57` |

Remotes in both forks:

- `upstream` → `panoptic-labs/...`, fetch only for normal work;
- `origin` → `vmbbz/...`, used for feature branches and pull requests.

Do not fork Uniswap v4, Robinhood's test token implementation, or Base's standard library unless we actually need to propose an upstream change. Pin the exact upstream dependency SHA and deployed bytecode in the product manifest. This minimizes our maintained diff and makes audits tractable.

Branch model:

- Product repo: short branches such as `docs/plan-round-2`, `feat/testnet-manifest`, and `feat/web-vertical-slice`.
- Core fork: `fix/pool-runtime-headroom` retains the pushed runtime candidate. `feat/robinhood-testnet-direct-deployment` builds on it with chain-neutral offline planning and loopback-only simulation tools at `f4abdd7...`. `feat/stock-token-compatibility-harness` adds only local test doubles, fixtures, lifecycle tests, and the loopback-Anvil verifier through `cfaf42c...`. None is an approved public deployment input until independent review is recorded.
- SDK fork: the already-created `feature/equity-options-base` from the pinned upstream `main` SHA, with chain/address data supplied by explicit deployment manifests.
- Never develop directly on fork `main`; keep it fast-forwardable from upstream.

Checkpoint A found that the public SDK repository is a source sync from Panoptic's private monorepo, not a self-contained development checkout: it declares the internal unpublished `@panoptic-eng/deployments@workspace:*`, but neither that package nor the workspace lockfile is public. Until an authorized complete workspace is available or the standalone source is repaired with parity tests, do not modify and publish an unbuildable fork. The Hour-32 product lane may consume exact public package `@panoptic-eng/sdk@1.0.49`—whose registry artifact is self-contained—and place stonkHedge-specific adapters in the product repo. Pin its registry integrity and lockfile; do not claim those adapters are upstream SDK changes.

Planning/implementation checkpoint rule:

1. Start with an issue or a plan delta that states the acceptance evidence.
2. For behavior changes, add a failing regression test before implementation.
3. Make the narrowest change that turns the focused test green.
4. Run the appropriate broader lane and `git diff --check`.
5. Commit only the repository-specific files for that checkpoint.
6. Push the feature branch and record commit SHA, tests, and any live transaction hashes in the product repo manifest.

## 3. Definition of the first running testnet vertical slice

“Running on Robinhood Chain testnet” is not satisfied by a successful deploy command. The vertical slice is complete only when all of the following evidence exists:

- The exact source SHAs and dependency SHAs are recorded.
- The public RPC returns chain ID `46630` before any broadcast.
- Deployment scripts run once in simulation mode and show the expected deployer.
- The chosen faucet-distributed Robinhood test Stock Token matches the pinned address, shared beacon/implementation, 18 decimals, multiplier interface, pause state, and expected symbol.
- A controllable local test token separately covers scheduled multiplier, pause, blocked-address, mint/burn, and administrative-burn failure paths; it is never presented as an issuer token.
- A test Stock Token / test WETH Uniswap v4 pool is initialized on the reviewed stonkHedge test PoolManager and seeded with bounded valueless liquidity.
- The unmodified or minimally changed Panoptic V4 shared stack is deployed and verified where possible.
- A Panoptic pool is registered over the exact pool key and its two CollateralTrackers are initialized.
- Two distinct test actors can deposit collateral.
- A writer and buyer can open the legs needed for a protective-put scenario.
- We can read position, premium, collateral, and solvency state through the SDK or an explicit interim script.
- The actors can settle premia and close normally.
- A controlled adverse-price scenario proves safe-mode/liquidation/force-exercise behavior without protocol insolvency.
- A deterministic local/fork multiplier scenario proves the monitor locks the market before the effective timestamp and keeps it locked through divergence. A live issuer-token multiplier test is required only if Robinhood schedules one during the test window.
- Every address and transaction hash is stored in a chain-specific manifest; no private key or secret is stored with it.
- A fresh machine can replay the read-only verification script against the manifest.

The first live UI may be a developer dashboard. It must label assets as valueless Robinhood Chain testnet tokens, show chain ID `46630`, link to the testnet explorer, distinguish stonkHedge-deployed Uniswap test infrastructure from official deployments, and never imply that the product is audited, issuer-endorsed, or production-ready.

## 4. Product scope

### 4.1 MVP testnet scope

- One qualified Robinhood test Stock Token / test WETH market.
- Panoptic-native single-leg long/short calls and puts.
- One-click strategy encoders for protective put, covered call, cash-secured put, and collar.
- Strategy preview with legs, token orientation, ticks/strikes, collateral impact, and worst-case warning.
- Manual close, premium settlement, safe-mode status, and liquidation test tooling.
- ERC-8056 multiplier/reference-price/issuer-policy monitor with an operator runbook.
- Read-only portfolio view and transaction builder; no autonomous trade execution.

### 4.2 Public alpha expansion

- Multiple qualified Robinhood test Stock Token markets, then a Base Sepolia B20 compatibility market.
- Four-leg spread/straddle/strangle/iron-condor presets after single-leg invariants pass.
- Scenario-based payoff and collateral views.
- Market registry, event indexer, and health dashboard.
- Testnet-only covered-call and cash-secured-put vault prototypes with strict caps.
- Role-separated guardian and deployer accounts.

### 4.3 Explicit non-goals for the first vertical slice

- No mainnet or real-value deployment.
- No promise of conventional expiry, European/American exercise, or cash settlement.
- No new tokenized-stock issuance.
- No cross-chain deployment or bridging.
- No portfolio margin across unrelated markets.
- No “aggressive” risk engine until conservative scenarios, fuzzing, and economic simulations are accepted.
- No custom Uniswap v4 hook unless a written requirement and threat model justify a new pool.
- No automated vault rollover, keeper custody, or agent trading.
- No issuer name/ticker allowlist without exact contract, chain, implementation, policy, multiplier, and oracle qualification.

## 5. Target architecture

```text
User / developer dashboard
          |
          v
stonkHedge SDK adapters -----> strategy encoder / transaction simulation
          |                                  |
          v                                  v
PanopticPoolV2 <----> RiskEngine <----> guardian safe-mode controls
     |       \
     |        +------> CollateralTracker(equity) + CollateralTracker(USDC)
     v
SemiFungiblePositionManagerV4
     |
     v
Reviewed testnet Uniswap v4 PoolManager ----> Stock Token/WETH PoolKey (hook fixed at creation)

Independent monitoring path:
ERC-8056 multiplier + issuer policy + qualified feed + AMM state
          |
          v
alerts / safe-mode recommendation / guardian runbook
```

The monitoring path is intentionally independent of transaction construction. A compromised UI must not be able to fabricate a healthy market signal.

## 6. Contract workstreams

### 6.1 Baseline before adaptations

First prove the pinned upstream code builds and its relevant V4 tests pass without changes. Capture:

- compiler and Foundry versions;
- submodule SHAs;
- exact test commands and counts;
- contract bytecode sizes;
- any skipped, flaky, or environment-blocked tests; and
- the upstream protocol-analysis findings that apply to our chosen code SHA.

The upstream repository contains security-analysis documents with medium-risk findings and proposed changes. Presence of those files is not proof that every finding is resolved in the pinned code. Build a finding-to-code matrix before testnet alpha and do not claim the fork is audited merely because audit files exist.

Checkpoint A established 233 focused V4 passes, zero failures, and one inherited skip at the pinned upstream commit. It also found a release-blocking bytecode problem: the upstream V4 config's Solidity `0.8.28`, optimizer-runs `399` `PanopticPoolV2` was `24,869` runtime bytes, `293` bytes over EIP-170. Optimizer-runs `1` alone produced `24,501` bytes and still missed a 256-byte safety margin by 181 bytes.

Checkpoint B resolves that measured blocker in pushed candidate `b0deb9f846dc15d890d96afdfd939c1091faeab9`. Both release configs now compile `PanopticPoolV2` with optimizer-runs `1`, and a behavior-preserving assembly implementation of the inherited `Multicall` return-data path reduces the exact linked runtime to `24,275` bytes: 301 bytes below EIP-170 and 45 bytes inside the required margin. Exact V3 and V4 size gates pass for every configured logic contract; the V4 release builder passes; 234 focused V4 tests execute successfully with zero failures; four new Multicall tests and three inherited multicall-range tests pass. One additional inherited SFPM test still contains an unconditional `vm.skip` and remains visible in source. These results make the branch a review candidate, not a deployment authorization: a second contributor must inspect the assembly, size configuration, attribution, and test sufficiency before any broadcast.

### 6.2 Test-asset strategy

Use two assets for two different jobs:

1. The public Robinhood testnet market uses an existing faucet-distributed Stock Token so the real proxy, access-control, ERC-8056, and wallet integration surfaces are exercised.
2. Local and controlled testnet failure harnesses use a stonkHedge-owned token outside the inherited Panoptic core so tests can trigger states that Robinhood's roles do not let us mutate on demand.

The controllable test asset must:

- behave as ERC-20 for PoolManager/Panoptic interactions;
- use configurable 18 decimals for simple first-pass accounting;
- expose current UI multiplier, pending multiplier, and `effectiveAt`;
- keep raw balances stable when the UI multiplier changes;
- emit implementation-matching scheduled-update events and an explicitly documented test-only cancellation path;
- support global pause, token pause, address-block, mint/burn, and administrative-burn scenarios; and
- clearly identify itself as valueless and test-only.

Prefer the verified Robinhood test implementation's interfaces for the primary lane and import `base/base-std` for the secondary B20 lane. Do not invent a third incompatible “stock token” interface. Never assume control over issuer roles in a production token.

### 6.3 Market registry and asset qualification

Avoid modifying `PanopticFactoryV4` merely to add a token whitelist. Put product curation in a separate stonkHedge registry/periphery contract unless the core itself needs an invariant. Each market record should include:

- chain ID and PoolId;
- full PoolKey, including hook address;
- raw token addresses and decimals;
- asset type and issuer;
- multiplier-interface support;
- reference-feed address/decimals/heartbeat;
- maximum reference/AMM deviation;
- market status: proposed, test, active, guarded, deprecated;
- risk-engine address and parameter-set hash; and
- evidence URI/manifest hash.

The underlying Panoptic factory can remain permissionless while the stonkHedge UI shows only qualified markets.

### 6.4 Equity risk controls

The current upstream RiskEngine hard-codes most economic parameters; only cross buffers and governance addresses are constructor inputs. Therefore “conservative” and “aggressive” variants are not two constructor presets today. The first implementation round must choose one of these approaches only after tests:

1. **Minimal-diff approach:** keep the upstream RiskEngine and deploy conservative cross buffers; add market gating and safe-mode automation in periphery/operations.
2. **Explicit variant approach:** derive a separately named `EquityRiskEngine` whose constants are changed and whose entire affected test matrix is rerun.
3. **Configurable-engine approach:** refactor constants into immutable packed parameters, accepting a larger audit surface and bytecode/deployment changes.

Default decision for the first live vertical slice: option 1. Test options 2 and 3 offline before choosing one for public alpha.

Required equity scenarios:

- normal 24/5 trading;
- after-hours/weekend pool trading while the reference market is closed;
- 5%, 10%, 25%, 50%, and 80% discontinuous gaps;
- low liquidity and one-sided liquidity;
- reference feed stale, paused, reverted, or wildly divergent;
- ERC-8056 scheduled split, reverse split, dividend adjustment, rescheduling, and emergency immediate update;
- issuer-token global/token pause, blocklist, administrative burn, and transfer failure during deposit, close, and liquidation;
- USDC pause/blacklist-style transfer failure;
- high utilization, interest-rate extremes, and liquidation cascades; and
- sequencer/RPC outage with delayed monitoring.

No numeric margin recommendation becomes a launch parameter solely from intuition. Each parameter set needs documented loss bounds, simulation data, fuzz/invariant results, and a review commit.

### 6.5 Strategy helpers

Keep helpers in SDK/periphery, not RiskEngine, unless an on-chain invariant requires otherwise.

For each preset, define token orientation, long/short direction, tick-range convention, position sizing, required approvals, and collateral source:

- Protective put: long downside convexity against an existing equity-token holding.
- Covered call: short call notional capped by deposited equity exposure.
- Cash-secured put: short put notional capped by stable collateral.
- Collar: protective put plus covered call in one atomic multi-leg position where supported.

Every helper must round-trip decode to the expected `TokenId`, reject wrong token order/pool/vegoid/tick spacing, simulate before signing, and expose the raw legs to the user.

### 6.6 Vaults

Vaults are not part of the first on-chain vertical slice. They add custody, accounting, keeper, pricing, slippage, rollover, and emergency-withdrawal risk. Prototype them only after direct strategy flows work.

The first vault prototype must have:

- immutable underlying market or a tightly governed allowlist;
- strict total-asset and per-transaction caps;
- no upgrade key owned by the deployer EOA;
- explicit manual-pause and unwind paths;
- exact accounting for pending premium and open positions;
- reentrancy and malicious-token tests;
- no auto-roll until keeper failure/replay simulations pass; and
- a separate audit scope.

## 7. Test strategy and evidence ladder

Tests progress in this order. A later layer never substitutes for an earlier one.

1. Static formatting, compiler warnings, SPDX/license, and secret scan.
2. Focused unit regression for each change.
3. Full relevant upstream deterministic tests.
4. Fuzz tests for token orientation, ticks, sizes, utilization, gaps, and multipliers.
5. Stateful invariants for solvency, shares/assets, premium conservation, and close/liquidation liveness.
6. Local Anvil V4 integration with mocks.
7. Robinhood-mainnet-fork read-only integration against canonical Stock Tokens and official Uniswap v4; never broadcast from this lane.
8. Robinhood Chain testnet simulation with the exact sender, candidate PoolManager, and manifest.
9. Bounded Robinhood Chain testnet broadcast.
10. Independent post-deploy verification from a clean process.
11. Base Sepolia B20 compatibility smoke lane after the primary public slice is reproducible.

Minimum invariants for our extensions:

- No supported action leaves an account reported solvent while liabilities exceed conservative asset value.
- Total CollateralTracker claims never exceed recoverable assets after modeled transfer failures.
- Multiplier changes never alter raw token conservation in our code.
- A guarded market cannot open or increase risk.
- A guarded market retains an unwind path where the underlying tokens permit transfer.
- Strategy encode → decode preserves pool, legs, ratios, token types, and direction.
- Registry status cannot change without the configured authority and emits complete evidence.
- Deployment replay either produces the same expected addresses or aborts before broadcast.

Every live acceptance report must distinguish:

- `PASS`: assertion executed and passed;
- `FAIL`: assertion executed and failed;
- `BLOCKED`: environment prevented execution;
- `SKIPPED`: lane intentionally not run; and
- `NOT APPLICABLE`: justified in writing.

## 8. Deployment and key-safety policy

The authorized testnet-only deployer is `0xCa60c8eF6934f8a97c6a503C4e3a46e87F5b08bD`; the same address is derived on every EVM chain. Robinhood's official faucet successfully sent the address `0.01` test ETH and `5` each of AMZN, AMD, TSLA, PLTR, and NFLX in transaction `0x4ad5005f8f19e454a2a4b0bbe111f3f5ead57a15b146023f87000b3c18e47d98`. Strict read-only verification passed afterward and pending nonce remained `0`. A separately controlled second actor, `0x04D5A0f57Cb2e110faC9703024888cd4562B6d6f`, received the same bounded faucet allocation in transaction `0xc9a5d901ddb0bd2d109fda652029550ec96b280433e9fb18e385da7c18a169b9`; its nonce also remained `0`. The deployer and second-actor funding gates are complete. Never import the deployer key into an uncontrolled browser wallet, and never substitute the actor as sender for the nonce-bound deployment plan. See `docs/deployment/2026-09-09-second-actor-funding.md`.

The same address remains funded on Base Sepolia for the secondary B20 lane. Re-check chain ID, native balance, token addresses, token balances, code hashes, and nonce immediately before every broadcast because chain state can change.

On Robinhood testnet the upstream sub-zero CREATE3 deployer is absent, so the reviewed candidate uses 16 ordinary CREATE transactions from nonce `0` through `15`. The exact plan has passed a fresh exact-sender fork simulation and post-deployment wiring checks. At public block `116025579` (`0xdcab383d68dcae824666aff3e3396206317620d54fad6c8883d3cdac17bcf550`, `2026-09-09T05:01:27Z`), the live deployer nonce remained `0`, all 16 predicted addresses were empty, and the current transaction-plan SHA-256 remained `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820`. Faucet receipts did not consume either account's nonce. These facts must still be re-read immediately before any broadcast.

This testnet fallback does not constrain mainnet. Robinhood mainnet `4663` has
the canonical Panoptic CREATE3 deployer plus canonical Safe v1.4.1 singleton,
proxy-factory, and MultiSend runtimes. On-chain Safe batching is therefore
supported. However, Panoptic's current salts embed its Ethereum 3-of-5 Safe
`0x82bf455e9ebd6a541ef10b683de1edcaf05ce7a1`, which is absent on Robinhood;
stonkHedge cannot reuse that authorization. Any future mainnet release needs
Panoptic's participation or newly mined salts bound to a separately audited
stonkHedge Safe. See
`docs/deployment/2026-09-08-faucet-and-mainnet-safe-readiness.md`.

The existing secret remains only in `C:\Users\cosyc\ClawStreet\.env`. Rules:

- Never print, paste, commit, copy, or transmit the key.
- Never add the ClawStreet `.env` as a submodule, symlink, artifact, or CI secret automatically.
- Prefer importing the key once into a password-protected Foundry keystore and use `--account`/`--sender`.
- If a one-process environment import is temporarily required, suppress command echo and delete the variable immediately after the command.
- Simulation must precede broadcast with the exact sender.
- Set explicit chain ID and RPC; abort if either is unexpected.
- Broadcast only bounded testnet transactions listed in a reviewed manifest.
- Never use this EOA as final protocol governance; public alpha uses a Safe with role separation and a guardian runbook.

The same public deployer has now been imported into the separate encrypted
Foundry keystore `stonkhedge-robinhood-deployer`; Foundry reported the exact
expected address. The distinct test actor remains in
`stonkhedge-robinhood-test-actor`. Only file existence and public account
metadata were inspected. The deployment operator must use the deployer
keystore; the actor keystore can never substitute for the nonce-bound sender.

The preferred gate remains a second contributor completing
`docs/review/2026-09-08-core-f4abdd7-and-v4-candidate.md`. On 2026-09-09, while
that contributor was unavailable, the owner explicitly chose a separate
owner/Codex clean-room reproduction for the valueless testnet path. The exact
core and evidence commits, all prescribed tests, strict live verifier, separate
critical calls, primary-source comparison, residual risks, and waiver boundary
are recorded in
`docs/review/2026-09-09-owner-clean-room-reproduction.md`. This permits fresh
offline nonce-derived artifact regeneration; it is not an independent-human
audit, mainnet approval, or broadcast authorization. The invited review remains
defence-in-depth, and its later rejection reopens the gate.

## 9. Hour-by-hour execution plan: public sandbox by Hour 32, hardened alpha by Hour 80

This is a dependency-ordered plan for one primary builder. “Hour” means one focused engineering hour, not a week estimate. The earliest public sandbox is intentionally targeted for Hour 32; Hours 33–80 deepen safety, strategy coverage, reproducibility, and user experience. If a security, license, chain-identity, or accounting gate fails, record `BLOCKED` and do not hide the failure merely to meet the clock.

Execution position on 2026-09-08: local Checkpoint B is complete at core `cfaf42c...`. Fourteen green lifecycle tests cover no-hook V4 initialization/liquidity/swaps, market wiring, two actors with matched long/short positions, premium accrual, close, withdrawal, multiplier separation, pause/block recovery, paused-liquidation failure/recovery, forced-burn observation, and bounded residual reconciliation. A clean chain-`31337` Anvil replay sent 33 sequential transactions with 33 successful receipts; the independent wrapper derived the final receipt from nonce, verified runtime/wiring/closed-position state, recomputed residuals, rejected non-loopback RPCs, and cleaned its artifacts.

Execution position on 2026-09-09: owner/Codex clean-room reproduction accepted
exact core `f4abdd7...` and the non-official V4 candidate for valueless testnet
under an explicit process waiver. Strict verification passed at block
`115884813`, with deployer nonce `0`, `0.01` ETH, and `5` of each Stock Token.
Fresh nonce-0 artifacts were then rebuilt twice deterministically and plan
`8b138a56...` passed a 16-receipt fork simulation plus 11 wiring assertions.
The separately controlled actor `0x04D5...6d6f` was subsequently created in an
external encrypted Foundry keystore and funded with `0.01` test ETH plus `5` of
each reviewed Stock Token; its receipt and live balances passed. Public
broadcast remains blocked on owner approval of the exact artifact/operator
hashes and creation of a bound authorization manifest. The operator candidate
passed 12 unit tests, a second 16-receipt runtime-hash fork replay, a
missing-authorization negative path, and a manifest-bound live index-0 dry-run.
It automatically repeats the strict verifier and state gates before signing,
sends at most one CREATE, verifies its receipt/address/runtime hash/next nonce,
and stops. No stonkHedge contract has been deployed on Robinhood testnet. See
`docs/deployment/2026-09-09-direct-deployment-operator-candidate.md`.

### Preflight and Hours 1–8: baseline, license, and Robinhood test assets

| Hour | Work | Required output/gate |
|---:|---|---|
| Preflight | Verify all three local checkouts, remotes, pinned branches, and clean status. | Repo topology matches Section 2; no unexpected files. |
| 1 | Record core, SDK, submodule, Foundry, Node, package-manager, compiler, and OS versions. | Machine-readable baseline manifest committed in the product repo. |
| 2 | Build pinned Panoptic core unchanged and capture sizes/warnings. | Build succeeds or an exact blocker is filed. |
| 3 | Run focused V4 factory, SFPM, RiskEngine, and PanopticPool tests. | Commands and pass/fail/skip counts tied to the core SHA. |
| 4 | Verify exact public SDK `1.0.49` package integrity and smoke its required exports; separately attempt the pinned source-fork install/build. | Published-package lane is reproducible; the private-workspace source blocker is explicit and no fake deployment package is introduced. |
| 5 | Resolve and archive Panoptic v2's live Additional Use Grant/change-date metadata. | Written testnet-use conclusion; public access remains gated if ambiguous. |
| 6 | Map applicable upstream security findings and the full deploy → close lifecycle. | Finding matrix plus caller/token-flow diagram. |
| 7 | Query chain `46630`; verify the five candidate Stock Tokens' code, shared implementation, roles, decimals, multiplier surface, and pause state. | Address-qualified asset report; ticker-only matches rejected. |
| 8 | Owner completes Robinhood's browser faucet flow for the deployer and a second test actor; re-read ETH and token balances without exposing keys. | At least two bounded actors can transact, or live work is `BLOCKED` while local work continues. |

**Checkpoint A:** Commit and push the reproducible baseline and asset-qualification evidence before changing protocol behavior.

### Hours 9–16: local Stock Token / Uniswap v4 / Panoptic slice

| Hour | Work | Required output/gate |
|---:|---|---|
| 9 | Specify a controllable test Stock Token matching the observed ERC-20/ERC-8056/admin surfaces. | Test matrix distinguishes exact issuer behavior from test-only extensions. |
| 10 | Write red tests, implement the minimum controllable token, and fuzz multiplier/rounding/timestamps. | Raw balance conservation and scheduled-multiplier tests pass. |
| 11 | Add global/token pause, blocklist, mint/burn, and administrative-burn lifecycle tests. | Deposit/open/close/liquidation failure semantics are explicit. |
| 12 | Deploy pinned Uniswap v4 PoolManager plus minimum local StateView/router and initialize Stock/WETH with `hooks = address(0)`. | Deterministic PoolKey, PoolId, and contract addresses recorded. |
| 13 | Seed two-sided liquidity and reconcile bidirectional swap deltas. | Pool state, balances, ticks, and allowances match expectations. |
| 14 | Deploy the unmodified shared Panoptic V4 stack and register the pool. | Factory event, RiskEngine, SFPM, and both CollateralTrackers reconcile. |
| 15 | Fund two actors, deposit collateral, open the smallest supported long/short pair, and settle premium. | Position IDs, solvency, and premium snapshots are recorded. |
| 16 | Close, withdraw, replay once from clean Anvil, and run the independent verifier. | No unexplained or above-budget residual accounting delta; unsafe replay is refused. |

**Checkpoint B:** Complete at core `cfaf42c...`: the local vertical-slice script, controllable test asset, tests, and verifier are committed and pushed. Nothing in this checkpoint is represented as issuer code or public deployment approval.

### Hours 17–24: bounded Robinhood Chain testnet deployment

| Hour | Work | Required output/gate |
|---:|---|---|
| 17 | Define chain-`46630` manifest schema and hard chain/address/code-hash gates. | Manifest includes sources, compiler, sender, external contracts, txs, and zero secrets. |
| 18 | Verify the existing candidate V4 stack against exact runtime hashes, PoolManager control state, PositionManager wiring, and source provenance; independently review the reuse decision. | Reuse is approved with explicit non-official status, or rejected with an exact mismatch. |
| 19 | If reuse is approved, skip infrastructure broadcast. If rejected, simulate and deploy only the pinned unmodified PoolManager/minimum periphery with the exact sender. | Zero transactions for approved reuse, or predicted addresses, nonce, gas budget, and reviewed stonkHedge test-infrastructure receipts. |
| 20 | Re-run the independent read-only verifier and compare runtime code, immutable wiring, constructor/control values, and ownership. | Verifier passes; explorer/provenance gaps are explicit and UI never says the candidate is official. |
| 21 | Select one faucet Stock Token based on balances and health; validate it and test WETH immediately before use. | Exact pair, token order, decimals, pause state, multiplier, and provenance pinned. |
| 22 | Freeze deployer activity; pass the strict verifier; read the live pending nonce; regenerate the Panoptic shared-stack addresses/artifacts; rerun the exact-sender fork simulation; and obtain separate broadcast approval. | Every predicted address is empty, artifacts are tied to the current nonce, and no intervening deployer transaction is permitted. |
| 23 | Deploy the Panoptic shared stack one transaction at a time against the accepted PoolManager, verifying each receipt, runtime, and immutable dependency before advancing. | All 16 expected contracts match the reviewed manifest; any mismatch stops the sequence. |
| 24 | Initialize the no-hook Stock/WETH pool, seed bounded liquidity, test both swap directions, register the Panoptic market, initialize trackers, deposit tiny collateral, and run the public verifier. | A functioning on-chain market exists; PoolId, token deltas, market wiring, and code reconcile or the UI remains blocked. |

**Checkpoint C:** Commit and push `robinhood-testnet-sandbox-0` deployment evidence. This is the first live-chain milestone, reached in hours, not weeks.

### Hours 25–32: minimum SDK, UI, and first-user sandbox

| Hour | Work | Required output/gate |
|---:|---|---|
| 25 | Document TokenId encoding and Stock/WETH orientation from code; create Solidity/published-SDK golden vectors in the product adapter. | Pool, legs, ratios, ticks, token types, and direction round-trip. |
| 26 | Add red product-adapter tests and implement protective-put and covered-call builders using exact SDK `1.0.49`; move them into the SDK fork only after its source build is reproducible. | Wrong pool/order/chain/ticks fail closed; raw legs remain visible. |
| 27 | Add transaction simulation, typed errors, deposit/open/settle/close builders, and locked-package smoke tests. | No state-changing payload is returned after a failed simulation; registry integrity remains pinned. |
| 28 | Scaffold a chain-`46630` wallet UI with explicit testnet, unaudited, non-endorsed, valueless-asset notices. | Wrong-chain wallets cannot construct or submit transactions. |
| 29 | Add manifest-driven asset/market panel with explorer links and live code/pause/multiplier checks. | Symbol never substitutes for address; stale/mismatched contracts fail closed. |
| 30 | Add deposit, protective-put, covered-call, position, settle, close, and raw-leg views. | UI output matches SDK golden vectors and surfaces simulation errors. |
| 31 | Run the complete flow with a second actor using only public instructions; document faucet and manual steps. | Independent user can reproduce or every blocker is recorded. |
| 32 | Publish the bounded sandbox and limitations page; open structured feedback intake. | Users can try the testnet flow; no audit, issuer partnership, or mainnet claim. |

**Checkpoint D:** Commit and push the SDK/UI sandbox and sanitized first-user acceptance report.

### Hours 33–40: market-health monitoring and safe mode

| Hour | Work | Required output/gate |
|---:|---|---|
| 33 | Specify AMM, multiplier, token-policy, sequencer, reference-price, and market-session health inputs. | ADR includes units, decimals, freshness, rounding, and source hierarchy. |
| 34 | Add feed tests for fresh, stale, zero, negative, revert, future timestamp, and wrong-chain data. | Every invalid feed state fails closed. |
| 35 | Implement a read-only adapter using an explicit test feed on `46630` and canonical feeds only in mainnet-fork reads. | No test feed is presented as official or used as a hidden collateral oracle. |
| 36 | Test scheduled multiplier ingestion, maturity, reschedule, immediate update, and missing-event recovery. | State reconstruction is deterministic from chain reads plus events. |
| 37 | Implement `healthy → pre-action → guarded → recovery candidate` monitor states. | Transition tests pass; guarded state blocks new/increased exposure. |
| 38 | Define deviation/gap thresholds and a two-source operator alert policy. | Runbook gives exact actor, call, preconditions, and rollback. |
| 39 | Integrate guarded status into SDK/UI simulation and retain permissible unwind paths. | Risk increase fails closed; close/withdraw behavior is tested. |
| 40 | Run gap/divergence/outage/recovery scenarios and record alert latency. | Scenario evidence meets the documented bounds; unlock remains manual. |

**Checkpoint E:** Commit the monitor, ADR, and runbook. Guardian automation remains disabled.

### Hours 41–48: solvency and hostile-token testing

| Hour | Work | Required output/gate |
|---:|---|---|
| 41 | Build deterministic 5/10/25/50/80% price-gap scenarios in both directions. | Expected solvency transitions and accepted loss bounds are written first. |
| 42 | Test extreme utilization and one-sided/near-empty liquidity. | No divide-by-zero, overflow, stuck close, or unexplained loss. |
| 43 | Test issuer global/token pause and blocked sender/recipient/spender across the full lifecycle. | Atomicity, accounting, and recovery behavior are documented. |
| 44 | Test administrative burn and quote-token transfer failures across the lifecycle. | Insolvency and denial-of-service implications are explicit. |
| 45 | Test multiplier changes before arbitrage, during divergence, and after recovery. | Guard prevents new exposure throughout the unsafe window. |
| 46 | Run stateful fuzzing across deposits, swaps, positions, settlement, close, liquidation, and token policy. | Solvency/share/premium/raw-balance invariants pass at recorded depth. |
| 47 | Run liquidation and force-exercise with adversarial actor ordering and sequencer delays. | No unexplained self-dealing or protocol-loss path. |
| 48 | Review gas/runtime bytecode against baseline and triage all findings. | Size budgets pass; every delta and unresolved risk has an owner. |

**Checkpoint F:** Commit only after the deep-risk lane is green; any unexplained accounting delta guards the public market.

### Hours 49–56: complete strategy UX and registry controls

| Hour | Work | Required output/gate |
|---:|---|---|
| 49 | Implement cash-secured-put tests/builder with explicit quote-collateral semantics. | Size and collateral previews fail closed on insufficient cover. |
| 50 | Implement collar tests and atomic multi-leg builder. | Encode/decode and leg-ratio invariants pass. |
| 51 | Add hostile-input coverage for stale registry, proxy upgrade, wrong beacon, wrong hook, decimals, and chain. | Typed errors block every mismatch. |
| 52 | Implement chain/address/code-hash-qualified market registry reads. | Tickers are display-only; registry evidence is inspectable. |
| 53 | Add scenario payoff, collateral, premium, and solvency previews. | UI states assumptions and rounding; results match SDK tests. |
| 54 | Add position history, RPC-confirmed critical state, and indexer-lag handling. | No critical action trusts indexer data alone. |
| 55 | Run SDK typecheck/lint/unit/build/package tests and UI unit/integration tests. | Exact green counts and skips captured. |
| 56 | Re-run a second independent user session across all four strategies. | Failures become release blockers or clearly disabled features. |

**Checkpoint G:** Commit and push the complete strategy round; product manifest pins exact core and SDK SHAs.

### Hours 57–64: candidate hardening and controlled upgrade

| Hour | Work | Required output/gate |
|---:|---|---|
| 57 | Remove unsafe key examples, migrate to a password-protected Foundry keystore, and run secret/history scans. | No private value in files, output, shell history instructions, or Git history. |
| 58 | Refactor all scripts around explicit chain configs and negative chain-ID/code-hash tests. | Unknown or drifted networks abort before broadcast. |
| 59 | Rehearse from fresh Anvil and a pinned read-only Robinhood mainnet fork. | Test stack reproduces; mainnet Stock/Uniswap reads match official registries. |
| 60 | Review all external addresses and bytecode against primary sources and current chain state. | Signed-off candidate manifest and risk exceptions. |
| 61 | Freeze candidate commits and rerun all release gates. | Candidate hash plus complete evidence bundle. |
| 62 | Simulate only required `sandbox-1` changes with exact sender; prefer no redeploy if immutable state is correct. | Change plan lists every transaction and rollback consequence. |
| 63 | Broadcast approved testnet-only changes and verify each receipt/state transition. | No unlisted transaction; old/new manifest relationship is explicit. |
| 64 | Publish immutable `robinhood-testnet-alpha-0` manifest and update the UI after verifier success. | Live addresses, txs, code hashes, commits, and limitations contain no secrets. |

**Checkpoint H:** Commit and push the candidate/upgrade evidence. A receipt alone is never acceptance evidence.

### Hours 65–72: live lifecycle acceptance

| Hour | Work | Required output/gate |
|---:|---|---|
| 65 | Fund/approve two bounded actors and reconcile deposits of both collateral types. | On-chain shares/assets and remaining approvals match. |
| 66 | Open the covered short leg that supplies the protective-put test. | Writer remains solvent; position evidence recorded. |
| 67 | Open the buyer's protective-put leg through the SDK/UI. | Simulation matches receipt; TokenId decodes exactly. |
| 68 | Generate controlled swaps/time progression and settle streaming premium. | Buyer/seller premium deltas reconcile within documented rounding. |
| 69 | Close normally and withdraw recoverable collateral. | End balances match lifecycle accounting. |
| 70 | Repeat with collar and one intentionally rejected unsafe strategy. | Atomic ratios pass; unsafe request fails before signature. |
| 71 | Execute a bounded adverse-price liquidation/force-exercise scenario. | Solvency transition and incentives match test expectations. |
| 72 | Execute the live guard/recovery runbook using controllable test infrastructure; on the issuer token, perform only authorized read/transfer scenarios. | Guard blocks risk and manual recovery is evidenced without pretending to control issuer roles. |

**Checkpoint I:** Commit a sanitized acceptance report with explorer links, timestamps, expected/actual state, and explicit failures.

### Hours 73–80: public-alpha UX and handoff

| Hour | Work | Required output/gate |
|---:|---|---|
| 73 | Complete desktop/mobile accessibility and transaction-state UX. | Wallet rejection, pending/failure/replacement, and guarded state are clear. |
| 74 | Add testnet faucet guidance and balance checks for every required asset. | A user cannot begin an impossible transaction. |
| 75 | Add issuer/asset explanation separating transferability, minting, redemption, and eligibility. | UI avoids “available to everyone” and false share-ownership claims. |
| 76 | Add live health dashboard for RPC, sequencer, token pause/multiplier, pool, and verifier state. | Stale/error states never render green. |
| 77 | Add support bundle export containing public addresses, tx hashes, versions, and no secrets. | A user can report a reproducible failure safely. |
| 78 | Run accessibility, mobile, hostile-wallet, RPC-outage, and stale-feed acceptance. | Results recorded with `PASS/FAIL/BLOCKED/SKIPPED`. |
| 79 | Replay from a clean checkout and new wallet using only public docs. | Reproduction time and every manual step are measured. |
| 80 | Freeze alpha-0, publish limitations/security contact, and triage the next hourly backlog. | Testnet alpha is usable; no mainnet-readiness or endorsement claim. |

**Checkpoint J:** Commit UI/docs/reproduction evidence and tag `robinhood-testnet-alpha-0` only if every Definition-of-Done item in Section 3 passes.

## 10. After Hour 80: post-alpha hourly backlog

### 10.1 Alpha hardening backlog

The Hour-32 sandbox and Hour-80 alpha are engineering proofs, not safe real-value derivatives launches. Budget the next `120–240+` focused engineering, research, review, and operations hours for:

- risk-parameter research and agent-based/economic simulations;
- deeper invariant campaigns and differential tests against upstream;
- market indexer, alerting, redundant RPCs, and operational dashboards;
- role migration to reviewed Safe/timelock/guardian arrangements;
- one capped vault prototype and keeper failure analysis;
- RHJ asset-by-asset legal/technical qualification and eligibility design for any real-value market;
- independent smart-contract and economic audits;
- bug bounty/testnet campaign;
- incident response, pause/unwind, and communication drills; and
- a new candidate freeze and full acceptance run.

### 10.2 Long-term critique and architecture challenge gates

The initial architecture is a hypothesis to test, not a commitment to preserve Panoptic, a particular chain, or every planned feature regardless of evidence. After the first-user sandbox, retain these explicit challenge tracks in the long-term plan:

- **Product/architecture fit:** benchmark Panoptic-native perpetual positions against simpler covered-strategy vaults, RFQ execution, dated options, and perpetual-futures hedges. Compare user comprehension, hedge error, capital efficiency, liquidity requirements, exit reliability, implementation risk, and licensing burden before deepening the fork.
- **Liquidity before catalogue size:** define who supplies each option side and the underlying Stock Token/WETH liquidity, what spread/depth/utilization makes a strategy usable, the finite incentive budget, manipulation cost, market-maker concentration limits, and an orderly market-deprecation path. Do not multiply assets or strategy presets while the first market is structurally illiquid.
- **Issuer and infrastructure dependency:** model proxy upgrades, blocklists, pauses, administrative burns, multiplier changes, feed outages, Stock Token redemption-policy changes, RPC/explorer/faucet instability, testnet resets, and chain discontinuation. Maintain a manifest-driven migration/unwind plan and measurable provider SLOs; composability does not remove these dependencies.
- **User evidence:** instrument the sandbox for privacy-respecting funnel metrics such as faucet completion, simulation rejection, strategy completion, close/unwind success, time-to-hedge, comprehension failures, and support incidents. Define go/no-go thresholds before adding leverage, vault custody, more chains, or autonomous actions.
- **Economic viability:** estimate deployment and verification cost, liquidity subsidies, monitoring/keeper expense, audit and legal cost, support load, fee revenue, adverse-selection loss, and tail-loss reserves. A technically working market is not automatically a sustainable product.
- **Governance and escape:** specify upgrade boundaries, immutable components, role separation, timelocks, emergency powers, public change notices, market deprecation, and user exits. A public alpha must not depend indefinitely on one deployer EOA or an undocumented manual operator.
- **Assurance depth:** add differential tests against the pinned upstream behavior, formal properties for stonkHedge-specific registry/guardian logic, independent economic review, and an external audit scope based on the actual final diff. Reusing audited dependencies does not audit their composition or our deployment.
- **Distribution and jurisdiction:** obtain qualified analysis of product classification, eligible users, interface restrictions, disclosures, sanctions/privacy obligations, issuer branding terms, and incident communications before any real-value access. Do not rely on wallet permissionlessness as a distribution policy.
- **Scope discipline:** keep the single-chain, one-market proof until reliability and user evidence justify expansion. Treat cross-chain messaging, new issuance, custom hooks, portfolio margin, automated vaults, and agent trading as separate products with their own threat models and stop/go decisions.

Each track needs an owner, measurable acceptance evidence, a review date or triggering event, and an explicit decision. An unresolved challenge remains `BLOCKED`; it must not disappear into a generic future-work list.

Mainnet requires a separate explicit authorization. Nothing in a green Robinhood testnet or Base Sepolia run authorizes movement of real funds or deployment to Robinhood chain ID `4663` or Base chain ID `8453`.

## 11. Planning-round and implementation commit cadence

At the end of each planning round:

1. Update this document's baseline date/status and decision log.
2. List assumptions promoted to decisions, rejected options, and open blockers.
3. Run Markdown/link/secret/diff checks.
4. Commit with `docs(plan): ...` in the product repo.
5. Push and record the commit SHA in the planning handoff and repository history; do not attempt an impossible self-referential SHA inside the same commit.

At the end of each implementation checkpoint:

1. Commit changes in the core or SDK fork first.
2. Push the feature branch.
3. Update the product manifest to pin those commit SHAs and evidence.
4. Commit the product manifest separately.

This keeps protocol diffs narrow and prevents a planning commit from falsely implying that contracts were built, audited, or deployed.

## 12. Decision log

| ID | Decision | Rationale | Revisit trigger |
|---|---|---|---|
| D-001 | Robinhood Chain testnet is the first public live chain; Base Sepolia is the secondary B20 lane. | Robinhood provides issuer-shaped valueless Stock Tokens and direct ecosystem relevance. | Testnet/faucet instability, license block, or an official issuer test environment with better support. |
| D-002 | Use Panoptic v2 core + SDK forks, not a new options AMM. | Shortest route to multi-leg perpetual option mechanics. | License denial, blocking core defects, or incompatible issuer-token behavior. |
| D-003 | No custom v4 hook in the first pool. | Panoptic V4 accepts an initialized PoolKey and upstream tests use a zero hook. | A written requirement cannot be met by periphery/monitoring. |
| D-004 | Use Robinhood's faucet Stock Token publicly and a separate controllable mock locally. | The issuer-shaped test asset proves real integration; the local mock gives deterministic control over multiplier and administrative failures. | Robinhood publishes a supported way for developers to trigger all failure states on its test token. |
| D-005 | Preserve Panoptic's internal price mechanics for vertical slice. | Replacing them with Chainlink changes the security model. | Separate oracle/risk specification and invariant proof accepted. |
| D-006 | Start with minimal-diff upstream RiskEngine. | Most risk parameters are compile-time constants; variants are a material fork. | Offline conservative-engine tests justify a reviewed fork. |
| D-007 | Strategy helpers live in SDK/periphery. | Better UX without enlarging core audit surface. | An enforceable on-chain invariant requires core validation. |
| D-008 | Vaults follow direct strategies. | Vault accounting/keeper/custody risk is a separate scope. | Direct live lifecycle and deep risk tests pass. |
| D-009 | Testnet evidence never implies mainnet approval. | Live chain behavior, licensing, legal eligibility, audits, and ops remain distinct gates. | Explicit mainnet planning round and authorization. |
| D-010 | Treat transferability, primary mint/redeem access, and legal eligibility as separate facts. | ERC-20 composability does not erase blocklist/pause powers or securities restrictions. | Issuer contracts and legal terms materially change. |
| D-011 | Prefer the existing chain-`46630` v4 candidate stack over a redundant deployment only while exact code hashes, ownership/control state, immutable wiring, and provenance pass the checked-in verifier and independent review. | Its PoolManager runtime exactly matches Uniswap's official Robinhood mainnet runtime and the complete testnet stack matches a source-pinned public manifest, saving several transactions; it remains non-official candidate infrastructure because Uniswap's registry has no `46630` entry. | Any runtime/control/wiring drift, reviewer rejection, or an official Uniswap `46630` registry entry triggers re-audit and re-planning. |
| D-012 | Treat Panoptic as the fastest testable architecture, not an irreversible product choice. | The alpha must validate hedge utility, user comprehension, liquidity, and licensing cost before the project deepens a protocol fork. | Hour-32/Hour-80 evidence or a blocking license/security result favors a simpler architecture. |
| D-013 | Keep expansion behind one-market evidence. | More assets, chains, vaults, and automation multiply liquidity, issuer-policy, operational, and legal failure modes. | The first market meets defined reliability, liquidity, unwind, and user-evidence thresholds. |
| D-014 | Proceed only with a bounded, valueless, non-monetized testnet under the base BUSL non-production grant. | The two ENS names referenced for extra rights are unset at the audited block, so no additional production permission can be assumed. | Licensor publishes resolvable records, provides written permission, or qualified counsel changes the interpretation. |
| D-015 | Use exact published SDK `1.0.49` plus product-local adapters for the first sandbox while retaining the SDK fork as a gated future lane. | The public source-sync fork cannot resolve its internal unpublished deployments workspace, while the public npm artifact is self-contained and has a pinned integrity hash. | An authorized complete workspace is available or the standalone fork is repaired and passes parity/build/package tests. |
| D-016 | Use core candidate `b0deb9f...` for deployment planning only after independent review; require automated 256-byte release headroom in both V3 and V4 configurations. | The candidate changes a shared assembly path and optimizer setting, so green tests and 301 bytes of measured headroom are necessary but not sufficient authorisation to broadcast. | Reviewer rejects the implementation, release sizes regress, or broader testing exposes a behavior difference. |
| D-017 | Use a 16-transaction EOA direct-CREATE plan on chain `46630`; do not pretend the absent canonical sub-zero CREATE3 deployer exists. | Exact addresses can be derived from the isolated sender's nonce, while preserving the upstream release builder's linking and constructor resolution. | The canonical deployer becomes available, the sender nonce changes, any predicted address is occupied, or reviewer rejects the direct path. |
| D-018 | Keep planning offline and simulation loopback-only; do not ship a raw-key broadcaster with the preparation checkpoint. | Separating artifact generation, exact fork proof, and signing reduces accidental public execution and gives the second contributor reviewable hashes. | Funding and both reviews pass and a separately specified, stop-on-first-failure public operator is approved. |
| D-019 | Treat independent review as a public-dependency gate, not an idle-work gate. | Local tests, fork rehearsal, adapters, UI, and monitoring do not consume public V4 state; public deployment and pool/liquidity actions do. | A reviewer finds a defect that invalidates local assumptions or the V4 candidate changes. |
| D-020 | Keep Robinhood testnet on direct CREATE, while retaining CREATE3 plus Safe batches as a separately planned mainnet option. | Chain `46630` lacks Panoptic's CREATE3 singleton; chain `4663` has it and canonical Safe runtimes, but Panoptic's salt-bound Safe is absent. | Panoptic publishes an official Robinhood release, deploys its Safe, or approves a different release process. |
| D-021 | Deploy every nonce-dependent Panoptic CREATE before any pool-initialization transaction from the same EOA. | Pool initialization would consume the deployer nonce and stale a previously generated 16-contract plan; freezing the EOA after regeneration makes the reviewed sequence reproducible. | Panoptic deployment moves to a nonce-independent mechanism or a separate operator performs initialization. |
| D-022 | Treat issuer pause and administrative burn as distinct solvency/exit hazards, not generic ERC-20 failures. | Local evidence shows owner close may succeed through internal balances during pause while withdrawal, external swaps, and liquidation fail; forced burn from PoolManager can also diverge raw reserves from cached CollateralTracker accounting. | Exact issuer behavior disproves the model or protocol-level reconciliation/guard controls are implemented and independently reviewed. |
| D-023 | Define local close acceptance as no unexplained residual above `2e12` raw units, rather than literal zero. | The matched Foundry close and clean Anvil replay expose documented rounding/fee effects: at 18 decimals the replay observed `0`/`1` AMM dust, zero credited-asset residual, and `531`/`32` PoolManager-claim deviations, all far below the `0.000002`-token test cap. | Asset decimals change, the residual scales with position size, a production risk limit is designed, or any run breaches the bound. |
| D-024 | Allow owner/Codex clean-room reproduction to replace the unavailable second-contributor gate only for offline regeneration and a valueless testnet sandbox. | Exact detached checkouts, full prescribed gates, independent live calls, and explicit residual-risk acceptance preserve useful review evidence without pretending two-human independence. | The invited reviewer rejects, any source/artifact/dependency state changes, value or production-like use is proposed, or a fresh gate fails. |
| D-025 | Use a file-based, keystore-backed operator that signs and submits exactly one nonce-bound CREATE per invocation. | Large initcode exceeds Windows command-line limits; full hash binding, exact prior runtime hashes, automatic strict/state checks, nonce-specific confirmation, and receipt reconciliation prevent an unsafe bulk or raw-key path. | Any artifact/operator hash changes, sender or nonce drifts, a runtime mismatch occurs, the RPC becomes untrusted, or a safer reviewed deployment mechanism becomes available. |

## 13. Open blockers and questions to resolve during execution

- Can the licensor or qualified counsel confirm that the planned valueless, non-monetized public sandbox remains non-production under BUSL-1.1? The current on-chain audit found no resolvable Additional Use Grant, so any production-like operation remains blocked.
- Which upstream security-analysis findings are actually fixed in `d65310d...`, and which remain design risks?
- Will the second contributor independently confirm the owner/Codex acceptance of core candidate `f4abdd7...`, including inherited runtime fix `b0deb9f...`? This is now defence-in-depth for the valueless testnet waiver, but remains mandatory for mainnet or real-value use; a rejection immediately reopens the testnet gate.
- Can the SDK source sync be made reproducible without access to Panoptic's private deployments workspace, or should stonkHedge keep all first-sandbox adapters in the product repo against pinned public SDK `1.0.49`?
- Will the second contributor independently confirm reuse of the non-official chain-`46630` V4 candidate? Owner/Codex reproduction passed on 2026-09-09 and Uniswap still had no official `46630` registry entry; a later official entry or reviewer mismatch requires re-audit.
- Which Chainlink feeds, if any, are officially supported on Robinhood testnet for the five faucet Stock Tokens? If none, the monitor uses an explicitly labelled test feed and mainnet feeds only in read-only fork tests.
- Can Base Sepolia B20 precompiles support the secondary compatibility scenarios, or should that lane remain on the reference mock?
- What is the safest unwind policy when an issuer freezes transfers while positions are open?
- Which jurisdiction, entity, and user eligibility model would apply to a later public UI? This needs qualified counsel, not a code-only answer.
- Who will hold deployer, guardian, treasurer, registry, and Safe roles for public alpha?
- What quantitative loss tolerance and liquidity assumptions define “conservative” for the first real-asset market?

These are gates, not footnotes. Any answer that changes architecture, authority, license scope, or real-asset eligibility triggers a new planning round and commit before implementation continues.
