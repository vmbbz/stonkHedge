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

## Honest remaining boundary at the 2026-10-11 check

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

## Post-submission addendum — 2026-10-20

The owner reported that both the Developer Experience Report and project form
were submitted before the event lock. The repository intentionally does not
store the raw form screenshot, contact email, prize wallet, Telegram handle, or
private confirmation receipt.

The following public surfaces were rechecked with unauthenticated HTTP GET
requests on 2026-10-20:

| Artifact | Public URL | Result |
|---|---|---|
| Stable hosted site | <https://stonkhedge.vercel.app/> | HTTP 200 |
| Immutable hosted deployment | <https://stonkhedge-emrdylgvn-katzs-projects-2f9ffaf0.vercel.app/> | HTTP 200; deployment `dpl_FGePgh7U19tUZRymumfxbY6jJ8Kh`, commit `eb76e6d`, region `cpt1` |
| Repository branch | <https://github.com/vmbbz/stonkHedge/tree/hackathon/bnb-tokenized-stocks-2026> | HTTP 200 |
| Submitted demo video | <https://www.youtube.com/watch?v=uyjI4A-HF5Y> | HTTP 200 |

This closes the earlier “no hosted URL” and “no video URL” evidence gaps. It
does not prove that the demo met the form's four-minute limit, that a BSC trade
occurred, or that the Binance API will avoid future upstream rate limits. The
accepted hosted surface remains live-data and unsigned-simulation only.
