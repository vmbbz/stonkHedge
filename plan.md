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



# stonkHedge build and Base Sepolia launch plan

**Planning baseline:** 2026-09-08
**Status:** Planning round 1; implementation has not started and no stonkHedge contracts have been deployed.
**Primary objective:** Deliver a reproducible Base Sepolia vertical slice for perpetual options and one-click equity hedging, then harden it into a public testnet alpha.
**Primary pair for the vertical slice:** mock B20-style equity / official Base Sepolia USDC.
**Mainnet:** Explicitly out of scope until the licensing, issuer, legal, audit, economic-risk, and operational gates below are all cleared.

This section supersedes the earlier draft from line 410 onward. The material before this section is a research conversation, not an approved specification.

## 1. Verified facts and corrections to the earlier draft

### 1.1 Base Sepolia and canonical contracts

Base Sepolia is the right environment for the first live integration. It uses chain ID `84532` and the public RPC `https://sepolia.base.org`. The RPC is suitable for development and smoke tests, but a dedicated provider should be used for sustained indexing and CI.

Canonical Base Sepolia addresses, verified against current first-party documentation:

| Component | Address |
|---|---|
| Uniswap v4 PoolManager | `0x05E73354cFDd6745C338b50BcFDfA3Aa6fA03408` |
| Uniswap v4 PositionManager | `0x4b2c77d209d3405f41a037ec6c77f7f5b8e2ca80` |
| Uniswap v4 Universal Router | `0x492e6456d9528771018deb9e87ef7750ef184104` |
| Uniswap v4 StateView | `0x571291b572ed32ce6751a2cb2486ebee8defb9b4` |
| Uniswap v4 Quoter | `0x4A6513c898fe1B2d0E78d3b0e0A4a151589B1cBa` |
| Permit2 | `0x000000000022D473030F116dDEE9F6B43aC78BA3` |
| Circle test USDC | `0x036CbD53842c5426634e7929541eC2318f3dCF7e` |
| Base WETH9 | `0x4200000000000000000000000000000000000006` |

Sources:

- Uniswap v4 deployments: https://developers.uniswap.org/docs/protocols/v4/deployments
- Base network/RPC reference: https://docs.base.org/base-chain/api-reference/rpc-overview
- Base system-contract reference: https://docs.base.org/base-chain/network-information/base-contracts
- Circle USDC addresses: https://developers.circle.com/stablecoins/usdc-contract-addresses

### 1.2 A Uniswap v4 hook cannot be attached after pool creation

The earlier statement that we can deploy a hook and attach it to an already-existing pool is wrong. A v4 pool is identified by its full `PoolKey`: `currency0`, `currency1`, `fee`, `tickSpacing`, and `hooks`. Changing the hook changes the pool ID. If a custom stonkHedge hook becomes necessary, we must initialize a new pool whose key contains the mined hook address and seed liquidity into that new pool.

Panoptic v2's current V4 architecture does **not** require its SFPM to be the pool's hook. `PanopticFactoryV4.deployNewPool` accepts an existing initialized `PoolKey`, checks it in PoolManager, and registers that pool with `SemiFungiblePositionManagerV4`. The upstream tests use `hooks = address(0)`. Therefore the cheapest Phase 1 route is:

1. Use the canonical Uniswap v4 PoolManager.
2. Initialize a normal mock-equity/USDC pool, initially with `hooks = address(0)`.
3. Deploy/register a Panoptic v2 stack over that pool.
4. Add a custom hook only if a separately documented requirement cannot be met by Panoptic, the guardian, SDK, or monitoring layer.

### 1.3 “Cash settlement” is not a small configuration change

Panoptic perpetual options are liquidity-range positions with streaming premia, burn/close, force-exercise, and liquidation mechanics. They are not conventional dated, cash-settled OCC-style contracts. A new expiry and cash-settlement subsystem would materially change the protocol and its security model. It is excluded from the first testnet vertical slice.

