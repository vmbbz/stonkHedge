# stonkHedge

stonkHedge is an early-stage project exploring Panoptic-native perpetual options and risk-management workflows for tokenized equities on Base.

The current repository is the product and delivery control plane. It contains the researched execution plan and will later hold chain manifests, deployment verification, monitoring, and the developer-facing application. Protocol and SDK changes remain isolated in auditable upstream forks.

## Start here

- Read [`plan.md`](./plan.md), beginning with **stonkHedge build and Base Sepolia launch plan**.
- Treat all material before that section as background research, not an approved specification.
- The current milestone is a valueless Base Sepolia vertical slice. No stonkHedge contracts have been deployed yet.

## Repository map

| Repository | Purpose |
|---|---|
| [`vmbbz/stonkHedge`](https://github.com/vmbbz/stonkHedge) | Product, plans, manifests, monitoring, and later UI |
| [`vmbbz/panoptic-v2-core`](https://github.com/vmbbz/panoptic-v2-core) | Protocol fork; upstream is `panoptic-labs/panoptic-v2-core` |
| [`vmbbz/panoptic-sdk`](https://github.com/vmbbz/panoptic-sdk) | SDK fork; upstream is `panoptic-labs/panoptic-sdk` |

## Safety and licensing

- Panoptic v2 core is currently licensed under BUSL-1.1 with an ENS-based Additional Use Grant. Testnet work does not imply production rights.
- Tokenized equities and equity options can be legally restricted. Mainnet asset enablement requires issuer, jurisdiction, and legal qualification.
- Never commit wallet keys, seed phrases, `.env` files, RPC credentials, or explorer API keys.
- A green testnet deployment is not mainnet authorization and is not evidence of an independent audit.
