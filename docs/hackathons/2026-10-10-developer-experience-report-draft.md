# Binance Web3 Developer Experience Report — builder-review draft

**Important:** the event says perfunctory or AI-generated reports are not
accepted. This document organizes the contemporaneous build log; it is not a
form submission. The actual builder must verify every fact, replace all owner
markers, choose subjective ratings personally, rewrite the final answer in
their own voice, and submit the official form.

Source log:
[`2026-10-09-binance-web3-dx-log.md`](./2026-10-09-binance-web3-dx-log.md)

## How to use this draft without submitting an AI-written report

The official form is a set of individual questions, not a document upload.
Use this file as an evidence index and write the final responses in the
builder's own voice inside the form.

1. Open the form and first answer the personal multiple-choice fields without
   copying from this draft: Web3 experience, previous Binance API experience,
   onboarding time, API-key time, ratings, use of `llms.txt`, code-example
   experience, rate-limit severity, and whether the builder will keep using
   the platform.
2. For each free-text field, select only the relevant facts below. Rewrite the
   answer as a first-person account of what the builder actually did and saw.
3. Keep exact endpoint names, response codes, error strings, timestamps, and
   latency figures unchanged. These are evidence, not prose to improvise.
4. Add one or two personal observations that are not in this file—for example,
   which error was most frustrating, what finally made the signing rule click,
   or which UI result made the product idea feel useful.
5. Remove any fact the builder cannot personally defend. Do not invent a start
   time, successful trade, liquidity depth, support interaction, AI-stack use,
   or production deployment.
6. Save a private copy of the final form answers before submitting, then submit
   the DX form before checking its confirmation in the project form.

### Live-form mapping

| Official question group | Use from this draft | Builder must supply personally |
|---|---|---|
| Submission details | project, repository, modules, platforms | email, experience, prior API use |
| Onboarding | exact signing-path issue and first-success timestamp | elapsed-time choices, ratings, where the builder first felt blocked |
| Documentation | documented schema drift and proposed corrections | rating, which examples the builder personally tried, `llms.txt` answer |
| API pitfalls | endpoint behavior, errors, latency, rate limiting, reconciliation | severity choices and the builder's judgment of reliability |
| AI stack | truthful `None` boundary | `N/A` rating and any personal reason for not adding execution authority |
| Tokenized stocks | Ondo/bStocks comparison, `5.10 USDT` quotes, session behavior, gaps | no claim of executed-trade liquidity or fill quality unless a later receipt proves it |
| Redesign and requested capabilities | concrete SDK, schema, retry, capacity, and orchestration proposals | the single change the builder values most and whether they will keep building |

The form states that a submission without this report is not scored and that
the report is worth 25% of the total. Specific criticism is an advantage here;
do not smooth away the production mismatches that made the integration harder.

## Submission details

| Field | Draft answer |
|---|---|
| Project | StonkHedge Gap Guardian |
| Contact email | `OWNER INPUT REQUIRED — same as registration and project form` |
| Public repository | `https://github.com/vmbbz/stonkHedge/tree/hackathon/bnb-tokenized-stocks-2026` |
| Team size | `OWNER INPUT REQUIRED` |
| Web3 experience | `OWNER INPUT REQUIRED` |
| Previous Binance Web3 API experience | `OWNER INPUT REQUIRED` |

## Modules and stacks actually used

- [x] RWA Data API
- [x] Trading API
- [x] Transaction API
- [ ] General Market API
- [ ] Wallet API / Address Portfolio
- [ ] DeFi API
- [ ] b402 Payments
- [ ] Agentic Wallet / Wallet Skills
- [ ] BNB Agent Studio

Tokenized-stock platforms exercised: **Ondo and bStocks**.

AI execution stack used: **None**. The product uses deterministic application
logic and the Binance REST APIs. AI assistance was used during development,
not as an in-product execution agent.

## Onboarding

### Time from opening the docs to the first successful API call

`OWNER INPUT REQUIRED — use the builder's actual start time; the first recorded successful call was 2026-10-09T12:58:51Z`

Do not derive a flattering duration after the fact. If the start time was not
recorded, state that plainly and give the first-success timestamp.

### Time to create an API project and obtain credentials

`OWNER INPUT REQUIRED — personal account timing`

### What was clear