The first product should present familiar risk outcomes—protective put, covered call, collar—using Panoptic-native perpetual positions. Dated/cash-settled options become a separate future design only after market validation.

### 1.4 Chainlink is a reference/risk input, not an automatic replacement oracle

Panoptic describes itself as oracle-free because position pricing and premium accounting derive from Uniswap liquidity and internal tick observations. Coinbase tokenized-equity Chainlink feeds report Total Return Value, combining equity price and the B20 multiplier. Those feeds are valuable for:

- detecting AMM/reference-price divergence;
- monitoring feed freshness and market-session state;
- triggering or recommending conservative safe mode;
- validating corporate-action transitions; and
- frontend reference pricing.

They must not silently replace the inherited Panoptic oracle inside collateral math in Phase 1. Any such replacement would require a separate specification, manipulation/failure analysis, and full invariant review.

### 1.5 B20 corporate actions affect risk even though raw AMM balances do not rebase

B20 is an ERC-20-compatible superset. The Asset variant keeps raw `balanceOf`, transfers, and AMM inventory unchanged while a UI multiplier changes the share-equivalent display value. Current Base documentation also defines scheduled multiplier updates through the ERC-8056-compatible surface.

That means stonkHedge must model a dangerous transition window: the claim represented by one raw token can change at the effective timestamp, while the AMM's raw balances remain unchanged and its price moves only through trading/arbitrage. Phase 1 therefore needs:

- a faithful mock with current and scheduled multipliers;
- monitoring of `UIMultiplierUpdated`, cancellation, pause, and issuer-policy events;
- a documented pre-effective and post-effective safe-mode policy;
- tests for immediate emergency updates and scheduled updates; and
- no automatic unlock until price/oracle divergence and pool health recover.

Base B20 references:

- Standard library: https://github.com/base/base-std
- B20 overview: https://github.com/base/base-std/blob/main/docs/overview.md
- Asset/multiplier behavior: https://github.com/base/base-std/blob/main/docs/concepts/multipliers.md

### 1.6 Tokenized-stock availability is a product and compliance dependency

Coinbase's current public material says its tokenized stocks are B20 tokens on Base, backed by underlying shares, and unavailable to US persons and other restricted jurisdictions. Testnet work must use valueless mocks until an issuer provides supported test assets and integration terms. Mainnet asset enablement must be allowlisted one contract address at a time after legal and technical qualification; tickers alone are never sufficient identifiers.

### 1.7 License gate: source-available does not equal unrestricted production use

The current `panoptic-v2-core` `LICENSE` is Business Source License 1.1. It points to `v2-license-grants.panoptic.eth`, sets a change date no later than 2028-03-01, and applies its terms to modifications and derivative works. Interfaces and some files have different licenses, while the SDK is MIT.

Actions allowed in this plan are limited to repository study, local development, tests, and a non-production testnet prototype, subject to final review of the live Additional Use Grant. Before branding, public production operation, monetization, or mainnet deployment:

- resolve and archive the current ENS Additional Use Grant and change-date record;
- obtain written legal interpretation or a commercial license if required;
- preserve upstream notices and per-file SPDX headers; and
- do not describe the core fork as MIT or unrestricted open source.

## 2. Repositories and source-control model

The project deliberately uses three repositories so product code and upstream-derived protocol code stay reviewable.

| Purpose | GitHub repository | Local checkout | Pinned planning baseline |
|---|---|---|---|
| Product, docs, deployment manifests, later web app/indexer | https://github.com/vmbbz/stonkHedge | `C:\dev-shared\stonkHedge` | planning round 1 commit |
| Protocol fork | https://github.com/vmbbz/panoptic-v2-core | `C:\dev-shared\stonkHedge-core` | upstream `d65310d6cfbaadb6910fa9446cc59c6541060749` |
| SDK fork | https://github.com/vmbbz/panoptic-sdk | `C:\dev-shared\stonkHedge-sdk` | upstream `aa971d1f9ea5836546cd5266bcbfb94138ef4f57` |

Remotes in both forks:

