# BNB Tokenized Stocks submission readiness

**Project:** StonkHedge Gap Guardian

**Track:** Main Track — Tokenized Stocks Products & Agents

**Branch:** `hackathon/bnb-tokenized-stocks-2026`

**Assessment time:** 2026-10-10 23:26 UTC / 2026-10-11 01:26 SAST

**Submission lock:** 2026-10-11 12:00 UTC / 14:00 SAST

**Status:** owner-reported submitted before the lock; public repository,
simulation-only deployment, video, and Developer Experience Report supplied

This document began as the release gate for the hackathon package and is now
the post-submission archive. It separates supplied evidence from known
limitations. A completed submission does not silently promote simulation
evidence into a real BSC transaction.

## Executive decision

StonkHedge was submitted without a wallet execution lane. The entry is a
working, original, live-API product: it discovers two
issuer representations of NVDA on BSC, normalizes their per-share prices,
classifies market-session risk, obtains a bounded live route, compiles exact
approval and swap payloads on the server, and runs both through the Binance
Transaction API simulator. It fails closed when the public sender lacks USDT.

The strongest omitted proof is a safe, owner-authorized small mainnet trade.
That proof did not exist at submission and must not be implied by the successful
approval simulation or the expected insufficient-balance failure.

The public repository and judge quickstart are accessible. The builder
confirmed submission of both the Developer Experience Report and project form.
The supplied deployment is <https://stonkhedge.vercel.app/> and the supplied
video is <https://www.youtube.com/watch?v=uyjI4A-HF5Y>. Both were rechecked by
unauthenticated HTTP request on 2026-10-20. Private form receipts remain
owner-held and are deliberately excluded from Git.

## Official requirement matrix

| Requirement | Status | Current evidence | Remaining action |
|---|---|---|---|
| Working project | **Pass** | Live Binance RWA, Trading, and Transaction API calls; 50 automated tests; production build | Preserve a stable public judge path |
| Tokenized stock central | **Pass** | Ondo `NVDAon` and bStocks `NVDAB` are the compared and quoted assets | None |
| Spot only | **Pass** | Exact USDT-to-tokenized-stock spot route; no derivative or perpetual path | Keep the BNB submission scoped away from the Robinhood/Panoptic lane |
| BSC mainnet | **Pass for data and simulation** | Chain `56` is bound through discovery, quote, build, and unsigned simulation | Do not describe this as a completed on-chain trade |
| Small live-amount demonstration | **Blocker against full track compliance** | No wallet, signature, broadcast, receipt, or post-state exists | Retain the disclosed limitation; any future proof is a new security and authorization milestone |
| Public repository | **Pass** | Public branch was supplied and returned HTTP 200 at the 2026-10-20 recheck | Keep it public through judging and preserve the event branch as provenance |
| Demo video, at most four minutes | **Submitted with duration variance** | Public video: <https://www.youtube.com/watch?v=uyjI4A-HF5Y> | The supplied recording exceeded the form's four-minute instruction; preserve this as a disclosed compliance risk rather than claiming a clean pass |
| Deployed link or judge-run instructions | **Pass** | Public simulation-only deployment at <https://stonkhedge.vercel.app/> plus the local quickstart | Keep credentials server-side and preserve the no-wallet/no-broadcast boundary |
| Developer Experience Report | **Submitted — user confirmed** | Builder completed the official form after editing the evidence-led draft | Retain the Google Forms receipt or confirmation screenshot privately |
| Submission form | **Submitted — user confirmed** | Builder reported completing the official project form before the lock | Retain private confirmation; do not commit personal form data |
| Assets remain accessible through judging | **Pass at 2026-10-20 recheck** | Repository branch, stable and immutable deployments, and video returned HTTP 200 unauthenticated | Keep repo, video, and run link accessible until judging ends on 23 October |

At submission time, the hackathon landing page called the video strongly
recommended but optional while the live submission form presented the
demo-video response as required. The event-time operational interpretation was
therefore **video required**.

## What is already demonstrable

### Live comparison

- chain `56` asset discovery through the Binance RWA Data API;
- Ondo `NVDAon` and bStocks `NVDAB` resolved from one `NVDA` search;
- strict issuer, platform, token-address, chain, timestamp, and schema binding;
- token-to-share normalization and symmetric cross-issuer gap calculation;
- explicit stale, paused, unreported, closed, and off-hours policy; and
- no cached or invented fallback when the upstream API fails.

At `2026-10-10T11:50:01.479Z`, the fresh comparison completed in `4,128 ms`
and measured an issuer-normalized gap of approximately `15.8038 bps`. Ondo
reported the undocumented `offhours` status and bStocks reported no session
label, so both representations correctly produced review warnings.

### Live bounded quote

- exact `5.10 USDT` input, chosen to clear the observed `5 USD` floor;
- one fresh `LiquidMesh` `SWAP` route for each representation;
- destination, input, output, receiver, vendor, route, approval target, quote
  identity, expiry, tax, impact, and chain validation; and
