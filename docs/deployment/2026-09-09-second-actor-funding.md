# Robinhood testnet second-actor funding — 2026-09-09

## Outcome

The separately controlled test actor
`0x04D5A0f57Cb2e110faC9703024888cd4562B6d6f` now has the assets required for
the two-user sandbox acceptance lane. Robinhood's faucet transaction
[`0xc9a5d901ddb0bd2d109fda652029550ec96b280433e9fb18e385da7c18a169b9`](https://explorer.testnet.chain.robinhood.com/tx/0xc9a5d901ddb0bd2d109fda652029550ec96b280433e9fb18e385da7c18a169b9)
succeeded and delivered `0.01` test ETH plus `5` each of AMZN, AMD, TSLA,
PLTR, and NFLX.

The actor is not the deployment sender and must not replace it. The reviewed
direct-CREATE plan remains bound to deployer
`0xCa60c8eF6934f8a97c6a503C4e3a46e87F5b08bD` at nonce `0`.

Sanitized machine-readable evidence is in
[`../../manifests/deployments/robinhood-testnet-second-actor-2026-09-09.json`](../../manifests/deployments/robinhood-testnet-second-actor-2026-09-09.json).

## Key boundary

The actor was created as a password-protected Foundry keystore outside the
repository at
`C:\Users\cosyc\.foundry\keystores\stonkhedge-robinhood-test-actor`.
Only the file's existence and filesystem metadata were inspected during this
checkpoint. No keystore payload, private key, or password was read, copied,
printed, or committed.

The actor is reserved for user/LP acceptance actions after deployment. It is
not an owner, guardian, treasurer, or deployment account.

## Faucet receipt

| Field | Value |
|---|---|
| Transaction | `0xc9a5d901ddb0bd2d109fda652029550ec96b280433e9fb18e385da7c18a169b9` |
| Status | `1` (`success`) |
| Block | `116017132` |
| Block hash | `0x8997f2dfdc485e03874383afe656aaff7911796dcfcf85c600317f0c46e69d1b` |
| Timestamp | `2026-09-09T04:44:24Z` |
| Faucet caller | `0xF691446e9386DEDF7364340fE35B09E8fE884d81` |
| Faucet distributor | `0x8762F93772c663c6a88Ba50900bd5381df2717Be` |
| Recipient | `0x04D5A0f57Cb2e110faC9703024888cd4562B6d6f` |
| Native transfer | `10000000000000000` wei (`0.01` test ETH) |
| Token mints | Five `5e18` transfers from the zero address, one per reviewed Stock Token |

The receipt logs and live `balanceOf` calls independently agree on the five
token deliveries. The faucet called its distributor; therefore the actor has
no outgoing faucet transaction and its nonce remains `0`.

## Pinned public recheck

At block `116025579`, hash
`0xdcab383d68dcae824666aff3e3396206317620d54fad6c8883d3cdac17bcf550`,
timestamp `2026-09-09T05:01:27Z`:

| Account | Native balance | Nonce | Runtime code |
|---|---:|---:|---|
| Second actor `0x04D5...6d6f` | `10000000000000000` wei | `0` | empty |
| Deployer `0xCa60...b08bD` | `10000000000000000` wei | `0` | empty |

Both accounts held exactly `5000000000000000000` units of every reviewed
18-decimal test Stock Token:

| Symbol | Address | Actor balance | Deployer balance |
|---|---|---:|---:|
| AMZN | `0x5884aD2f920c162CFBbACc88C9C51AA75eC09E02` | `5e18` | `5e18` |
| AMD | `0x71178BAc73cBeb415514eB542a8995b82669778d` | `5e18` | `5e18` |
| TSLA | `0xC9f9c86933092BbbfFF3CCb4b105A4A94bf3Bd4E` | `5e18` | `5e18` |
| PLTR | `0x1FBE1a0e43594b3455993B5dE5Fd0A7A266298d0` | `5e18` | `5e18` |
| NFLX | `0x3b8262A63d25f0477c4DDE23F83cfe22Cb768C93` | `5e18` | `5e18` |

The strict chain/dependency/deployer verifier completed successfully against a
current RPC head of `116022906`. A prior run reached only the local 120-second
command limit after reporting PASS results; it was not counted. The completed
retry is the gate result.

The current transaction-plan SHA-256 remains
`8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820`,
the deployer nonce remains `0`, and all 16 predicted CREATE addresses were
empty at the pinned block.

## Current boundary

The second-actor creation and funding gate is `PASS`. Public deployment remains
`NO_GO` until:

1. the existing deployer key is imported locally into a distinct encrypted
   Foundry keystore and its public address is confirmed without exposing the
   key;
2. the exact artifact hashes and stop-on-first-mismatch operator procedure
   receive a separate broadcast review; and
3. the strict verifier, pending nonce, plan hash, and 16 empty-address checks
   pass again immediately before the first signed transaction.

Nothing in this checkpoint authorizes use of the second actor to deploy or
authorizes any public broadcast.