- `upstream` → `panoptic-labs/...`, fetch only for normal work;
- `origin` → `vmbbz/...`, used for feature branches and pull requests.

Do not fork Uniswap v4 or Base's standard library unless we actually need to propose an upstream change. Pin them as dependencies. This minimizes our maintained diff and makes audits tractable.

Branch model:

- Product repo: short branches such as `docs/plan-round-2`, `feat/testnet-manifest`, and `feat/web-vertical-slice`.
- Core fork: `feature/equity-options-base` from the pinned upstream `main` SHA.
- SDK fork: `feature/equity-options-base` from the pinned upstream `main` SHA.
- Never develop directly on fork `main`; keep it fast-forwardable from upstream.

Planning/implementation checkpoint rule:

1. Start with an issue or a plan delta that states the acceptance evidence.
2. For behavior changes, add a failing regression test before implementation.
3. Make the narrowest change that turns the focused test green.
4. Run the appropriate broader lane and `git diff --check`.
5. Commit only the repository-specific files for that checkpoint.
6. Push the feature branch and record commit SHA, tests, and any live transaction hashes in the product repo manifest.

## 3. Definition of the first running testnet vertical slice

“Running on Base Sepolia” is not satisfied by a successful deploy command. The vertical slice is complete only when all of the following evidence exists:

- The exact source SHAs and dependency SHAs are recorded.
- The public RPC returns chain ID `84532` before any broadcast.
- Deployment scripts run once in simulation mode and show the expected deployer.
- A valueless mock B20-style equity token exists with current multiplier, scheduled multiplier, pause, and policy/freeze behaviors needed by tests.
- An official test USDC / mock equity Uniswap v4 pool is initialized on the canonical PoolManager and seeded with bounded test liquidity.
- The unmodified or minimally changed Panoptic V4 shared stack is deployed and verified where possible.
- A Panoptic pool is registered over the exact pool key and its two CollateralTrackers are initialized.
- Two distinct test actors can deposit collateral.
- A writer and buyer can open the legs needed for a protective-put scenario.
- We can read position, premium, collateral, and solvency state through the SDK or an explicit interim script.
- The actors can settle premia and close normally.
- A controlled adverse-price scenario proves safe-mode/liquidation/force-exercise behavior without protocol insolvency.
- A scheduled multiplier scenario proves the monitor locks the market before the effective timestamp and keeps it locked through divergence.
- Every address and transaction hash is stored in a chain-specific manifest; no private key or secret is stored with it.
- A fresh machine can replay the read-only verification script against the manifest.

The first live UI may be a developer dashboard. It must label assets as test tokens, show Base Sepolia, link to the explorer, and never imply that the testnet product is audited or production-ready.

## 4. Product scope

### 4.1 MVP testnet scope

- One mock equity/USDC market.
- Panoptic-native single-leg long/short calls and puts.
- One-click strategy encoders for protective put, covered call, cash-secured put, and collar.
- Strategy preview with legs, token orientation, ticks/strikes, collateral impact, and worst-case warning.
- Manual close, premium settlement, safe-mode status, and liquidation test tooling.
- B20 multiplier/reference-price monitor with an operator runbook.
- Read-only portfolio view and transaction builder; no autonomous trade execution.

### 4.2 Public alpha expansion

- Multiple qualified mock-equity markets.
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
Canonical Uniswap v4 PoolManager ----> equity/USDC PoolKey (hook fixed at creation)

Independent monitoring path:
B20 multiplier + issuer policy + Chainlink TRV + AMM state
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

### 6.2 Mock equity asset

Implement the test asset outside the inherited core whenever possible. It must:

- behave as ERC-20 for PoolManager/Panoptic interactions;
- use configurable 18 decimals for simple first-pass accounting;
- expose current UI multiplier, pending multiplier, and `effectiveAt`;
- keep raw balances stable when the UI multiplier changes;
- emit canonical-style scheduled-update and cancellation events;
- support pause/freeze/policy failure scenarios; and
- clearly identify itself as valueless and test-only.