The documentation clearly established HMAC-SHA256 authentication, the need for
both an API key and secret, timestamp/nonce fields, and the major RWA, Trading,
and Transaction API surfaces. The hackathon page gave a useful end-to-end map
from token discovery to quote, build, and simulation.

### Where the implementation got stuck

1. The `/build` prefix must appear in both the request URL and the raw path
   covered by the signature. This is documented, but it is easy to miss and is
   consequential enough to deserve a complete signing example beside every
   language snippet.
2. The bStocks underlying-market response returned `marketStatus: null` and
   several null market-data fields where the published model presents strings.
3. Ondo later returned undocumented `marketStatus: "offhours"` while the
   documented enum listed only `premarket`, `regular`, `postmarket`,
   `overnight`, `closed`, and `pause`.
4. Exactly `5 USDT` was rejected with `Minimum order amount is 5 USD`; `5.10`
   cleared the floor. The effective rule is USD notional and the strict edge
   behavior is not obvious from a raw token amount.
5. The tokenized-stock route returned `executionMode: SWAP` rather than the
   RFQ-only expectation formed from the docs.
6. A live SWAP build omitted `tx.signatureData`, although the response model
   presents an array.
7. Successful simulations returned `failReason: ""` rather than `null`.
8. During an underlying-session transition, the API returned business code
   `40367` and `The stock market is shifting its trading phase`.

## Documentation

### Rating

`OWNER INPUT REQUIRED — subjective rating from the form's scale`

### Most useful pages

- Authentication, especially the signature formula and `/build` warning;
- RWA Data API for platform/search/profile/market relationships;
- Trading API for quote and transaction-build fields; and
- Transaction API for simulation request and state-change evidence.

### Specific documentation issues

- Update the underlying-market schema with field-level nullability by platform
  and include `offhours` in `statusInfo.marketStatus`, or state that the enum is
  open-ended and provide a versioning policy.
- Define the units and strict inequality behavior of the minimum-order rule.
  Include one tokenized-stock example that fails at exactly `$5` and succeeds
  above it.
- Document when tokenized-stock routes return `SWAP` versus `RFQ`, including
  what signing material each mode requires.
- Mark `signatureData` optional for routes where it is legitimately omitted.
- Define absent failure reasons consistently: either `null` or empty string,
  and align examples with production.
- Add the session-transition business code `40367`, expected duration, and
  recommended retry behavior.

### Example that would have saved the most time

A complete TypeScript example that signs the exact serialized path and body,
searches `NVDA`, selects a BSC issuer representation, requests the minimum
valid USDT route, builds an exact approval plus SWAP transaction, and simulates
both independently—with every response field annotated as required, optional,
nullable, or platform-specific.

## API reliability and behavior

### Rating

`OWNER INPUT REQUIRED — subjective rating`

### Recorded latency

- first platform/search acceptance: `2,902 ms`;
- expanded platform/search/price/profile/market check: `3,437 ms`;
- first browser-shape repeat: `7,570 ms`;
- 2026-10-10 comparison after `offhours` compatibility: `4,128 ms`;
- initial Ondo/bStocks quotes: `2,795 ms` / `1,845 ms`;
- 2026-10-10 Ondo/bStocks quotes: `2,684 ms` / `2,184 ms`.

One end-to-end handler attempt exceeded the local upstream timeout and returned
a redacted HTTP `504`; one bounded retry succeeded. This makes timeout and
retry behavior important for a live UI. Repeated acceptance and screenshot
rehearsals later triggered business code `42900` with `Rate limit exceeded`.
The response did not expose an exact quota window or safe retry time through
the current client, so the run stopped rather than polling aggressively.

### Error quality

The minimum-order and trading-phase messages were actionable once observed.
Schema drift was harder: a strict client initially failed on production values
that were not represented by the documented schema. Error objects should
include a stable machine code, field path, retryability classification, and
documentation link.

### Trust and reconciliation

The APIs repeat enough transaction identity to build strong local controls,
but the client still needs to bind every route/build/simulation response to
chain, addresses, amounts, quote ID, sender, vendor, expected output, value,
and slippage. For safety, StonkHedge independently decodes the approval and
simulates approval and swap separately. The public response contains only
selectors and hashes, not executable calldata.

## Tokenized-stock-specific observations