- quote metadata only in the browser—no executable transaction bytes.

At the same acceptance checkpoint, Ondo quoted approximately
`0.0221037 NVDAon` in `2,684 ms` and bStocks quoted approximately
`0.02211223 NVDAB` in `2,184 ms`.

### Exact unsigned simulation

- canonical `approve(spender, 5.10 USDT)` decoding;
- swap binding to the same fresh quote, sender, amount, vendor, destination,
  expected/minimum output, zero native value, and `0.5%` slippage cap;
- independent approval and swap simulation; and
- only selectors, SHA-256 fingerprints, statuses, counts, and failure reasons
  returned to the browser.

Fresh rehearsals at `2026-10-10T11:50:28.281Z` and
`2026-10-10T11:50:32.190Z` returned approval `SUCCESS`, swap `FAILED` with
`BEP20: transfer amount exceeds balance`, and final verdict `BLOCKED` for the
unfunded public sender. This is successful fail-closed acceptance, not a trade.

## Historical submission-critical path

These were the event-time action items. They are retained for provenance, not
as a current execution queue:

1. **Judge path:** supplied the stable Vercel simulation-only URL and retained
   the public quickstart permalink.
2. **Evidence capture:** E1 through E6 are stored under
   `docs/hackathons/evidence/2026-10-10/`; recheck Git provenance after the
   final evidence commit and push.
3. **Demo recording:** a public recording was supplied after secret review. It
   exceeded the requested four-minute limit, which remains a disclosed risk.
4. **DX report:** submitted according to the builder. Preserve private proof of
   submission; do not add the email receipt or personal form response to Git.
5. **Project form:** owner-reported submitted with the public repo, video,
   deployment, and judge instructions for the Main Track.
6. **Freeze:** app deployment commit `eb76e6d` is recorded; public surfaces were
   rechecked unauthenticated on 2026-10-20 and remain available.

The browser-wallet state machine was not added. It remains a separate security
milestone and receives no implied authority from the completed submission.

## Owner-only inputs

Repository automation cannot truthfully invent or submit these:

- registration/contact email;
- ERC-20 prize wallet address or Binance UID;
- optional Telegram handle;
- team size and personal Web3/Binance experience;
- subjective onboarding, documentation, reliability, and AI-stack ratings;
- confirmation of eligibility and applicable-law compliance;
- final approval of any BSC mainnet budget and wallet transaction;
- video hosting account and final upload; and
- the actual clicks that submit both official forms.

## Judge quickstart boundary

The local judge path requires Node.js 22 and a judge-provided Binance Web3 API
key plus HMAC secret in ignored `.env.local`. Those credentials stay in the
server process. The application never accepts a wallet secret or private key.
The public sender passed to the scripts is only an address.

```powershell
git clone https://github.com/vmbbz/stonkHedge.git
cd stonkHedge
npm ci
Copy-Item .env.example .env.local
notepad .env.local
npm run check
npm run bnb:rwa:check -- NVDA
npm run bnb:rwa:quote -- 0x6719E877C05b2d6c28aBceA405fC033FEeF5750f NVDA 5.1 ondo
npm run bnb:rwa:simulate -- NVDA 0xa9ee28c80f960b889dfbd1902055218cba016f75 0x6719E877C05b2d6c28aBceA405fC033FEeF5750f
npm run build
npm run bnb:rwa:demo
```

Open `http://127.0.0.1:3000/#gap-guardian` for the local browser flow, or use
<https://stonkhedge.vercel.app/#gap-guardian> for the hosted simulation-only
surface. The local server serves the production build and API adapter from one
loopback origin; neither surface has a wallet or broadcast method.

The expected simulation result for the recorded unfunded sender is approval
`SUCCESS`, swap `FAILED`, verdict `BLOCKED`. A different external balance or
route is allowed to change that live result; the software must surface the new
state rather than force the recorded output.

## Freeze record

The live-drift compatibility checkpoint used during event preparation was:

```text
d28f3ad13a235f5968e9e8c43cebe35961b36069
```

The accepted hosted application deployment is bound to commit `eb76e6d` and
deployment `dpl_FGePgh7U19tUZRymumfxbY6jJ8Kh`. Later documentation-only
consolidation commits do not rewrite that deployment provenance.

## Official links

- [Hackathon requirements, deadline, track rules, and judging](https://www.bnbchain.org/en/hackathons/tokenized-stocks)
- [Project submission form](https://docs.google.com/forms/d/e/1FAIpQLSdMtogkNnWzkI6xUifE78Ks4TohOM1YuWMuNgV-UPLVnpHD4Q/viewform?usp=send_form)
- [Developer Experience Report form](https://docs.google.com/forms/d/e/1FAIpQLSfBkyWAYZ5JjzzUXRHlRgi7TjAIPUCkxPtV81eJgyBmGfrJiQ/viewform?usp=send_form)
