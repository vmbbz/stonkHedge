#!/usr/bin/env python3
"""Qualify the live PLTR/WETH lifecycle start without transaction authority.

All contract and account reads are pinned to one public Robinhood testnet
block. Pending nonces are sampled immediately afterwards and must equal the
pinned confirmed nonces. The tool never loads a wallet, signs, constructs a
raw transaction, or submits a transaction.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


REPOSITORY = Path(__file__).resolve().parents[1]
MARKETS = REPOSITORY / "manifests" / "markets"
DEFAULT_CHAIN = REPOSITORY / "manifests" / "chains" / "robinhood-testnet-46630.json"
DEFAULT_GENESIS = MARKETS / "robinhood-testnet-pltr-weth-public-genesis-2026-09-11.json"
DEFAULT_POLICY = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-inputs-2026-09-14.json"
DEFAULT_PLAN = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-proposal-2026-09-14.json"
DEFAULT_REHEARSAL = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-fork-rehearsal-2026-09-14.json"
DEFAULT_OUTPUT = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-execution-preflight-2026-09-15.json"
DEFAULT_RPC_URL = "https://rpc.testnet.chain.robinhood.com"


def _load_sibling(name: str, filename: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required sibling module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


snapshotter = _load_sibling(
    "stonkhedge_lifecycle_snapshotter", "capture_robinhood_lifecycle_inputs.py"
)
lifecycle_simulator = _load_sibling(
    "stonkhedge_lifecycle_simulator", "simulate_robinhood_two_actor_lifecycle_fork.py"
)
qualifier = snapshotter.qualifier


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


def _assert_actor_unchanged(
    role: str, captured: dict[str, Any], planned: dict[str, Any]
) -> None:
    for captured_name, planned_name in (
        ("address", "address"),
        ("confirmedNonce", "confirmedNonce"),
        ("nativeBalanceWei", "nativeBalanceWei"),
        ("pltrBalance", "pltrBalance"),
        ("wethBalance", "wethBalance"),
        ("collateralTracker0Shares", "collateralTracker0Shares"),
        ("collateralTracker1Shares", "collateralTracker1Shares"),
        ("openLegs", "openLegs"),
        ("blockedByStockRegistry", "blockedByStockRegistry"),
    ):
        if str(captured[captured_name]).lower() != str(planned[planned_name]).lower():
            raise RuntimeError(f"{role} {captured_name} changed after accepted rehearsal")
    if captured["initialAllowances"] != planned["initialAllowances"]:
        raise RuntimeError(f"{role} initial allowance state changed")


def qualify(
    rpc: Any,
    *,
    chain: dict[str, Any],
    genesis: dict[str, Any],
    policy: dict[str, Any],
    lifecycle_plan: dict[str, Any],
    lifecycle_plan_path: Path,
    rehearsal: dict[str, Any],
    rehearsal_path: Path,
    source_paths: dict[str, Path],
) -> dict[str, Any]:
    lifecycle_simulator.validate_plan(lifecycle_plan, lifecycle_plan_path)
    if not str(rehearsal.get("status", "")).startswith(
        "PASS_LOOPBACK_TWO_ACTOR_LIFECYCLE_THROUGH_CLOSE"
    ):
        raise ValueError("accepted lifecycle rehearsal did not pass")
    bindings = rehearsal.get("sourceBindings", {})
    if bindings.get("lifecyclePlanBodySha256") != lifecycle_plan.get(
        "planBodySha256"
    ):
        raise ValueError("rehearsal plan-body binding drifted")
    if bindings.get("lifecyclePlanFileSha256") != file_sha256(lifecycle_plan_path):
        raise ValueError("rehearsal plan-file binding drifted")
    if rehearsal.get("publicExecution", {}).get("broadcastAttempted") is not False:
        raise ValueError("rehearsal must prove no public broadcast")

    buyer = lifecycle_plan["roles"]["buyer"]["address"]
    captured = snapshotter.capture(
        rpc,
        chain=chain,
        genesis=genesis,
        policy=policy,
        buyer_address=buyer,
        source_paths={},
    )
    if not _all_false(captured.get("authorization")):
        raise RuntimeError("read-only snapshot unexpectedly grants authority")
    for role in ("writer", "buyer"):
        _assert_actor_unchanged(
            role, captured["actors"][role], lifecycle_plan["roles"][role]
        )

    market = captured["marketState"]
    if market["poolId"] != lifecycle_plan["market"]["poolId"]:
        raise RuntimeError("live PoolId changed")
    if market["currentTick"] != lifecycle_plan["market"]["referenceTick"]:
        raise RuntimeError("live pool tick changed after accepted rehearsal")
    if market["activeLiquidity"] != lifecycle_plan["market"]["referenceActiveLiquidity"]:
        raise RuntimeError("live active liquidity changed after accepted rehearsal")
    if captured["proposedExposure"] != policy["proposedExposure"] | {
        "rehearsalOnlyExpiry": captured["proposedExposure"]["rehearsalOnlyExpiry"]
    }:
        raise RuntimeError("accepted exposure policy changed")

    pending_nonces: dict[str, int] = {}
    for role in ("writer", "buyer"):
        address = qualifier.normalize_address(captured["actors"][role]["address"])
        pending = int(rpc.call("eth_getTransactionCount", [address, "pending"]), 16)
        confirmed = int(captured["actors"][role]["confirmedNonce"])
        if pending != confirmed:
            raise RuntimeError(f"{role} has a public pending-nonce gap")
        pending_nonces[role] = pending

    body = {
        "schemaVersion": 1,
        "status": "PASS_PUBLIC_LIFECYCLE_EXECUTION_PREFLIGHT_NO_AUTHORITY",
        "mode": "PINNED_READ_ONLY_STATE_PLUS_PENDING_NONCES_NO_KEYS_NO_SIGNING_NO_BROADCAST",
        "classification": lifecycle_plan["classification"],
        "network": captured["network"],
        "sourceBindings": {
            name: {
                "path": repository_relative(path),
                "sha256": file_sha256(path),
            }
            for name, path in source_paths.items()
        },
        "plan": {
            "planBodySha256": lifecycle_plan["planBodySha256"],
            "planFileSha256": file_sha256(lifecycle_plan_path),
            "rehearsalFileSha256": file_sha256(rehearsal_path),
        },
        "marketState": market,
        "actors": captured["actors"],
        "pendingNonces": pending_nonces,
        "checks": {
            "acceptedPlanAndRehearsalHashesMatch": True,
            "writerStateUnchanged": True,
            "buyerStateUnchanged": True,
            "poolStateUnchanged": True,
            "stockControlsEligible": True,
            "confirmedAndPendingNoncesEqual": True,
        },
        "authorization": {
            "signing": False,
            "publicBroadcast": False,
            "wrapping": False,
            "approvals": False,
            "swaps": False,
            "collateralDeposits": False,
            "optionPositions": False,
            "withdrawals": False,
            "otherMarkets": False,
            "mainnet": False,
        },
        "publicExecution": {"ready": False, "broadcastAttempted": False},
        "nextGate": "BUILD_NONCE_AND_DEADLINE_BOUND_CANDIDATE_THEN_EXACT_FORK_OPERATOR_SIMULATION",
    }
    body["preflightBodySha256"] = canonical_sha256(body)
    return body


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL)
    parser.add_argument("--chain", type=Path, default=DEFAULT_CHAIN)
    parser.add_argument("--genesis", type=Path, default=DEFAULT_GENESIS)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--rehearsal", type=Path, default=DEFAULT_REHEARSAL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rpc = qualifier.CastReadOnlyRpc(args.rpc_url)
    result = qualify(
        rpc,
        chain=load_json(args.chain),
        genesis=load_json(args.genesis),
        policy=load_json(args.policy),
        lifecycle_plan=load_json(args.plan),
        lifecycle_plan_path=args.plan,
        rehearsal=load_json(args.rehearsal),
        rehearsal_path=args.rehearsal,
        source_paths={
            "chainManifest": args.chain,
            "genesisManifest": args.genesis,
            "exposurePolicy": args.policy,
            "lifecyclePlan": args.plan,
            "lifecycleRehearsal": args.rehearsal,
            "qualifier": Path(__file__).resolve(),
        },
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "output": str(args.output),
                "referenceBlock": result["network"]["referenceBlock"],
                "writerPendingNonce": result["pendingNonces"]["writer"],
                "buyerPendingNonce": result["pendingNonces"]["buyer"],
                "signing": False,
                "publicBroadcast": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
