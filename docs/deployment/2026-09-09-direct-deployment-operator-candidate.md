# Robinhood direct-deployment operator candidate — 2026-09-09

## Outcome

The file-based Robinhood direct-deployment operator is ready for owner review.
Its read-only index-0 preflight passed against the exact regenerated plan, both
evidence manifests, the supplemental runtime-hash replay, and current public
chain state. No public transaction was signed or broadcast.

The operator is
[`../../scripts/operate_robinhood_direct_deployment.py`](../../scripts/operate_robinhood_direct_deployment.py).
Its tests are
[`../../scripts/tests/test_operate_robinhood_direct_deployment.py`](../../scripts/tests/test_operate_robinhood_direct_deployment.py),
and its machine-readable runtime/preflight evidence is
[`../../manifests/deployments/robinhood-testnet-direct-operator-2026-09-09.json`](../../manifests/deployments/robinhood-testnet-direct-operator-2026-09-09.json).

This is an executable candidate, not broadcast authorization. An authorization
manifest is deliberately absent. `--execute` was tested without that file and
stopped before signing.

## Why a file-based operator is necessary

The reviewed plan contains initcode between 3,269 and 40,654 bytes. Passing the
larger values as hex in `cast send --create <hex>` exceeds Windows' process
command-line limit. The operator instead:

1. reads the exact reviewed JSON plan from disk;
2. recomputes every initcode hash using Foundry's Ethereum Keccak
   implementation over standard input;
3. RLP-encodes one legacy EIP-155 contract-creation transaction in memory;
4. asks Foundry to sign only its 32-byte digest through the encrypted keystore;
   and
5. submits the signed transaction through JSON-RPC standard input.

The operator has no raw-private-key or password argument. The password remains
inside Foundry's hidden prompt. The script does not print or persist the
signature or raw signed transaction.

## Exact bindings

| Item | SHA-256 |
|---|---|
| Operator | `556e0751d787df3149412bc2dd417f57d7c10e7481878a9acf35853709e4db25` |
| Operator tests | `caf22226bebc45e4e8df57a55e60b660e5668e32deab9bafa74efceacf77cfd9` |
| Direct transaction plan | `8b138a56a2b284a61994b1ec60206b246a3a8e17cc56f0ec38b95590e3ed0820` |
| Fork simulation report | `8964382c7049999de814d286f229cf55f2a1d087b1b34b8443f82a11354b9910` |
| Owner-regenerated deployment manifest | `7887e802f2240542b550cd1aecbd76381e0933461743f2833ed822e65cdaa7bf` |
| Second-actor funding manifest | `66da6f25f60c6f1ccfc5c05a6289ddded3d6282327e3944b08afb00394048a22` |
| Operator/runtime manifest | `98c36a8063afd97580ec23ce86018982ecc37d3f4e2101a96351d10ff1bc5b83` |

An eventual authorization manifest must repeat and bind these inputs. Changing
the operator, plan, report, or evidence manifest invalidates authorization.

## Enforced execution behavior

The operator defaults to a read-only dry-run and enforces:

- exact official RPC URL and chain ID `46630`;
- exact deployer `0xCa60c8eF6934f8a97c6a503C4e3a46e87F5b08bD`;
- exact full-file and per-initcode hashes;
- exact pending nonce for the selected index;
- empty code at the selected and every future CREATE address;
- exact byte length and runtime code hash at every prior CREATE address;
- positive balance, a bounded gas price, and gas estimate below `2^24`;
- a testnet-only authorization manifest with an approver, UTC timestamp,
  artifact bindings, maximum index, and one-at-a-time policy;
- an exact plan- and nonce-specific confirmation phrase;
- an automatic rerun of the strict Robinhood verifier before signing;
- a second complete nonce/address/gas preflight after that verifier;
- Foundry signature verification against the expected deployer;
- one `eth_sendRawTransaction` call per invocation;
- successful receipt, exact created address, exact runtime length and hash, and
  next pending nonce before PASS; and
- an unconditional stop after one successful transaction.

If submission returns an indeterminate error, the operator tells the user not
to retry until the explorer, pending nonce, and expected address are checked.
If a mined CREATE fails, its nonce is consumed: stop and regenerate the entire
remaining plan rather than advancing to the next index.

