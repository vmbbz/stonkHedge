# E6 redacted live-acceptance transcript

**Capture completed:** 2026-10-10T12:26:26.396Z / 14:26:26 SAST

**Application revision:** `d28f3ad13a235f5968e9e8c43cebe35961b36069`

**Source:** loopback production build with a server-only Binance Web3 adapter

**Boundary:** BSC API data and unsigned simulation only. No wallet, private
key, signing operation, broadcast operation, or transaction receipt was used.

## Comparison

```text
request: NVDA issuer comparison on BSC chain 56
resolved underlying: NVDA / Nvidia Corp
representations: 2
Ondo: NVDAon, normalized per share $230.67, price freshness 2 seconds
bStocks: NVDAB, normalized per share $230.29, price freshness 9 seconds
issuer-normalized gap: 16.24 bps
API observation: 2026-10-10 14:26 SAST
warnings: Ondo off-hours; bStocks session label unreported
```

## Bounded quote

```text
input: 5.10 USDT
selected representation: NVDAon by Ondo
estimated output: 0.02210062 NVDAon
vendor and mode: LiquidMesh / SWAP
reported price impact: 0.00%
reported path: Kipseli + Uniswap V4
receiver binding: 0x6719e8...f5750f
approval target: 0xb44446...5fdda5
browser payload: decoded metadata only; no transaction built
```

## Unsigned simulation

```text
approval: SUCCESS
swap: FAILED
reason: BEP20 transfer amount exceeds balance
final verdict: BLOCKED
approval selector: 0x095ea7b3
swap selector: 0xad43f73d
exact approval: 5.10 USDT
slippage cap: 0.5%
vendor: LiquidMesh
safety result: no signing gate opened
```

The application retained SHA-256 fingerprints for the non-executable payloads
but did not return raw quote IDs or executable calldata to the browser. The
machine-readable record is [`capture-manifest.json`](./capture-manifest.json),
and the visible results are preserved in E1 through E4.
