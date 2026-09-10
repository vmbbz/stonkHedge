# Progress content

`progress.json` is the editorial layer for the build-in-public dashboard. Add
one entry after a meaningful, evidence-backed round of work.

Required fields describe the target, status, summary, outcomes, commits,
contract references, transaction references, evidence, media, and related
repository documents. Contract and transaction facts are generated from the
canonical deployment and market manifests; do not duplicate or hand-edit an
address merely to change the website.

Before committing an entry:

1. link only to checked-in evidence or a canonical explorer transaction;
2. distinguish external/reused contracts from StonkHedge deployments;
3. say what is still excluded or untested;
4. use `next` for a target and `complete` only after reconciliation; and
5. run `npm run check`.

The content-integrity tests reject duplicate IDs, unknown contract or
transaction references, malformed hashes, and broken repository document
paths.