Prefer importing `base/base-std` interfaces and mocks over inventing incompatible B20 interfaces. A real B20 precompile smoke lane can be added after the mock lane is deterministic.

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
- B20 scheduled split, reverse split, dividend adjustment, cancellation, and emergency immediate update;
- B20 transfer pause/freeze/seize behavior during deposit, close, and liquidation;
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
7. Base-mainnet-fork or Base-Sepolia-fork read-only integration against canonical infrastructure.
8. Base Sepolia simulation with the exact sender and manifest.
9. Bounded Base Sepolia broadcast.
10. Independent post-deploy verification from a clean process.

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

The authorized Base Sepolia deployer is `0xCa60c8eF6934f8a97c6a503C4e3a46e87F5b08bD`. A current read-only check on 2026-09-08 confirmed chain ID `84532`, `0.026802719585322719` test ETH, and `19.9` official Base Sepolia test USDC. Re-check all three immediately before broadcast because balances and chain state can change.

The existing secret remains only in `C:\Users\cosyc\ClawStreet\.env`. Rules:

- Never print, paste, commit, copy, or transmit the key.
- Never add the ClawStreet `.env` as a submodule, symlink, artifact, or CI secret automatically.
- Prefer importing the key once into a password-protected Foundry keystore and use `--account`/`--sender`.
- If a one-process environment import is temporarily required, suppress command echo and delete the variable immediately after the command.
- Simulation must precede broadcast with the exact sender.
- Set explicit chain ID and RPC; abort if either is unexpected.
- Broadcast only bounded testnet transactions listed in a reviewed manifest.
- Never use this EOA as final protocol governance; public alpha uses a Safe with role separation and a guardian runbook.

## 9. Hour-by-hour execution plan: first 80 focused engineering hours

This is a dependency-ordered plan for one primary builder. “Hour” means one focused engineering hour; calendar time can be spread across days. If a gate fails, stop the clocked sequence, open a blocker entry, and fix or re-plan before advancing.

### Preflight and Hours 1–8: repositories, licensing, and reproducible baseline

| Hour | Work | Required output/gate |
|---:|---|---|
| Preflight | Verify all three local checkouts, remotes, default branches, and clean status. | Repo-topology record matches Section 2; no unexpected files. |
| 1 | Configure fork remotes and create `feature/equity-options-base` without modifying fork `main`. | `origin` and `upstream` verified; branch pushed. |
| 2 | Record core, SDK, submodule, Foundry, Node, npm/pnpm, and compiler versions. | Machine-readable baseline manifest committed in product repo. |
| 3 | Resolve and archive the live Panoptic v2 Additional Use Grant/change-date metadata. | License note states what testnet use is allowed and what remains counsel-gated. |
| 4 | Run secret scan and inspect all `.env.example`/deployment scripts for unsafe key use. | No secret value in Git history or working trees; remediation issues filed. |
| 5 | Build pinned Panoptic core with no source changes. | Build log, bytecode-size snapshot, and warnings recorded. |
| 6 | Run focused V4 factory and SFPM tests. | Exact commands and pass/fail counts recorded; failures become blockers. |
| 7 | Run focused RiskEngine/PanopticPool tests relevant to V4. | Baseline behavior evidence linked to SHA. |
| 8 | Install/build/test the pinned SDK without changing generated sources. | SDK baseline report; generated/untracked artifacts cleaned or ignored. |

**Checkpoint A:** Commit baseline manifest and evidence in `stonkHedge`. Do not edit protocol behavior until Checkpoint A is green.

### Hours 9–16: threat model and test asset

