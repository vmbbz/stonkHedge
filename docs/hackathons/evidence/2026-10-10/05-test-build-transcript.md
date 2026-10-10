# E5 test and production-build transcript

**Executed:** 2026-10-11 01:26 SAST

**Working revision before this evidence update:**
`a32165a866bb4b2a692c8f0386a012e2af693b57`

**Command:** `npm run check`

**Result:** PASS

```text
> stonkhedge-build-in-public@0.1.0 check
> npm run test && npm run build

> stonkhedge-build-in-public@0.1.0 test
> vitest run

 RUN  v5.0.0 C:/dev-shared/stonkHedge

 Test Files  9 passed (9)
      Tests  48 passed (48)
   Start at  01:26:44
   Duration  1.75s (import 53%, transform 37%, tests 8%, worker 2%)

> stonkhedge-build-in-public@0.1.0 build
> tsc -b && vite build

vite v7.3.6 building client environment for production...
transforming...
20 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                         1.26 kB | gzip:   0.63 kB
dist/assets/index-DrNSO43U.css         39.94 kB | gzip:   9.73 kB
dist/assets/index-ESoHv620.js         160.92 kB | gzip:  41.24 kB | map:   154.84 kB
dist/assets/architecture-CI6KN22Y.js  496.43 kB | gzip: 125.18 kB | map: 2,717.44 kB
built in 4.52s
```

The transcript contains no environment values, API credentials, authorization
headers, private keys, wallet material, quote identifiers, or transaction
calldata.
