# Public-access check before final submission

**Checked:** 2026-10-11 01:28 SAST

The checks below used unauthenticated HTTP requests. No GitHub, Vercel, or
Binance credentials were supplied.

| Artifact | Public URL | Result |
|---|---|---|
| Repository branch | <https://github.com/vmbbz/stonkHedge/tree/hackathon/bnb-tokenized-stocks-2026> | HTTP 200; page title identified the expected branch |
| Public README | <https://raw.githubusercontent.com/vmbbz/stonkHedge/hackathon/bnb-tokenized-stocks-2026/README.md> | HTTP 200; 12,670 bytes before this evidence update |
| Judge instructions | <https://raw.githubusercontent.com/vmbbz/stonkHedge/hackathon/bnb-tokenized-stocks-2026/docs/hackathons/2026-10-10-submission-readiness.md> | HTTP 200; document contained `Judge quickstart boundary` |

The GitHub HTML page for the judge-instruction document returned one transient
HTTP 503 during the audit, while the same public branch and raw document both
returned HTTP 200. The submission should link to the normal GitHub permalink;
the raw check establishes that the committed document itself is public.

## Honest remaining boundary

- The linked Vercel project reported **no deployments found**. Do not submit a
  guessed Vercel alias as a deployed application.
- The official requirement permits a deployed link **or** instructions a judge
  can follow. The public judge quickstart fulfills the latter route.
- The final demo-video URL does not exist yet. E8 remains partial until the
  final sub-four-minute video is uploaded and its share URL opens in a private
  browser window without an account prompt.
- Final Git provenance must be checked after this evidence update is committed
  and pushed, because a document cannot contain the hash of the commit that
  contains itself.
