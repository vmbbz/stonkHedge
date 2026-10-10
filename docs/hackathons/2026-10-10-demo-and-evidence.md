# StonkHedge Gap Guardian demo and evidence runbook

**Target duration:** 3:20–3:35

**Hard limit:** 4:00

**Submission lock:** 11 October 2026 at 12:00 UTC / 14:00 SAST

**Demo boundary:** BSC mainnet data, live quote, and unsigned simulation; no
wallet, signing, broadcast, or completed trade unless a later separately
authorized milestone adds and proves that path

## Product and demo in one sentence each

**StonkHedge:** a risk-first interface for tokenized stocks that helps users
compare issuer wrappers and inspect a proposed route before anything can touch
a wallet.

**This BNB demo:** Gap Guardian uses live Binance Web3 APIs on BSC to discover
and normalize two issuer-specific versions of NVDA, request one bounded
`5.10 USDT` route, and turn it into redacted unsigned simulation evidence that
stops when the sender has no funds.

The first sentence explains the product. The second explains the exact feature
and evidence being demonstrated. Do not merge the broader Robinhood testnet
options milestone into this BNB spot-product recording.

## Recording preparation

1. Close unrelated applications, tabs, password managers, wallet extensions,
   notifications, and chat windows.
2. Use a clean browser profile. Keep developer credentials only in the local
   server environment; never open `.env.local` during recording.
3. Set the browser to 1440×900 or 1920×1080 at 100% zoom.
4. Start from the immutable submission revision. Run `npm run check` once
   before recording and save the terminal output as evidence.
5. Verify the live comparison and one quote immediately before recording.
   Upstream data is ephemeral; if the API is unavailable, stop rather than
   substituting a fixture while describing it as live.
6. Use the public, unfunded receiver
   `0x6719E877C05b2d6c28aBceA405fC033FEeF5750f`. It is an address only; do not
   open, import, or expose any wallet secret.
7. Disable desktop notifications and inspect the full captured frame before
   publishing.

## Fast Windows recording setup

Prefer OBS Studio because it can isolate the browser and microphone and can
recover a recording if the application closes unexpectedly.

1. In OBS, create a **Window Capture** source for the clean browser window.
   Do not capture the entire desktop unless the browser-capture method fails.
2. Set the canvas and output to `1920x1080`, `30 FPS`, with the browser at
   `100%` zoom. Record to `MKV`, then use **File -> Remux Recordings** to make
   the uploadable `MP4`. This avoids losing the whole take if OBS or Windows
   closes during recording.
3. Add the microphone as an audio input and make a ten-second scratch
   recording. Confirm that speech is clear, system notification sounds are
   absent, and no password-manager or wallet overlay appears.
4. Start the application from a terminal that will not be captured:

   ```powershell
   cd C:\dev-shared\stonkHedge
   npm run check
   npm run bnb:rwa:demo
   ```

5. Open `http://127.0.0.1:3000/#gap-guardian`, maximize the clean browser,
   and position the page at the hero before starting the take.
6. Make one silent rehearsal using the already-captured evidence before using
   another live request. During the real take, run the comparison, quote, and
   simulation once each. Repeated retries can consume the upstream quota.
7. Stop recording after the honest close, remux to MP4, and watch the entire
   file once at normal speed. Reject the take if it exceeds four minutes,
   leaks a notification or secret, loses audio, or describes a simulation as
   a transaction.

If OBS is unavailable, Windows Game Bar (`Win+Alt+R`) is an acceptable
fallback. Capture only the browser application, verify the microphone toggle,
and perform the same ten-second scratch test first.

## Submission-day recording order

Record a complete simulation-only fallback before attempting any new mainnet
execution work. That guarantees the submission has an honest demo even if a
wallet integration, funding step, live route, or receipt later fails.

1. **Take A — current revision:** use the script below exactly and retain the
   simulation-only close.
2. Upload Take A privately or unlisted, open the share URL signed out, and
   retain it as the submission fallback.
3. Only after Take A is safe may a separately reviewed and authorized mainnet
   proof be attempted.
4. If that proof succeeds and reconciles on BscScan, record **Take B**. Replace
   the simulation-only close with a brief receipt and post-state segment. Do
   not splice a manual wallet trade into the product story unless the receipt
   is bound to the same token, exact input, receiver, route intent, and product
   revision.

The saved screenshots are evidence and rehearsal aids. They are not a
substitute for showing the working browser flow in the video.

