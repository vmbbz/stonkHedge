# Contributing to stonkHedge

Thank you for helping build stonkHedge. This project combines inherited smart-contract code, chain integrations, an SDK, and a user-facing product. Small, evidence-backed changes are easier to review and materially safer than broad cross-repository rewrites.

This guide is the working agreement for the project owner, collaborators, and external contributors. It applies even when only two people are coding.

## 1. Read before changing code

1. Read the approved section of [`plan.md`](./plan.md), beginning at **stonkHedge build and Robinhood Chain testnet launch plan**.
2. Read the nearest repository `README`, license, build configuration, and relevant tests before editing inherited logic.
3. Run the product repository's baseline verifier and record any existing failure before introducing a new one:

   ```powershell
   pwsh -File .\scripts\verify-baseline.ps1
   ```

   Before chain-specific simulation or deployment work, also run the live Robinhood testnet verifier. `-SkipFundingGate` is permitted only for read-only qualification; deployment preflight uses strict mode:

   ```powershell
   pwsh -File .\scripts\verify-robinhood-testnet.ps1 -SkipFundingGate
   pwsh -File .\scripts\verify-robinhood-testnet.ps1
   ```

4. Do not treat a testnet receipt, green unit test, or third-party audit file as proof that the complete product is safe or mainnet-ready.

## 2. Choose the correct repository

| Repository | Put these changes here | Do not put these changes here |
|---|---|---|
| `vmbbz/stonkHedge` | Product UI, chain manifests, deployment verification, monitoring, runbooks, architecture decisions, and public evidence | Modified Panoptic contracts or a private deployment key |
| `vmbbz/panoptic-v2-core` | The smallest reviewed protocol or contract change, its Foundry regression tests, and contract-specific documentation | Product UI, chain-specific secrets, or speculative product helpers |
| `vmbbz/panoptic-sdk` | Typed reads, simulations, transaction builders, encoders/decoders, SDK tests, and package documentation | Deployment authority, private keys, or protocol invariants that belong on-chain |

If one feature touches multiple repositories, split it into reviewable checkpoints. Land and push core changes first, then SDK changes, then update the product manifest with the exact commit SHAs. Never combine unrelated work merely because it supports the same milestone.

## 3. Local checkout and remotes

The expected Windows layout is:

```text
C:\dev-shared\stonkHedge
C:\dev-shared\stonkHedge-core
C:\dev-shared\stonkHedge-sdk
```

The product repository uses `origin` for `vmbbz/stonkHedge`. Each Panoptic fork uses:

- `origin`: the `vmbbz` fork, for project branches and pull requests;
- `upstream`: the corresponding `panoptic-labs` repository, fetch-only for ordinary work.

Never develop directly on either fork's `main`. Keep it available for clean upstream synchronization. A collaborator without write access to the `vmbbz` organization should push the same feature branch to their own fork and open a pull request; do not share GitHub credentials.

Before starting a branch:

```powershell
git status --short --branch
git fetch origin
# Core and SDK forks only:
git fetch upstream
```

Create a short-lived branch from the commit named by the current product manifest. Suggested names are:

- `feat/issue-number-short-name`
- `fix/issue-number-short-name`
- `test/issue-number-short-name`
- `docs/issue-number-short-name`

Do not rebase or force-push another contributor's branch without agreement. If upstream moved, record the old and new upstream SHAs and review the complete range before rebasing or merging it.

## 4. Define the checkpoint first

Every significant change starts with an issue or a plan delta containing:

- the user or protocol problem;
- the repository and components in scope;
- explicit non-goals;
- security, accounting, licensing, and deployment risks;
- acceptance evidence and exact test lanes;
- rollback or disable behavior; and
- cross-repository dependencies, if any.

For a behavior change, first add the smallest regression that fails for the intended reason. Preserve inherited behavior outside the stated scope. If the change appears to require a large refactor, document why the existing design cannot safely satisfy the requirement before rewriting it.

## 5. Implementation workflow

