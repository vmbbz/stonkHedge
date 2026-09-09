# Robinhood direct-deployment authorization — 2026-09-09

## Decision

The project owner explicitly approved the exact testnet-only plan and operator
recorded in
[`../../manifests/deployments/robinhood-testnet-direct-authorization-2026-09-09.json`](../../manifests/deployments/robinhood-testnet-direct-authorization-2026-09-09.json).
The approval covers transaction indexes `0` through `15`, but only through the
enforced one-transaction/wait/verify/stop workflow.

The approval does not cover pool initialization, liquidity, market
registration, a different plan or operator, Robinhood mainnet, production-like
operation, monetization, or real value.

## Exact approved inputs

| Item | Approved value |
|---|---|
| Chain | Robinhood Chain testnet `46630` |
| Sender | `0xCa60c8eF6934f8a97c6a503C4e3a46e87F5b08bD` |
| Plan SHA-256 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Operator SHA-256 | `556e0751d787df3149412bc2dd417f57d7c10e7481878a9acf35853709e4db25` |
| Maximum index | `15` |
| Policy | `ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH` |
| Approval time | `2026-09-09T05:48:11Z` |

The machine-readable authorization also binds the simulation report,
deployment preflight, second-actor funding evidence, runtime-hash operator
manifest, and operator commit `5edba99`.

## Operational boundary

Authorization does not bypass any gate. For each selected index, the operator
must:

1. validate all bound hashes and the exact chain/sender/plan;
2. verify the current pending nonce and every prior/future CREATE address;
3. run the strict chain/dependency/token/deployer verifier;
4. repeat the complete public-state and gas preflight;
5. accept the encrypted keystore password only through Foundry's hidden local
   prompt;
6. verify the signature belongs to the authorized deployer;
7. submit exactly one transaction;
8. wait for and verify its receipt, created address, runtime length, runtime
   hash, and next nonce; and
9. stop before the next index.

Any indeterminate submission result requires an explorer/nonce/address check
before another action. Any mined failure consumes its nonce and revokes safe
continuation under the current plan.

The private key and keystore password must never enter chat, Git, a command-line
argument, an environment variable, or a committed file.

## Friend-review status

The invited review remains defence-in-depth for this valueless testnet sequence.
It remains mandatory for mainnet or real-value use, and any rejection during
this sequence immediately stops further transactions.