## Pacing guardrails learned from the rehearsal

The first recorded rehearsal was technically healthy but lasted `13:01`. Its
opening four minutes had not yet reached the simulation, and its final section
drifted into the separate Robinhood testnet story. The final take must correct
that editorial problem:

- begin speaking within two seconds of the first frame;
- keep narration continuous while scrolling, typing, and waiting for results;
- spend no more than the allocated time on any result card;
- use only the hero and Gap Guardian section—do not enter Architecture,
  Timeline, Contracts, Transactions, or the Robinhood lifecycle;
- perform one comparison, one quote, and one simulation; and
- stop recording immediately after the final boundary statement.

If a live response takes longer than the narration allocated to it, briefly say
that the request is live and keep speaking about the visible safety controls.
Do not fill the delay by navigating to another part of the site.

## Shot-by-shot script

### 0:00–0:25 — what StonkHedge is and what this demo tests

**Visual:** StonkHedge hero, then scroll to Gap Guardian.

**Narration:**

> StonkHedge is a risk-first interface for tokenized stocks. It helps users
> compare issuer wrappers and inspect a proposed route before anything can
> touch a wallet. For BNB Hack, we built Gap Guardian on BSC. This demo tests
> live discovery, issuer-normalized comparison, a bounded quote, and unsigned
> transaction simulation.

### 0:25–1:05 — why the comparison matters

**Visual:** Arrive at Gap Guardian and keep the explanation card visible.

**Narration:**

> A tokenized stock can keep trading while its underlying exchange is closed,
> and one company can have several on-chain representations with different
> issuers, ratios, prices, and controls. Comparing raw token prices can
> therefore be misleading. Gap Guardian makes those differences explicit
> before a user chooses a route.

### 1:05–1:45 — live issuer comparison

**Action:** Search `NVDA` and select **Compare live**.

**Visual:** Show both issuer cards, normalized price, issuer gap, session,
freshness, protection evidence, and warnings.

**Narration:**

> One signed server-side RWA search resolves Ondo NVDAon and bStocks NVDAB on
> BSC mainnet. We normalize each price by its token-to-share ratio before
> calculating the issuer gap. The session values and freshness come from the
> live response. Missing, off-hours, or unfamiliar states become visible
> review warnings instead of being guessed into a green signal.

Pause for no more than three seconds on the clickable contract links and API
observation time. Narrate the state actually shown; do not assume that a prior
`offhours` observation will repeat, and do not describe `referencePrice` as an
official exchange quote.

### 1:45–2:20 — bounded live route

**Action:** Keep `5.1 USDT`, choose `NVDAon · ondo`, paste the public receiver,
and select **Get read-only quote**.

**Visual:** Show output, route vendor, execution mode, reported path, impact,
freshness window, receiver binding, and approval target.

**Narration:**

> The amount is deliberately fixed at 5.10 USDT. In testing, one dollar and
> exactly five were rejected by the five-dollar notional rule. The browser gets
> live route metadata, never transaction bytes. Chain, tokens, amount,
> receiver, vendor, quote identity, expiry, and approval target are checked by
> the server and independently checked again in the browser.

### 2:20–3:00 — compile and simulate

**Action:** Select **Compile & simulate a fresh route**.

**Visual:** Show the exact approval, slippage cap, selectors, minimum output,
approval result, swap failure, reasons, and simulation-only boundary.

**Narration:**

> The server gets a fresh route, decodes an exact approval for 5.10 USDT,
> builds the swap with a 0.5 percent slippage cap, and sends the approval and
> swap independently to the Transaction API simulator. Here the approval
> succeeds, but the unfunded public address cannot execute the swap. StonkHedge
> therefore returns BLOCKED and opens no signing gate. Raw calldata and quote
> IDs never reach the page.

If the visible verdict differs, describe exactly what is shown. A `CLEAR`
simulation is still not a signature, broadcast, or completed trade.

### 3:00–3:20 — engineering depth without leaving the proof

**Visual:** Remain on the simulation proof card. Do not navigate to the site's
Robinhood-focused Architecture section.

**Narration:**

> Forty-eight automated tests cover request signing, schema validation, issuer
> and route binding, expiry, redaction, and source boundaries. The integration
> also recorded real API behavior that differed from the published schemas,
> including nullable session data, an undocumented state, omitted signature
> data, and empty-string failure reasons.

### 3:20–3:35 — honest close

