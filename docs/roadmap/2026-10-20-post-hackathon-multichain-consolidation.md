# Post-hackathon multichain consolidation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the completed BNB hackathon branch into StonkHedge's
evergreen product history without weakening the Robinhood execution boundary,
then leave `main` ready for a freshly planned Robinhood lifecycle continuation.

**Architecture:** StonkHedge remains one product with two isolated EVM lanes.
Robinhood Chain testnet is the deployed Panoptic options mechanism test; BSC
mainnet is an issuer-aware discovery, quote, and unsigned-simulation surface.
They share UI, policy vocabulary, evidence schemas, and fail-closed discipline,
but never inherit each other's contracts, balances, nonces, or authority.

**Tech Stack:** Markdown architecture and operations records, JSON-backed
TypeScript/Vite site, Vitest, Vercel serverless functions, Git feature-branch
integration.

---

## Accepted product decision

The BNB hackathon is a completed delivery event, not the new primary protocol
roadmap. Its useful product work survives as the BSC Gap Guardian lane. The next
state-changing engineering milestone remains Robinhood lifecycle completion,
starting from the reconciled canonical prefix through index `17` and requiring
a fresh plan, exact-head replay, and new authorization before index `18`.

No part of this consolidation authorizes a Robinhood transaction, a BSC wallet
connection, a BSC broadcast, a BSC contract deployment, or any mainnet spend.

### Task 1: Reconcile evergreen product status

**Files:**

- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/architecture/robinhood-testnet-system.md`
- Modify: `plan.md`

- [x] **Step 1: Replace event-time BNB language with post-hackathon product language**

  Describe Gap Guardian as a retained BSC simulation-only lane, link the live
  site, and preserve the exact zero-contract/zero-broadcast boundary.

- [x] **Step 2: Reconcile Robinhood state through index 17**

  Update every current-state summary, flow label, and next-step paragraph that
  still reports `0..16`, `17/29`, or a stop before buyer WETH approval. The
  accepted state is `0..17`, `18/29`, stopped after the exact buyer WETH
  approval and before index `18`, the buyer WETH deposit.

- [x] **Step 3: Add the multichain decision to the master plan**

  Add a post-hackathon roadmap section and decision-log entry defining
  Robinhood as the primary deployed options lane and BSC as the current
  issuer/route-safety lane. State that a BSC options deployment requires its
  own infrastructure, issuer, liquidity, licensing, security, and authority
  qualification.

- [x] **Step 4: Check the edited claims**

  Run:

  ```powershell
  rg -n "Active BNB|not yet recorded|0\.\.16|17/29|stopped before buyer WETH approval" README.md docs plan.md
  ```

  Expected: no stale current-state claim remains; historical evidence may keep
  its original values when explicitly dated.

### Task 2: Reconcile hosted deployment and public-access evidence

**Files:**

- Modify: `docs/deployment/2026-10-09-bnb-preview-deployment.md`
- Modify: `docs/hackathons/evidence/2026-10-10/07-public-access-check.md`
- Modify: `docs/hackathons/2026-10-10-submission-readiness.md`

- [x] **Step 1: Record the actual hosted release**

  Record stable URL `https://stonkhedge.vercel.app`, immutable deployment URL
  `https://stonkhedge-emrdylgvn-katzs-projects-2f9ffaf0.vercel.app`, deployment
  ID `dpl_FGePgh7U19tUZRymumfxbY6jJ8Kh`, Vercel region `cpt1`, and release commit
  `eb76e6d`. Preserve the earlier failed Preview attempts as chronology rather
  than presenting them as the current state.

- [x] **Step 2: Record the runtime boundary honestly**

  State that the server-side module-resolution and US-origin jurisdiction
  failures were fixed, that static hosting returned HTTP 200, and that the
  final live Binance smoke test reached the upstream API before receiving
  business code `42900` after repeated acceptance traffic. Do not describe a
  rate-limited call as a product or deployment failure.

- [x] **Step 3: Close event-time evidence without publishing PII**

  Mark the event package as owner-reported submitted and the delivery window as
  closed. Do not commit the raw Google Form screenshot, email address, wallet
  address, Telegram handle, API credentials, quote IDs, or executable calldata.

### Task 3: Index the post-hackathon roadmap

**Files:**

- Modify: `docs/README.md`
- Modify: `docs/roadmap/2026-10-20-post-hackathon-multichain-consolidation.md`

- [x] **Step 1: Add this roadmap to the documentation map**

  Place it before event-specific documents and make the immediate sequence
  explicit: consolidate BSC evidence, complete Robinhood indexes `18..28`,
  derive withdrawals from canonical post-close state, then decide whether BSC
  remains a safety lens or receives a separately qualified execution design.

- [x] **Step 2: Self-review the roadmap**

  Run:

  ```powershell
  rg -n "T[B]D|T[O]DO|implement l[a]ter|fill i[n]" docs/roadmap/2026-10-20-post-hackathon-multichain-consolidation.md
  ```

  Expected: no output.

### Task 4: Verify, commit, push, and integrate

**Files:**

- Verify: all tracked files changed by Tasks 1-3
- Preserve untracked: `buildl.md`

- [x] **Step 1: Verify documentation and source hygiene**

  Run:

  ```powershell
  git diff --check
  git diff -- . ':!buildl.md'
  git status --short
  ```

  Expected: no whitespace error, no credential file, and `buildl.md` remains
  untracked and unstaged.

- [x] **Step 2: Run the full repository gate**

  Run:

  ```powershell
  npm run check
  ```

  Expected: all Vitest files pass and the TypeScript/Vite production build exits
  zero.

- [ ] **Step 3: Commit and push the feature branch**

  Stage only the roadmap and reconciled documentation, commit with
  `docs(roadmap): consolidate post-hackathon multichain plan`, push
  `hackathon/bnb-tokenized-stocks-2026`, and verify its remote SHA equals local
  `HEAD`.

- [ ] **Step 4: Fast-forward main and verify again**

  Switch to `main`, fetch `origin`, require that `origin/main` is an ancestor of
  the feature branch, fast-forward `main`, rerun `npm run check`, push `main`,
  and verify local `main`, `origin/main`, and the integrated feature SHA match.
  Do not delete the event branch in this round; it remains submission
  provenance.

## Round-2 handoff

After integration, the next branch is a Robinhood continuation-planning branch.
Its first output is read-only: a fresh public snapshot proving buyer nonce,
writer nonce, exact index-17 WETH allowance, balances, runtimes, issuer controls,
and market wiring. Only then may it generate and simulate a new time-bound
index-`18..28` continuation and request separate authorization.
