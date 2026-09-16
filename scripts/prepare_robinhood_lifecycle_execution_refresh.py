#!/usr/bin/env python3
"""Build a fresh-clock continuation after the accepted lifecycle prefix.

The transformer preserves transactions 0 through 4 as mined history, inserts
two bounded Permit2 renewals, refreshes only future Permit2 expirations and
UniversalRouter deadlines, and assigns fresh nonces to the remaining calls. It
has no RPC, keystore, signing, serialization, or broadcast capability.
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
DEFAULT_PRIOR_PLAN = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-execution-candidate-2026-09-15.json"
DEFAULT_PREFLIGHT = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-refresh-preflight-2026-09-16.json"
DEFAULT_OUTPUT = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-refresh-candidate-2026-09-16.json"
COMPLETED_PREFIX = 5
CHAIN_ID = 46630
OFFICIAL_RPC_URL = "https://rpc.testnet.chain.robinhood.com"
SWAP_DEADLINE_SECONDS = 4 * 60 * 60
PERMIT2_EXPIRATION_SECONDS = 6 * 60 * 60
MINIMUM_SECONDS_AT_EXECUTION_START = 2 * 60 * 60
MINIMUM_SECONDS_AT_SWAP = 30 * 60


def _load_sibling(name: str, filename: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required sibling module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base_planner = _load_sibling(
    "stonkhedge_lifecycle_base_planner",
    "prepare_robinhood_lifecycle_execution_plan.py",
)
qualifier = base_planner.qualifier


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


def _replace_calldata(transaction: dict[str, Any], raw: bytes) -> None:
    transaction["calldata"] = "0x" + raw.hex()
    transaction["calldataKeccak256"] = "0x" + keccak(raw).hex()


def _refresh_future_calldata(
    transactions: list[dict[str, Any]], *, permit_expiration: int, swap_deadline: int
) -> tuple[list[int], list[int]]:
    permit_selector = keccak(b"approve(address,address,uint160,uint48)")[:4]
    swap_selector = keccak(b"execute(bytes,bytes[],uint256)")[:4]
    permit_indexes: list[int] = []
    swap_indexes: list[int] = []
    for transaction in transactions[COMPLETED_PREFIX:]:
        raw = bytes.fromhex(transaction["calldata"][2:])
        intent = transaction["decodedIntent"]
        if raw[:4] == permit_selector:
            token, spender, amount, _ = abi_decode(
                ["address", "address", "uint160", "uint48"], raw[4:]
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
            intent["clockClassification"] = "REFRESHED_CONTINUATION_TIME_BOUND"
            permit_indexes.append(int(transaction["ordinal"]))
        elif raw[:4] == swap_selector:
            commands, inputs, _ = abi_decode(["bytes", "bytes[]", "uint256"], raw[4:])
            _replace_calldata(
                transaction,
                swap_selector
                + abi_encode(
                    ["bytes", "bytes[]", "uint256"],
                    [commands, inputs, swap_deadline],
                ),
            )
            intent["deadline"] = str(swap_deadline)
            intent["clockClassification"] = "REFRESHED_CONTINUATION_TIME_BOUND"
            swap_indexes.append(int(transaction["ordinal"]))
    return permit_indexes, swap_indexes


def validate_preflight(
    preflight: dict[str, Any], preflight_path: Path, prior: dict[str, Any], prior_path: Path
) -> None:
    if preflight.get("status") != "PASS_PUBLIC_LIFECYCLE_REFRESH_PREFLIGHT_NO_AUTHORITY":
        raise ValueError("lifecycle refresh preflight did not pass")
    if preflight.get("network", {}).get("chainId") != CHAIN_ID:
        raise ValueError("refresh preflight chain ID drifted")
    if preflight.get("completedPrefixCount") != COMPLETED_PREFIX:
        raise ValueError("refresh completed prefix drifted")
    if preflight.get("priorPlan") != {
        "executionPlanBodySha256": prior["executionPlanBodySha256"],
        "executionPlanFileSha256": file_sha256(prior_path),
    }:
        raise ValueError("refresh preflight prior-plan binding drifted")
    if preflight.get("authorization") != {
        "signing": False,
        "publicBroadcast": False,
    }:
        raise ValueError("refresh preflight authorization boundary drifted")
    if preflight.get("publicExecution") != {
        "ready": False,
        "broadcastAttempted": False,
    }:
        raise ValueError("refresh preflight public-execution boundary drifted")
    qualifier_binding = preflight.get("qualifier", {})
    qualifier_path = REPOSITORY / qualifier_binding.get("path", "")
    if (
        not qualifier_path.is_file()
        or qualifier_binding.get("sha256") != file_sha256(qualifier_path)
    ):
        raise ValueError("refresh preflight qualifier binding drifted")
    body = dict(preflight)
    expected = body.pop("preflightBodySha256", None)
    if expected != canonical_sha256(body):
        raise ValueError("refresh preflight body hash drifted")
    if not Path(preflight_path).is_file():
        raise ValueError("refresh preflight file is unavailable")


def _renewal_from(transaction: dict[str, Any], label: str) -> dict[str, Any]:
    renewal = copy.deepcopy(transaction)
    renewal["phase"] = "WRITER_SWAP_PERMISSION_REFRESH"
    renewal["label"] = label
    renewal["authorizedForBroadcast"] = False
    return renewal


def build_refresh_plan(
    prior_plan_path: Path, preflight_path: Path, generator_path: Path
) -> dict[str, Any]:
    prior_plan_path = Path(prior_plan_path)
    preflight_path = Path(preflight_path)
    generator_path = Path(generator_path)
    prior = load_json(prior_plan_path)
    preflight = load_json(preflight_path)
    prior_body = dict(prior)
    prior_hash = prior_body.pop("executionPlanBodySha256", None)
    if prior_hash != canonical_sha256(prior_body):
        raise ValueError("prior lifecycle candidate body hash drifted")
    if len(prior.get("transactions", [])) != 25:
        raise ValueError("prior lifecycle candidate transaction count drifted")
    validate_preflight(preflight, preflight_path, prior, prior_plan_path)

    writer = qualifier.normalize_address(prior["roles"]["writer"]["address"])
    buyer = qualifier.normalize_address(prior["roles"]["buyer"]["address"])
    continuation_starts = {
        writer: int(preflight["nonceVector"][writer]),
        buyer: int(preflight["nonceVector"][buyer]),
    }
    prefix = copy.deepcopy(prior["transactions"][:COMPLETED_PREFIX])
    remaining = copy.deepcopy(prior["transactions"][COMPLETED_PREFIX:])
    renewals = [
        _renewal_from(
            prior["transactions"][3],
            "writer refreshes exact PLTR Permit2 allowance to UniversalRouter",
        ),
        _renewal_from(
            prior["transactions"][4],
            "writer refreshes exact WETH Permit2 allowance to UniversalRouter",
        ),
    ]
    transactions = prefix + renewals + remaining
    for ordinal, transaction in enumerate(transactions):
        transaction["ordinal"] = ordinal

    reference_timestamp = int(preflight["network"]["referenceTimestampUnix"])
    swap_deadline = reference_timestamp + SWAP_DEADLINE_SECONDS
    permit_expiration = reference_timestamp + PERMIT2_EXPIRATION_SECONDS
    permit_indexes, swap_indexes = _refresh_future_calldata(
        transactions,
        permit_expiration=permit_expiration,
        swap_deadline=swap_deadline,
    )
    if permit_indexes != [5, 6, 23, 24] or swap_indexes != [7, 8, 19, 20]:
        raise ValueError(
            f"refresh deadline-bearing transaction set drifted: {permit_indexes}, {swap_indexes}"
        )

    vector = dict(continuation_starts)
    for transaction in transactions[COMPLETED_PREFIX:]:
        sender = qualifier.normalize_address(transaction["sender"])
        transaction["requiredNonceStateBefore"] = dict(vector)
        transaction["nonce"] = vector[sender]
        vector[sender] += 1
        transaction["requiredNonceStateAfter"] = dict(vector)
        transaction["authorizedForBroadcast"] = False

    source_bindings = copy.deepcopy(prior["sourceBindings"])
    source_bindings.update(
        {
            "priorExecutionCandidate": {
                "path": repository_relative(prior_plan_path),
                "sha256": file_sha256(prior_plan_path),
                "executionPlanBodySha256": prior["executionPlanBodySha256"],
            },
            "priorSimulationReport": {
                "path": "manifests/markets/robinhood-testnet-pltr-weth-lifecycle-execution-operator-simulation-2026-09-15.json",
                "sha256": file_sha256(
                    MARKETS
                    / "robinhood-testnet-pltr-weth-lifecycle-execution-operator-simulation-2026-09-15.json"
                ),
            },
            "refreshPreflight": {
                "path": repository_relative(preflight_path),
                "sha256": file_sha256(preflight_path),
                "preflightBodySha256": preflight["preflightBodySha256"],
            },
            "generator": {
                "path": repository_relative(generator_path),
                "sha256": file_sha256(generator_path),
            },
        }
    )

    body = copy.deepcopy(prior)
    body.pop("executionPlanBodySha256", None)
    body.update(
        {
            "mode": "UNSIGNED_PREFIX_BOUND_REFRESHED_CONTINUATION_NO_SIGNING_NO_BROADCAST",
            "network": {
                "name": prior["network"]["name"],
                "chainId": CHAIN_ID,
                "rpc": OFFICIAL_RPC_URL,
                "referenceBlock": preflight["network"]["referenceBlock"],
                "referenceBlockHash": preflight["network"]["referenceBlockHash"],
                "referenceTimestampUnix": reference_timestamp,
                "referenceTimestampUtc": preflight["network"]["referenceTimestampUtc"],
            },
            "sourceBindings": source_bindings,
            "continuationInitialState": {
                "completedPrefixCount": COMPLETED_PREFIX,
                "observed": copy.deepcopy(preflight["observed"]),
                "evidencePrefix": copy.deepcopy(preflight["evidencePrefix"]),
            },
            "executionStartIndex": COMPLETED_PREFIX,
            "executionClock": {
                "referenceTimestampUnix": reference_timestamp,
                "swapDeadlineUnix": swap_deadline,
                "permit2ExpirationUnix": permit_expiration,
                "minimumSecondsRemainingAtTransactionZero": MINIMUM_SECONDS_AT_EXECUTION_START,
                "minimumSecondsRemainingAtDeadlineTransaction": MINIMUM_SECONDS_AT_SWAP,
                "deadlineBearingTransactionIndexes": permit_indexes + swap_indexes,
                "swapDeadlineTransactionIndexes": swap_indexes,
                "permit2WindowLastTransactionIndex": max(permit_indexes),
                "classification": "SHORT_LIVED_REFRESHED_CONTINUATION_NOT_AUTHORIZATION",
            },
            "continuationStartNonces": continuation_starts,
            "nextNonces": vector,
            "transactionCount": len(transactions),
            "transactionCountsBySender": {
                writer: sum(
                    1
                    for transaction in transactions
                    if qualifier.normalize_address(transaction["sender"]) == writer
                ),
                buyer: sum(
                    1
                    for transaction in transactions
                    if qualifier.normalize_address(transaction["sender"]) == buyer
                ),
            },
            "transactions": transactions,
            "authorization": {key: False for key in prior["authorization"]},
            "publicExecution": {
                "ready": False,
                "broadcastAttempted": False,
                "blockingReasons": [
                    "the refreshed continuation has not passed exact-head simulation",
                    "no refreshed hash-bound authorization manifest exists",
                    "each sender keystore must derive its committed role address",
                ],
            },
            "nextGate": "EXACT_HEAD_REFRESH_SIMULATION_THEN_NEW_HASH_BOUND_AUTHORIZATION",
        }
    )
    body["executionPlanBodySha256"] = canonical_sha256(body)
    return body


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-plan", type=Path, default=DEFAULT_PRIOR_PLAN)
    parser.add_argument("--preflight", type=Path, default=DEFAULT_PREFLIGHT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_refresh_plan(args.prior_plan, args.preflight, Path(__file__).resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "status": plan["status"],
                "output": str(args.output),
                "executionPlanBodySha256": plan["executionPlanBodySha256"],
                "executionStartIndex": plan["executionStartIndex"],
                "remainingTransactionCount": len(plan["transactions"])
                - plan["executionStartIndex"],
                "continuationStartNonces": plan["continuationStartNonces"],
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
