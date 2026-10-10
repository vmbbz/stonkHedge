# BNB simulation-only preview deployment

**Date:** 2026-10-09

**Branch:** `hackathon/bnb-tokenized-stocks-2026`

**Prepared revision:** the branch commit containing this runbook; record the
exact deployed SHA during live preview acceptance

**Deployment state:** Vercel project linked and branch-scoped Preview secrets
configured; no deployment has yet passed the Preview-target acceptance gate

**Boundary:** preview only; no wallet, private key, signing, broadcast, or
mainnet spend

## Purpose

This preview exposes Gap Guardian's live comparison, bounded quote, and
unsigned-simulation experience to reviewers without opening an execution path.
The Vite application remains static. `/api/bnb/rwa.ts` is deployed as a Node.js
function and is the only component allowed to read Binance Web3 credentials.

The repository-level `vercel.json` uses Vite's detected build, gives the API
function up to 60 seconds for its bounded upstream sequence, enables request
cancellation, and applies browser security headers. It does not embed
credentials or override the build with legacy `builds` or `routes` rules.
The package pins Node.js `22.x`, matching the locally accepted runtime and
avoiding an unreviewed runtime jump during deployment.

`.vercelignore` excludes local environment files, Vercel link metadata,
dependency/build artifacts, transaction build directories, and the unrelated
local `buildl.md` file from the CLI upload boundary.

## Vercel settings

Use these exact project settings:

| Setting | Value |
|---|---|
| Repository | `vmbbz/stonkHedge` |
| Git branch | `hackathon/bnb-tokenized-stocks-2026` |
| Framework preset | Vite |
| Root directory | `./` |
| Install command | default (`npm install`) |
| Build command | `npm run build` |
| Output directory | `dist` |
| Production deployment | **No**; create a Preview deployment |

Configure these values in **Project Settings → Environment Variables** and
scope both to **Preview**. If Vercel offers branch scoping, restrict them to
`hackathon/bnb-tokenized-stocks-2026`:

- `BINANCE_WEB3_API_KEY`
- `BINANCE_WEB3_SECRET_KEY`

Do not use a `VITE_` prefix. Do not paste either value into source code, build
logs, screenshots, chat, or this document. `BINANCE_WEB3_BASE_URL` and
`BINANCE_WEB3_TIMEOUT_MS` are optional; the checked defaults are the official
`/build` endpoint and eight seconds per upstream call.

Vercel applies changed environment variables only to new deployments, so
redeploy after adding or rotating either credential.

## Authentication and deployment

The local Vercel CLI is authenticated as `cosychiruka-7184`, and this checkout
is linked to `katzs-projects-2f9ffaf0/stonkhedge`. The Vercel project is connected
to `vmbbz/stonkHedge`, with `main` confirmed as its production branch.

On 2026-10-10, Vercel CLI `62.7.0` classified both a default deployment and an
explicit `--target=preview` deployment as `production`. The operator removed
both deployments (`dpl_F95uiwe9aoBCeeptXKmVFw5wiwVU` and
`dpl_GPZgKiqmhzsNwuPDTQfy1q8PHh5w`); the production alias subsequently returned
`404`. Neither deployment is accepted evidence.

Do not create another direct CLI deployment for this gate. Trigger the Preview
through the connected Git integration by pushing this non-production branch:

```powershell
cd C:\dev-shared\stonkHedge
git push origin hackathon/bnb-tokenized-stocks-2026
```

Vercel's Git integration should create a Preview because the branch differs
from `main`. Inspect the resulting deployment and require `target: preview`
before opening or testing its URL. Never use `--prod`, promote, or assign the
production alias for this milestone. `.vercel/` remains local and ignored.

## Acceptance

After Vercel reports the preview as Ready, run the repository smoke test with
the public, unfunded buyer address:

```powershell
npm run bnb:rwa:preview -- https://YOUR-PREVIEW.vercel.app 0x6719E877C05b2d6c28aBceA405fC033FEeF5750f
```

The required result is:

- comparison response parses and resolves Ondo `NVDAon`;
- API responses include `private, no-store` and `nosniff`;
- exact `5.10 USDT` approval simulation returns `SUCCESS`;
- unfunded swap simulation returns `FAILED`;
- public verdict is `BLOCKED`; and
- no local API credential, wallet, key, signature, or broadcast method is used.

Also inspect the page in a clean browser session at desktop and mobile widths.
Confirm that Compare live, Get read-only quote, and Compile & simulate a fresh
route work, that the simulation proof contains no raw calldata, and that the
browser console has no Content Security Policy violations.

Repository preparation passed `46/46` automated tests, the TypeScript/Vite
production build, and JSON/configuration validation. The production dependency
audit reports zero advisories. The full audit reports one high-severity advisory
in development-only transitive dependency `source-map-js@1.2.1`; it is not part
of the production dependency tree or browser bundle. A lockfile-only upgrade
was deliberately rejected because `package-lock.json` is bound into frozen
Robinhood lifecycle evidence and the provenance test correctly detected the
hash drift. Resolve this only through an explicit evidence-baseline migration,
not by rewriting historical manifests during preview preparation.

## Stop conditions

Stop and do not promote the preview if any of these occur:

- either credential appears in client JavaScript, network query parameters, or
  logs;
- the function returns executable calldata to the browser;
- the preview lacks `no-store` on API responses;
- the selected chain, sender, token, amount, approval, or slippage changes;
- a simulation error is converted into a clear verdict;
- Vercel deploys from `main` instead of the hackathon branch; or
- the command attempts a production deployment.

The in-memory request budget is defense in depth, not a globally durable rate
limit across serverless instances. Before a broad public launch, add a durable
quota/rate-limit service or platform firewall rule and monitor Binance API
usage.

## Next gate

Record the immutable preview URL, deployed Git SHA, timestamp, response
boundaries, and smoke-test output. Only then should work begin on the separately
reviewed, disabled-by-default wallet confirmation state machine.

## Sources

- [Vercel project configuration](https://vercel.com/docs/project-configuration/vercel-json)
- [Vercel environment variables](https://vercel.com/docs/environment-variables)
- [Vercel preview environments](https://vercel.com/docs/deployments/environments)
- [Vercel Git deployments](https://vercel.com/docs/git)
