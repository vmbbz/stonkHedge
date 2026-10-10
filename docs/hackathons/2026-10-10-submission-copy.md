# BNB Tokenized Stocks submission copy

This is a copy-ready worksheet, not evidence that the project form has been
submitted. The builder confirmed that the separate Developer Experience Report
was submitted on 2026-10-11. Replace every `OWNER INPUT REQUIRED` marker and
recheck all links in a signed-out browser.

## Project submission form

### Team / project name

StonkHedge Gap Guardian

### Contact email

`OWNER INPUT REQUIRED — use the same email used for registration and the DX report`

### Prize wallet or Binance UID

`OWNER INPUT REQUIRED — ERC-20-compatible address able to receive BSC tokens, or accepted Binance UID`

Do not use a Robinhood testnet-only address by accident. Verify the final
value character by character before submission.

### Telegram handle

`OWNER INPUT REQUIRED — optional`

### What did you build?

StonkHedge Gap Guardian is a BSC tokenized-stock risk and transaction-
simulation interface for people who need to understand what they are buying
before they act. It uses the Binance Web3 RWA Data API to resolve and compare
Ondo NVDAon and bStocks NVDAB, normalizes each issuer's on-chain price by its
token-to-share ratio, and surfaces freshness, underlying-market session,
reference-price, attestation, pause, and issuer-gap risk.

For either representation, the user can request one deliberately bounded
`5.10 USDT` live route through the Trading API. StonkHedge binds the quote to
BSC chain `56`, the exact tokens, amount, public receiver, vendor, approval
target, route identity, expiry, output, and a `0.5%` slippage cap. It then
compiles an exact ERC-20 approval and swap on the server and sends both
unsigned payloads to the Transaction API simulator. The browser receives only
decoded intent, selectors, SHA-256 byte fingerprints, statuses, and reasons—no
raw calldata, key, signature, or broadcast method.

The live demonstration intentionally uses an unfunded public sender: exact
approval simulation succeeds, swap simulation fails for insufficient USDT,
and the product returns `BLOCKED`. This revision is a transparent
discovery-to-simulation product, not a claim that an on-chain swap occurred.

**Binance Web3 modules used:** RWA Data API, Trading API, Transaction API.

**Tokenized-stock platforms:** Ondo and bStocks.

### Track selection

- [x] Main Track — Tokenized Stocks Products & Agents
- [ ] Best Use of Agentic Wallet / Wallet Skills
- [ ] Best Use of BNB Agent Studio

Do not select a special track merely because it is listed. This revision does
not integrate Agentic Wallet, Wallet Skills, or Agent Studio.

### Public repository URL

`https://github.com/vmbbz/stonkHedge/tree/hackathon/bnb-tokenized-stocks-2026`

### Demo video URL

`OWNER INPUT REQUIRED — public URL, final runtime <= 4:00`

### Deployed link or judge-run instructions

Preferred:

`OWNER INPUT REQUIRED — accepted public simulation-only deployment URL`

Fallback judge instructions:

`https://github.com/vmbbz/stonkHedge/blob/hackathon/bnb-tokenized-stocks-2026/docs/hackathons/2026-10-10-submission-readiness.md#judge-quickstart-boundary`

The linked Vercel project had no deployment on 2026-10-11. Use the public
judge-instruction permalink rather than a guessed Vercel alias. The quickstart
requires judge-provided Binance Web3 developer credentials, but those remain
server-side and the official form explicitly accepts runnable instructions in
place of a deployment.

### Developer Experience Report confirmation

Select exactly: `Yes, I have submitted it`.

The builder confirmed completing the official DX form on 2026-10-11. Keep the
Google Forms receipt or confirmation screenshot private unless it contains no
personal information.

## Final one-line pitch

StonkHedge turns the risky gap between 24/7 tokenized stocks and their
underlying market into an issuer-aware, live, fail-closed transaction proof.

## Short public description

Compare Ondo and bStocks representations of NVDA on BSC, understand market-
hours and issuer risk, inspect a bounded live route, and simulate the exact
approval and swap without exposing keys or opening a signing path.

## Honest limitations

- No browser wallet, signature, broadcast, transaction receipt, or post-trade
  reconciliation exists in this revision.
- The recorded sender is unfunded, so the live swap simulation is expected to
  fail and the product must return `BLOCKED`.
- Reference prices are upstream per-share conversion data, not represented as
  official exchange quotes.
- Route availability and reported impact do not guarantee reserves, fills, or
  future execution.
- Tokenized equities may have issuer, transfer, jurisdiction, and legal
  restrictions. The project is not investment advice.