| Hour | Work | Required output/gate |
|---:|---|---|
| 9 | Map deploy → register pool → deposit → open → settle → close → liquidate call flows. | Contract/caller/token-flow diagram reviewed against code. |
| 10 | Map guardian, builder, treasurer, deployer, registry, and end-user authorities. | Least-privilege role matrix with testnet owners. |
| 11 | Build the upstream-audit finding matrix for the pinned core SHA. | Each relevant medium/high item marked resolved, accepted, open, or not applicable with code evidence. |
| 12 | Specify `MockB20Equity` against current Base B20/ERC-8056 interfaces. | Interface and behavioral test cases approved before implementation. |
| 13 | Write failing tests for raw/scaled balance and multiplier conversions. | Red tests prove balance invariants and rounding expectations. |
| 14 | Implement the minimal multiplier surface and scheduled activation. | Focused tests green; no AMM/core modification. |
| 15 | Add pause/freeze/policy failure modes and canonical-style events. | Red-to-green tests cover deposit, transfer, and `transferFrom` failures. |
| 16 | Add fuzz tests for multiplier values, timestamps, conversion rounding, and cancellation. | Fuzz lane passes with bounds documented. |

**Checkpoint B:** Commit mock specification, implementation, and test evidence in the correct repo. Tag it test-only and valueless.

### Hours 17–24: local Uniswap v4 and Panoptic vertical slice

| Hour | Work | Required output/gate |
|---:|---|---|
| 17 | Write local deployment config for canonical-like PoolManager, mock equity, and mock/official-interface USDC. | Config contains no secret and pins all addresses/fees/tick spacing. |
| 18 | Deploy local tokens and initialize equity/USDC PoolKey with `hooks = address(0)`. | Deterministic local transaction trace and PoolId. |
| 19 | Seed bounded two-sided liquidity and execute swaps in both directions. | StateView balances/tick and swap deltas reconcile. |
| 20 | Deploy the unmodified shared Panoptic V4 stack locally. | SFPM, guardian, builder factory, RiskEngine, references, and factory addresses recorded. |
| 21 | Register the Panoptic pool through `PanopticFactoryV4.deployNewPool`. | `PoolDeployed` event reconciles with PoolKey, RiskEngine, and trackers. |
| 22 | Fund two actors and deposit both collateral assets. | Shares/assets and allowances reconcile for both CollateralTrackers. |
| 23 | Reproduce the smallest upstream-supported short/long option flow. | Position TokenIds, sizes, collateral, and premium snapshots recorded. |
| 24 | Settle and close the positions; verify all residual balances. | No unexplained debt, shares, allowance, or stuck-token delta. |

**Checkpoint C:** Commit a reproducible local vertical-slice script plus read-only verifier. The script must be idempotent or explicitly refuse unsafe replay.

### Hours 25–32: SDK strategy primitives

| Hour | Work | Required output/gate |
|---:|---|---|
| 25 | Document TokenId leg encoding and equity/USDC token-orientation rules from code. | Golden vectors reviewed against Solidity utilities. |
| 26 | Add failing SDK tests for protective-put encoding/decoding. | Red tests cover both token orderings and invalid ticks. |
| 27 | Implement protective-put builder and simulation payload. | Golden vectors green; raw legs exposed. |
| 28 | Add covered-call tests and builder. | Notional cannot exceed declared cover in helper validation. |
| 29 | Add cash-secured-put tests and builder. | Stable collateral preview and max-size checks green. |
| 30 | Add collar tests and atomic multi-leg builder. | Encode/decode round trip and ratio validation green. |
| 31 | Add hostile-input tests: wrong chain, pool, hook, vegoid, decimals, and stale registry. | Every hostile input fails closed with typed errors. |
| 32 | Run SDK typecheck, lint, unit tests, package build, and package smoke test. | All SDK gates pass; commit SHA recorded. |

**Checkpoint D:** Commit and push SDK helper round. Product repo manifest pins the SDK feature commit.

### Hours 33–40: equity risk monitoring and safe mode

