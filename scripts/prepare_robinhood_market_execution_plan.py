#!/usr/bin/env python3
"""Build a nonce/time-bound unsigned PLTR/WETH execution candidate.

This offline transformer consumes the accepted exposure, a successful fresh
read-only preflight, and the deterministic base plan. It binds consecutive
nonces and refreshes only the deadline-bearing calldata. It has no RPC, key,
signing, transaction-serialization, or broadcast capability.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


def _load_sibling(name: str, filename: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required sibling module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fork_planner = _load_sibling(
    "stonkhedge_market_fork_planner", "prepare_robinhood_market_fork_plan.py"
)
planner = fork_planner.planner
verifier = fork_planner.verifier

REPOSITORY = Path(__file__).resolve().parents[1]
MARKETS = REPOSITORY / "manifests" / "markets"
DEFAULT_BASE_PLAN = MARKETS / "robinhood-testnet-pltr-weth-offline-plan-2026-09-09.json"
DEFAULT_PREFLIGHT = (
    MARKETS / "robinhood-testnet-pltr-weth-execution-preflight-2026-09-10.json"
)
DEFAULT_ACCEPTANCE = (
    MARKETS
    / "robinhood-testnet-pltr-weth-execution-planning-acceptance-2026-09-10.json"
)
DEFAULT_OUTPUT = (
    MARKETS / "robinhood-testnet-pltr-weth-execution-candidate-2026-09-10.json"
)
CHAIN_ID = 46630
OFFICIAL_RPC_URL = "https://rpc.testnet.chain.robinhood.com"

BODY_FIELDS = (
    "status",
    "mode",
    "network",
    "sourceBindings",
    "market",
    "actor",
    "contracts",
    "priceAndLiquidity",
    "maximumExposure",
    "executionClock",
    "initialState",
    "predictedMarketContracts",
    "gasPolicy",
    "startNonce",
    "nextNonce",
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


def _repository_relative(path: Path, generator_path: Path) -> str:
    root = Path(generator_path).resolve().parents[1]
    try:
        return Path(path).resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"source must remain inside repository: {path}") from exc


def _all_false(values: Any) -> bool:
    return (
        isinstance(values, dict)
        and bool(values)
        and all(value is False for value in values.values())
    )


def _check_result(preflight: dict[str, Any], name: str) -> Any:
    matches = [
        result
        for result in preflight.get("checks", {}).get("results", [])
        if result.get("name") == name and result.get("status") == "PASS"
    ]
    if len(matches) != 1:
        raise ValueError(f"preflight check is absent or ambiguous: {name}")
    return matches[0]["actual"]


def _validate_acceptance(
    acceptance: dict[str, Any], acceptance_path: Path, base_plan: dict[str, Any]
) -> None:
    if (
        acceptance.get("status")
        != "OWNER_ACCEPTED_EXECUTION_PLANNING_ONLY_NO_SIGNING_NO_BROADCAST"
    ):
        raise ValueError("execution-planning acceptance status is invalid")
    if acceptance.get("network", {}).get("chainId") != CHAIN_ID:
        raise ValueError("execution-planning acceptance chain is invalid")
    if planner.normalize_address(
        acceptance.get("actor", "")
    ) != planner.normalize_address(base_plan["actor"]["address"]):
        raise ValueError("execution-planning acceptance actor drifted")
    if acceptance.get("market") != {
        "symbol": base_plan["market"]["symbol"],
        "poolId": base_plan["market"]["poolId"],
        "poolKey": base_plan["market"]["poolKey"],
    }:
        raise ValueError("execution-planning acceptance market drifted")

    exposure = acceptance.get("acceptedExecutionPlanningExposure", {})
    expected_exposure = {
        "classification": base_plan["priceAndLiquidity"]["classification"],
        "testWethPerPltr": "0.001",
        "sqrtPriceX96": base_plan["priceAndLiquidity"]["sqrtPriceX96"],
        "wrapNativeWei": base_plan["maximumExposureProposal"]["wrapNativeWei"],
        "maximumPltrTransfer": base_plan["maximumExposureProposal"][
            "maximumPltrTransfer"
        ],
        "maximumWethTransfer": base_plan["maximumExposureProposal"][
            "maximumWethTransfer"
        ],
        "tickLower": base_plan["priceAndLiquidity"]["tickLower"],
        "tickUpper": base_plan["priceAndLiquidity"]["tickUpper"],
        "liquidity": base_plan["priceAndLiquidity"]["liquidity"],
        "factorySalt": base_plan["predictedMarketContracts"]["factorySalt"],
        "permit2AllowanceLifetimeSeconds": 7200,
        "liquidityDeadlineSeconds": 3600,
        "allowanceCleanupRequired": True,
        "warning": (
            "Never label or display the synthetic ratio as a live PLTR, equity, "
            "issuer, or oracle price."
        ),
    }
    if exposure != expected_exposure:
        raise ValueError("execution-planning acceptance exposure drifted")
    if acceptance.get("authorizedWork") != {
        "prepareFreshNonceAndTimeBoundExecutionCandidate": True,
        "implementOneStepOperator": True,
        "simulateExecutionCandidateOnLoopbackAnvil": True,
    }:
        raise ValueError("execution-planning acceptance work scope drifted")
    if not _all_false(acceptance.get("authorization")):
        raise ValueError("execution-planning acceptance authorization must stay false")

    bindings = acceptance.get("evidenceBindings", {})
    for name, expected_path in (
        ("baseOfflinePlan", DEFAULT_BASE_PLAN),
        (
            "successfulForkRehearsal",
            MARKETS / "robinhood-testnet-pltr-weth-fork-rehearsal-2026-09-09.json",
        ),
    ):
        binding = bindings.get(name, {})
        path = Path(acceptance_path).resolve().parent / binding.get("path", "")
        if path.resolve() != expected_path.resolve() or not path.is_file():
            raise ValueError(f"execution-planning acceptance {name} path drifted")
        if binding.get("sha256") != file_sha256(path):
            raise ValueError(f"execution-planning acceptance {name} hash drifted")
    if bindings["baseOfflinePlan"].get("planBodySha256") != base_plan.get(
        "planBodySha256"
    ):
        raise ValueError("execution-planning acceptance base-plan body drifted")
    rehearsal = load_json(
        Path(acceptance_path).resolve().parent
        / bindings["successfulForkRehearsal"]["path"]
    )
    if rehearsal.get("status") != bindings["successfulForkRehearsal"].get("status"):
        raise ValueError("execution-planning acceptance rehearsal status drifted")


def execution_plan_body_sha256(plan: dict[str, Any]) -> str:
    return planner.canonical_sha256({field: plan[field] for field in BODY_FIELDS})


def build_execution_plan(
    base_plan_path: Path,
    preflight_path: Path,
    acceptance_path: Path,
    generator_path: Path,
) -> dict[str, Any]:
    base_plan_path = Path(base_plan_path)
    preflight_path = Path(preflight_path)
    acceptance_path = Path(acceptance_path)
    generator_path = Path(generator_path)
    base_plan = load_json(base_plan_path)
    preflight = load_json(preflight_path)
    acceptance = load_json(acceptance_path)

    reference_timestamp = fork_planner._validate_preflight(
        base_plan, base_plan_path, preflight
    )
    _validate_acceptance(acceptance, acceptance_path, base_plan)
    if not _all_false(preflight.get("authorization")):
        raise ValueError("preflight authorization must remain false")

    exposure_acceptance = acceptance["acceptedExecutionPlanningExposure"]
    liquidity_deadline = reference_timestamp + int(
        exposure_acceptance["liquidityDeadlineSeconds"]
    )
    permit_expiration = reference_timestamp + int(
        exposure_acceptance["permit2AllowanceLifetimeSeconds"]
    )
    transactions = copy.deepcopy(base_plan["transactions"])
    fork_planner._refresh_deadlines(transactions, permit_expiration, liquidity_deadline)
    start_nonce = int(preflight["observations"]["actorPendingNonce"])
    if int(preflight["observations"]["actorConfirmedNonce"]) != start_nonce:
        raise ValueError("preflight nonce gap prevents execution planning")
    for ordinal, transaction in enumerate(transactions):
        transaction["nonce"] = start_nonce + ordinal
        transaction["authorizedForBroadcast"] = False
        intent = transaction.get("decodedIntent", {})
        if intent.get("clockClassification") == "FORK_ONLY_REHEARSAL":
            intent["clockClassification"] = (
                "EXECUTION_CANDIDATE_REQUIRES_SEPARATE_AUTHORIZATION"
            )
        transaction["requiredPreState"] = [
            value.replace("fork timestamp", "execution block timestamp")
            for value in transaction.get("requiredPreState", [])
        ]
        transaction["expectedPostState"] = [
            value.replace("fork-only rehearsal", "execution-candidate")
            for value in transaction.get("expectedPostState", [])
        ]

    predicted = copy.deepcopy(base_plan["predictedMarketContracts"])
    predicted["create3Proxy"] = fork_planner.predict_create3_proxy(
        base_plan["contracts"]["panopticFactoryV4"], predicted["derivedSalt32"]
    )
    maximum_exposure = copy.deepcopy(base_plan["maximumExposureProposal"])
    maximum_exposure["status"] = "OWNER_ACCEPTED_FOR_EXECUTION_PLANNING_ONLY"

    plan: dict[str, Any] = {
        "schemaVersion": 1,
        "status": "EXECUTION_CANDIDATE_REQUIRES_SEPARATE_AUTHORIZATION",
        "mode": "UNSIGNED_NONCE_AND_TIME_BOUND_NO_SIGNING_NO_BROADCAST",
        "network": {
            "name": base_plan["network"]["name"],
            "chainId": CHAIN_ID,
            "rpc": OFFICIAL_RPC_URL,
            "referenceBlock": preflight["network"]["blockNumber"],
            "referenceBlockHash": preflight["network"]["blockHash"],
            "referenceBlockTimestamp": preflight["network"]["blockTimestamp"],
        },
        "sourceBindings": {
            "basePlan": {
                "path": _repository_relative(base_plan_path, generator_path),
                "sha256": file_sha256(base_plan_path),
                "planBodySha256": base_plan["planBodySha256"],
            },
            "freshPreflight": {
                "path": _repository_relative(preflight_path, generator_path),
                "sha256": file_sha256(preflight_path),
                "verifierSha256": preflight["sourceBindings"]["verifierSha256"],
            },
            "executionPlanningAcceptance": {
                "path": _repository_relative(acceptance_path, generator_path),
                "sha256": file_sha256(acceptance_path),
            },
            "generator": {
                "path": _repository_relative(generator_path, generator_path),
                "sha256": file_sha256(generator_path),
            },
        },
        "market": copy.deepcopy(base_plan["market"]),
        "actor": copy.deepcopy(base_plan["actor"]),
        "contracts": copy.deepcopy(base_plan["contracts"]),
        "priceAndLiquidity": copy.deepcopy(base_plan["priceAndLiquidity"]),
        "maximumExposure": maximum_exposure,
        "executionClock": {
            "referenceTimestampUnix": reference_timestamp,
            "liquidityDeadlineUnix": liquidity_deadline,
            "permit2ExpirationUnix": permit_expiration,
            "minimumSecondsRemainingAtTransactionZero": 1800,
            "classification": "TIME_BOUND_EXECUTION_CANDIDATE_NOT_AUTHORIZATION",
        },
        "initialState": {
            "nativeBalanceWei": str(
                _check_result(
                    preflight,
                    "actor native balance covers wrap plus reserve before gas",
                )
            ),
            "pltrBalance": str(
                _check_result(
                    preflight, "actor PLTR balance covers LP cap plus reserve"
                )
            ),
            "wethBalance": str(
                _check_result(
                    preflight,
                    "actor starts with zero WETH for deterministic wrap accounting",
                )
            ),
            "positionManagerNextTokenIdFloor": preflight["observations"][
                "positionManagerNextTokenId"
            ],
            "actorPositionManagerNftBalance": "0",
            "activeLiquidity": preflight["observations"]["activeLiquidity"],
        },
        "predictedMarketContracts": predicted,
        "gasPolicy": {
            "maximumGasPriceWei": "100000000",
            "maximumGasLimitPerTransaction": 0xFF0000,
            "estimateMultiplierBps": 12500,
            "estimateAdditiveBuffer": 50000,
            "operatorMustRecheckAfterSigning": True,
        },
        "startNonce": start_nonce,
        "nextNonce": start_nonce + len(transactions),
        "transactionCount": len(transactions),
        "transactions": transactions,
        "authorization": copy.deepcopy(acceptance["authorization"]),
        "publicExecution": {
            "ready": False,
            "blockingReasons": [
                "the one-step operator candidate has not yet passed exact-plan simulation",
                "this candidate becomes stale if nonce, deadlines, or required state changes",
                "no hash-bound signing or public broadcast authorization exists",
            ],
        },
        "nextGate": "ONE_STEP_OPERATOR_EXACT_PLAN_LOOPBACK_SIMULATION",
    }
    plan["executionPlanBodySha256"] = execution_plan_body_sha256(plan)
    return plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-plan", type=Path, default=DEFAULT_BASE_PLAN)
    parser.add_argument("--preflight", type=Path, default=DEFAULT_PREFLIGHT)
    parser.add_argument("--acceptance", type=Path, default=DEFAULT_ACCEPTANCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_execution_plan(
        args.base_plan, args.preflight, args.acceptance, Path(__file__).resolve()
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Wrote unsigned execution candidate: {args.output}")
    print(f"Execution-plan body SHA-256: {plan['executionPlanBodySha256']}")
    print(f"Nonce range: {plan['startNonce']} through {plan['nextNonce'] - 1}")
    print("NO RPC, KEY, SIGNING, SERIALIZATION, OR BROADCAST CAPABILITY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
