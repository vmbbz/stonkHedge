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

- first authenticated call result, status, and measured latency;
- actual platform and BSC token counts returned to this developer project;
- exact permission errors, if any;
- tokenized-stock price, market-status, and quote behavior;
- support response quality if the integration blocks; and
- Agentic Wallet installation and execution experience.

## Sources consulted

- [Hackathon rules and resources](https://www.bnbchain.org/en/hackathons/tokenized-stocks)
- [Authentication](https://web3.binance.com/en/dev-docs/authentication)
- [RWA Data API](https://web3.binance.com/en/dev-docs/catalog/web3-wallet/api/rest-api/rwa-data)
