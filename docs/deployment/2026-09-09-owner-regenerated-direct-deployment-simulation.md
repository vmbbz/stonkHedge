# Owner-regenerated Robinhood direct-deployment simulation — 2026-09-09

## Outcome

Fresh nonce-bound artifacts for core
`f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d` passed exact size checks and a
16-transaction Anvil fork simulation. All CREATE addresses matched, every
receipt succeeded, every runtime was non-empty, final local nonce was `16`, and
11 constructor/wiring assertions passed.

The work used the testnet-only owner review waiver recorded in
[`../review/2026-09-09-owner-clean-room-reproduction.md`](../review/2026-09-09-owner-clean-room-reproduction.md).
No private key was read, no transaction was signed, and nothing was broadcast.
Public deployment remains `NO_GO` until the separate test actor is securely
created and funded, the fresh artifacts receive a broadcast review, and an
immediate state check passes.

Sanitized machine-readable evidence is in
[`../../manifests/deployments/robinhood-testnet-direct-preflight-2026-09-09-owner.json`](../../manifests/deployments/robinhood-testnet-direct-preflight-2026-09-09-owner.json).
The large config, bundle, plan, and report remain outside Git in the separate
local review workspace.

## Fresh public snapshot

Artifact generation started from:

| Field | Value |
|---|---|
| Chain | Robinhood testnet `46630` |
| Block | `115890338` |
| Block hash | `0x9a658071cbb6d9ed54a3a78d82c86c1c72a12afb8b2048360ea16f7fec97f315` |
| Timestamp | `2026-09-09T00:12:17Z` |
| Deployer | `0xCa60c8eF6934f8a97c6a503C4e3a46e87F5b08bD` |
| Pending nonce | `0` |
| Native balance | `0.01` test ETH |

The generated plan covers nonces `0` through `15`. Before simulation, all 16
predicted public addresses had empty code. A second public recheck at block
`115895680`, hash
`0x3e95ca511f7ab706a0ba769c7c105f3a83c1348fd19edf91c7e1448e3ab57fb7`,
confirmed nonce `0`, unchanged native balance, and all 16 addresses still empty.

## Artifact evidence

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Direct config | 9,551 | `728898b3f201e3c4421b00e9fcb2b7587796971e55fef73ac504a081da489cc0` |
| Release bundle | 588,811 | `aec0fa8797c950dbdd80dea7a3737b5cf1fa7b41eef3217ca254238b5aaa372c` |
| Transaction plan | 592,897 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Simulation report | 6,512 | `8964382c7049999de814d286f229cf55f2a1d087b1b34b8443f82a11354b9910` |

The simulation report binds to the exact transaction-plan hash above.

The direct config matches the historical nonce-0 config byte-for-byte. The
fresh bundle and plan have the same byte lengths but different hashes from the
2026-09-08 artifacts. A second bundle build in the current clean checkout
reproduced `aec0fa...a372c` byte-for-byte. The source of the historical
environment/artifact drift was not established, so the historical bundle and
plan were not reused. The fresh plan is the only current candidate.

## Gates reproduced

- derived-config dry run: PASS, 7 metadata plus 9 logic deployments;
- exact EIP-170/EIP-3860 size gate with 256-byte runtime policy margin: PASS;
- transaction-plan validation: PASS, 16 consecutive zero-value CREATEs;
- same-checkout repeat bundle: byte-for-byte PASS;
- loopback Anvil client and target chain ID: PASS;
- exact plan execution: 16 successful receipts, final nonce `16`;
- created-address and non-empty-runtime checks: 16/16 PASS; and
- constructor/wiring checks: 11/11 PASS.

`PanopticPoolV2` remains the tightest logic runtime at 24,275 bytes, leaving 301
bytes below EIP-170. `PanopticFactoryV4` remains the largest initcode at 40,654
bytes and the largest simulated transaction at 10,749,128 gas, below the
configured 16,711,680 transaction gas limit.

The wiring assertions checked:

- guardian admin and treasurer;
- BuilderFactory owner;
- RiskEngine guardian, BuilderFactory, two cross buffers, and vegoid;
- PanopticPoolV2's SFPM reference; and
- PanopticFactoryV4 name and symbol.

## Current boundary

The deployer EOA must remain frozen. Any outgoing transaction changes the nonce
and invalidates all four artifacts.

Before public broadcast:

1. create the second actor through a hidden-password, encrypted-keystore flow;
2. use Robinhood's address-based faucet and verify that actor's ETH and Stock
   Token balances;
3. repeat strict V4/deployer verification and all 16 empty-code checks;
4. compare the exact four hashes above in a separate broadcast review; and
5. send at most one planned transaction, wait for the receipt and expected
   runtime, then decide whether to continue.

No pool initialization, token approval, liquidity action, or market
registration may consume the deployer nonce before all 16 CREATEs finish.
