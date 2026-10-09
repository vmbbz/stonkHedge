# Binance Web3 integration experience log

This is the contemporaneous source record for the hackathon Developer
Experience Report. It records observed work and must not be padded with
invented calls, latency, errors, or opinions. The final report must be reviewed
and edited by the builders because the event explicitly rejects perfunctory or
AI-generated reports.

## 2026-10-09: onboarding and documentation pass

### Observed

- The project owner registered for the event, confirmed an allowed
  jurisdiction, created a Binance Web3 developer account, and obtained an API
  key.
- The documentation makes clear that authenticated calls also require a
  separately protected Secret Key for HMAC-SHA256 signing.
- Authentication depends on an easy-to-miss path rule: `/build` must appear in
  both the request URL and the raw path included in the signature.
- The API documentation warns that omitting `/build` is the leading cause of
  error `40102 Invalid signature`.
- The RWA platform and search endpoints are signed read operations. Search can
  resolve a ticker, company name, or contract address and return representations
  across multiple chains and issuers.
- The event requires BSC mainnet for the tokenized-stock demonstration. BSC
  testnet faucet assets can test generic wallet plumbing but cannot satisfy the
  final proof. The event says teams fund their own mainnet wallets and that a
  few dollars is sufficient.

### Engineering response

- Added a server-only HMAC client; no credential uses a `VITE_` prefix or enters
  the browser bundle.
- Preserved raw query ordering and `%20` encoding rather than relying on a
  helper that may encode spaces as `+`.
- Added a unique anti-replay nonce, five-second receive window, eight-second
  request timeout, strict response validation, and redacted public errors.
- Added a read-only verifier that reports platforms and BSC ticker matches but
  has no wallet, signing, or broadcast capability.

### Still to observe

- exact permission errors, if any;
- transaction-build and simulation behavior;
- support response quality if the integration blocks; and
- Agentic Wallet installation and execution experience.

## 2026-10-09: first authenticated acceptance

### Observed

- The first server-only `NVDA` check passed at `2026-10-09T12:58:51Z` in
  `2,902 ms`. It returned 459 Ondo tickers with 458 BSC tokens and 91 bStocks
  tickers with 91 BSC tokens.
- Search resolved two chain-56 representations: Ondo `NVDAon` at
  `0xa9ee28c80f960b889dfbd1902055218cba016f75` and bStocks `NVDAB` at
  `0x02fca66c1d1afb4e2a7884261eb00f63598a7436`.
- The expanded platform, search, price, profile, and market check passed in
  `3,437 ms`. At that observation, Ondo reported token-to-share ratio
  `1.0017152487959898`, a `regular` market status, and daily plus monthly
  attestation-report support. bStocks reported ratio
  `1.000778223752807865` and collateral-report support.
- The production bStocks response returned `openState: true`,
  `reasonCode: TRADING`, and `marketStatus: null`. Several market-data fields
  were also null even though the published response table presents them as
  strings. The strict first parser rejected this as an invalid status.
- A final repeat including independent browser-shape validation completed in
  `7,570 ms`. It measured a `0.2693 bps` issuer-normalized gap: Ondo received a
  clear read-only signal, while bStocks received a review warning solely
  because its session label was unreported.
- Direct invocation of the public comparison route returned HTTP `200`, chain
  `56`, both symbols, a request ID, `Cache-Control: private, no-store`, and the
  explicit `READ_ONLY_NO_WALLET_NO_SIGNING_NO_BROADCAST` boundary.

### Engineering response

- Kept exact chain/address/platform identity binding and strict parsing, but
  accepted observed per-platform nullability for the session label and
  variable market-data fields.
- Did not infer `regular` from `openState`. The interface labels the bStocks
  session as unreported and emits a review warning.
- Added a bounded comparison aggregator: one search, one batch price request,
  then parallel profile and market calls for no more than eight BSC assets.
- Added independent browser response validation, token-to-share normalization,
  symmetric cross-issuer gap calculation, freshness/session/pause policy, and
  an honest no-cached-value error state.
- The acceptance script remains read-only and prints only public RWA data. No
  authentication header, wallet, private key, signature, or transaction is
  produced.

## 2026-10-09: exact-input quote acceptance

### Observed

- The generic Trading API quote requires a public receiver for tokenized-stock
  routes, even though the call itself is read-only. StonkHedge used the existing
  public unprivileged test-buyer address; no key was loaded or connected.
- A `1 USDT` exact-input request was rejected with `Minimum order amount is 5
  USD`. Exactly `5 USDT` was rejected with the same response, demonstrating
  that the threshold is USD notional rather than a raw stablecoin quantity.
- A `5.10 USDT` request cleared the live floor. The Ondo `NVDAon` acceptance
  completed in `2,795 ms` and returned one best route from `LiquidMesh`,
  approximately `0.02216819 NVDAon`, reported price impact
  `0.0009675127%`, and PancakeSwap V4 plus Uniswap V4 route segments.
- The same bounded check for bStocks `NVDAB` completed in `1,845 ms` and
  returned one best `LiquidMesh` route, approximately `0.02216217 NVDAB`,
  reported price impact `0.0008714545%`, and a PancakeSwap V4 segment.
- Both responses used `executionMode: SWAP`. This differs from the RFQ-only
  expectation formed from the Trading API documentation. The output was still
  quote metadata only; no approval payload, swap calldata, signature, or
  transaction was requested or produced.
- Binance quote timestamps were given a shorter local 20-second lifetime. Both
  accepted routes passed independent browser-shape validation with roughly 15
  seconds remaining after the complete search-plus-quote round trip.
- The first end-to-end public-handler check hit an upstream timeout and returned
  a redacted HTTP `504` with a request ID and `Cache-Control: private,
  no-store`. One bounded retry returned HTTP `200`, chain `56`, one `SWAP`
  route, the explicit read-only boundary, and the same no-store policy. This is
  useful evidence that transient upstream latency must remain visible rather
  than being replaced with cached or invented quote data.

### Engineering response

- Fixed the public input at `5.10 USDT` so the demo stays narrowly bounded and
  reliably clears the observed `5 USD` notional floor.
- Allowed only the two observed/documented aggregator modes, `RFQ` and `SWAP`,
  and display the actual value. Every other mode fails closed.
- Bound every route to chain `56`, exact raw input, BSC USDT, the
  Binance-discovered RWA contract, unique quote ID, and exactly one best route.
  The browser independently repeats the material identity checks.
- Added expiry, honeypot, tax, impact, and route-availability policy. The UI
  explicitly says route metadata is not reserve depth or fill certainty.
- Kept the endpoint and acceptance script read-only. Transaction building,
  approval, simulation, wallet connection, and broadcast remain out of scope.

## Sources consulted

- [Hackathon rules and resources](https://www.bnbchain.org/en/hackathons/tokenized-stocks)
- [Authentication](https://web3.binance.com/en/dev-docs/authentication)
- [RWA Data API](https://web3.binance.com/en/dev-docs/catalog/web3-wallet/api/rest-api/rwa-data)
- [Trading API](https://web3.binance.com/en/dev-docs/catalog/web3-wallet/api/rest-api/trading-api)
