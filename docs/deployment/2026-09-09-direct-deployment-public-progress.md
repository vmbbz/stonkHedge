# Robinhood direct-deployment public progress — 2026-09-09

## Current state

The authorized Robinhood Chain testnet direct-CREATE sequence is in progress
and stopped safely after transaction index `8`. Exactly nine of the 16
approved zero-value CREATE transactions have been broadcast.

The machine-readable checkpoint is
[`../../manifests/deployments/robinhood-testnet-direct-public-progress-2026-09-09.json`](../../manifests/deployments/robinhood-testnet-direct-public-progress-2026-09-09.json).

## Transaction 0 evidence

| Item | Verified value |
|---|---|
| Plan SHA-256 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Label | `dataContracts[0]` |
| Nonce | `0` |
| Transaction | [`0xbf6ad4dd...4fda9e`](https://explorer.testnet.chain.robinhood.com/tx/0xbf6ad4ddcf9a22f584f53de5053186a2d9e5ab93eecbfb0847633ab1ac4fda9e) |
| Receipt | success (`status = 1`) |
| Block | `116058458` |
| Created address | `0x05449292522e3FCCD58dB4f947A94BD083d5e13d` |
| Gas used | `5,781,743` |
| Runtime length | `24,439` bytes |
| Runtime code hash | `0xdd0ec57b873af7e553fbd9404281da95203e426929ecb3dfb419bbcbcd87aa7f` |
| External operator evidence SHA-256 | `21996edbaa19301942a8738f92ad141cb9927ec96590c5ef8f67f95977a09201` |

The receipt was queried independently after the operator returned. The runtime
was then fetched again from the expected address and matched the frozen runtime
length and hash.

## Transaction 1 evidence

| Item | Verified value |
|---|---|
| Plan SHA-256 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Label | `dataContracts[1]` |
| Nonce | `1` |
| Transaction | [`0x2faa5abd...6c2050`](https://explorer.testnet.chain.robinhood.com/tx/0x2faa5abd65568cf95a5439e86bc312fab2586a6f287c29a2d77fb2c32f6c2050) |
| Receipt | success (`status = 1`) |
| Block | `116067257` |
| Created address | `0xb1820CEE1BE8b9eDdC382eE83304efBe5ceD0019` |
| Gas used | `5,016,221` |
| Runtime length | `20,669` bytes |
| Runtime code hash | `0x97d0d1afc82d4dba1ebaabd94ef9cdc7e38789cf81a410565d2502634c446615` |
| External operator evidence SHA-256 | `53b872a07ef9f85b3144e7b92af77970525f993e7f58124b0e29c5b68b44078f` |

The transaction-1 receipt and deployed runtime were independently fetched from
the public RPC after the operator stopped, with exact matches to the frozen
plan and simulation evidence.

## Transaction 2 evidence

| Item | Verified value |
|---|---|
| Plan SHA-256 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Label | `dataContracts[2]` |
| Nonce | `2` |
| Transaction | [`0x122f1406...dce1dcd`](https://explorer.testnet.chain.robinhood.com/tx/0x122f14060ca93053445646b08260b0290400c45e4fa76e6925c634e59dce1dcd) |
| Receipt | success (`status = 1`) |
| Block | `116071445` |
| Created address | `0xa318218fEA30EA64c223A1c8E96551c68B007656` |
| Gas used | `5,034,762` |
| Runtime length | `20,141` bytes |
| Runtime code hash | `0x3027b6042e96eabda4468d04a6366f717c3546f2e106b51b5b490574529e7097` |
| External operator evidence SHA-256 | `c0acc47ec082f1c876ed71f5f9de4522db7cf4925e5f5269884399f56676ffe1` |

The transaction-2 receipt and runtime were independently re-read from the
public RPC and matched the frozen plan exactly.

## Transaction 3 evidence

| Item | Verified value |
|---|---|
| Plan SHA-256 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Label | `dataContracts[3]` |
| Nonce | `3` |
| Transaction | [`0x5a97890e...05d977`](https://explorer.testnet.chain.robinhood.com/tx/0x5a97890ee1c6262d39d8808cfa7f15e67d1e6e513b15d0f1af3498ecc905d977) |
| Receipt | success (`status = 1`) |
| Block | `116075738` |
| Created address | `0xbAD75CD571AeE30644aBe85Da20B6Fa527106c5d` |
| Gas used | `4,319,052` |
| Runtime length | `17,266` bytes |
| Runtime code hash | `0xa6b6c4a12dfb4616558a30a3596c6739691e37385e69f8a366f7a43abb98d3e9` |
| External operator evidence SHA-256 | `9078163fab18e22e0ec41ce7cc06df0630d41051b5db0ba0d5f3e0803b8e4f54` |

The transaction-3 receipt and runtime were independently re-read from the
public RPC and matched the frozen plan exactly.

## Transaction 4 evidence

| Item | Verified value |
|---|---|
| Plan SHA-256 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Label | `dataContracts[4]` |
| Nonce | `4` |
| Transaction | [`0x3574eb67...3f5a3b`](https://explorer.testnet.chain.robinhood.com/tx/0x3574eb675f52135c29f4396cef21c92458bab91fecdc08ace1653e2e903f5a3b) |
| Receipt | success (`status = 1`) |
| Block | `116079235` |
| Created address | `0x1F6f1daab8b0d9605D7A880bD738aEe6Fd764107` |
| Gas used | `5,787,367` |
| Runtime length | `23,768` bytes |
| Runtime code hash | `0xabdee20968abd3e6dddcd1ba58d0f5c7890a14122a01cefa0db86278acf43e32` |
| External operator evidence SHA-256 | `d13d30be62c6761f1f4f7d96f0cad527ac4a98763e1b085db20bd46218684a05` |

The transaction-4 receipt and runtime were independently re-read from the
public RPC and matched the frozen plan exactly.

## Transaction 5 evidence

| Item | Verified value |
|---|---|
| Plan SHA-256 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Label | `dataContracts[5]` |
| Nonce | `5` |
| Transaction | [`0x7e92dc21...6cba42f`](https://explorer.testnet.chain.robinhood.com/tx/0x7e92dc2190ee5e89e32e3cff19cb933a00fe94202c36229104c905cea6cba42f) |
| Receipt | success (`status = 1`) |
| Block | `116082889` |
| Created address | `0xB1D560De10Fb3733d7A5dFefED0388A2435fdaBA` |
| Gas used | `5,845,225` |
| Runtime length | `24,482` bytes |
| Runtime code hash | `0xd2bff9530ad0696f844e93d21e22e09572653ab5b07d7571a6c7d6829ea54552` |
| External operator evidence SHA-256 | `4ec37fcb30b4e190197016f615af890b838f9207da32acc4c197607de0114930` |

The transaction-5 receipt and runtime were independently re-read from the
public RPC and matched the frozen plan exactly.

## Transaction 6 evidence

| Item | Verified value |
|---|---|
| Plan SHA-256 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Label | `dataContracts[6]` |
| Nonce | `6` |
| Transaction | [`0x74d6aaf6...b1cf7e`](https://explorer.testnet.chain.robinhood.com/tx/0x74d6aaf6568918c2b22aea366593ec2a3a7c4cdad48b123b9cc43f06ebb1cf7e) |
| Receipt | success (`status = 1`) |
| Block | `116087683` |
| Created address | `0x19E58B3113579A02c2C266e1be0049766F333338` |
| Gas used | `1,350,738` |
| Runtime length | `5,602` bytes |
| Runtime code hash | `0x01a10a5c6d647a90937bd3e5ca3cfc9d7ee260feff04d4dc0a27a72461b21a4c` |
| External operator evidence SHA-256 | `86b4b75ff5972cceffa7331bb2cd7d1112e99f967641e611aae4c7448d3527d4` |

The transaction-6 receipt and runtime were independently re-read from the
public RPC and matched the frozen plan exactly.

## Transaction 7 evidence

| Item | Verified value |
|---|---|
| Plan SHA-256 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Label | `PanopticMath` |
| Nonce | `7` |
| Transaction | [`0x76517a4e...d0e9ca`](https://explorer.testnet.chain.robinhood.com/tx/0x76517a4e1b3c045a474a0123508143d29a0d6571b492a9f84a756ba151d0e9ca) |
| Receipt | success (`status = 1`) |
| Block | `116091933` |
| Created address | `0x45bb5b5719bB2B6cf516BE7C063B4D318890D3e7` |
| Gas used | `805,690` |
| Runtime length | `3,217` bytes |
| Runtime code hash | `0x3ac5052d577e4eab2a5d19f2f6fa439ef8a566842b27fcc00cd6316ecc1a563a` |
| External operator evidence SHA-256 | `4fc3ccf713b773506dbe3de523045ed8f4e87b62227801c76386469928d4eba4` |

The `PanopticMath` receipt and runtime were independently re-read from the
public RPC and matched the frozen plan exactly.

## Transaction 8 evidence

| Item | Verified value |
|---|---|
| Plan SHA-256 | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Label | `InteractionHelper` |
| Nonce | `8` |
| Transaction | [`0x137518d0...83cd99`](https://explorer.testnet.chain.robinhood.com/tx/0x137518d0c035b72d9e2a155320eae6a58c9a968e105f99e2bbaeace77183cd99) |
| Receipt | success (`status = 1`) |
| Block | `116100739` |
| Created address | `0xDCf9936b330D6957CaD463f850D1F2B6F1eABc3A` |
| Gas used | `1,658,573` |
| Runtime length | `7,020` bytes |
| Runtime code hash | `0x400dce9bcf7100fffe197f589166b3fb9ca221d834c44834dc9fdd120a1aa1cf` |
| External operator evidence SHA-256 | `b9c464a2f3bae3aeb247fb9c4962ecf753d7aa5d635e0df7bd402c55965e4422` |

The `InteractionHelper` receipt and runtime were independently re-read from
the public RPC and matched the frozen plan exactly.

## Continuation gate

A read-only index-9 operator preflight passed at block `116101398`:

- deployer pending nonce: `9`;
- prior deployments verified: `9`;
- remaining predicted addresses verified empty: `7`;
- deployer balance: `0.00964400629` test ETH;
- next deployment: `CollateralTrackerV2` at
  `0x41119aAd1c69dba3934D0A061d312A52B06B27DF`; and
- next gas estimate: `5,010,674`, below the plan gas limit of `16,711,680`.

No index-9 transaction was signed or broadcast during that preflight. The
sequence remains governed by the approved one-transaction/wait/verify/stop
policy. Pool initialization, liquidity provision, and market registration are
still outside this authorization.
