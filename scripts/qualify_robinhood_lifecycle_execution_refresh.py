#!/usr/bin/env python3
"""Capture the public state after the accepted lifecycle prefix.

This qualifier reads chain state and the external one-step evidence for indexes
0 through 4. It has no wallet, signing, transaction serialization, or public
submission path.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPOSITORY = Path(__file__).resolve().parents[1]
MARKETS = REPOSITORY / "manifests" / "markets"
DEFAULT_PRIOR_PLAN = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-execution-candidate-2026-09-15.json"
DEFAULT_EVIDENCE_DIR = Path.home() / ".foundry" / "stonkhedge-evidence" / "pltr-weth-lifecycle-2026-09-15"
DEFAULT_OUTPUT = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-refresh-preflight-2026-09-16.json"
DEFAULT_RPC_URL = "https://rpc.testnet.chain.robinhood.com"
COMPLETED_PREFIX = 5
CHAIN_ID = 46630


def _load_sibling(name: str, filename: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required sibling module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


operator = _load_sibling(
    "stonkhedge_lifecycle_refresh_operator", "operate_robinhood_lifecycle.py"
)
qualifier = operator.qualifier


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


def _evidence_name(transaction: dict[str, Any]) -> str:
    return (
        f"lifecycle-index-{int(transaction['ordinal']):02d}-"
        f"nonce-{int(transaction['nonce'])}.json"
    )


def _validate_evidence(
    client: Any,
    plan: dict[str, Any],
    plan_path: Path,
    evidence_dir: Path,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    plan_file_hash = file_sha256(plan_path)
    for index, transaction in enumerate(plan["transactions"][:COMPLETED_PREFIX]):
        path = evidence_dir / _evidence_name(transaction)
        evidence = load_json(path)
        if evidence.get("status") != "PASS_STOP_BEFORE_NEXT":
            raise ValueError(f"prefix evidence {index} did not pass")
        if evidence.get("executionPlanBodySha256") != plan["executionPlanBodySha256"]:
            raise ValueError(f"prefix evidence {index} plan body drifted")
        if evidence.get("executionPlanFileSha256") != plan_file_hash:
            raise ValueError(f"prefix evidence {index} plan file drifted")
        intent = evidence.get("intent", {})
        if (
            intent.get("transactionIndex") != index
            or qualifier.normalize_address(intent.get("sender", ""))
            != qualifier.normalize_address(transaction["sender"])
            or intent.get("nonce") != transaction["nonce"]
            or intent.get("calldataKeccak256") != transaction["calldataKeccak256"]
        ):
            raise ValueError(f"prefix evidence {index} intent drifted")
        mined = evidence.get("minedTransaction", {})
        transaction_hash = evidence.get("transactionHash", "").lower()
        receipt = client.call("eth_getTransactionReceipt", [transaction_hash])
        public_transaction = client.call("eth_getTransactionByHash", [transaction_hash])
        if (
            not receipt
            or receipt.get("status") != "0x1"
            or not public_transaction
            or public_transaction.get("hash", "").lower() != transaction_hash
            or int(public_transaction.get("nonce", "0x0"), 16) != int(transaction["nonce"])
            or qualifier.normalize_address(public_transaction.get("from", ""))
            != qualifier.normalize_address(transaction["sender"])
            or qualifier.normalize_address(public_transaction.get("to", ""))
            != qualifier.normalize_address(transaction["to"])
            or mined.get("transactionHash", "").lower() != transaction_hash
        ):
            raise ValueError(f"prefix evidence {index} public receipt drifted")
        if evidence.get("postNonceVector") != transaction["requiredNonceStateAfter"]:
            raise ValueError(f"prefix evidence {index} post-nonce vector drifted")
        result.append(
            {
                "transactionIndex": index,
                "nonce": transaction["nonce"],
                "sender": transaction["sender"],
                "transactionHash": transaction_hash,
                "receiptBlock": int(receipt["blockNumber"], 16),
                "evidenceFileName": path.name,
                "evidenceFileSha256": file_sha256(path),
                "operatorSha256": evidence["operatorSha256"],
            }
        )
    return result


def qualify(
    client: Any,
    *,
    prior_plan: dict[str, Any],
    prior_plan_path: Path,
    evidence_dir: Path,
    qualifier_path: Path,
) -> dict[str, Any]:
    operator.validate_execution_plan(prior_plan, prior_plan_path)
    if int(client.call("eth_chainId", []), 16) != CHAIN_ID:
        raise RuntimeError("public RPC chain ID mismatch")
    evidence = _validate_evidence(client, prior_plan, prior_plan_path, evidence_dir)
    state = operator.verify_state(client, prior_plan, COMPLETED_PREFIX)
    block = client.call("eth_getBlockByNumber", ["latest", False])
    vector = state["nonceVector"]
    for actor, expected in vector.items():
        for tag in ("latest", "pending"):
            actual = int(client.call("eth_getTransactionCount", [actor, tag]), 16)
            if actual != int(expected):
                raise RuntimeError(f"{actor} {tag} nonce drifted during refresh capture")
    timestamp = int(block["timestamp"], 16)
    body: dict[str, Any] = {
        "schemaVersion": 1,
        "status": "PASS_PUBLIC_LIFECYCLE_REFRESH_PREFLIGHT_NO_AUTHORITY",
        "mode": "PINNED_READ_ONLY_PARTIAL_STATE_PLUS_PREFIX_RECEIPTS_NO_KEYS_NO_SIGNING_NO_BROADCAST",
        "classification": prior_plan["classification"],
        "network": {
            "name": prior_plan["network"]["name"],
            "chainId": CHAIN_ID,
            "rpc": DEFAULT_RPC_URL,
            "referenceBlock": int(block["number"], 16),
            "referenceBlockHash": block["hash"].lower(),
            "referenceTimestampUnix": timestamp,
            "referenceTimestampUtc": datetime.fromtimestamp(
                timestamp, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "priorPlan": {
            "executionPlanBodySha256": prior_plan["executionPlanBodySha256"],
            "executionPlanFileSha256": file_sha256(prior_plan_path),
        },
        "qualifier": {
            "path": Path(qualifier_path).resolve().relative_to(REPOSITORY).as_posix(),
            "sha256": file_sha256(qualifier_path),
        },
        "completedPrefixCount": COMPLETED_PREFIX,
        "evidencePrefix": evidence,
        "nonceVector": vector,
        "observed": state["observed"],
        "externalState": state["external"],
        "checks": {
            "allFiveEvidenceFilesPassed": True,
            "allFivePublicReceiptsSucceeded": True,
            "partialStateMatchesCompletedPrefix": True,
            "confirmedAndPendingNoncesEqual": True,
            "externalRuntimeAndWiringMatch": True,
        },
        "authorization": {"signing": False, "publicBroadcast": False},
        "publicExecution": {"ready": False, "broadcastAttempted": False},
        "nextGate": "BUILD_REFRESHED_CONTINUATION_THEN_EXACT_HEAD_SIMULATION",
    }
    body["preflightBodySha256"] = canonical_sha256(body)
    return body


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL)
    parser.add_argument("--prior-plan", type=Path, default=DEFAULT_PRIOR_PLAN)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = operator.direct_operator.JsonRpcClient(args.rpc_url)
    result = qualify(
        client,
        prior_plan=load_json(args.prior_plan),
        prior_plan_path=args.prior_plan,
        evidence_dir=args.evidence_dir,
        qualifier_path=Path(__file__).resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "output": str(args.output),
                "referenceBlock": result["network"]["referenceBlock"],
                "completedPrefixCount": result["completedPrefixCount"],
                "nonceVector": result["nonceVector"],
                "signing": False,
                "publicBroadcast": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
