# BNB Tokenized Stocks submission readiness

**Project:** StonkHedge Gap Guardian

**Track:** Main Track — Tokenized Stocks Products & Agents

**Branch:** `hackathon/bnb-tokenized-stocks-2026`

**Assessment time:** 2026-10-10 23:26 UTC / 2026-10-11 01:26 SAST

**Submission lock:** 2026-10-11 12:00 UTC / 14:00 SAST

**Status:** technically demonstrable; DX report submitted; video and project
form still outstanding

This is the release gate for the hackathon package. It separates evidence that
already exists from work that still has to happen. A checked item means the
artifact exists and can be reproduced; it does not silently promote simulation
evidence into a real BSC transaction.

## Executive decision

StonkHedge should submit even if the wallet execution lane is not completed.
The current entry is a working, original, live-API product: it discovers two
issuer representations of NVDA on BSC, normalizes their per-share prices,
classifies market-session risk, obtains a bounded live route, compiles exact
approval and swap payloads on the server, and runs both through the Binance
Transaction API simulator. It fails closed when the public sender lacks USDT.

The strongest remaining improvement is a safe, owner-authorized small mainnet
proof because the track rules explicitly say to dry-run while building and
then demonstrate with a small live amount. That proof does not exist today.
It must not be implied by the successful approval simulation or the expected
insufficient-balance failure.

The public repository and judge quickstart are accessible, and the builder has
confirmed submission of the Developer Experience Report. The remaining
submission-critical tasks are to record and publish the final demo video,
verify its URL signed out, complete the project form, and retain the final
submission confirmation before the lock.

## Official requirement matrix

| Requirement | Status | Current evidence | Remaining action |
|---|---|---|---|
| Working project | **Pass** | Live Binance RWA, Trading, and Transaction API calls; 48 automated tests; production build | Preserve a stable submission revision and judge path |
| Tokenized stock central | **Pass** | Ondo `NVDAon` and bStocks `NVDAB` are the compared and quoted assets | None |
| Spot only | **Pass** | Exact USDT-to-tokenized-stock spot route; no derivative or perpetual path | Keep the BNB submission scoped away from the Robinhood/Panoptic lane |
| BSC mainnet | **Pass for data and simulation** | Chain `56` is bound through discovery, quote, build, and unsigned simulation | Do not describe this as a completed on-chain trade |
| Small live-amount demonstration | **Blocker against full track compliance** | No wallet, signature, broadcast, receipt, or post-state exists | Either implement and separately authorize a bounded browser-wallet proof, or submit with this limitation disclosed |
| Public repository | **Pass** | Public branch at the exact remote revision recorded below | Freeze/tag the final submission revision and keep it public through judging |
| Demo video, at most four minutes | **Missing** | Script and evidence plan are prepared separately | Record, review for secrets, upload, and test the public URL |
| Deployed link or judge-run instructions | **Pass via instructions** | Public README and submission-readiness quickstart both resolve without credentials; the linked Vercel project has no deployment | Submit the public judge-instruction permalink, and do not claim a hosted site exists |
| Developer Experience Report | **Submitted — user confirmed** | Builder completed the official form after editing the evidence-led draft | Retain the Google Forms receipt or confirmation screenshot privately |
| Submission form | **Not submitted** | Copy-ready draft is prepared separately | Owner supplies contact, prize wallet/Binance UID, optional Telegram, video URL, and run URL/instructions |
| Assets remain accessible through judging | **Not yet locked** | Repository is public | Keep repo, video, and run link accessible until judging ends on 23 October |

The hackathon landing page calls the video strongly recommended but optional.
The live submission form currently presents the demo-video response as
required. The safe operational interpretation is therefore **video required**.

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

## Submission-critical path

Complete these in order so that optional product work cannot consume the
submission window:

1. **Judge path:** use the verified public quickstart permalink. Do not enter a
   Vercel URL because the linked project currently has no deployment.
2. **Evidence capture:** E1 through E6 are stored under
   `docs/hackathons/evidence/2026-10-10/`; recheck Git provenance after the
   final evidence commit and push.
3. **Demo recording:** record the prepared sub-four-minute story; inspect the
   entire frame and audio for secrets, unrelated tabs, notifications, wallet
   balances, or personal information before upload.
4. **DX report:** submitted according to the builder. Preserve private proof of
   submission; do not add the email receipt or personal form response to Git.
5. **Project form:** add the public repo, video, and exact public run
   instructions; select only the Main Track unless additional stacks are
   actually integrated.
6. **Freeze:** run all checks, tag or record the final SHA, test every URL in a
   signed-out browser, and keep all three artifacts public through judging.

If there is time after steps 1–5 are secure, decide whether to build the
browser-wallet state machine. That is a separate security milestone, not a
demo-polish task.

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
git switch hackathon/bnb-tokenized-stocks-2026
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

Open `http://127.0.0.1:3000/#gap-guardian` for the browser flow. The local
server serves the production build and API adapter from one loopback origin;
it is not exposed publicly and has no wallet or broadcast method.

The expected simulation result for the recorded unfunded sender is approval
`SUCCESS`, swap `FAILED`, verdict `BLOCKED`. A different external balance or
route is allowed to change that live result; the software must surface the new
state rather than force the recorded output.

## Freeze record

The live-drift compatibility checkpoint is remote at:

```text
d28f3ad13a235f5968e9e8c43cebe35961b36069
```

Replace this with the final submission SHA after the demo/report artifacts are
committed and pushed.

## Official links

- [Hackathon requirements, deadline, track rules, and judging](https://www.bnbchain.org/en/hackathons/tokenized-stocks)
- [Project submission form](https://docs.google.com/forms/d/e/1FAIpQLSdMtogkNnWzkI6xUifE78Ks4TohOM1YuWMuNgV-UPLVnpHD4Q/viewform?usp=send_form)
- [Developer Experience Report form](https://docs.google.com/forms/d/e/1FAIpQLSfBkyWAYZ5JjzzUXRHlRgi7TjAIPUCkxPtV81eJgyBmGfrJiQ/viewform?usp=send_form)