1. Confirm the branch begins at the pinned baseline and the worktree contains no unrelated files.
2. Add the red regression for changed behavior.
3. Implement the narrowest coherent fix.
4. Run focused tests while iterating.
5. Run the broader repository lane appropriate to the affected surface.
6. Inspect `git diff`, run `git diff --check`, and scan the staged files for secrets.
7. Update documentation whenever architecture, public behavior, configuration, deployment, or operational procedure changes.
8. Commit the completed checkpoint with only its files staged.
9. Push the feature branch and open a pull request using the repository template.
10. After dependent core or SDK changes land, pin their immutable SHAs in the product manifest and verify again from the product repository.

Do not leave placeholder contracts, fake addresses, inflated sample payloads, disabled assertions, or unexplained skipped tests in a checkpoint. A deliberately incomplete lane must fail closed and be labeled `BLOCKED` or `SKIPPED` with a reason.

## 6. Test and evidence expectations

Use the test ladder in `plan.md`. At minimum:

- Documentation/configuration: parse structured files, validate internal links or referenced paths, run a secret scan, and run `git diff --check`.
- Core contracts: focused Foundry regression, relevant V4/RiskEngine/Pool/SFPM tests, then fuzz or invariant coverage proportional to the accounting risk.
- SDK: typecheck, lint, focused Vitest regression, broader unit suite, build, and package smoke test where the checkout supports them.
- Product/UI: unit and integration tests plus wrong-chain, failed-simulation, stale-manifest, wallet-rejection, and accessibility paths.
- Deployment changes: exact-chain simulation, reviewed manifest, bounded broadcast, receipt reconciliation, runtime-code verification, and independent read-only verification.

Report each lane as `PASS`, `FAIL`, `BLOCKED`, `SKIPPED`, or `NOT APPLICABLE`. Include the exact command, commit SHA, relevant counts, and reason for every non-pass result. Never summarize a blocked or unrun lane as green.

Live acceptance matters. For an end-to-end flow, capture public chain ID, actors' public addresses, transaction hashes, expected versus actual state, and timestamps without exposing secrets.

## 7. Review rules for two-person collaboration

- The author does not approve their own security-sensitive change.
- The other collaborator reviews contract accounting, deployment manifests, chain addresses, role/ownership changes, upgrade paths, and any code that can move or lock assets.
- Verify addresses by chain ID and runtime code; names and tickers are display metadata, not identity.
- Resolve review conversations in the pull request. Material design changes require an updated plan or architecture decision before merge.
- Prefer squash merge for a noisy iteration branch and ordinary merge/rebase only when preserving individual commits adds audit value.
- Delete merged feature branches only after the immutable merge commit and product manifest pin are recorded.

When the friend's GitHub handle is known, add branch protection and required review rules in GitHub. Do not add a guessed `CODEOWNERS` identity.

## 8. Commit conventions

Use concise Conventional Commit-style subjects:

```text
feat(core): add guarded market entry check
fix(sdk): reject mismatched pool token order
test(core): cover scheduled multiplier transition
docs(project): record baseline blocker
chore(manifest): pin testnet deployment evidence
```

A commit should compile or clearly document why it cannot. Avoid drive-by formatting and unrelated cleanup. Generated files belong in Git only when they are deterministic, reviewed release inputs/outputs and the repository explicitly requires them.

## 9. Secrets and deployment safety

Never commit or paste:

- private keys, seed phrases, keystores, passwords, or `.env` contents;
- private RPC/API tokens, explorer keys, session cookies, or CI secrets;
- shell output that accidentally includes any of the above.

Public wallet addresses, public contract addresses, transaction hashes, and bytecode hashes are acceptable evidence. The authorized testnet deployer address is public, but its private key remains outside these repositories.

All broadcast tooling must require an explicit chain ID, expected sender, reviewed address manifest, simulation result, and bounded transaction list. Mainnet deployment or movement of real value requires separate, explicit authorization and is outside the current contribution scope.

## 10. Pull-request acceptance

A pull request is ready only when:

- its scope and non-goals are clear;
- the diff contains no unrelated user work;
- new behavior has regression coverage;
- required lanes are green or honestly marked with accepted blockers;
- licenses and inherited notices are preserved;
- documentation and manifests match the code;
- no secret or machine-specific artifact is staged;
- rollback/disable behavior is understood; and
- a reviewer can reproduce the evidence from the exact commit.

Use the pull-request template; do not replace evidence with “works on my machine.”