| Hour | Work | Required output/gate |
|---:|---|---|
| 33 | Specify market-health inputs, freshness rules, session states, and deviation formula. | Monitoring ADR includes decimals and rounding direction. |
| 34 | Write unit tests for Chainlink-style TRV reads: fresh, stale, negative, zero, revert, future timestamp. | Red tests cover every invalid feed state. |
| 35 | Implement read-only reference-price adapter and frontend display conversion. | Adapter never becomes hidden collateral oracle. |
| 36 | Write tests for scheduled multiplier event ingestion and effective-time transitions. | Red tests cover schedule, reschedule rejection, cancel, mature, emergency update. |
| 37 | Implement monitor state machine: healthy → pre-action → guarded → recovery candidate. | Deterministic transition tests green. |
| 38 | Define safe-mode thresholds and two-source alert policy; no automatic unlock. | Runbook gives exact actor, call, preconditions, and rollback. |
| 39 | Integrate guarded status into transaction simulation so risk-increasing actions fail closed. | Open/increase blocked; permitted unwind behavior tested. |
| 40 | Run gap/divergence/recovery scenarios and record alert latency. | Scenario report demonstrates guard before scheduled effective time. |

**Checkpoint E:** Commit monitor and runbook. Guardian automation remains disabled until reviewed separately.

### Hours 41–48: solvency, liquidation, and token-failure testing

| Hour | Work | Required output/gate |
|---:|---|---|
| 41 | Create scenario harness for 5/10/25/50/80% gaps and both price directions. | Deterministic scenario seeds and expected solvency transitions. |
| 42 | Test extreme utilization and one-sided/near-empty liquidity. | No divide-by-zero, overflow, stuck close, or unexplained loss. |
| 43 | Test equity token pause during deposit/open/settle/close/liquidation. | Failure semantics documented; recovery path proven where possible. |
| 44 | Test USDC transfer failure/blacklist-like behavior across the same lifecycle. | Atomicity and accounting invariants hold. |
| 45 | Test multiplier transition before arbitrage, during divergence, and after recovery. | Guarded state prevents new exposure throughout unsafe window. |
| 46 | Run stateful fuzzing across deposits, positions, swaps, settlements, and multiplier actions. | Solvency/share/premium invariants pass at agreed run depth. |
| 47 | Run liquidation and force-exercise multi-actor tests with adversarial ordering. | No profitable self-dealing or protocol-loss path beyond accepted bounds. |
| 48 | Review gas and runtime bytecode changes against baseline. | Regressions explained; EIP-170 and deployment budgets pass. |

**Checkpoint F:** Commit only after the deep risk lane is green. Any unexplained accounting delta blocks live deployment.

### Hours 49–56: deployment hardening and fork rehearsal

| Hour | Work | Required output/gate |
|---:|---|---|
| 49 | Define Base Sepolia deployment manifest schema and address-derivation checks. | JSON schema includes source, compiler, config, sender, chain, contracts, txs. |
| 50 | Refactor test deployment scripts to accept explicit chain config and reject unknown chain IDs. | Negative-chain tests green. |
| 51 | Remove direct private-key CLI examples from stonkHedge runbooks; add keystore flow. | Secret scan green and command history cannot expose key. |
| 52 | Rehearse full deployment on fresh Anvil with exact script entrypoints. | One-command deploy plus independent verify succeeds. |
| 53 | Rehearse on an Anvil fork of Base Sepolia canonical contracts. | Canonical PoolManager/StateView calls succeed at pinned block. |
| 54 | Simulate deployment with the real Base Sepolia sender and no broadcast. | Predicted addresses, gas, nonce, and balance budget captured. |
| 55 | Review manifest line by line; compare every external address to first-party sources. | Two-person review preferred; otherwise explicit self-review checklist. |
| 56 | Freeze the candidate commits/config and rerun all release gates. | Candidate manifest hash and green evidence bundle. |

**Checkpoint G:** Commit the deployment candidate. No source changes after this checkpoint without invalidating the candidate and repeating Hours 54–56.

### Hours 57–64: bounded Base Sepolia deployment

