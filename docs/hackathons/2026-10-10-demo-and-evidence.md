# StonkHedge Gap Guardian demo and evidence runbook

**Target duration:** 3:35–3:50

**Hard limit:** 4:00

**Demo boundary:** BSC mainnet data, live quote, and unsigned simulation; no
wallet, signing, broadcast, or completed trade unless a later separately
authorized milestone adds and proves that path

## Story in one sentence

StonkHedge compares two issuer-specific versions of NVDA on BSC, explains the
risk of trading while the underlying session is off-hours or unreported, and
turns one bounded `5.10 USDT` route into an exact, redacted simulation proof
that stops when the sender has no funds.

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

## Tonight's recording order

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

## Shot-by-shot script

### 0:00–0:25 — the problem

**Visual:** StonkHedge hero, then scroll to Gap Guardian.

**Narration:**

> Tokenized stocks keep trading when the underlying market is closed, and the
> same company can have multiple issuer wrappers with different prices and
> controls. StonkHedge Gap Guardian makes those differences visible before a
> user acts.

### 0:25–1:15 — live issuer comparison

**Action:** Search `NVDA` and select **Compare live**.

**Visual:** Show both issuer cards, normalized price, issuer gap, session,
freshness, protection evidence, and warnings.

**Narration:**

> One signed server-side RWA search resolves Ondo NVDAon and bStocks NVDAB on
> BSC mainnet. We normalize by each token-to-share ratio before calculating the
> cross-issuer gap. Today Ondo reports an undocumented `offhours` state, while
> bStocks omits the session label. We surface both as review warnings instead
> of guessing that the market is regular.

Pause briefly on the raw contract links and the “API observation” time. Do not
claim that `referencePrice` is an official exchange quote.

### 1:15–2:05 — bounded live route

**Action:** Keep `5.1 USDT`, choose `NVDAon · ondo`, paste the public receiver,
and select **Get read-only quote**.

**Visual:** Show output, route vendor, execution mode, reported path, impact,
freshness window, receiver binding, and approval target.

**Narration:**

> The amount is deliberately fixed at 5.10 USDT: Binance rejected one dollar
> and exactly five because the route has a five-dollar notional floor. The
> browser receives live route metadata, not transaction bytes. Chain, tokens,
> amount, receiver, vendor, quote identity, expiry, and approval target are all
> checked twice—server-side and again in the browser.

### 2:05–2:55 — compile and simulate

**Action:** Select **Compile & simulate a fresh route**.

**Visual:** Show the exact approval, slippage cap, selectors, minimum output,
approval result, swap failure, reasons, and simulation-only boundary.

**Narration:**

> The server gets a fresh route, decodes an exact approval for 5.10 USDT,
> builds the swap with a 0.5 percent slippage cap, and sends both unsigned calls
> to the Transaction API simulator. The approval simulation succeeds. The swap
> fails because this public address has no USDT, so StonkHedge returns BLOCKED
> and opens no signing gate. Raw calldata and quote IDs never reach the page.

### 2:55–3:25 — engineering depth

**Visual:** Briefly show the architecture document or test output.

**Narration:**

> Forty-eight automated tests cover HMAC request identity, upstream schema
> validation, issuer and route binding, expiry, policy, redaction, and source
> boundaries. The integration also recorded real documentation drift: null
> session fields, an undocumented offhours value, omitted signature data, an
> empty-string failure reason, and the actual minimum-order behavior.

### 3:25–3:45 — honest close

**Visual:** Return to the blocked proof card and product name.

**Narration:**

> This submission proves a live BSC discovery-to-simulation workflow. It does
> not claim a completed swap: there is no wallet, signature, broadcast, or
> receipt in this revision. StonkHedge turns uncertainty into visible evidence
> and stops when the evidence is insufficient.

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
