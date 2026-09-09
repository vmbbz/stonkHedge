#!/usr/bin/env python3
"""Derive an unsigned, loopback-only fork plan from the accepted market plan.

The committed market plan deliberately contains historical deadlines. This
offline transformer binds one successful strict-preflight head and refreshes
only the two Permit2 expirations and PositionManager liquidity deadline for
local Anvil rehearsal. It has no RPC, key, signing, serialization, or broadcast
capability.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from eth_abi import decode as abi_decode
from eth_utils import keccak


def _load_sibling(name: str, filename: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required sibling module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


planner = _load_sibling("stonkhedge_market_planner", "prepare_robinhood_market_plan.py")
verifier = _load_sibling("stonkhedge_market_verifier", "verify_robinhood_market_plan.py")

REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_BASE_PLAN = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-offline-plan-2026-09-09.json"
)
DEFAULT_PREFLIGHT = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-initial-preflight-2026-09-09.json"
)
DEFAULT_OUTPUT = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-fork-plan-2026-09-09.json"
)
ACTOR_MANIFEST = (
    REPOSITORY
    / "manifests"
    / "deployments"
    / "robinhood-testnet-second-actor-2026-09-09.json"
)
CHAIN_ID = 46630
CREATE3_PROXY_BYTECODE_HASH = bytes.fromhex(
    "21c35dbe1b344a2488cf3321d6ce542f8e9f305544ff09e4993a62319a497c1f"
)

FORK_BODY_FIELDS = (
    "status",
    "mode",
    "network",
    "sourceBindings",
    "market",
    "actor",
    "contracts",
    "priceAndLiquidity",
    "maximumExposureProposal",
    "forkClock",
    "predictedMarketContracts",
    "transactions",
    "authorization",
    "publicExecution",
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON manifest must contain an object: {path}")
    return value


def _all_false(values: Any) -> bool:
    return (
        isinstance(values, dict)
        and bool(values)
        and all(value is False for value in values.values())
    )


def _unix_timestamp(value: str) -> int:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError("preflight block timestamp is not ISO-8601 UTC") from exc
    if parsed.utcoffset() is None:
        raise ValueError("preflight block timestamp must include a UTC offset")
    return int(parsed.timestamp())


def _repository_relative(path: Path, generator_path: Path) -> str:
    root = Path(generator_path).resolve().parents[1]
    try:
        return Path(path).resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"source must remain inside repository: {path}") from exc


def _replace_calldata(transaction: dict[str, Any], calldata: str) -> None:
    raw = bytes.fromhex(calldata[2:])
    transaction["calldata"] = calldata
    transaction["calldataBytes"] = len(raw)
    transaction["calldataKeccak256"] = "0x" + keccak(raw).hex()


def predict_create3_proxy(factory: str, salt32: str) -> str:
    factory_bytes = bytes.fromhex(planner.normalize_address(factory)[2:])
    try:
        salt_bytes = bytes.fromhex(planner.normalize_hash(salt32, "CREATE3 salt")[2:])
    except ValueError as exc:
        raise ValueError("CREATE3 salt must be a 32-byte hex value") from exc
    digest = keccak(
        b"\xff" + factory_bytes + salt_bytes + CREATE3_PROXY_BYTECODE_HASH
    )
    return "0x" + digest[-20:].hex()


def _refresh_deadlines(
    transactions: list[dict[str, Any]], permit_expiration: int, liquidity_deadline: int
) -> None:
    for ordinal in (3, 4):
        transaction = transactions[ordinal]
        intent = transaction["decodedIntent"]
        _replace_calldata(
            transaction,
            planner.encode_call(
                "approve(address,address,uint160,uint48)",
                ["address", "address", "uint160", "uint48"],
                [
                    intent["token"],
                    intent["spender"],
                    int(intent["amount"]),
                    permit_expiration,
                ],
            ),
        )
        intent["expiration"] = permit_expiration
        intent["clockClassification"] = "FORK_ONLY_REHEARSAL"
        transaction["expectedPostState"] = [
            transaction["expectedPostState"][0].replace(
                "historical rehearsal expiration", "fork-only rehearsal expiration"
            )
        ]

    liquidity = transactions[6]
    raw = bytes.fromhex(liquidity["calldata"][2:])
    expected_selector = planner.function_selector("modifyLiquidities(bytes,uint256)")
    if raw[:4] != expected_selector:
        raise ValueError("base liquidity transaction selector drifted")
    unlock_data, original_deadline = abi_decode(["bytes", "uint256"], raw[4:])
    if int(original_deadline) != int(liquidity["decodedIntent"]["deadline"]):
        raise ValueError("base liquidity deadline decode drifted")
    _replace_calldata(
        liquidity,
        planner.encode_call(
            "modifyLiquidities(bytes,uint256)",
            ["bytes", "uint256"],
            [unlock_data, liquidity_deadline],
        ),
    )
    liquidity["decodedIntent"]["deadline"] = liquidity_deadline
    liquidity["decodedIntent"]["clockClassification"] = "FORK_ONLY_REHEARSAL"
    liquidity["requiredPreState"] = [
        (
            "fork timestamp is not past the fork-only liquidity deadline"
            if value == "historical rehearsal timestamp is not past the encoded deadline"
            else value
        )
        for value in liquidity["requiredPreState"]
    ]


def fork_plan_body_sha256(plan: dict[str, Any]) -> str:
    return planner.canonical_sha256({field: plan[field] for field in FORK_BODY_FIELDS})


def _validate_preflight(
    base_plan: dict[str, Any], base_plan_path: Path, preflight: dict[str, Any]
) -> int:
    verifier.validate_offline_plan(base_plan, base_plan_path)
    if preflight.get("status") != "PASS_INITIAL_MARKET_PREFLIGHT":
        raise ValueError("strict initial preflight did not pass")
    if preflight.get("network", {}).get("chainId") != CHAIN_ID:
        raise ValueError("preflight chain ID drifted")
    if preflight.get("checks", {}).get("failed") != 0:
        raise ValueError("plan-specific preflight contains failed checks")
    if preflight.get("qualificationChecks", {}).get("failed") != 0:
        raise ValueError("complete qualification contains failed checks")
    if preflight.get("publicExecution", {}).get("ready") is not False:
        raise ValueError("preflight must keep public execution disabled")
    if not _all_false(preflight.get("authorization")):
        raise ValueError("preflight authorization must remain entirely false")
    if preflight.get("plan", {}).get("planBodySha256") != base_plan.get(
        "planBodySha256"
    ):
        raise ValueError("preflight plan body binding drifted")
    if preflight.get("plan", {}).get("poolId") != base_plan["market"]["poolId"]:
        raise ValueError("preflight PoolId binding drifted")
    if preflight.get("plan", {}).get("actor", "").lower() != base_plan["actor"][
        "address"
    ].lower():
        raise ValueError("preflight actor binding drifted")
    if preflight.get("sourceBindings", {}).get("planFileSha256") != file_sha256(
        base_plan_path
    ):
        raise ValueError("preflight plan file binding drifted")
    if preflight.get("sourceBindings", {}).get("verifierSha256") != file_sha256(
        Path(verifier.__file__)
    ):
        raise ValueError("preflight verifier binding drifted")
    if preflight.get("sourceBindings", {}).get("qualifierSha256") != file_sha256(
        Path(verifier.qualifier.__file__)
    ):
        raise ValueError("preflight qualifier binding drifted")
    if preflight.get("sourceBindings", {}).get("actorManifestSha256") != file_sha256(
        ACTOR_MANIFEST
    ):
        raise ValueError("preflight actor-manifest binding drifted")
    return _unix_timestamp(preflight["network"]["blockTimestamp"])


def build_fork_plan(
    base_plan_path: Path, preflight_path: Path, generator_path: Path
) -> dict[str, Any]:
    base_plan_path = Path(base_plan_path)
    preflight_path = Path(preflight_path)
    generator_path = Path(generator_path)
    base_plan = load_json(base_plan_path)
    preflight = load_json(preflight_path)
    fork_timestamp = _validate_preflight(base_plan, base_plan_path, preflight)

    original_clock = base_plan["rehearsalClock"]
    liquidity_lifetime = int(original_clock["liquidityDeadlineUnix"]) - int(
        original_clock["referenceTimestampUnix"]
    )
    permit_lifetime = int(original_clock["permit2ExpirationUnix"]) - int(
        original_clock["referenceTimestampUnix"]
    )
    if liquidity_lifetime <= 0 or permit_lifetime <= liquidity_lifetime:
        raise ValueError("base rehearsal deadline lifetimes drifted")
    liquidity_deadline = fork_timestamp + liquidity_lifetime
    permit_expiration = fork_timestamp + permit_lifetime

    transactions = copy.deepcopy(base_plan["transactions"])
    _refresh_deadlines(transactions, permit_expiration, liquidity_deadline)
    if any(transaction.get("nonce") is not None for transaction in transactions):
        raise ValueError("fork plan transactions must keep nonces unset")
    if any(
        transaction.get("authorizedForBroadcast") is not False
        for transaction in transactions
    ):
        raise ValueError("fork plan transactions must remain unauthorized")

    inherited_bindings = {
        key: value
        for key, value in base_plan["sourceBindings"].items()
        if not isinstance(value, dict)
    }
    predicted_market_contracts = copy.deepcopy(base_plan["predictedMarketContracts"])
    predicted_market_contracts["create3Proxy"] = predict_create3_proxy(
        base_plan["contracts"]["panopticFactoryV4"],
        predicted_market_contracts["derivedSalt32"],
    )

    plan: dict[str, Any] = {
        "schemaVersion": 1,
        "status": "FORK_REHEARSAL_ONLY_NO_PUBLIC_BROADCAST",
        "mode": "LOOPBACK_ANVIL_ONLY_NO_KEYS_NO_SIGNING_NO_PUBLIC_BROADCAST",
        "network": {
            "name": base_plan["network"]["name"],
            "chainId": CHAIN_ID,
            "forkBlock": preflight["network"]["blockNumber"],
            "forkBlockHash": preflight["network"]["blockHash"],
            "forkBlockTimestamp": preflight["network"]["blockTimestamp"],
            "rpcPolicy": "HTTP_LOOPBACK_ANVIL_ONLY",
        },
        "sourceBindings": {
            "basePlan": {
                "path": _repository_relative(base_plan_path, generator_path),
                "sha256": file_sha256(base_plan_path),
                "planBodySha256": base_plan["planBodySha256"],
            },
            "initialPreflight": {
                "path": _repository_relative(preflight_path, generator_path),
                "sha256": file_sha256(preflight_path),
                "verifierSha256": preflight["sourceBindings"]["verifierSha256"],
            },
            "generator": {
                "path": _repository_relative(generator_path, generator_path),
                "sha256": file_sha256(generator_path),
            },
            **inherited_bindings,
        },
        "market": copy.deepcopy(base_plan["market"]),
        "actor": copy.deepcopy(base_plan["actor"]),
        "contracts": copy.deepcopy(base_plan["contracts"]),
        "priceAndLiquidity": copy.deepcopy(base_plan["priceAndLiquidity"]),
        "maximumExposureProposal": copy.deepcopy(
            base_plan["maximumExposureProposal"]
        ),
        "forkClock": {
            "referenceTimestampUnix": fork_timestamp,
            "localCompatibilityTimestampUnix": fork_timestamp + 1,
            "liquidityDeadlineUnix": liquidity_deadline,
            "permit2ExpirationUnix": permit_expiration,
            "classification": "LOCAL_FORK_ONLY_NOT_VALID_FOR_PUBLIC_EXECUTION",
        },
        "predictedMarketContracts": predicted_market_contracts,
        "transactionCount": len(transactions),
        "transactions": transactions,
        "requiredSimulatorGuards": [
            "RPC URL is plain HTTP loopback with no credentials or path",
            "client identifies as Anvil before any mutation",
            "chain ID, fork block number, hash, and timestamp exactly match this plan",
            "strict initial verifier passes locally before impersonation",
            "only the accepted second actor is impersonated",
            "no account balance or contract storage is fabricated for the positive path",
            "each transaction receipt and exact post-state reconcile before continuing",
            "negative cases run only inside snapshots that are reverted",
            "CREATE3 proxy collision fault injection is verified inside its snapshot",
        ],
        "authorization": copy.deepcopy(base_plan["authorization"]),
        "publicExecution": {
            "ready": False,
            "blockingReasons": copy.deepcopy(
                preflight["publicExecution"]["blockingReasons"]
            ),
        },
        "nextGate": "LOOPBACK_ANVIL_POSITIVE_AND_NEGATIVE_REHEARSAL",
    }
    plan["forkPlanBodySha256"] = fork_plan_body_sha256(plan)
    return plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-plan", type=Path, default=DEFAULT_BASE_PLAN)
    parser.add_argument("--preflight", type=Path, default=DEFAULT_PREFLIGHT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_fork_plan(args.base_plan, args.preflight, Path(__file__).resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Wrote loopback-only fork plan: {args.output}")
    print(f"Fork-plan body SHA-256: {plan['forkPlanBodySha256']}")
    print(f"Pinned block: {plan['network']['forkBlock']}")
    print("NO RPC, KEYS, SIGNING, SERIALIZATION, OR PUBLIC BROADCAST CAPABILITY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
