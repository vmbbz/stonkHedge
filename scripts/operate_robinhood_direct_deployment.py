#!/usr/bin/env python3
"""Preflight or send exactly one reviewed Robinhood direct-CREATE transaction.

The default mode is read-only. Execution requires a separate authorization
manifest, an exact confirmation phrase, and a password-protected Foundry
keystore. The script never accepts a raw private key or password argument.

Large initcode is read from the plan and encoded in-process so Windows does not
have to carry it in a command-line argument. Foundry signs only the 32-byte
legacy EIP-155 transaction digest through the encrypted keystore.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Callable


CHAIN_ID = 46630
OFFICIAL_RPC_URL = "https://rpc.testnet.chain.robinhood.com"
DEFAULT_GAS_LIMIT = 0xFF0000  # 16,711,680; strictly below 2^24.
EIP7825_TRANSACTION_GAS_LIMIT = 1 << 24
DEFAULT_MAX_GAS_PRICE_WEI = 100_000_000
ADDRESS_PATTERN = re.compile(r"^0x[0-9a-fA-F]{40}$")
HASH_PATTERN = re.compile(r"^(?:0x)?[0-9a-fA-F]{64}$")
HEX_BYTES_PATTERN = re.compile(r"^0x(?:[0-9a-fA-F]{2})+$")
SIGNATURE_PATTERN = re.compile(r"^0x[0-9a-fA-F]{130}$")


def _int_bytes(value: int) -> bytes:
    if not isinstance(value, int) or value < 0:
        raise ValueError("RLP integers must be non-negative")
    if value == 0:
        return b""
    return value.to_bytes((value.bit_length() + 7) // 8, "big")


def _length_prefix(length: int, short_offset: int, long_offset: int) -> bytes:
    if length <= 55:
        return bytes([short_offset + length])
    encoded_length = _int_bytes(length)
    return bytes([long_offset + len(encoded_length)]) + encoded_length


def rlp_encode(value) -> bytes:
    """Encode bytes, non-negative integers, or nested lists as canonical RLP."""

    if isinstance(value, int):
        return rlp_encode(_int_bytes(value))
    if isinstance(value, str):
        raise TypeError("RLP strings must be encoded explicitly as bytes")
    if isinstance(value, (list, tuple)):
        payload = b"".join(rlp_encode(item) for item in value)
        return _length_prefix(len(payload), 0xC0, 0xF7) + payload
    if not isinstance(value, bytes):
        raise TypeError(f"unsupported RLP value: {type(value).__name__}")
    if len(value) == 1 and value[0] < 0x80:
        return value
    return _length_prefix(len(value), 0x80, 0xB7) + value


def _normalize_hash(value: str, name: str) -> str:
    if not isinstance(value, str) or HASH_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a 32-byte hex hash")
    return value.lower().removeprefix("0x")


def _validate_address(value: str, name: str) -> None:
    if not isinstance(value, str) or ADDRESS_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a 20-byte hex address")


def _hex_bytes(value: str, name: str) -> bytes:
    if not isinstance(value, str) or HEX_BYTES_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be non-empty even-length hex bytes")
    return bytes.fromhex(value[2:])


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cast_keccak(payload: bytes) -> str:
    result = subprocess.run(
        ["cast", "keccak"],
        input="0x" + payload.hex(),
        capture_output=True,
        text=True,
        check=True,
    )
    digest = result.stdout.strip()
    return "0x" + _normalize_hash(digest, "cast keccak output")


def compute_create_address(
    sender: str,
    nonce: int,
    hasher: Callable[[bytes], str] = cast_keccak,
) -> str:
    _validate_address(sender, "sender")
    digest = hasher(rlp_encode([bytes.fromhex(sender[2:]), nonce]))
    normalized = _normalize_hash(digest, "CREATE digest")
    return "0x" + normalized[-40:]


def validate_plan(
    plan: dict,
    initcode_hasher: Callable[[bytes], str] = cast_keccak,
    address_computer: Callable[[str, int], str] = compute_create_address,
) -> None:
    if plan.get("status") != "SIMULATION_REQUIRED":
        raise ValueError("plan status must be SIMULATION_REQUIRED")
    if plan.get("deploymentMethod") != "EOA_CREATE":
        raise ValueError("plan deployment method must be EOA_CREATE")
    if plan.get("chainId") != CHAIN_ID:
        raise ValueError(f"plan chain ID must be {CHAIN_ID}")

    sender = plan.get("sender")
    _validate_address(sender, "plan sender")
    start_nonce = plan.get("startNonce")
    next_nonce = plan.get("nextNonce")
    transactions = plan.get("transactions")
    if not isinstance(start_nonce, int) or start_nonce < 0:
        raise ValueError("plan start nonce must be non-negative")
    if not isinstance(transactions, list) or not transactions:
        raise ValueError("plan transactions must be a non-empty array")
    if plan.get("transactionCount") != len(transactions):
        raise ValueError("plan transaction count mismatch")
    if next_nonce != start_nonce + len(transactions):
        raise ValueError("plan next nonce mismatch")

    for index, transaction in enumerate(transactions):
        expected_nonce = start_nonce + index
        if transaction.get("ordinal") != index:
            raise ValueError(f"transaction {index} ordinal mismatch")
        if not isinstance(transaction.get("label"), str) or not transaction["label"]:
            raise ValueError(f"transaction {index} label is invalid")
        if transaction.get("from", sender).lower() != sender.lower():
            raise ValueError(f"transaction {index} sender mismatch")
        if transaction.get("to") is not None:
            raise ValueError(f"transaction {index} is not contract creation")
        if transaction.get("nonce") != expected_nonce:
            raise ValueError(f"transaction {index} nonce is not consecutive")
        if transaction.get("valueWei") != "0":
            raise ValueError(f"transaction {index} value must be zero")

        address = transaction.get("expectedCreatedAddress")
        _validate_address(address, f"transaction {index} expected address")
        recomputed_address = address_computer(sender, expected_nonce)
        if recomputed_address.lower() != address.lower():
            raise ValueError(f"transaction {index} CREATE address mismatch")

        initcode = _hex_bytes(transaction.get("initcode"), f"transaction {index} initcode")
        if transaction.get("initcodeBytes") != len(initcode):
            raise ValueError(f"transaction {index} initcode byte length mismatch")
        expected_hash = _normalize_hash(
            transaction.get("initcodeHash"), f"transaction {index} initcode hash"
        )
        actual_hash = _normalize_hash(
            initcode_hasher(initcode), f"transaction {index} recomputed initcode hash"
        )
        if actual_hash != expected_hash:
            raise ValueError(f"transaction {index} initcode hash mismatch")


def validate_simulation_report(report: dict, plan: dict, plan_hash: str) -> None:
    if report.get("status") != "PASS" or report.get("mode") != "LOCAL_ANVIL_ONLY":
        raise ValueError("simulation report must be a passing local-Anvil report")
    for field in ("chainId", "sender", "startNonce", "nextNonce"):
        left = report.get(field)
        right = plan.get(field)
        if isinstance(left, str) and isinstance(right, str):
            matches = left.lower() == right.lower()
        else:
            matches = left == right
        if not matches:
            raise ValueError(f"simulation report {field} mismatch")
    if _normalize_hash(report.get("planSha256"), "report plan hash") != _normalize_hash(
        plan_hash, "plan hash"
    ):
        raise ValueError("simulation report plan hash mismatch")

    deployments = report.get("deployments")
    transactions = plan["transactions"]
    if not isinstance(deployments, list) or len(deployments) != len(transactions):
        raise ValueError("simulation deployment count mismatch")
    for index, (deployment, transaction) in enumerate(zip(deployments, transactions)):
        if deployment.get("label") != transaction.get("label"):
            raise ValueError(f"simulation deployment {index} label mismatch")
        if deployment.get("nonce") != transaction.get("nonce"):
            raise ValueError(f"simulation deployment {index} nonce mismatch")
        if deployment.get("expectedCreatedAddress", "").lower() != transaction.get(
            "expectedCreatedAddress", ""
        ).lower():
            raise ValueError(f"simulation deployment {index} address mismatch")
        if _normalize_hash(
            deployment.get("initcodeHash"), f"simulation deployment {index} initcode hash"
        ) != _normalize_hash(
            transaction.get("initcodeHash"), f"transaction {index} initcode hash"
        ):
            raise ValueError(f"simulation deployment {index} initcode hash mismatch")
        if not isinstance(deployment.get("runtimeBytes"), int) or deployment["runtimeBytes"] <= 0:
            raise ValueError(f"simulation deployment {index} runtime bytes are invalid")


def validate_evidence_manifests(
    deployment_manifest: dict,
    funding_manifest: dict,
    plan: dict,
    plan_hash: str,
    report_hash: str,
) -> None:
    if deployment_manifest.get("network", {}).get("chainId") != plan["chainId"]:
        raise ValueError("deployment manifest network chain mismatch")
    artifacts = deployment_manifest.get("artifacts", {})
    if _normalize_hash(
        artifacts.get("transactionPlan", {}).get("sha256"), "manifest plan hash"
    ) != _normalize_hash(plan_hash, "plan hash"):
        raise ValueError("deployment manifest plan hash mismatch")
    if _normalize_hash(
        artifacts.get("simulationReport", {}).get("sha256"), "manifest report hash"
    ) != _normalize_hash(report_hash, "report hash"):
        raise ValueError("deployment manifest report hash mismatch")
    method = deployment_manifest.get("deploymentMethod", {})
    if method.get("value") != "EOA_CREATE":
        raise ValueError("deployment manifest method mismatch")
    if method.get("chainId", plan["chainId"]) != plan["chainId"]:
        raise ValueError("deployment manifest chain mismatch")
    if method.get("sender", "").lower() != plan["sender"].lower():
        raise ValueError("deployment manifest sender mismatch")
    if method.get("startNonce") != plan["startNonce"]:
        raise ValueError("deployment manifest start nonce mismatch")
    if method.get("transactionCount") != len(plan["transactions"]):
        raise ValueError("deployment manifest transaction count mismatch")

    if funding_manifest.get("status") != "SECOND_ACTOR_FUNDED_STRICT_PREFLIGHT_PASS_BROADCAST_BLOCKED":
        raise ValueError("second-actor funding manifest status mismatch")
    if funding_manifest.get("network", {}).get("chainId") != plan["chainId"]:
        raise ValueError("funding manifest chain mismatch")
    if funding_manifest.get("deployerRecheck", {}).get("address", "").lower() != plan[
        "sender"
    ].lower():
        raise ValueError("funding manifest deployer mismatch")
    funding_plan = funding_manifest.get("deploymentPlan", {})
    if _normalize_hash(funding_plan.get("sha256"), "funding manifest plan hash") != _normalize_hash(
        plan_hash, "plan hash"
    ):
        raise ValueError("funding manifest plan hash mismatch")
    if funding_manifest.get("broadcastGates", {}).get("secondActorKeystoreAndFunding") != "PASS":
        raise ValueError("second-actor funding gate is not PASS")


def validate_operator_manifest(
    operator_manifest: dict,
    plan: dict,
    report: dict,
    plan_hash: str,
    report_hash: str,
    operator_hash: str | None = None,
) -> None:
    if operator_manifest.get("status") != "OPERATOR_RUNTIME_HASH_REPLAY_PASS_AUTHORIZATION_REQUIRED":
        raise ValueError("operator manifest status mismatch")
    if operator_manifest.get("network", {}).get("chainId") != plan["chainId"]:
        raise ValueError("operator manifest chain mismatch")
    bindings = operator_manifest.get("artifactBindings", {})
    if _normalize_hash(bindings.get("transactionPlanSha256"), "operator plan hash") != _normalize_hash(
        plan_hash, "plan hash"
    ):
        raise ValueError("operator manifest plan hash mismatch")
    if _normalize_hash(
        bindings.get("simulationReportSha256"), "operator report hash"
    ) != _normalize_hash(report_hash, "report hash"):
        raise ValueError("operator manifest report hash mismatch")
    if operator_hash is not None and _normalize_hash(
        bindings.get("operatorSha256"), "operator script hash"
    ) != _normalize_hash(operator_hash, "operator hash"):
        raise ValueError("operator manifest script hash mismatch")

    expected = operator_manifest.get("expectedDeployments")
    if not isinstance(expected, list) or len(expected) != len(plan["transactions"]):
        raise ValueError("operator manifest deployment count mismatch")
    for index, (entry, transaction, deployment) in enumerate(
        zip(expected, plan["transactions"], report["deployments"])
    ):
        if entry.get("ordinal") != index or entry.get("label") != transaction["label"]:
            raise ValueError(f"operator deployment {index} identity mismatch")
        if entry.get("address", "").lower() != transaction["expectedCreatedAddress"].lower():
            raise ValueError(f"operator deployment {index} address mismatch")
        if entry.get("runtimeBytes") != deployment["runtimeBytes"]:
            raise ValueError(f"operator deployment {index} runtime bytes mismatch")
        _normalize_hash(entry.get("runtimeCodeHash"), f"operator deployment {index} runtime hash")


def validate_authorization(
    authorization: dict,
    plan: dict,
    plan_hash: str,
    index: int,
    *,
    operator_hash: str | None = None,
    report_hash: str | None = None,
    deployment_manifest_hash: str | None = None,
    funding_manifest_hash: str | None = None,
    operator_manifest_hash: str | None = None,
) -> None:
    if authorization.get("status") != "AUTHORIZED_ONE_TRANSACTION_AT_A_TIME":
        raise ValueError("authorization status is not executable")
    if authorization.get("chainId") != plan["chainId"]:
        raise ValueError("authorization chain mismatch")
    if authorization.get("sender", "").lower() != plan["sender"].lower():
        raise ValueError("authorization sender mismatch")
    if _normalize_hash(authorization.get("planSha256"), "authorization plan hash") != _normalize_hash(
        plan_hash, "plan hash"
    ):
        raise ValueError("authorization plan hash mismatch")
    maximum = authorization.get("maximumTransactionIndex")
    if not isinstance(maximum, int) or index > maximum:
        raise ValueError("authorization does not cover this transaction index")
    if authorization.get("executionPolicy") != "ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH":
        raise ValueError("authorization execution policy mismatch")
    if authorization.get("testnetOnly") is not True:
        raise ValueError("authorization must be explicitly testnet-only")
    if not isinstance(authorization.get("approvedBy"), str) or not authorization["approvedBy"].strip():
        raise ValueError("authorization approver is missing")
    if not isinstance(authorization.get("approvedAt"), str) or not authorization["approvedAt"].endswith("Z"):
        raise ValueError("authorization timestamp must be UTC")
    bindings = {
        "operatorSha256": operator_hash,
        "simulationReportSha256": report_hash,
        "deploymentManifestSha256": deployment_manifest_hash,
        "fundingManifestSha256": funding_manifest_hash,
        "operatorManifestSha256": operator_manifest_hash,
    }
    for field, expected in bindings.items():
        if expected is not None and _normalize_hash(
            authorization.get(field), f"authorization {field}"
        ) != _normalize_hash(expected, field):
            raise ValueError(f"authorization {field} mismatch")


class JsonRpcClient:
    def __init__(self, rpc_url: str, timeout: float = 45.0):
        if rpc_url != OFFICIAL_RPC_URL:
            raise ValueError(f"RPC URL must be exactly {OFFICIAL_RPC_URL}")
        self.rpc_url = rpc_url
        self.timeout = timeout
        self.request_id = 0

    def call(self, method: str, params: list):
        self.request_id += 1
        try:
            result = subprocess.run(
                [
                    "cast",
                    "rpc",
                    method,
                    "--raw",
                    "--rpc-url",
                    self.rpc_url,
                    "--rpc-timeout",
                    str(int(self.timeout)),
                ],
                input=json.dumps(params, separators=(",", ":")),
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            detail = (error.stderr or error.stdout or "unknown Foundry RPC error").strip()
            raise RuntimeError(f"{method} RPC request failed: {detail}") from error
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"{method} returned invalid JSON") from error


def validate_public_state(
    rpc,
    plan: dict,
    report: dict,
    operator_manifest: dict,
    *,
    index: int,
    gas_limit: int,
    max_gas_price: int,
) -> dict:
    transactions = plan["transactions"]
    if not isinstance(index, int) or index < 0 or index >= len(transactions):
        raise ValueError("transaction index is outside the plan")
    if gas_limit <= 0 or gas_limit >= EIP7825_TRANSACTION_GAS_LIMIT:
        raise ValueError("gas limit must be positive and below 2^24")
    if max_gas_price <= 0:
        raise ValueError("maximum gas price must be positive")

    chain_id = int(rpc.call("eth_chainId", []), 16)
    if chain_id != plan["chainId"]:
        raise RuntimeError(f"chain ID mismatch: expected {plan['chainId']}, got {chain_id}")
    block = rpc.call("eth_getBlockByNumber", ["latest", False])
    if not isinstance(block, dict):
        raise RuntimeError("latest block response is invalid")
    block_number_hex = block.get("number")
    block_hash = block.get("hash")
    block_timestamp_hex = block.get("timestamp")
    if (
        not isinstance(block_number_hex, str)
        or not isinstance(block_hash, str)
        or HASH_PATTERN.fullmatch(block_hash) is None
        or not isinstance(block_timestamp_hex, str)
    ):
        raise RuntimeError("latest block identity is incomplete")
    sender = plan["sender"]
    expected_nonce = plan["startNonce"] + index
    nonce = int(rpc.call("eth_getTransactionCount", [sender, "pending"]), 16)
    if nonce != expected_nonce:
        raise RuntimeError(f"pending nonce mismatch: expected {expected_nonce}, got {nonce}")

    for offset, (transaction, deployment) in enumerate(
        zip(transactions, report["deployments"])
    ):
        address = transaction["expectedCreatedAddress"]
        code = rpc.call("eth_getCode", [address, block_number_hex])
        if not isinstance(code, str) or not code.startswith("0x") or len(code) % 2:
            raise RuntimeError(f"invalid runtime response at {address}")
        runtime_bytes = (len(code) - 2) // 2
        if offset < index:
            expected_bytes = deployment["runtimeBytes"]
            if runtime_bytes != expected_bytes:
                raise RuntimeError(
                    f"prior address {address} runtime bytes {runtime_bytes}; expected {expected_bytes}"
                )
            expected_hash = _normalize_hash(
                operator_manifest["expectedDeployments"][offset]["runtimeCodeHash"],
                f"prior deployment {offset} runtime hash",
            )
            actual_hash = _normalize_hash(
                cast_keccak(_hex_bytes(code, f"prior deployment {offset} runtime")),
                f"prior deployment {offset} recomputed runtime hash",
            )
            if actual_hash != expected_hash:
                raise RuntimeError(f"prior address {address} runtime hash mismatch")
        elif runtime_bytes != 0:
            raise RuntimeError(f"future address {address} is not empty")

    balance = int(rpc.call("eth_getBalance", [sender, block_number_hex]), 16)
    gas_price = int(rpc.call("eth_gasPrice", []), 16)
    if gas_price <= 0 or gas_price > max_gas_price:
        raise RuntimeError(
            f"gas price {gas_price} exceeds allowed range 1..{max_gas_price}"
        )
    maximum_cost = gas_limit * gas_price
    if balance < maximum_cost:
        raise RuntimeError(
            f"deployer balance {balance} is below maximum transaction cost {maximum_cost}"
        )

    current = transactions[index]
    estimate = int(
        rpc.call(
            "eth_estimateGas",
            [
                {
                    "from": sender,
                    "data": current["initcode"],
                    "gas": hex(gas_limit),
                    "value": "0x0",
                },
                block_number_hex,
            ],
        ),
        16,
    )
    if estimate <= 0 or estimate > gas_limit:
        raise RuntimeError(f"gas estimate {estimate} exceeds gas limit {gas_limit}")
    return {
        "chainId": chain_id,
        "blockNumber": int(block_number_hex, 16),
        "blockHash": block_hash,
        "blockTimestamp": int(block_timestamp_hex, 16),
        "sender": sender,
        "nonce": nonce,
        "transactionIndex": index,
        "label": current["label"],
        "expectedCreatedAddress": current["expectedCreatedAddress"],
        "balanceWei": balance,
        "gasPriceWei": gas_price,
        "gasLimit": gas_limit,
        "gasEstimate": estimate,
        "maximumCostWei": maximum_cost,
        "priorAddressesVerified": index,
        "emptyAddressesVerified": len(transactions) - index,
    }


def unsigned_legacy_transaction(
    *, nonce: int, gas_price: int, gas_limit: int, data: bytes, chain_id: int
) -> bytes:
    return rlp_encode(
        [nonce, gas_price, gas_limit, b"", 0, data, chain_id, 0, 0]
    )


def parse_signature(signature: str) -> tuple[int, int, int]:
    if not isinstance(signature, str) or SIGNATURE_PATTERN.fullmatch(signature) is None:
        raise ValueError("signer returned an invalid 65-byte signature")
    raw = bytes.fromhex(signature[2:])
    r = int.from_bytes(raw[:32], "big")
    s = int.from_bytes(raw[32:64], "big")
    recovery = raw[64]
    if recovery in (27, 28):
        parity = recovery - 27
    elif recovery in (0, 1):
        parity = recovery
    else:
        raise ValueError(f"signature recovery byte is invalid: {recovery}")
    if r == 0 or s == 0:
        raise ValueError("signature r and s must be nonzero")
    return r, s, parity


def build_signed_legacy_transaction(
    *,
    nonce: int,
    gas_price: int,
    gas_limit: int,
    data: bytes,
    chain_id: int,
    r: int,
    s: int,
    parity: int,
) -> str:
    if parity not in (0, 1):
        raise ValueError("signature parity must be zero or one")
    eip155_v = chain_id * 2 + 35 + parity
    raw = rlp_encode([nonce, gas_price, gas_limit, b"", 0, data, eip155_v, r, s])
    return "0x" + raw.hex()


def sign_digest_with_foundry(digest: str, keystore: Path, sender: str) -> tuple[int, int, int]:
    if not keystore.is_file():
        raise FileNotFoundError(f"keystore not found: {keystore}")
    print("Foundry will now prompt once for the encrypted keystore password.")
    result = subprocess.run(
        ["cast", "wallet", "sign", digest, "--no-hash", "--keystore", str(keystore)],
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        check=True,
    )
    signature = result.stdout.strip()
    parse_signature(signature)
    subprocess.run(
        [
            "cast",
            "wallet",
            "verify",
            "--address",
            sender,
            "--no-hash",
            digest,
            signature,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return parse_signature(signature)


def run_strict_verifier(rpc_url: str) -> None:
    verifier = Path(__file__).resolve().with_name("verify-robinhood-testnet.ps1")
    if not verifier.is_file():
        raise FileNotFoundError(f"strict verifier not found: {verifier}")
    print("Running the strict Robinhood chain, dependency, token, and deployer verifier.")
    subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(verifier), "-RpcUrl", rpc_url],
        check=True,
    )


def confirmation_phrase(plan_hash: str, nonce: int) -> str:
    normalized = _normalize_hash(plan_hash, "plan hash")
    return f"BROADCAST_ROBINHOOD_{CHAIN_ID}_PLAN_{normalized[:8]}_NONCE_{nonce}"


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")
    temporary.replace(path)


def _poll_receipt(rpc, transaction_hash: str, timeout_seconds: int = 300) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        receipt = rpc.call("eth_getTransactionReceipt", [transaction_hash])
        if receipt is not None:
            return receipt
        time.sleep(1)
    raise TimeoutError(
        f"receipt still pending for {transaction_hash}; do not resubmit until nonce and address are checked"
    )


def _parse_int(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected a decimal or 0x-prefixed integer") from error


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--simulation-report", required=True, type=Path)
    parser.add_argument("--deployment-manifest", required=True, type=Path)
    parser.add_argument("--funding-manifest", required=True, type=Path)
    parser.add_argument("--operator-manifest", required=True, type=Path)
    parser.add_argument("--rpc-url", required=True)
    parser.add_argument("--index", required=True, type=int)
    parser.add_argument("--gas-limit", type=_parse_int, default=DEFAULT_GAS_LIMIT)
    parser.add_argument(
        "--max-gas-price", type=_parse_int, default=DEFAULT_MAX_GAS_PRICE_WEI
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--authorization-manifest", type=Path)
    parser.add_argument("--keystore", type=Path)
    parser.add_argument("--confirmation")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    plan = _read_json(args.plan)
    report = _read_json(args.simulation_report)
    deployment_manifest = _read_json(args.deployment_manifest)
    funding_manifest = _read_json(args.funding_manifest)
    operator_manifest = _read_json(args.operator_manifest)
    plan_hash = file_sha256(args.plan)
    report_hash = file_sha256(args.simulation_report)
    operator_hash = file_sha256(Path(__file__).resolve())
    deployment_manifest_hash = file_sha256(args.deployment_manifest)
    funding_manifest_hash = file_sha256(args.funding_manifest)
    operator_manifest_hash = file_sha256(args.operator_manifest)

    validate_plan(plan)
    validate_simulation_report(report, plan, plan_hash)
    validate_evidence_manifests(
        deployment_manifest, funding_manifest, plan, plan_hash, report_hash
    )
    validate_operator_manifest(
        operator_manifest, plan, report, plan_hash, report_hash, operator_hash
    )
    rpc = JsonRpcClient(args.rpc_url)
    preflight = validate_public_state(
        rpc,
        plan,
        report,
        operator_manifest,
        index=args.index,
        gas_limit=args.gas_limit,
        max_gas_price=args.max_gas_price,
    )
    preflight.update(
        {
            "status": "READ_ONLY_PREFLIGHT_PASS",
            "planSha256": plan_hash,
            "simulationReportSha256": report_hash,
            "operatorManifestSha256": operator_manifest_hash,
            "broadcastAttempted": False,
        }
    )
    print(json.dumps(preflight, indent=2))

    if not args.execute:
        print("Dry-run only: no key was opened, no transaction was signed, and nothing was broadcast.")
        return

    if args.authorization_manifest is None:
        raise ValueError("--authorization-manifest is required with --execute")
    if args.keystore is None:
        raise ValueError("--keystore is required with --execute")
    if args.output_dir is None:
        raise ValueError("--output-dir is required with --execute")
    repository_root = Path(__file__).resolve().parents[1]
    try:
        args.output_dir.resolve().relative_to(repository_root)
    except ValueError:
        pass
    else:
        raise ValueError("execution output directory must be outside the Git repository")

    authorization = _read_json(args.authorization_manifest)
    validate_authorization(
        authorization,
        plan,
        plan_hash,
        args.index,
        operator_hash=operator_hash,
        report_hash=report_hash,
        deployment_manifest_hash=deployment_manifest_hash,
        funding_manifest_hash=funding_manifest_hash,
        operator_manifest_hash=operator_manifest_hash,
    )
    current = plan["transactions"][args.index]
    expected_confirmation = confirmation_phrase(plan_hash, current["nonce"])
    if args.confirmation != expected_confirmation:
        raise ValueError(f"confirmation mismatch; expected exactly {expected_confirmation}")

    run_strict_verifier(args.rpc_url)
    # Re-read every nonce/address/gas gate after the longer strict verifier and
    # use this second snapshot as the signing input.
    preflight = validate_public_state(
        rpc,
        plan,
        report,
        operator_manifest,
        index=args.index,
        gas_limit=args.gas_limit,
        max_gas_price=args.max_gas_price,
    )
    data = _hex_bytes(current["initcode"], "current initcode")
    unsigned = unsigned_legacy_transaction(
        nonce=current["nonce"],
        gas_price=preflight["gasPriceWei"],
        gas_limit=args.gas_limit,
        data=data,
        chain_id=plan["chainId"],
    )
    digest = cast_keccak(unsigned)
    r, s, parity = sign_digest_with_foundry(digest, args.keystore, plan["sender"])
    raw_transaction = build_signed_legacy_transaction(
        nonce=current["nonce"],
        gas_price=preflight["gasPriceWei"],
        gas_limit=args.gas_limit,
        data=data,
        chain_id=plan["chainId"],
        r=r,
        s=s,
        parity=parity,
    )

    # Close the most consequential race after signing. Any mismatch discards the
    # signature without publishing it and leaves the public nonce unchanged.
    final_nonce = int(rpc.call("eth_getTransactionCount", [plan["sender"], "pending"]), 16)
    final_code = rpc.call("eth_getCode", [current["expectedCreatedAddress"], "latest"])
    final_gas_price = int(rpc.call("eth_gasPrice", []), 16)
    if final_nonce != current["nonce"]:
        raise RuntimeError("pending nonce changed after signing; raw transaction was not published")
    if final_code != "0x":
        raise RuntimeError("expected address became occupied after signing; raw transaction was not published")
    if final_gas_price > preflight["gasPriceWei"]:
        raise RuntimeError("gas price increased after signing; raw transaction was not published")

    try:
        transaction_hash = rpc.call("eth_sendRawTransaction", [raw_transaction])
    except Exception as error:
        raise RuntimeError(
            "transaction submission returned an indeterminate error; do not retry until the pending nonce, expected address, and explorer are checked"
        ) from error
    if not isinstance(transaction_hash, str) or HASH_PATTERN.fullmatch(transaction_hash) is None:
        raise RuntimeError("RPC returned an invalid transaction hash")

    output_path = args.output_dir / f"nonce-{current['nonce']:02d}-{transaction_hash[2:10]}.json"
    evidence = {
        "status": "SUBMITTED_RECEIPT_PENDING",
        "chainId": plan["chainId"],
        "planSha256": plan_hash,
        "transactionIndex": args.index,
        "label": current["label"],
        "nonce": current["nonce"],
        "expectedCreatedAddress": current["expectedCreatedAddress"],
        "transactionHash": transaction_hash,
        "gasLimit": args.gas_limit,
        "gasPriceWei": preflight["gasPriceWei"],
    }
    _write_json(output_path, evidence)
    print(f"Submitted {transaction_hash}; waiting for its receipt.")

    receipt = _poll_receipt(rpc, transaction_hash)
    if receipt.get("status") != "0x1":
        evidence.update({"status": "FAILED_STOP", "receipt": receipt})
        _write_json(output_path, evidence)
        raise RuntimeError("deployment receipt failed; stop and regenerate from the new nonce")
    actual_address = receipt.get("contractAddress")
    if not isinstance(actual_address, str) or actual_address.lower() != current[
        "expectedCreatedAddress"
    ].lower():
        evidence.update({"status": "ADDRESS_MISMATCH_STOP", "receipt": receipt})
        _write_json(output_path, evidence)
        raise RuntimeError("created address mismatch; stop immediately")

    runtime = rpc.call("eth_getCode", [actual_address, "latest"])
    runtime_bytes = (len(runtime) - 2) // 2 if isinstance(runtime, str) and runtime.startswith("0x") else -1
    expected_runtime_bytes = report["deployments"][args.index]["runtimeBytes"]
    expected_runtime_hash = _normalize_hash(
        operator_manifest["expectedDeployments"][args.index]["runtimeCodeHash"],
        "expected runtime hash",
    )
    actual_runtime_hash = (
        _normalize_hash(cast_keccak(_hex_bytes(runtime, "deployed runtime")), "deployed runtime hash")
        if runtime_bytes >= 0
        else ""
    )
    final_nonce = int(rpc.call("eth_getTransactionCount", [plan["sender"], "pending"]), 16)
    if (
        runtime_bytes != expected_runtime_bytes
        or actual_runtime_hash != expected_runtime_hash
        or final_nonce != current["nonce"] + 1
    ):
        evidence.update(
            {
                "status": "POST_STATE_MISMATCH_STOP",
                "receipt": receipt,
                "runtimeBytes": runtime_bytes,
                "expectedRuntimeBytes": expected_runtime_bytes,
                "runtimeCodeHash": "0x" + actual_runtime_hash if actual_runtime_hash else None,
                "expectedRuntimeCodeHash": "0x" + expected_runtime_hash,
                "pendingNonce": final_nonce,
            }
        )
        _write_json(output_path, evidence)
        raise RuntimeError("post-deployment runtime or nonce mismatch; stop immediately")

    evidence.update(
        {
            "status": "PASS_STOP_BEFORE_NEXT",
            "receipt": receipt,
            "runtimeBytes": runtime_bytes,
            "runtimeCodeHash": "0x" + actual_runtime_hash,
            "pendingNonce": final_nonce,
        }
    )
    _write_json(output_path, evidence)
    print(json.dumps(evidence, indent=2))
    print("One transaction completed. Stop here and review before selecting the next index.")


if __name__ == "__main__":
    main()
