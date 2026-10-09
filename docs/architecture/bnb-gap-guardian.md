# BNB Gap Guardian architecture

**Status:** live read-only comparison and exact-input quote vertical slice

**Network:** BNB Smart Chain (`56`)

**Execution boundary:** no wallet connection, transaction building, approval,
signing, simulation, or broadcast

Gap Guardian compares supported BSC tokenized-stock representations without
treating different issuers as interchangeable. The first accepted ticker is
NVDA because the live Binance Web3 RWA search resolves both Ondo `NVDAon` and
bStocks `NVDAB` on chain `56`.

## Data flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant A as /api/bnb/rwa
    participant W as Binance Web3 RWA API
    B->>A: GET operation=compare&q=NVDA
    A->>W: signed search
    W-->>A: BSC issuer representations
    par bounded fan-out, maximum 8 assets
      A->>W: batch token prices
      A->>W: underlying profiles
      A->>W: underlying market states
    end
    A->>A: validate chain, address, platform, schema
    A-->>B: public comparison data only
    B->>B: normalize price by token-to-share ratio
    B->>B: classify freshness, session, pause, and cross-issuer gap
    B->>A: GET operation=quote, selected token, 5.10 USDT, public receiver
    A->>W: signed exact-input aggregator quote
    W-->>A: short-lived RFQ or SWAP route metadata
    A->>A: bind chain, input, token, receiver, route IDs, best route
    A-->>B: quote metadata only; no calldata or transaction
    B->>B: independently validate identity, mode, expiry, impact, tax, route
```

The API key and HMAC secret exist only in the server environment. The browser
receives neither signing material nor authentication headers. The public route
accepts an enumerated operation, rate-limits callers, disables caching, and
maps upstream failures to redacted errors with request IDs.

## Exact-input quote model

The live quote is deliberately fixed at `5.10 USDT` (`5100000000000000000`
raw units). Binance rejected both `1 USDT` and exactly `5 USDT` with
`Minimum order amount is 5 USD`; `5.10 USDT` provides a small buffer above the
dollar-denominated floor without turning the read-only feature into an
arbitrary-notional proxy.

The selected destination must first be discovered by the RWA search on chain
`56`. The server then requires every returned route to repeat the exact input
amount, BSC USDT contract, selected RWA contract, and chain. Quote IDs must be
unique and exactly one route must be marked best. The browser repeats those
checks, restricts modes to `RFQ` or `SWAP`, and rejects responses older than a
conservative 20-second local lifetime. The public payload contains quote
metadata only. It does not expose transaction calldata and cannot call an
approval, build, simulation, signing, or broadcast endpoint.

The screen treats honeypot flags, token tax over 10%, and absolute reported
price impact over 1% as blocking evidence. Missing impact, impact above 0.5%,
missing route segments, or the final five seconds of lifetime produce a review
warning. Route count and route segments show current quote availability; they
are not represented as reserve depth, guaranteed fill, or future liquidity.

## Price model

For each representation:

```text
normalized price per share = token price / token-to-share ratio
```

For two or more issuers, the displayed gap is the symmetric difference between
the highest and lowest normalized prices:

```text
gap bps = (high - low) / ((high + low) / 2) * 10,000
```

This is an issuer-to-issuer on-chain comparison. Binance explicitly documents
its `referencePrice` as a per-share conversion derived from on-chain token
price, not an official quote from a traditional exchange. The interface repeats
that limitation and does not describe the result as an arbitrage opportunity.

## Policy order

The browser applies deterministic signals in descending severity:

1. `MARKET_PAUSED`, `MARKET_MAINTENANCE`, `ASSET_PAUSED`, `ASSET_LIMITED`, or
   `UNSUPPORTED` produces **Do not act**.
2. A token price older than 15 minutes produces **Review conditions**.
3. A non-regular, closed, or unreported underlying session produces
   **Review conditions**.
4. An issuer-normalized gap above 100 basis points produces
   **Review conditions**.
5. Otherwise the read-only signal is clear. This is not trade approval.

A closed underlying session is not mislabeled as an issuer halt: on-chain
transfers may continue, but price discovery has a different risk profile.

## Schema and identity controls

- Search terms are limited to 1-80 visible characters.
- Price requests are deduplicated and limited to 100 addresses; the comparison
  fan-out is capped at eight representations.
- Every BSC address must be a 20-byte EVM address.
- Price, profile, and market responses must repeat the searched chain, address,
  and platform. A mismatch fails the whole comparison.
- Decimal strings are parsed explicitly and timestamps must be safe integers.
- The browser independently validates the public response identity and the
  timestamp-vector length before rendering.
- No cached or invented value replaces failed live data.

## Observed production drift

On 2026-10-09, the first expanded live check found a useful documentation gap:
the bStocks NVDA market response returned `openState: true` and
`reasonCode: TRADING`, but `marketStatus: null`. It also returned null for some
market-data fields that the published schema presents as strings. The first
strict parser stopped on that response. The accepted implementation now allows
documented per-asset nullability while rendering the missing session label as
**unreported** and raising a review warning. It does not infer `regular` from
`openState`.

The first quote integration found a second live/documentation divergence.
Binance rejected exactly `5 USDT` because the endpoint enforces a `5 USD`
notional floor. At `5.10 USDT`, both accepted NVDA representations returned
`executionMode: SWAP` through `LiquidMesh`, rather than an RFQ-only response.
The implementation therefore allows only the two known modes, renders the
actual mode, and fails closed on any other value. This does not authorize a
swap: the integration still calls only the quote endpoint.

At the 2026-10-09 acceptance observation, Ondo `NVDAon` reported one route,
approximately `0.02216819 NVDAon`, `0.0009675127%` price impact, and PancakeSwap
V4 plus Uniswap V4 segments. bStocks `NVDAB` reported one route, approximately
`0.02216217 NVDAB`, `0.0008714545%` price impact, and a PancakeSwap V4 segment.
These are ephemeral observations, not reusable prices.

## Runtime surfaces

| Surface | Responsibility |
|---|---|
| `server/binanceWeb3.ts` | signing, timeouts, schema validation, identity binding, bounded aggregation |
| `api/bnb/rwa.ts` | public GET route, operation allow-list, rate limit, redacted errors |
| `src/bnb/gapGuardian.ts` | browser response validation, normalization, gap math, risk classification |
| `src/bnb/readOnlyQuote.ts` | independent quote identity, amount, route, expiry, and risk validation |
| `src/main.ts` | accessible search and comparison rendering |
| `scripts/check_bnb_rwa_api.ts` | credential-safe live acceptance evidence |
| `scripts/check_bnb_rwa_quote.ts` | metadata-only exact-input quote acceptance; no execution path |

## Next boundary

The next product gate is transaction preparation plus simulation for the exact
selected route, while remaining unable to sign or broadcast. It must prove
chain, sender, receiver, token, amount, allowance target, value, calldata,
expiry, and quote identity; it must also handle changed-wallet, changed-route,
expired-quote, simulation-revert, and excessive-approval cases. Wallet
connection and any BSC mainnet spend remain later, separately authorized gates.

## Sources

- [Binance Web3 RWA Data API](https://web3.binance.com/en/dev-docs/catalog/web3-wallet/api/rest-api/rwa-data)
- [Binance Web3 authentication](https://web3.binance.com/en/dev-docs/authentication)
- [Binance Web3 Trading API](https://web3.binance.com/en/dev-docs/catalog/web3-wallet/api/rest-api/trading-api)
- [BNB Hack: Tokenized Stocks Edition](https://www.bnbchain.org/en/hackathons/tokenized-stocks)
