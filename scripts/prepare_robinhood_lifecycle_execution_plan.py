#!/usr/bin/env python3
"""Build a dual-sender nonce/time-bound lifecycle execution candidate offline.

The transformer binds the reviewed 25-call lifecycle to a fresh public
preflight, assigns an independent nonce sequence to each ordinary-user role,
and refreshes only Permit2 expirations and UniversalRouter deadlines. It has no
RPC, wallet, signing, serialization, or broadcast capability.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from eth_abi import decode as abi_decode
from eth_abi import encode as abi_encode
from eth_hash.auto import keccak


REPOSITORY = Path(__file__).resolve().parents[1]
MARKETS = REPOSITORY / "manifests" / "markets"
DEFAULT_BASE_PLAN = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-proposal-2026-09-14.json"
DEFAULT_REHEARSAL = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-fork-rehearsal-2026-09-14.json"
DEFAULT_PREFLIGHT = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-execution-preflight-2026-09-15.json"
DEFAULT_OUTPUT = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-execution-candidate-2026-09-15.json"
CHAIN_ID = 46630
OFFICIAL_RPC_URL = "https://rpc.testnet.chain.robinhood.com"
SWAP_DEADLINE_SECONDS = 4 * 60 * 60
PERMIT2_EXPIRATION_SECONDS = 6 * 60 * 60
MINIMUM_SECONDS_AT_TRANSACTION_ZERO = 2 * 60 * 60
MINIMUM_SECONDS_AT_DEADLINE_TRANSACTION = 30 * 60


def _load_sibling(name: str, filename: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required sibling module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


simulator = _load_sibling(
    "stonkhedge_lifecycle_simulator", "simulate_robinhood_two_actor_lifecycle_fork.py"
)
qualifier = simulator.qualifier


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


def repository_relative(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(REPOSITORY).as_posix()
    except ValueError as exc:
        raise ValueError(f"bound source must be inside the repository: {path}") from exc


def _all_false(value: Any) -> bool:
    return isinstance(value, dict) and bool(value) and all(
        item is False for item in value.values()
    )


def _replace_calldata(transaction: dict[str, Any], raw: bytes) -> None:
    transaction["calldata"] = "0x" + raw.hex()
    transaction["calldataKeccak256"] = "0x" + keccak(raw).hex()


def _refresh_time_bound_calldata(
    transactions: list[dict[str, Any]], *, permit_expiration: int, swap_deadline: int
) -> list[int]:
    changed: list[int] = []
    permit_selector = keccak(b"approve(address,address,uint160,uint48)")[:4]
    swap_selector = keccak(b"execute(bytes,bytes[],uint256)")[:4]
    for transaction in transactions:
        raw = bytes.fromhex(transaction["calldata"][2:])
        intent = transaction["decodedIntent"]
        if raw[:4] == permit_selector:
            token, spender, amount, old_expiration = abi_decode(
                ["address", "address", "uint160", "uint48"], raw[4:]
            )
            intended = int(intent["expiration"])
            if int(old_expiration) != intended:
                raise ValueError(
                    f"transaction {transaction['ordinal']} Permit2 decode drifted"
                )
            new_expiration = permit_expiration if int(amount) > 0 else 0
            _replace_calldata(
                transaction,
                permit_selector
                + abi_encode(
                    ["address", "address", "uint160", "uint48"],
                    [token, spender, amount, new_expiration],
                ),
            )
            intent["expiration"] = str(new_expiration)
            intent["clockClassification"] = "EXECUTION_CANDIDATE_TIME_BOUND"
            changed.append(int(transaction["ordinal"]))
        elif raw[:4] == swap_selector:
            commands, inputs, old_deadline = abi_decode(
                ["bytes", "bytes[]", "uint256"], raw[4:]
            )
            intended = int(intent["deadline"])
            if int(old_deadline) != intended:
                raise ValueError(
                    f"transaction {transaction['ordinal']} swap deadline decode drifted"
                )
            _replace_calldata(
                transaction,
                swap_selector
                + abi_encode(
                    ["bytes", "bytes[]", "uint256"],
                    [commands, inputs, swap_deadline],
                ),
            )
            intent["deadline"] = str(swap_deadline)
            intent["clockClassification"] = "EXECUTION_CANDIDATE_TIME_BOUND"
            changed.append(int(transaction["ordinal"]))
    if changed != [3, 4, 5, 6, 17, 18, 21, 22]:
        raise ValueError(f"deadline-bearing transaction set drifted: {changed}")
    return changed


def validate_preflight(
    preflight: dict[str, Any],
    preflight_path: Path,
    base_plan: dict[str, Any],
    base_plan_path: Path,
    rehearsal_path: Path,
) -> None:
    if preflight.get("status") != "PASS_PUBLIC_LIFECYCLE_EXECUTION_PREFLIGHT_NO_AUTHORITY":
        raise ValueError("lifecycle execution preflight did not pass")
    if preflight.get("network", {}).get("chainId") != CHAIN_ID:
        raise ValueError("preflight chain ID drifted")
    if not _all_false(preflight.get("authorization")):
        raise ValueError("preflight authorization must remain false")
    if preflight.get("publicExecution") != {
        "ready": False,
        "broadcastAttempted": False,
    }:
        raise ValueError("preflight public-execution boundary drifted")
    if preflight.get("plan") != {
        "planBodySha256": base_plan["planBodySha256"],
        "planFileSha256": file_sha256(base_plan_path),
        "rehearsalFileSha256": file_sha256(rehearsal_path),
    }:
        raise ValueError("preflight source-plan bindings drifted")
    body = dict(preflight)
    expected = body.pop("preflightBodySha256", None)
    if expected != canonical_sha256(body):
        raise ValueError("preflight body hash drifted")
    if not Path(preflight_path).is_file():
        raise ValueError("preflight file is unavailable")


def build_execution_plan(
    base_plan_path: Path,
    rehearsal_path: Path,
    preflight_path: Path,
    generator_path: Path,
) -> dict[str, Any]:
    base_plan_path = Path(base_plan_path)
    rehearsal_path = Path(rehearsal_path)
    preflight_path = Path(preflight_path)
    generator_path = Path(generator_path)
    base = load_json(base_plan_path)
    rehearsal = load_json(rehearsal_path)
    preflight = load_json(preflight_path)
    simulator.validate_plan(base, base_plan_path)
    if not str(rehearsal.get("status", "")).startswith(
        "PASS_LOOPBACK_TWO_ACTOR_LIFECYCLE_THROUGH_CLOSE"
    ):
        raise ValueError("source lifecycle rehearsal did not pass")
    validate_preflight(
        preflight, preflight_path, base, base_plan_path, rehearsal_path
    )

    writer = qualifier.normalize_address(base["roles"]["writer"]["address"])
    buyer = qualifier.normalize_address(base["roles"]["buyer"]["address"])
    starts = {
        writer: int(preflight["pendingNonces"]["writer"]),
        buyer: int(preflight["pendingNonces"]["buyer"]),
    }
    if starts[writer] != int(preflight["actors"]["writer"]["confirmedNonce"]):
        raise ValueError("writer pending nonce drifted")
    if starts[buyer] != int(preflight["actors"]["buyer"]["confirmedNonce"]):
        raise ValueError("buyer pending nonce drifted")

    reference_timestamp = int(preflight["network"]["referenceTimestampUnix"])
    swap_deadline = reference_timestamp + SWAP_DEADLINE_SECONDS
    permit_expiration = reference_timestamp + PERMIT2_EXPIRATION_SECONDS
    transactions = copy.deepcopy(base["transactions"])
    changed = _refresh_time_bound_calldata(
        transactions,
        permit_expiration=permit_expiration,
        swap_deadline=swap_deadline,
    )
    consumed = {writer: 0, buyer: 0}
    for transaction in transactions:
        sender = qualifier.normalize_address(transaction["sender"])
        before = {role: starts[role] + consumed[role] for role in (writer, buyer)}
        transaction["nonce"] = before[sender]
        transaction["requiredNonceStateBefore"] = before
        consumed[sender] += 1
        transaction["requiredNonceStateAfter"] = {
            role: starts[role] + consumed[role] for role in (writer, buyer)
        }
        transaction["authorizedForBroadcast"] = False

    body: dict[str, Any] = {
        "schemaVersion": 1,
        "status": "LIFECYCLE_EXECUTION_CANDIDATE_REQUIRES_SEPARATE_AUTHORIZATION",
        "mode": "UNSIGNED_DUAL_SENDER_NONCE_AND_TIME_BOUND_NO_SIGNING_NO_BROADCAST",
        "classification": base["classification"],
        "warning": base["warning"],
        "network": {
            "name": base["network"]["name"],
            "chainId": CHAIN_ID,
            "rpc": OFFICIAL_RPC_URL,
            "referenceBlock": preflight["network"]["referenceBlock"],
            "referenceBlockHash": preflight["network"]["referenceBlockHash"],
            "referenceTimestampUnix": reference_timestamp,
            "referenceTimestampUtc": preflight["network"]["referenceTimestampUtc"],
        },
        "sourceBindings": {
            "genesisManifest": base["sourceBindings"]["genesisManifest"],
            "genesisManifestSha256": base["sourceBindings"]["genesisManifestSha256"],
            "chainManifest": base["sourceBindings"]["chainManifest"],
            "chainManifestSha256": base["sourceBindings"]["chainManifestSha256"],
            "baseLifecyclePlan": {
                "path": repository_relative(base_plan_path),
                "sha256": file_sha256(base_plan_path),
                "planBodySha256": base["planBodySha256"],
            },
            "successfulLifecycleRehearsal": {
                "path": repository_relative(rehearsal_path),
                "sha256": file_sha256(rehearsal_path),
            },
            "freshExecutionPreflight": {
                "path": repository_relative(preflight_path),
                "sha256": file_sha256(preflight_path),
                "preflightBodySha256": preflight["preflightBodySha256"],
            },
            "generator": {
                "path": repository_relative(generator_path),
                "sha256": file_sha256(generator_path),
            },
        },
        "market": copy.deepcopy(base["market"]),
        "roles": copy.deepcopy(base["roles"]),
        "exposureCaps": copy.deepcopy(base["exposureCaps"]),
        "tokenIds": copy.deepcopy(base["tokenIds"]),
        "initialState": {
            "marketState": copy.deepcopy(preflight["marketState"]),
            "actors": copy.deepcopy(preflight["actors"]),
        },
        "executionClock": {
            "referenceTimestampUnix": reference_timestamp,
            "swapDeadlineUnix": swap_deadline,
            "permit2ExpirationUnix": permit_expiration,
            "minimumSecondsRemainingAtTransactionZero": MINIMUM_SECONDS_AT_TRANSACTION_ZERO,
            "minimumSecondsRemainingAtDeadlineTransaction": MINIMUM_SECONDS_AT_DEADLINE_TRANSACTION,
            "deadlineBearingTransactionIndexes": changed,
            "classification": "SHORT_LIVED_EXECUTION_CANDIDATE_NOT_AUTHORIZATION",
        },
        "gasPolicy": {
            "maximumGasPriceWei": "100000000",
            "maximumGasLimitPerTransaction": 0xF00000,
            "estimateMultiplierBps": 12500,
            "estimateAdditiveBuffer": 50000,
        },
        "startNonces": {writer: starts[writer], buyer: starts[buyer]},
        "nextNonces": {
            writer: starts[writer] + consumed[writer],
            buyer: starts[buyer] + consumed[buyer],
        },
        "transactionCount": len(transactions),
        "transactionCountsBySender": {writer: consumed[writer], buyer: consumed[buyer]},
        "transactions": transactions,
        "operatorPolicy": {
            "mode": "ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH",
            "bothSenderNoncesMustMatchBeforeEveryStep": True,
            "exactCalldataAndReceiptRequired": True,
            "separateKeystoreChosenByTransactionSender": True,
            "executionEvidenceMustRemainOutsideRepository": True,
        },
        "authorization": {key: False for key in base["authorization"]},
        "publicExecution": {
            "ready": False,
            "broadcastAttempted": False,
            "blockingReasons": [
                "the dual-sender one-step operator has not yet passed exact-head simulation",
                "no hash-bound public authorization manifest exists",
                "each sender keystore must independently derive its committed role address",
            ],
        },
        "nextGate": "EXACT_HEAD_OPERATOR_SIMULATION_THEN_EXPLICIT_HASH_BOUND_PUBLIC_AUTHORIZATION",
    }
    body["executionPlanBodySha256"] = canonical_sha256(body)
    return body


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-plan", type=Path, default=DEFAULT_BASE_PLAN)
    parser.add_argument("--rehearsal", type=Path, default=DEFAULT_REHEARSAL)
    parser.add_argument("--preflight", type=Path, default=DEFAULT_PREFLIGHT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_execution_plan(
        args.base_plan,
        args.rehearsal,
        args.preflight,
        Path(__file__).resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "status": plan["status"],
                "output": str(args.output),
                "executionPlanBodySha256": plan["executionPlanBodySha256"],
                "startNonces": plan["startNonces"],
                "nextNonces": plan["nextNonces"],
                "swapDeadlineUnix": plan["executionClock"]["swapDeadlineUnix"],
                "permit2ExpirationUnix": plan["executionClock"]["permit2ExpirationUnix"],
                "signing": False,
                "publicBroadcast": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
