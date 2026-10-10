# BNB Gap Guardian public demo evidence

**Capture date:** 2026-10-10

**Application revision:** `d28f3ad13a235f5968e9e8c43cebe35961b36069`

**Runtime:** loopback production build plus server-only Binance Web3 adapter

**Boundary:** live BSC API and unsigned simulation; no wallet, private key,
signature, broadcast, transaction receipt, or mainnet spend

These screenshots were captured from the real application after live Binance
Web3 responses. They are not design mockups. The capture used the public,
unfunded receiver `0x6719E877C05b2d6c28aBceA405fC033FEeF5750f` and never loaded a keystore.

## Captured artifacts

| File | What it proves | SHA-256 |
|---|---|---|
| [`01-live-comparison-desktop.png`](./01-live-comparison-desktop.png) | One NVDA search resolved live Ondo and bStocks BSC representations, a `16.24 bps` normalized gap, current freshness, and honest off-hours/unreported-session warnings | `FCDA196B4E8F002F3E2CC16230A0B748E334352FF071BC9069A49BED6BA3EB98` |
| [`02-live-quote-desktop.png`](./02-live-quote-desktop.png) | Exact `5.10 USDT` returned a live LiquidMesh SWAP route for `NVDAon`, approximately `0.02210062 NVDAon`, with Kipseli and Uniswap V4 segments | `0194307B3A4CDA5D83F6DF263F3B417D3FF6943066A57483B6B4E65F7F016312` |
| [`03-live-simulation-desktop.png`](./03-live-simulation-desktop.png) | Exact approval simulation returned `SUCCESS`; swap returned `FAILED` for insufficient balance; verdict remained blocked and exposed no raw calldata | `602CEB50B71D36F24F35DAE6D2CA636A55BEBA344E6DB039735F6EF3E43B870E` |
| [`04-live-comparison-mobile.png`](./04-live-comparison-mobile.png) | The same live two-issuer comparison reflowed at a `390 px` mobile viewport without a second upstream request | `1510D0C25B7DBD8314FC313CA65409F409242209E6099CBD4FB0318328CCBDAA` |
| [`capture-manifest.json`](./capture-manifest.json) | Machine-readable capture time, filenames, browser, public receiver, redacted UI summaries, and the no-signing/no-broadcast boundary | `892CE06A5E20DF4E41ECABFF36F26C569E404F1A7AB86B5B630C642D16A971BB` |
| [`05-test-build-transcript.md`](./05-test-build-transcript.md) | A fresh `npm run check` passed 48 tests in 9 files and completed the TypeScript/Vite production build | `846CD4E4894239ED09AF1E130E6DFE5B6F856523E1EF3B1C417655D873A50C5D` |
| [`06-live-acceptance-transcript.md`](./06-live-acceptance-transcript.md) | Public-safe comparison, quote, and unsigned-simulation results transcribed from the capture manifest without raw quote IDs or calldata | `60DBBD0BA340D0BE93B47F24FAC4CFFC51F017293976891BA6AF1799AC1AB295` |
| [`07-public-access-check.md`](./07-public-access-check.md) | Unauthenticated HTTP checks for the repository, README, and judge instructions, plus the honest video/deployment boundary | `5F5C9EC659D3F726B7B9A2AF9972CD7B9F57FA0513A4079906FBE115FE450946` |

The final capture completed at `2026-10-10T12:26:26.396Z` (14:26 SAST). Quote
and simulation values are ephemeral and must not be reused as current market
data.

## Final evidence status

| Gate | Status | Evidence or next action |
|---|---|---|
| E1 desktop comparison | PASS | `01-live-comparison-desktop.png` |
| E2 bounded quote | PASS | `02-live-quote-desktop.png` |
| E3 blocked simulation | PASS | `03-live-simulation-desktop.png` |
| E4 mobile layout | PASS | `04-live-comparison-mobile.png` |
| E5 test/build transcript | PASS | `05-test-build-transcript.md` |
| E6 live acceptance transcript | PASS | `06-live-acceptance-transcript.md` and `capture-manifest.json` |
| E7 Git provenance | RECHECK AT HANDOFF | Compare local `HEAD` with the public remote branch after the final evidence commit is pushed |
| E8 public access | PARTIAL | `07-public-access-check.md` proves the repo and judge instructions; upload the final video and verify its URL signed out |

No Vercel deployment existed when this matrix was updated on 2026-10-11.
The official requirement permits a deployed link **or** instructions a judge
can follow, so the public judge quickstart is the truthful fallback.

## Visual review

The four images and capture manifest were inspected after capture. They contain:

- public token and receiver addresses only;
- live prices, route metadata, selectors, and the public simulator reason;
- no API key, HMAC secret, authorization header, private key, wallet export,
  raw quote ID, or executable calldata; and
- clear `no signing`, `no transaction built`, and simulation-only wording.

An earlier raw browser screenshot that showed only the animated hero was
rejected and is not part of this evidence set.

## Validation in the same work session

- `npm run check`: **PASS**, 9 test files and 48 tests, followed by a
  successful TypeScript/Vite production build;
- `npm audit --omit=dev`: **PASS**, zero production vulnerabilities;
- local root response: HTTP `200` with CSP and `X-Frame-Options: DENY`;
- direct request for `/.env.local`: HTTP `404`; and
- production JavaScript `HEAD`: HTTP `200` with the expected JavaScript media
  type.

## Capture tooling and quota observation

Run the local application and capture flow with:

```powershell
npm run build
npm run bnb:rwa:demo
npm run bnb:rwa:evidence -- http://127.0.0.1:3000/ docs/hackathons/evidence/2026-10-10 0x6719E877C05b2d6c28aBceA405fC033FEeF5750f
```

An initial automated sequence completed the three desktop states, then its
mobile reload hit Binance business code `42900` (`Rate limit exceeded`). The
capture tool was changed to reflow the already-loaded comparison for mobile
evidence rather than issue another upstream request. The corrected full run
then passed and produced the four artifacts and manifest indexed above.