| Hour | Work | Required output/gate |
|---:|---|---|
| 57 | Re-check chain ID, deployer derivation, nonce, ETH, official test USDC, and RPC health. | All values match the reviewed manifest/budget; key is never printed. |
| 58 | Deploy mock equity and verify interface/event behavior on-chain. | Receipt successful; read-only verifier passes; test-only label published. |
| 59 | Initialize the exact equity/USDC V4 pool and capture PoolId. | PoolKey/PoolId independently recomputed and StateView returns initialized state. |
| 60 | Seed bounded liquidity and execute minimum bidirectional swaps. | Receipts and pool deltas reconcile; no excessive approvals remain. |
| 61 | Deploy shared Panoptic V4 contracts in reviewed order. | Code exists at predicted addresses; constructor/immutable values verified. |
| 62 | Deploy/register the Panoptic market and initialize CollateralTrackers. | `PoolDeployed` event and all getters match manifest. |
| 63 | Verify contracts on explorer where supported and run independent read-only verification. | Source/compiler/constructor metadata linked; unresolved verification noted. |
| 64 | Publish the deployment manifest and freeze it as `base-sepolia-alpha-0`. | Manifest contains every tx/address/commit and zero secrets. |

**Checkpoint H:** Commit and push the live manifest. A receipt alone is insufficient; the read-only verifier must pass.

### Hours 65–72: live lifecycle acceptance

| Hour | Work | Required output/gate |
|---:|---|---|
| 65 | Fund/approve two bounded test actors and deposit both collateral types. | On-chain shares/assets reconcile. |
| 66 | Open the covered short leg needed to supply the test protective put. | Writer remains solvent; position evidence recorded. |
| 67 | Open the buyer protective-put leg through the SDK builder. | Simulation matched receipt; TokenId decodes exactly. |
| 68 | Generate controlled swaps/time progression and settle streaming premium. | Buyer/seller premium deltas reconcile within documented rounding. |
| 69 | Close the normal position path and withdraw recoverable collateral. | End balances match expected lifecycle accounting. |
| 70 | Repeat with collar multi-leg flow. | Atomic leg ratios and close path pass. |
| 71 | Execute controlled adverse-price/liquidation or force-exercise scenario. | Solvency transition and incentive accounting match tests. |
| 72 | Schedule a multiplier change and execute the live guard/recovery runbook. | Market blocks new risk before effective time; no automatic unlock. |

**Checkpoint I:** Commit a sanitized acceptance report with explorer links, timestamps, expected/actual state, and explicit failures or gaps.

### Hours 73–80: developer UI and handoff

| Hour | Work | Required output/gate |
|---:|---|---|
| 73 | Scaffold Base-Sepolia-only developer UI with wallet connection and chain lock. | Wrong-chain state cannot build or submit transactions. |
| 74 | Add market/asset panel sourced from the deployment manifest and live reads. | Addresses, test labels, pool health, and explorer links render correctly. |
| 75 | Add strategy selector and raw-leg preview for four MVP presets. | Preview matches SDK golden vectors. |
| 76 | Add collateral/premium/solvency preview with simulation errors surfaced. | No transaction can bypass preflight simulation in the UI. |
| 77 | Add position list, settle, close, and guarded-market status. | Read model handles indexer lag by confirming critical state via RPC. |
| 78 | Run desktop/mobile accessibility and failure-state pass. | Wallet rejection, RPC outage, stale feed, and guarded market are clear. |
| 79 | Replay the complete vertical slice from a clean checkout using public docs. | Reproduction report lists exact setup time and any manual steps. |
| 80 | Freeze alpha-0, publish limitations, and triage the next risk/UX backlog. | Testnet demo is running; no mainnet-readiness claim. |

**Checkpoint J:** Commit UI/docs/reproduction evidence and tag the product repo `base-sepolia-alpha-0` only if every Definition-of-Done item in Section 3 passes.

## 10. After Hour 80: public testnet alpha roadmap

The 80-hour vertical slice is an engineering proof, not a safe public derivatives launch. Estimate another 6–10+ focused weeks for:

