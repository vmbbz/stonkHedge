# BNB simulation-only preview deployment

**Date:** 2026-10-09

**Branch:** `hackathon/bnb-tokenized-stocks-2026`

**Accepted hosted revision:** `eb76e6d`

**Deployment state:** accepted simulation-only hosted release at
<https://stonkhedge.vercel.app/>; immutable deployment
<https://stonkhedge-emrdylgvn-katzs-projects-2f9ffaf0.vercel.app/>; deployment
ID `dpl_FGePgh7U19tUZRymumfxbY6jJ8Kh`; function region `cpt1`

**Boundary:** hosted review surface only; no wallet, private key, signing,
broadcast, BSC contract deployment, or mainnet spend

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

## Post-hackathon resolution

The original Preview-only procedure below repeatedly failed closed because
Vercel classified the first deployment as Production. The owner later
authorized one Production-target bootstrap solely to unblock and verify the
simulation-only site. That authorization did not include a custom domain,
wallet, signing, broadcast, blockchain transaction, or production secret
expansion.

Two application fixes were required before the hosted lane was accepted:

- commit `4bbbb28` corrected serverless module resolution; and
- commit `eb76e6d` pinned the Binance-facing function to Vercel region `cpt1`,
  avoiding the Binance jurisdiction denial observed from a US function region.

The accepted deployment is `dpl_FGePgh7U19tUZRymumfxbY6jJ8Kh`, with stable URL
<https://stonkhedge.vercel.app/> and immutable URL
<https://stonkhedge-emrdylgvn-katzs-projects-2f9ffaf0.vercel.app/>. Both public
URLs returned HTTP 200 in the unauthenticated 2026-10-20 consolidation check.
The final live API smoke test reached Binance successfully and then returned
business code `42900` after repeated acceptance traffic. That is an upstream
rate-limit boundary, not evidence of a failed Vercel build or a successful
trade.

The hosted lane remains simulation-only. No subsequent documentation or branch
integration grants permission to connect a wallet, sign, broadcast, spend, or
deploy contracts on BSC.

## Original Preview settings

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
| Original target | **Preview**; the later accepted bootstrap is documented above |

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

## Original authentication and failed Preview chronology

The local Vercel CLI is authenticated as `cosychiruka-7184`, and this checkout
is linked locally to `katzs-projects-2f9ffaf0/stonkhedge`. The Vercel project's
Git connection to `vmbbz/stonkHedge` was removed during containment; before
disconnecting, `main` was confirmed as its production branch.