**Visual:** Return to the blocked proof card and product name.

**Narration:**

> This proves a live BSC discovery-to-simulation workflow, not a completed
> trade. This revision has no wallet, signature, broadcast, or receipt.
> StonkHedge turns uncertainty into visible evidence and stops when the
> evidence is insufficient.

End immediately. Do not add a long credits slide that risks crossing 4:00.

## Required evidence set

| ID | Artifact | Acceptance |
|---|---|---|
| E1 | Desktop live comparison screenshot | Both issuer cards, gap, timestamp/freshness, session warnings, no secrets |
| E2 | Desktop bounded quote screenshot | `5.10 USDT`, issuer, output, vendor/mode, impact, receiver abbreviation, approval target |
| E3 | Desktop simulation screenshot | Approval `SUCCESS`, swap `FAILED`, `BLOCKED`, selectors/hashes only, safety boundary |
| E4 | Mobile layout screenshot | Comparison or proof remains legible at 390px width |
| E5 | Test/build transcript | 48 tests pass and Vite production build succeeds |
| E6 | Live acceptance transcript | Current comparison, quote, and simulation output with timestamps and no credentials |
| E7 | Git provenance | Final local SHA equals the public remote branch SHA |
| E8 | Public-access proof | Repo, video, and deployed/run-instruction links open signed out |

Store screenshots and public-safe transcripts under
`docs/hackathons/evidence/2026-10-10/`. Never store `.env.local`, auth headers,
raw quote IDs, executable calldata, private keys, wallet exports, or browser
profiles there.

## Recording acceptance checklist

- [ ] Runtime is the final submission SHA.
- [ ] Video is at most four minutes.
- [ ] NVDA comparison is visibly live, not a fixture.
- [ ] Both issuer/platform names and BSC context are visible.
- [ ] The quote is exactly `5.10 USDT`.
- [ ] Simulation is described as simulation, not a transaction.
- [ ] The missing live trade is disclosed in voice or on screen.
- [ ] No secret, private key, full wallet UI, personal notification, or unrelated
      browser tab appears.
- [ ] Captions or clear narration explain the user value and safety behavior.
- [ ] The upload is publicly viewable in a signed-out window.

## If the live API changes during recording

- `offhours`, `closed`, `overnight`, or an unreported session is acceptable if
  the UI labels it honestly.
- A different quote output or issuer gap is expected; narrate the live value.
- A phase-change, timeout, rate-limit, or route-unavailable error is valid
  evidence, but wait for the bounded retry window rather than editing the UI or
  substituting cached data.
- If the simulation unexpectedly returns `CLEAR`, do not imply permission to
  trade. The revision still has no wallet or broadcast path.
- Stop on any identity mismatch, unexpected executable field, secret exposure,
  or non-BSC route.

## Video handoff

Repository automation can prepare the scene, capture screenshots, preserve
transcripts, and generate the exact shot list. The builder should record or
approve the final narration because it contains personal product claims and
must match what is visibly demonstrated. After recording, save a local master
outside Git, upload a compressed copy to a stable public host, and place only
the public URL in the submission form.

## Small-mainnet-proof decision gate

The track rule says to dry-run with the Transaction API and then demonstrate
with a small live amount. The project form does not expose a separate receipt
field, but a completed, reconciled proof is therefore the strongest reading
of full track compliance. The current revision deliberately stops before
wallet connection or broadcast, so this proof is **not yet present**.

Do not rush a mainnet transaction merely to change the narration. Attempt the
proof only when all of these are true:

- Take A, the DX report, and the project-form copy are already safe;
- a dedicated BSC mainnet browser wallet controlled by the builder is
  available without sharing its private key or seed phrase;
- the wallet has exactly budgeted mainnet USDT plus enough BNB for approval,
  swap, and recovery gas;
- a reviewed state machine binds chain `56`, BSC USDT, one Binance-discovered
  tokenized-stock contract, exact `5.10 USDT` input, receiver, spender, minimum
  output, route expiry, and zero native swap value;
- approval and swap are freshly simulated, separately confirmed by the user,
  and stopped on any identity, expiry, balance, allowance, or gas mismatch;
- approval and swap receipts plus token/allowance post-state can be reconciled
  publicly; and
- the builder gives a new, explicit mainnet signing and broadcast
  authorization after reviewing the final transaction plan.

A testnet token, an unsigned successful simulation, an approval alone, or an
unrelated manual swap does not satisfy this proof.