- risk-parameter research and agent-based/economic simulations;
- deeper invariant campaigns and differential tests against upstream;
- market indexer, alerting, redundant RPCs, and operational dashboards;
- role migration to reviewed Safe/timelock/guardian arrangements;
- one capped vault prototype and keeper failure analysis;
- issuer and legal qualification for any real tokenized equity;
- independent smart-contract and economic audits;
- bug bounty/testnet campaign;
- incident response, pause/unwind, and communication drills; and
- a new candidate freeze and full acceptance run.

Mainnet requires a separate explicit authorization. Nothing in a green Base Sepolia run authorizes movement of real funds or deployment to chain ID `8453`.

## 11. Planning-round and implementation commit cadence

At the end of each planning round:

1. Update this document's baseline date/status and decision log.
2. List assumptions promoted to decisions, rejected options, and open blockers.
3. Run Markdown/link/secret/diff checks.
4. Commit with `docs(plan): ...` in the product repo.
5. Push and record the commit SHA here.

At the end of each implementation checkpoint:

1. Commit changes in the core or SDK fork first.
2. Push the feature branch.
3. Update the product manifest to pin those commit SHAs and evidence.
4. Commit the product manifest separately.

This keeps protocol diffs narrow and prevents a planning commit from falsely implying that contracts were built, audited, or deployed.

## 12. Decision log

| ID | Decision | Rationale | Revisit trigger |
|---|---|---|---|
| D-001 | Base Sepolia is the first live chain. | Canonical v4 contracts exist; cheap valueless testing. | Canonical deployment changes or chain instability. |
| D-002 | Use Panoptic v2 core + SDK forks, not a new options AMM. | Shortest route to multi-leg perpetual option mechanics. | License denial, blocking core defects, or incompatible B20 behavior. |
| D-003 | No custom v4 hook in the first pool. | Panoptic V4 accepts an initialized PoolKey and upstream tests use a zero hook. | A written requirement cannot be met by periphery/monitoring. |
| D-004 | Use a faithful mock equity before a real issuer token. | Deterministic corporate-action/failure tests and no eligibility dependency. | Issuer offers supported test asset and integration terms. |
| D-005 | Preserve Panoptic's internal price mechanics for vertical slice. | Replacing them with Chainlink changes the security model. | Separate oracle/risk specification and invariant proof accepted. |
| D-006 | Start with minimal-diff upstream RiskEngine. | Most risk parameters are compile-time constants; variants are a material fork. | Offline conservative-engine tests justify a reviewed fork. |
| D-007 | Strategy helpers live in SDK/periphery. | Better UX without enlarging core audit surface. | An enforceable on-chain invariant requires core validation. |
| D-008 | Vaults follow direct strategies. | Vault accounting/keeper/custody risk is a separate scope. | Direct live lifecycle and deep risk tests pass. |
| D-009 | Testnet evidence never implies mainnet approval. | Live chain behavior, licensing, legal eligibility, audits, and ops remain distinct gates. | Explicit mainnet planning round and authorization. |

## 13. Open blockers and questions to resolve during execution

- What exactly does the live Panoptic v2 Additional Use Grant permit for a publicly accessible Base Sepolia derivative work?
- Which upstream security-analysis findings are actually fixed in `d65310d...`, and which remain design risks?
- Does the current Panoptic V4 deployment script compile and fit Base limits unchanged with the pinned Foundry version?
- Which Chainlink Coinbase tokenized-equity feeds exist on Base Sepolia, if any? If none, the monitor uses mocks on testnet and real feed interfaces only in fork tests.
- Can current Base Sepolia B20 precompiles support the exact corporate-action behaviors needed, or should alpha remain on the reference mock?
- What is the safest unwind policy when an issuer freezes transfers while positions are open?
- Which jurisdiction, entity, and user eligibility model would apply to a later public UI? This needs qualified counsel, not a code-only answer.
- Who will hold deployer, guardian, treasurer, registry, and Safe roles for public alpha?
- What quantitative loss tolerance and liquidity assumptions define “conservative” for the first real-asset market?

These are gates, not footnotes. Any answer that changes architecture, authority, license scope, or real-asset eligibility triggers a new planning round and commit before implementation continues.