Receipt evidence must be written outside the Git repository. The operator never
selects the next transaction automatically.

## Reproduced evidence

### Tests and encoding

- Python compile: PASS.
- Operator unit tests: 12 PASS, 0 FAIL.
- EIP-155 RLP/signing cross-check: the raw transaction matched the independent
  locally installed `eth-account` implementation byte-for-byte and recovered
  the same ephemeral signer. `eth-account` is not a runtime dependency.
- Missing-authorization negative path: PASS; `--execute` stopped before signing.

### Runtime-hash replay

The exact plan was replayed with 16 successful CREATE receipts on a loopback
Anvil fork at public block `116040196`, hash
`0x12a994298982c53950d4292eb177d65d1464e6ac7824cd58821af866228772b0`,
timestamp `2026-09-09T05:34:03Z`. The final local nonce was `16`, all 16
runtime byte lengths matched the original simulation, and exact runtime code
hashes are recorded in the operator manifest. The Anvil process was stopped.

An initial attempt to repeat the historical block-`115890338` fork failed
before startup because the public RPC no longer served the required archive
state. It produced no deployment receipt and is not counted. The original
pinned simulation remains the constructor/wiring evidence; the current-head
replay supplements it with runtime hashes.

### Final manifest-bound public dry-run

At block `116042618`, hash
`0x1786755401cc28dd1cc2fa8f6dcf4dcd2fc986350b5910ceedecc8c6bf580418`,
timestamp `2026-09-09T05:39:52Z`:

- deployer pending nonce: `0`;
- deployer native balance: `10000000000000000` wei;
- current transaction: index/nonce `0`, `dataContracts[0]`;
- expected CREATE address: `0x05449292522e3FCCD58dB4f947A94BD083d5e13d`;
- empty predicted addresses: 16/16;
- gas price: `10000000` wei;
- estimate: `5983057` gas;
- fixed gas limit: `16711680`; and
- broadcast attempted: false.

The first Python HTTPS transport attempt refused the RPC's certificate as
expired under the machine's 2026 clock. TLS validation was not disabled. The
operator now uses Foundry's successful RPC transport and sends large JSON
parameters over standard input; it does not use Foundry's `--insecure` flag.

## Reproduce the read-only review

From `C:\dev-shared\stonkHedge`:

```powershell
python .\scripts\operate_robinhood_direct_deployment.py `
  --plan C:\dev-shared\stonkHedge-review\artifacts\robinhood-46630-20260909-owner\transaction-plan.json `
  --simulation-report C:\dev-shared\stonkHedge-review\artifacts\robinhood-46630-20260909-owner\simulation-report.json `
  --deployment-manifest .\manifests\deployments\robinhood-testnet-direct-preflight-2026-09-09-owner.json `
  --funding-manifest .\manifests\deployments\robinhood-testnet-second-actor-2026-09-09.json `
  --operator-manifest .\manifests\deployments\robinhood-testnet-direct-operator-2026-09-09.json `
  --rpc-url https://rpc.testnet.chain.robinhood.com `
  --index 0
```

This command does not open a key or sign or broadcast anything.

## Owner review and approval gate

Before an authorization manifest is created, the owner should verify:

1. the seven exact hashes in this document;
2. sender, chain, nonce range `0..15`, expected addresses, and role assignments;
3. that this remains a valueless, non-monetized Robinhood testnet deployment;
4. that 16 non-atomic CREATE transactions and stop/regenerate behavior are
   accepted;
5. that reuse of the non-official chain-`46630` V4 candidate remains accepted
   under the recorded testnet waiver;
6. that the encrypted deployer keystore reports the exact sender and its
   password remains private; and
7. that only one transaction may be submitted and reviewed at a time.

The owner can approve after that review by replying with all three facts: the
full plan SHA-256, the full operator SHA-256, and the maximum transaction index
authorized. A friend review remains valuable defence-in-depth; any later
rejection stops the testnet sequence and remains mandatory before mainnet or
real-value use.

Until that explicit approval is recorded and converted into the exact bound
authorization manifest, public broadcast remains `NO_GO`.
