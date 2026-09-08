# stonkHedge

stonkHedge is an early-stage project exploring Panoptic-native perpetual options and risk-management workflows for Robinhood Stock Tokens. The first public integration lane targets Robinhood Chain testnet; Base Sepolia remains a secondary ERC-8056 compatibility lane.

The current repository is the product and delivery control plane. It contains the researched execution plan and will later hold chain manifests, deployment verification, monitoring, and the developer-facing application. Protocol and SDK changes remain isolated in auditable upstream forks.

## Start here

- Read [`plan.md`](./plan.md), beginning with **stonkHedge build and Robinhood Chain testnet launch plan**.
- Read [`CONTRIBUTING.md`](./CONTRIBUTING.md) before starting work across the product, protocol, or SDK repositories.
- Use the [Checkpoint B evidence](./docs/baseline/2026-09-08-checkpoint-b.md), checked-in baseline manifest, and verifier before changing inherited protocol behavior.
- Review the [exact-sender direct-deployment simulation](./docs/deployment/2026-09-08-direct-deployment-simulation.md) and its sanitized manifest before any Robinhood testnet deployment work.
- See the [verified faucet and mainnet Safe-readiness evidence](./docs/deployment/2026-09-08-faucet-and-mainnet-safe-readiness.md) for the current funding state and the distinction between on-chain Safe support and Panoptic's salt-bound Safe.
- Complete the [independent core and candidate-V4 review gate](./docs/review/2026-09-08-core-f4abdd7-and-v4-candidate.md) before any public transaction trusts the candidate or any nonce-derived artifact is regenerated for broadcast.
- Use the [controllable Stock Token specification](./docs/specs/controllable-stock-token.md) for local issuer-failure testing; never present that test double as issuer code or deploy it as a public Robinhood Stock Token.
- Reproduce the [standalone controllable-token harness evidence](./docs/testing/2026-09-08-controllable-stock-token-harness.md) at core commit `159dabd...`; protocol lifecycle integration remains pending.
- Run `pwsh -File .\scripts\verify-robinhood-testnet.ps1` before any chain-specific simulation or broadcast. Use `-SkipFundingGate` only for read-only infrastructure qualification.
- Treat all material before that section as background research, not an approved specification.
- The current milestone is a valueless Robinhood Chain testnet vertical slice. No stonkHedge contracts have been deployed yet.

## Repository map

| Repository | Purpose |
|---|---|
| [`vmbbz/stonkHedge`](https://github.com/vmbbz/stonkHedge) | Product, plans, manifests, monitoring, and later UI |
| [`vmbbz/panoptic-v2-core`](https://github.com/vmbbz/panoptic-v2-core) | Protocol fork; upstream is `panoptic-labs/panoptic-v2-core` |
| [`vmbbz/panoptic-sdk`](https://github.com/vmbbz/panoptic-sdk) | SDK fork; upstream is `panoptic-labs/panoptic-sdk` |

The repositories are intentionally separate. Contract changes belong in the core fork, transaction construction and decoding belong in the SDK fork, and chain manifests, public evidence, monitoring, and the application belong here.

## Safety and licensing

- Panoptic v2 core is currently licensed under BUSL-1.1 with an ENS-based Additional Use Grant. Testnet work does not imply production rights.
- Tokenized equities and equity options can be legally restricted. Mainnet asset enablement requires issuer, jurisdiction, and legal qualification.
- Never commit wallet keys, seed phrases, `.env` files, RPC credentials, or explorer API keys.
- A green testnet deployment is not mainnet authorization and is not evidence of an independent audit.