On 2026-10-10, the local Vercel CLI `51.6.1` classified both a default
deployment and an explicit `--target=preview` deployment as `production`.
Vercel's remote build image reported CLI `62.7.0`. A subsequent Git
integration build from the non-production hackathon branch and a REST
deployment with the target omitted were also classified as `production`. This
matches the open upstream Vercel issue
[`vercel/vercel#17069`](https://github.com/vercel/vercel/issues/17069).

The operator removed all eight rejected deployments:

- `dpl_F95uiwe9aoBCeeptXKmVFw5wiwVU` — default CLI;
- `dpl_GPZgKiqmhzsNwuPDTQfy1q8PHh5w` — explicit CLI Preview target;
- `dpl_323yeUj4KXAUet7TcQyuyKaUQfWq` — Git integration; and
- `dpl_Hkj1HyaPMvo93uMAEeBDHvR79ByL` — REST target omitted; and
- `dpl_6ivnKzh7TAC4pAWD29ZKgP79uB7S` — Git integration after the blocker
  documentation commit; and
- `dpl_7YUuVrEWKv12jwtQvG3UJvBLn6BL` — Git integration after automatic
  deployments were set to `disabled`, showing that setting had not contained
  the webhook path; and
- `dpl_chc4sYLSDhZB3ZGMbnuBYyiqViFN` — explicitly authorized, Production-target
  bootstrap with `--skip-domain`; rejected before any Preview attempt because
  Vercel nevertheless assigned the project alias
  `stonkhedge-katzs-projects-2f9ffaf0.vercel.app`; and
- `dpl_9Suusv3RhQRMM4ghmFswUVGWm2Fa` — explicit `--target=preview` attempt after
  the bootstrap had been removed; Vercel still returned `target: production`
  and assigned `stonkhedge.vercel.app`, so the deployment was deleted before
  any smoke test or application request.

The seventh attempt began only after confirming that Production had no
environment variables, the public Production alias returned `404`, and the
project had no deployments. The command was limited to the simulation-only
site and did not contain a wallet, signer, private key, blockchain broadcast,
or transaction path. When the alias mismatch appeared, the operator did not
attempt the planned Preview. The bootstrap was deleted immediately. At
`2026-10-10T11:32:35Z`, the immutable deployment URL, assigned project alias,
and public Production alias all returned `404`; Vercel listed zero deployments
and Production still had no environment variables.

The eighth attempt tested whether the completed-and-removed bootstrap had
changed Vercel's first-deployment state. It had not. The local CLI rejected
combining `--target=preview` with `--skip-domain` before creating a deployment,
because `--skip-domain` is accepted only for Production targets. The operator
then used the explicit Preview target alone, inspected the returned metadata,
and stopped when it reported Production. At `2026-10-10T11:43:36Z`, Vercel
again listed zero deployments, Production had no environment variables, and
the rejected deployment URL, assigned public alias, and project alias all
returned `404`.

At the end of the eighth attempt, Vercel listed zero deployments for the
project and the production alias returned `404`. The Git integration was
disconnected to prevent feature-branch pushes from silently recreating
Production. None of those eight deployments is accepted Preview evidence. At
that time, no retry was permitted until one of these gates was explicitly
chosen:

1. Vercel resolves the upstream Preview-classification defect; or
2. Vercel Support provides a documented path that can create the first Preview
   without assigning any Production or project alias, and the owner separately
   authorizes that exact procedure.

Those one-time domainless bootstrap and follow-up Preview authorizations were
consumed and failed closed. The separately authorized accepted hosted release
is recorded above; it does not retroactively turn the failed attempts into
Preview evidence or create standing permission for another deployment.
`.vercel/` remains local and ignored.

## Original acceptance procedure

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

Repository preparation originally passed `46/46` automated tests, the TypeScript/Vite
production build, and JSON/configuration validation. The production dependency
audit reports zero advisories. The full audit reports one high-severity advisory
in development-only transitive dependency `source-map-js@1.2.1`; it is not part
of the production dependency tree or browser bundle. A lockfile-only upgrade
was deliberately rejected because `package-lock.json` is bound into frozen
Robinhood lifecycle evidence and the provenance test correctly detected the
hash drift. Resolve this only through an explicit evidence-baseline migration,
not by rewriting historical manifests during preview preparation.

## Hosted-lane stop conditions

Stop and do not promote the preview if any of these occur:

- either credential appears in client JavaScript, network query parameters, or
  logs;
- the function returns executable calldata to the browser;
- the preview lacks `no-store` on API responses;
- the selected chain, sender, token, amount, approval, or slippage changes;
- a simulation error is converted into a clear verdict;
- a deployment revision is not traceable to the reviewed repository state; or
- a new deployment, alias, secret-scope change, wallet path, signing path, or
  broadcast is attempted without explicit review and authority.

The in-memory request budget is defense in depth, not a globally durable rate
limit across serverless instances. Before a broad public launch, add a durable
quota/rate-limit service or platform firewall rule and monitor Binance API
usage.

## Next gate

Keep the hosted BSC lane read-only and unsigned. Retest the API only after the
upstream rate-limit window clears, preserve credential redaction and `no-store`
responses, and do not add a wallet confirmation state machine by extension of
the hackathon deployment. Any BSC execution path requires a new architecture,
threat model, tests, and explicit authority. The immediate state-changing
product milestone remains the separately planned Robinhood testnet lifecycle
continuation from index `18`.

## Sources

- [Vercel project configuration](https://vercel.com/docs/project-configuration/vercel-json)
- [Vercel environment variables](https://vercel.com/docs/environment-variables)
- [Vercel preview environments](https://vercel.com/docs/deployments/environments)
- [Vercel Git deployments](https://vercel.com/docs/git)
- [Vercel first-deployment Preview bug](https://github.com/vercel/vercel/issues/17069)
