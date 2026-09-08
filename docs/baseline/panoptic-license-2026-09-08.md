# Panoptic V2 license gate — 2026-09-08

## Conclusion

Pinned Panoptic V2 core commit `d65310d6cfbaadb6910fa9446cc59c6541060749` is primarily licensed under Business Source License 1.1. Its base text permits copying, modification, derivative works, redistribution, and **non-production** use, requires the license to remain conspicuously displayed, and changes to GPL-2.0-or-later on the earlier of `2028-03-01` or an alternative date named through ENS.

At Ethereum block `25932700`, neither ENS child name referenced by the license existed as a configured ENS node, and the parent resolver did not support wildcard resolution. No Additional Use Grant and no earlier change date could therefore be retrieved. stonkHedge must not infer production rights from a blank record.

Project policy for the current milestone:

- local work and a bounded, valueless, non-monetized testnet integration used for development/testing may continue under the base non-production grant;
- the core fork must retain the license and every file-specific SPDX/license notice;
- the sandbox must be clearly labeled testnet, valueless, unaudited, and non-production;
- no fees, monetization, real-value custody, mainnet deployment, or production service may rely on this review; and
- written permission from the licensor or qualified legal advice is required before production-like public operation.

This is an engineering policy based on the observable license text, not legal advice.

## Pinned source

- Repository: https://github.com/panoptic-labs/panoptic-v2-core
- Commit: `d65310d6cfbaadb6910fa9446cc59c6541060749`
- License file: https://github.com/panoptic-labs/panoptic-v2-core/blob/d65310d6cfbaadb6910fa9446cc59c6541060749/LICENSE
- Licensor named by the file: Axicon Labs Limited
- Licensed work: Panoptic V2, copyright 2023–2026
- Additional Use Grant pointer: `v2-license-grants.panoptic.eth`
- Change-date pointer: `v2-license-date.panoptic.eth`
- Fallback change date: `2028-03-01`
- Change license: GPL-2.0-or-later

The repository also identifies different licenses for interfaces, tokens, `Multicall.sol`, and some libraries/types. File-level notices control those files and must not be normalized away.

## Reproducible ENS evidence

Ethereum mainnet ENS Registry: `0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e`

Configured resolver for `panoptic.eth`: `0x4976fb03C32e5B8cfe2b6cCB31c09Ba78EBaBa41`

| Name | Namehash | Registry owner | Registry resolver |
|---|---|---|---|
| `v2-license-grants.panoptic.eth` | `0x38e8f75e6ab9821e6e758b97e6839d633af36f915ab744f4199243097a50eab0` | zero address | zero address |
| `v2-license-date.panoptic.eth` | `0x5d06f6febea5b42bcf56d5f1539d08096584988dcd26f1800ef7e858cb4c1365` | zero address | zero address |
| `panoptic.eth` | `0x349f067c97eba7f3986c4d6d3580af1045f117c5964ecfa6ef380421f19bbe36` | `0x5f4ea55444339a6Edf19a57906245aC1CeD2e7c5` | `0x4976fb03C32e5B8cfe2b6cCB31c09Ba78EBaBa41` |

The parent resolver returned `false` for ENSIP-10 extended/wildcard resolver interface `0x9061b923`. Direct `contenthash`, `addr`, and common `text` lookups against the grant child name on that resolver returned empty/zero values. Direct common `text` lookups for the date child were also empty.

Representative commands:

```powershell
cast namehash v2-license-grants.panoptic.eth
cast namehash v2-license-date.panoptic.eth
cast call --rpc-url https://ethereum-rpc.publicnode.com 0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e "owner(bytes32)(address)" 0x38e8f75e6ab9821e6e758b97e6839d633af36f915ab744f4199243097a50eab0
cast call --rpc-url https://ethereum-rpc.publicnode.com 0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e "resolver(bytes32)(address)" 0x38e8f75e6ab9821e6e758b97e6839d633af36f915ab744f4199243097a50eab0
cast call --rpc-url https://ethereum-rpc.publicnode.com 0x4976fb03C32e5B8cfe2b6cCB31c09Ba78EBaBa41 "supportsInterface(bytes4)(bool)" 0x9061b923
```

Re-run these reads immediately before any public release because ENS state is mutable. Archive the block number, results, core commit, and exact license text each time.
