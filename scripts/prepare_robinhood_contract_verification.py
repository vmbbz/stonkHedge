#!/usr/bin/env python3
"""Audit and prepare Robinhood testnet source verification without submitting it.

The default mode is read-only. It reconciles the 16 direct-CREATE deployments
and three market clones against live runtime bytecode, queries Blockscout's
source-verification status, and writes a compact inventory. ``--print-command``
prints one exact Foundry command for review; it never executes that command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from eth_hash.auto import keccak


REPOSITORY = Path(__file__).resolve().parents[1]
DEPLOYMENTS = REPOSITORY / "manifests" / "deployments"
MARKETS = REPOSITORY / "manifests" / "markets"
DEFAULT_DEPLOYMENT_MANIFEST = (
    DEPLOYMENTS / "robinhood-testnet-direct-public-progress-2026-09-09.json"
)
DEFAULT_MARKET_MANIFEST = (
    MARKETS / "robinhood-testnet-pltr-weth-public-genesis-2026-09-11.json"
)
DEFAULT_OUTPUT = (
    DEPLOYMENTS
    / "robinhood-testnet-contract-verification-inventory-2026-09-19.json"
)
DEFAULT_RPC_URL = "https://rpc.testnet.chain.robinhood.com"
DEFAULT_EXPLORER_URL = "https://explorer.testnet.chain.robinhood.com"
DEFAULT_VERIFIER_URL = DEFAULT_EXPLORER_URL + "/api/"
CHAIN_ID = 46630
SOURCE_COMMIT = "f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d"
DIRECT_CONFIG_SHA256 = (
    "728898b3f201e3c4421b00e9fcb2b7587796971e55fef73ac504a081da489cc0"
)
METADATA_PACKAGE_SHA256 = (
    "c5d1b27e67ee4b62d865c240d428afc00115dc38a741988edcf1f2a22631b5f8"
)
COMPILER_VERSION = "0.8.28"
EVM_VERSION = "cancun"
LICENSE = "BUSL-1.1"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON manifest must contain an object: {path}")
    return value


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _hex_bytes(value: str, name: str) -> bytes:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError(f"{name} must be 0x-prefixed hex")
    try:
        return bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ValueError(f"{name} must be valid even-length hex") from exc


class JsonRpcClient:
    def __init__(self, url: str):
        self.url = url

    def call(self, method: str, params: list[Any]) -> Any:
        try:
            result = subprocess.run(
                [
                    "cast",
                    "rpc",
                    method,
                    "--raw",
                    "--rpc-url",
                    self.url,
                    "--rpc-timeout",
                    "30",
                ],
                input=json.dumps(params, separators=(",", ":")),
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "unknown Foundry RPC error").strip()
            raise RuntimeError(f"RPC {method} failed: {detail}") from exc
        return json.loads(result.stdout)


def fetch_explorer_payload(explorer_url: str, address: str) -> dict[str, Any]:
    url = f"{explorer_url.rstrip('/')}/api/v2/smart-contracts/{address}"
    try:
        result = subprocess.run(
            [
                "curl.exe",
                "--fail",
                "--silent",
                "--show-error",
                "--location",
                "--max-time",
                "30",
                "--header",
                "Accept: application/json",
                "--user-agent",
                "StonkHedge-verifier/1",
                url,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "unknown Blockscout error").strip()
        if "404" in detail:
            return {"_notIndexed": True}
        raise RuntimeError(f"Blockscout read failed for {address}: {detail}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"unexpected Blockscout response for {address}")
    return payload


def classify_explorer_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("_notIndexed"):
        return {"status": "NOT_INDEXED"}
    implementations = []
    for implementation in payload.get("implementations") or []:
        if isinstance(implementation, dict) and implementation.get("address_hash"):
            implementations.append(
                {
                    "address": implementation["address_hash"],
                    "name": implementation.get("name"),
                }
            )
    verified = bool(payload.get("source_code"))
    compact = {
        "status": "SOURCE_VERIFIED" if verified else "BYTECODE_ONLY",
        "creationStatus": payload.get("creation_status"),
        "proxyType": payload.get("proxy_type"),
        "implementations": implementations,
    }
    if verified:
        compact.update(
            {
                "contractName": payload.get("name"),
                "filePath": payload.get("file_path"),
                "compilerVersion": payload.get("compiler_version"),
                "optimizationEnabled": payload.get("optimization_enabled"),
                "optimizationRuns": payload.get("optimization_runs"),
                "evmVersion": payload.get("evm_version"),
                "verifiedAt": payload.get("verified_at"),
            }
        )
    return compact


def runtime_identity(client: Any, address: str) -> dict[str, Any]:
    code = client.call("eth_getCode", [address, "latest"])
    raw = _hex_bytes(code, f"runtime code for {address}")
    return {
        "bytes": len(raw),
        "keccak256": "0x" + keccak(raw).hex(),
    }


def _git_output(core_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(core_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def validate_source_checkout(
    core_root: Path, direct_config_path: Path
) -> tuple[dict[str, Any], Path]:
    core_root = Path(core_root).resolve()
    direct_config_path = Path(direct_config_path).resolve()
    if _git_output(core_root, "rev-parse", "HEAD").lower() != SOURCE_COMMIT:
        raise ValueError(f"core checkout must be exact commit {SOURCE_COMMIT}")
    if _git_output(core_root, "status", "--porcelain"):
        raise ValueError("core checkout must be clean")
    if file_sha256(direct_config_path) != DIRECT_CONFIG_SHA256:
        raise ValueError("direct deployment config hash mismatch")
    metadata_path = core_root / "metadata" / "out" / "MetadataPackage.json"
    if file_sha256(metadata_path) != METADATA_PACKAGE_SHA256:
        raise ValueError("metadata package hash mismatch")
    config = load_json(direct_config_path)
    deployment = config.get("directDeployment", {})
    if deployment.get("chainId") != CHAIN_ID or deployment.get("mode") != "CREATE":
        raise ValueError("direct config is not the Robinhood direct-CREATE release")
    return config, metadata_path


def _expected_identity(transaction: dict[str, Any]) -> dict[str, Any]:
    return {
        "bytes": int(transaction["runtimeBytes"]),
        "keccak256": transaction["runtimeCodeHash"].lower(),
    }


def _base_record(
    *,
    label: str,
    address: str,
    transaction_hash: str,
    expected: dict[str, Any],
    client: Any,
    explorer_fetcher: Callable[[str], dict[str, Any]],
) -> dict[str, Any]:
    live = runtime_identity(client, address)
    explorer = classify_explorer_payload(explorer_fetcher(address))
    return {
        "label": label,
        "address": address,
        "explorerUrl": f"{DEFAULT_EXPLORER_URL}/address/{address}",
        "creationTransactionHash": transaction_hash,
        "expectedRuntime": expected,
        "liveRuntime": live,
        "runtimeIdentityMatches": live == expected,
        "explorer": explorer,
    }


def build_inventory(
    deployment_manifest: dict[str, Any],
    market_manifest: dict[str, Any],
    direct_config: dict[str, Any],
    core_root: Path,
    client: Any,
    explorer_fetcher: Callable[[str], dict[str, Any]],
) -> dict[str, Any]:
    if int(client.call("eth_chainId", []), 16) != CHAIN_ID:
        raise ValueError("RPC chain ID mismatch")
    latest = client.call("eth_getBlockByNumber", ["latest", False])
    transactions = deployment_manifest["transactions"]
    direct_order = direct_config["directDeployment"]["order"]
    if len(transactions) != 16 or len(direct_order) != 16:
        raise ValueError("expected exactly 16 direct deployments")
    config_by_name = direct_config["logicContracts"]
    records = []
    for transaction, order in zip(transactions, direct_order):
        if (
            transaction["label"] != order["label"]
            or transaction["createdAddress"].lower()
            != order["expectedAddress"].lower()
        ):
            raise ValueError("direct deployment manifest/config order mismatch")
        label = transaction["label"]
        record = _base_record(
            label=label,
            address=transaction["createdAddress"],
            transaction_hash=transaction["transactionHash"],
            expected=_expected_identity(transaction),
            client=client,
            explorer_fetcher=explorer_fetcher,
        )
        if label.startswith("dataContracts["):
            record.update(
                {
                    "kind": "METADATA_DATA_STORE",
                    "sourceVerificationPolicy": (
                        "RUNTIME_HASH_ONLY_NO_SOLIDITY_ARTIFACT"
                    ),
                }
            )
        else:
            options = config_by_name[label]
            source_path = options["path"].removeprefix("./")
            source_file = Path(core_root) / source_path
            links = []
            for library_name in options.get("links", []):
                library = config_by_name[library_name]
                links.append(
                    {
                        "contract": library_name,
                        "sourcePath": library["path"].removeprefix("./"),
                        "address": library["deployment"]["address"],
                    }
                )
            record.update(
                {
                    "kind": "SOURCE_IMPLEMENTATION",
                    "sourcePath": source_path,
                    "sourceSha256": file_sha256(source_file),
                    "artifactName": options.get("artifactName", label),
                    "compiler": {
                        "version": COMPILER_VERSION,
                        "evmVersion": EVM_VERSION,
                        "optimizerEnabled": True,
                        "optimizerRuns": int(options["optimizeRuns"]),
                        "viaIR": False,
                    },
                    "license": LICENSE,
                    "libraries": links,
                    "constructorArguments": (
                        "PRESENT_GENERATED_ON_DEMAND"
                        if options.get("constructorArgs")
                        else "NONE"
                    ),
                    "sourceVerificationPolicy": (
                        "VERIFY_EXACT_IMPLEMENTATION_FROM_BOUND_SOURCE_COMMIT"
                    ),
                }
            )
        records.append(record)

    registered = market_manifest["registeredMarket"]
    market_transaction = registered["poolDeployedEvent"]["transactionHash"]
    clone_specs = [
        (
            "PLTR_WETH_PanopticPool",
            registered["panopticPool"],
            direct_config["logicContracts"]["PanopticPoolV2"]["deployment"][
                "address"
            ],
        ),
        (
            "PLTR_WETH_CollateralTracker0",
            registered["collateralTracker0"],
            direct_config["logicContracts"]["CollateralTrackerV2"]["deployment"][
                "address"
            ],
        ),
        (
            "PLTR_WETH_CollateralTracker1",
            registered["collateralTracker1"],
            direct_config["logicContracts"]["CollateralTrackerV2"]["deployment"][
                "address"
            ],
        ),
    ]
    for label, clone, implementation in clone_specs:
        expected = {
            "bytes": int(clone["runtimeBytes"]),
            "keccak256": clone["runtimeKeccak256"].lower(),
        }
        record = _base_record(
            label=label,
            address=clone["address"],
            transaction_hash=market_transaction,
            expected=expected,
            client=client,
            explorer_fetcher=explorer_fetcher,
        )
        record.update(
            {
                "kind": "IMMUTABLE_ARGUMENTS_CLONE",
                "implementation": implementation,
                "sourceVerificationPolicy": (
                    "VERIFY_IMPLEMENTATION_THEN_ASSOCIATE_CLONE"
                ),
            }
        )
        records.append(record)

    runtime_failures = [r["label"] for r in records if not r["runtimeIdentityMatches"]]
    source_records = [r for r in records if r["kind"] == "SOURCE_IMPLEMENTATION"]
    source_verified = [
        r for r in source_records if r["explorer"]["status"] == "SOURCE_VERIFIED"
    ]
    observed_timestamp = int(latest["timestamp"], 16)
    body = {
        "schemaVersion": 1,
        "status": (
            "PASS_RUNTIME_IDENTITY_SOURCE_PUBLICATION_PENDING"
            if not runtime_failures and len(source_verified) < len(source_records)
            else "PASS_RUNTIME_IDENTITY_AND_SOURCE_VERIFIED"
            if not runtime_failures
            else "FAIL_RUNTIME_IDENTITY"
        ),
        "mode": "READ_ONLY_AUDIT_AND_OFFLINE_COMMAND_PREPARATION",
        "network": {
            "chainId": CHAIN_ID,
            "rpcUrl": DEFAULT_RPC_URL,
            "explorerUrl": DEFAULT_EXPLORER_URL,
            "blockNumber": int(latest["number"], 16),
            "blockHash": latest["hash"],
            "blockTimestamp": datetime.fromtimestamp(
                observed_timestamp, timezone.utc
            ).isoformat().replace("+00:00", "Z"),
        },
        "sourceBinding": {
            "repository": "https://github.com/vmbbz/panoptic-v2-core.git",
            "commit": SOURCE_COMMIT,
            "cleanCheckoutRequired": True,
            "directConfigSha256": DIRECT_CONFIG_SHA256,
            "metadataPackageSha256": METADATA_PACKAGE_SHA256,
            "compilerVersion": COMPILER_VERSION,
            "evmVersion": EVM_VERSION,
            "license": LICENSE,
        },
        "summary": {
            "totalContracts": len(records),
            "directDeployments": 16,
            "metadataDataStores": len(
                [r for r in records if r["kind"] == "METADATA_DATA_STORE"]
            ),
            "sourceImplementations": len(source_records),
            "immutableArgumentsClones": len(
                [r for r in records if r["kind"] == "IMMUTABLE_ARGUMENTS_CLONE"]
            ),
            "runtimeIdentityPass": len(records) - len(runtime_failures),
            "runtimeIdentityFailures": runtime_failures,
            "sourceImplementationsVerifiedOnExplorer": len(source_verified),
            "sourceImplementationsPendingOnExplorer": len(source_records)
            - len(source_verified),
        },
        "contracts": records,
        "authorization": {
            "sourcePublicationAuthorized": False,
            "transactionSigningAuthorized": False,
            "publicTransactionBroadcastAuthorized": False,
        },
        "nextGate": (
            "OWNER_REVIEW_OF_EXACT_SOURCE_PUBLICATION_COMMANDS_THEN_SEPARATE_"
            "APPROVAL_TO_SUBMIT_TO_BLOCKSCOUT"
        ),
    }
    body["inventoryBodySha256"] = canonical_sha256(body)
    return body


def _format_abi_arg(type_name: str, value: Any) -> str:
    if type_name.endswith("[]"):
        inner_type = type_name[:-2]
        return "[" + ",".join(_format_abi_arg(inner_type, item) for item in value) + "]"
    if type_name == "bytes32":
        if isinstance(value, str) and value.startswith("0x"):
            return value
        if isinstance(value, (bytes, bytearray)):
            return "0x" + bytes(value).ljust(32, b"\x00").hex()
        raise TypeError(f"unsupported bytes32 value: {value!r}")
    return str(value)


def _abi_encode(types: list[str], values: list[Any]) -> str:
    signature = "f(" + ",".join(types) + ")"
    result = subprocess.run(
        [
            "cast",
            "abi-encode",
            signature,
            *[_format_abi_arg(t, v) for t, v in zip(types, values)],
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _inject_metadata(config: dict[str, Any], metadata_path: Path) -> None:
    metadata = load_json(metadata_path)
    config["env"]["MD_PROPERTIES"] = [
        property_name.encode("utf-8") for property_name in metadata["properties"]
    ]
    config["env"]["MD_INDICES"] = [
        [int(index) for index in indices] for indices in metadata["indices"]
    ]
    config["env"]["MD_POINTERS"] = [
        [
            (int(pointer["size"]) << 208)
            + (int(pointer["start"]) << 160)
            + int(config["dataContracts"][pointer["codeIndex"]]["address"], 16)
            for pointer in pointers
        ]
        for pointers in metadata["pointers"]
    ]


def build_verification_command(
    config: dict[str, Any],
    metadata_path: Path,
    contract_name: str,
) -> list[str]:
    if contract_name not in config["logicContracts"]:
        raise ValueError(f"unknown source implementation: {contract_name}")
    _inject_metadata(config, metadata_path)
    options = config["logicContracts"][contract_name]
    artifact_name = options.get("artifactName", contract_name)
    command = [
        "forge",
        "verify-contract",
        options["deployment"]["address"],
        f"{options['path']}:{artifact_name}",
        "--compiler-version",
        COMPILER_VERSION,
        "--optimizer-runs",
        str(options["optimizeRuns"]),
        "--evm-version",
        EVM_VERSION,
        "--chain-id",
        str(CHAIN_ID),
        "--rpc-url",
        DEFAULT_RPC_URL,
        "--verifier",
        "blockscout",
        "--verifier-url",
        DEFAULT_VERIFIER_URL,
        "--license-type",
        LICENSE,
    ]
    for library_name in options.get("links", []):
        library = config["logicContracts"][library_name]
        library_artifact = library.get("artifactName", library_name)
        command.extend(
            [
                "--libraries",
                (
                    f"{library['path']}:{library_artifact}:"
                    f"{library['deployment']['address']}"
                ),
            ]
        )
    if options.get("constructorArgs"):
        values = list(options["constructorArgs"][0])
        types = list(options["constructorArgs"][1])
        for index, value in enumerate(values):
            if isinstance(value, str) and value.startswith("@"):
                values[index] = config["logicContracts"][value[1:]]["deployment"][
                    "address"
                ]
            elif isinstance(value, str) and value.startswith("$"):
                values[index] = config["env"][value[1:]]
        command.extend(["--constructor-args", _abi_encode(types, values)])
    command.append("--watch")
    return command


def format_powershell_command(command: list[str]) -> str:
    def quote(value: str) -> str:
        if not value or any(character.isspace() for character in value):
            return "'" + value.replace("'", "''") + "'"
        return value

    return " `\n  ".join(quote(part) for part in command)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deployment-manifest", type=Path, default=DEFAULT_DEPLOYMENT_MANIFEST)
    parser.add_argument("--market-manifest", type=Path, default=DEFAULT_MARKET_MANIFEST)
    parser.add_argument("--core-root", type=Path, required=True)
    parser.add_argument("--direct-config", type=Path, required=True)
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL)
    parser.add_argument("--explorer-url", default=DEFAULT_EXPLORER_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--print-command",
        metavar="CONTRACT",
        help="print one exact source-verification command without running it",
    )
    args = parser.parse_args()

    config, metadata_path = validate_source_checkout(args.core_root, args.direct_config)
    if args.print_command:
        command = build_verification_command(config, metadata_path, args.print_command)
        print("# REVIEW ONLY: this command was not executed")
        print(f"Set-Location '{Path(args.core_root).resolve()}'")
        print(format_powershell_command(command))
        return 0

    client = JsonRpcClient(args.rpc_url)
    inventory = build_inventory(
        load_json(args.deployment_manifest),
        load_json(args.market_manifest),
        config,
        Path(args.core_root),
        client,
        lambda address: fetch_explorer_payload(args.explorer_url, address),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(inventory, indent=2) + "\n").encode("utf-8"))
    print(
        json.dumps(
            {
                "status": inventory["status"],
                "output": str(args.output),
                "outputSha256": file_sha256(args.output),
                "inventoryBodySha256": inventory["inventoryBodySha256"],
                "summary": inventory["summary"],
                "submissionAttempted": False,
            },
            indent=2,
        )
    )
    return 0 if not inventory["summary"]["runtimeIdentityFailures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
