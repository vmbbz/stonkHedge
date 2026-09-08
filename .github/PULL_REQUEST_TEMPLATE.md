## Summary

What problem does this change solve, and what is the user/protocol outcome?

## Scope and non-goals

- Repository/component in scope:
- Explicitly out of scope:
- Related core/SDK/product issues or pull requests:

## Risk review

- Accounting/solvency impact:
- Token/issuer-policy impact:
- Chain, deployment, role, or upgrade impact:
- Licensing/legal/public-copy impact:
- Rollback or disable path:

## Tests and evidence

List exact commands and results. Use `PASS`, `FAIL`, `BLOCKED`, `SKIPPED`, or `NOT APPLICABLE`.

| Status | Command or live check | Evidence/counts |
|---|---|---|
|  |  |  |

For live-chain changes, include only public chain IDs, addresses, transaction hashes, code hashes, and expected/actual state.

## Security checklist

- [ ] No secret, `.env` value, private RPC credential, keystore, or private key is included.
- [ ] External addresses are verified by chain ID and code, not ticker/name alone.
- [ ] State-changing calls simulate successfully and fail closed when prerequisites drift.
- [ ] Inherited licenses, notices, and strategic behavior are preserved.
- [ ] No unrelated, generated, temporary, or machine-specific files are staged.

## Documentation and manifests

- [ ] User/developer documentation is updated where behavior or architecture changed.
- [ ] Product manifests pin every dependent core/SDK commit and deployment artifact.
- [ ] A clean reviewer can reproduce the relevant evidence from this commit.

## Reviewer focus

Call out the lines, assumptions, or failure modes that deserve the closest second-person review.