### Issuer differences

- One `NVDA` search returned both Ondo `NVDAon` and bStocks `NVDAB` on BSC.
- Ondo reported daily and monthly attestation support; bStocks reported
  collateral-report support.
- The token-to-share ratios differ, so raw token prices are not directly
  comparable. StonkHedge divides token price by the issuer ratio before
  calculating the symmetric gap.
- bStocks omitted the market-session label while reporting the underlying open
  and trading. Ondo later reported the undocumented `offhours` label.

### Liquidity, slippage, and routes

At the recorded checks, `5.10 USDT` produced one LiquidMesh SWAP route for
each representation. The 2026-10-10 outputs were approximately
`0.0221037 NVDAon` and `0.02211223 NVDAB`; reported price impact was very small.
This proves current quote availability, not pool depth or fill certainty. A
liquidity-depth or maximum-input endpoint would enable a more defensible
capacity view than repeatedly probing quotes.

### Outside-hours behavior

The most useful production observation was that on-chain availability and
underlying-session labels do not line up cleanly. `openState: true` appeared
with both an unreported session and `offhours`. Applications need a stable
session taxonomy and an explicit distinction between underlying exchange
hours, issuer restrictions, and on-chain transfer/swap availability.

### Price gaps

The first accepted repeat measured approximately `0.2693 bps`; the
2026-10-10 check measured approximately `15.8038 bps`. These are ephemeral
issuer-normalized observations, not arbitrage claims. The API would be easier
to use if it returned an explicit normalized per-share value and provenance
for the reference timestamp.

## AI stack feedback

No Agentic Wallet, Wallet Skills, CLI execution layer, or BNB Agent Studio was
used. The reason was scope and safety: the core deterministic discovery,
policy, quote, build, and simulation path had to be trustworthy before adding
an agent with execution authority.

`OWNER INPUT REQUIRED — if the form asks for a rating when "None" is selected,
choose the form's not-applicable option or explain this boundary honestly.`

## Redesign suggestions

1. Publish an official TypeScript SDK that owns canonical serialization and
   signing and exports runtime schemas generated from the same source as the
   docs.
2. Add schema versions and machine-readable OpenAPI/JSON Schema with explicit
   nullable/optional fields and an open-enum compatibility policy.
3. Expose one orchestrated dry-run endpoint that returns discovery, quote,
   decoded approval, transaction build, simulation, and a deterministic
   identity digest. Keep the component endpoints for advanced users.
4. Add stable retryability metadata and request IDs to every error.
5. Add a quote-capacity/depth endpoint and document how issuer wrapper ratios,
   market sessions, and transfer restrictions affect tokenized-stock routes.
6. Provide production fixtures for every issuer/platform and every market
   phase, including null fields, `offhours`, phase transitions, RFQ, and SWAP.

## Requested capabilities

- official SDK/signing helpers for TypeScript and other common languages;
- generated runtime validators;
- per-issuer market-session and transfer-status taxonomy;
- route depth / maximum safe input guidance;
- quote-to-build-to-simulation identity hash;
- batch profile/market endpoint for multi-issuer comparison;
- published business-code catalog with retry behavior; and
- a sandbox mode whose response shapes match mainnet tokenized-stock routes.

## Single change that would save the most time

Ship a versioned TypeScript SDK generated from the production schema, with a
single documented NVDA discovery-to-simulation example and fixtures for Ondo
and bStocks. That would remove most signing, nullability, enum, and field-drift
guesswork without hiding the underlying API.

## Would the builder use the platform again?

`OWNER INPUT REQUIRED — personal conclusion and explanation`

Suggested factual basis: the aggregated surface is valuable because it joins
issuer discovery, market state, route construction, and simulation, but a
production integration currently needs defensive runtime validation and
explicit handling for documentation drift.

## Pre-submission builder checklist

- [ ] Replace every `OWNER INPUT REQUIRED` marker.
- [ ] Verify each timestamp and number against the source log.
- [ ] Remove any claim the builder did not personally observe.
- [ ] Add the builder's own ratings and wording.
- [ ] Keep the AI-stack “None” answer consistent with the project form.
- [ ] Submit the DX form before checking its confirmation on the project form.
- [ ] Save a private copy of the final submitted answers outside the repository
      if the form does not provide a response receipt.
