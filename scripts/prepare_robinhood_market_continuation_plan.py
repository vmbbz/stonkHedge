#!/usr/bin/env python3
"""Build an unsigned continuation plan after public genesis indexes 0-3.

The transformer consumes canonical public-progress evidence and the previously
authorized execution plan. It repeats the PLTR Permit2 approval with a fresh
expiry, prepares the eight still-unexecuted intents, and binds nonces 4-12.
It has no RPC, key, signing, serialization, or broadcast capability.
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


execution_planner = _load_sibling(
    "stonkhedge_market_execution_planner",
    "prepare_robinhood_market_execution_plan.py",
)
planner = execution_planner.planner
fork_planner = execution_planner.fork_planner

REPOSITORY = Path(__file__).resolve().parents[1]
MARKETS = REPOSITORY / "manifests" / "markets"
DEFAULT_PREVIOUS_PLAN = (
    MARKETS / "robinhood-testnet-pltr-weth-execution-candidate-2026-09-10.json"
)
DEFAULT_PROGRESS = (
    MARKETS / "robinhood-testnet-pltr-weth-public-progress-2026-09-10.json"
)
DEFAULT_ACCEPTANCE = (
    MARKETS
    / "robinhood-testnet-pltr-weth-execution-planning-acceptance-2026-09-10.json"
)
DEFAULT_AUTHORIZATION = (
    MARKETS / "robinhood-testnet-pltr-weth-execution-authorization-2026-09-10.json"
)
DEFAULT_OUTPUT = (
    MARKETS / "robinhood-testnet-pltr-weth-continuation-candidate-2026-09-10.json"
)
SOURCE_ORDINALS = (3, 4, 5, 6, 7, 8, 9, 10, 11)
CONTINUATION_LIQUIDITY_DEADLINE_SECONDS = 14_400
CONTINUATION_PERMIT2_LIFETIME_SECONDS = 21_600
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
    "stateSchedule",
    "continuation",
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
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON manifest must contain an object: {path}")
    return value


def _relative(path: Path, generator_path: Path) -> str:
    try:
        return (
            Path(path)
            .resolve()
            .relative_to(Path(generator_path).resolve().parents[1])
            .as_posix()
        )
    except ValueError as exc:
        raise ValueError(f"source must remain inside repository: {path}") from exc


def execution_plan_body_sha256(plan: dict[str, Any]) -> str:
    return planner.canonical_sha256({field: plan[field] for field in BODY_FIELDS})


def _validate_progress(
    previous: dict[str, Any],
    previous_path: Path,
    progress: dict[str, Any],
    authorization_path: Path,
) -> None:
    if progress.get("status") != "PASS_STOPPED_AFTER_INDEX_3_FOR_DEADLINE_REFRESH":
        raise ValueError("continuation progress status is invalid")
    if progress.get("network", {}).get("chainId") != execution_planner.CHAIN_ID:
        raise ValueError("continuation progress chain is invalid")
    if planner.normalize_address(
        progress.get("actor", "")
    ) != planner.normalize_address(previous["actor"]["address"]):
        raise ValueError("continuation progress actor drifted")
    bindings = progress.get("sourceBindings", {})
    if bindings.get("executionPlanBodySha256") != previous.get(
        "executionPlanBodySha256"
    ):
        raise ValueError("continuation progress plan body drifted")
    if bindings.get("executionPlanFileSha256") != file_sha256(previous_path):
        raise ValueError("continuation progress plan file drifted")
    if bindings.get("authorizationManifestSha256") != file_sha256(authorization_path):
        raise ValueError("continuation progress authorization file drifted")
    if progress.get("completedThroughTransactionIndex") != 3:
        raise ValueError("continuation progress must stop after index 3")
    completed = progress.get("completedTransactions")
    if not isinstance(completed, list) or len(completed) != 4:
        raise ValueError("continuation progress transaction evidence is incomplete")
    for index, (record, transaction) in enumerate(
        zip(completed, previous["transactions"][:4])
    ):
        expected = {
            "index": index,
            "nonce": transaction["nonce"],
            "to": transaction["to"],
            "valueWei": transaction["valueWei"],
            "calldataKeccak256": transaction["calldataKeccak256"],
            "status": "PASS",
        }
        for field, value in expected.items():
            actual = record.get(field)
            if field == "to":
                actual = planner.normalize_address(actual)
                value = planner.normalize_address(value)
            if actual != value:
                raise ValueError(
                    f"continuation progress transaction {index} {field} drifted"
                )
        planner.normalize_hash(record.get("transactionHash", ""), "transaction hash")
        planner.normalize_hash(record.get("blockHash", ""), "block hash")
        planner.normalize_hash(
            "0x" + record.get("externalEvidenceSha256", ""),
            "external evidence hash",
        )

    state = progress.get("postState", {})
    exposure = previous["maximumExposure"]
    expected_state = {
        "pendingNonce": 4,
        "pltrBalance": previous["initialState"]["pltrBalance"],
        "wethBalance": exposure["wrapNativeWei"],
        "erc20Allowances": {
            "PLTR": exposure["maximumPltrTransfer"],
            "WETH": exposure["maximumWethTransfer"],
        },
        "sqrtPriceX96": "0",
        "tick": 0,
        "activeLiquidity": "0",
        "positionManagerActorNftBalance": "0",
        "factoryMapping": "0x0000000000000000000000000000000000000000",
    }
    for field, value in expected_state.items():
        if state.get(field) != value:
            raise ValueError(f"continuation progress state {field} drifted")
    permit = state.get("permit2Allowances", {})
    if permit.get("PLTR", {}).get("amount") != exposure["maximumPltrTransfer"]:
        raise ValueError("continuation PLTR Permit2 allowance drifted")
    if permit.get("WETH", {}).get("amount") != "0":
        raise ValueError("continuation WETH Permit2 allowance is not zero")
    if int(state.get("nativeBalanceWei", "0")) <= 0:
        raise ValueError("continuation native balance is invalid")
    if int(state.get("positionManagerNextTokenIdFloor", "0")) <= 0:
        raise ValueError("continuation NFT floor is invalid")
    if not execution_planner._all_false(progress.get("authorization")):
        raise ValueError("continuation progress authorization must remain false")


def _allowance_state(
    pltr_erc20: int,
    weth_erc20: int,
    pltr_permit2: int,
    weth_permit2: int,
    *,
    pltr_expiration: int,
    weth_expiration: int,
    original_phase: int,
) -> dict[str, Any]:
    return {
        "originalCompletedSteps": original_phase,
        "erc20": {"PLTR": str(pltr_erc20), "WETH": str(weth_erc20)},
        "permit2": {
            "PLTR": {
                "amount": str(pltr_permit2),
                "expiration": pltr_expiration if pltr_permit2 else 0,
            },
            "WETH": {
                "amount": str(weth_permit2),
                "expiration": weth_expiration if weth_permit2 else 0,
            },
        },
    }


def build_continuation_plan(
    previous_plan_path: Path,
    progress_path: Path,
    acceptance_path: Path,
    authorization_path: Path,
    generator_path: Path,
) -> dict[str, Any]:
    previous = load_json(previous_plan_path)
    progress = load_json(progress_path)
    acceptance = load_json(acceptance_path)
    _validate_progress(previous, previous_plan_path, progress, authorization_path)
    execution_planner._validate_acceptance(
        acceptance, acceptance_path, load_json(execution_planner.DEFAULT_BASE_PLAN)
    )

    reference_timestamp = int(progress["network"]["referenceTimestampUnix"])
    exposure_acceptance = acceptance["acceptedExecutionPlanningExposure"]
    liquidity_deadline = reference_timestamp + CONTINUATION_LIQUIDITY_DEADLINE_SECONDS
    permit_expiration = reference_timestamp + CONTINUATION_PERMIT2_LIFETIME_SECONDS
    refreshed_transactions = copy.deepcopy(previous["transactions"])
    fork_planner._refresh_deadlines(
        refreshed_transactions, permit_expiration, liquidity_deadline
    )
    transactions = [
        copy.deepcopy(refreshed_transactions[index]) for index in SOURCE_ORDINALS
    ]
    start_nonce = int(progress["postState"]["pendingNonce"])
    for ordinal, (source_ordinal, transaction) in enumerate(
        zip(SOURCE_ORDINALS, transactions)
    ):
        transaction["sourceOrdinal"] = source_ordinal
        transaction["ordinal"] = ordinal
        transaction["nonce"] = start_nonce + ordinal
        transaction["authorizedForBroadcast"] = False

    max_pltr = int(previous["maximumExposure"]["maximumPltrTransfer"])
    max_weth = int(previous["maximumExposure"]["maximumWethTransfer"])
    amount0 = int(
        previous["priceAndLiquidity"]["expectedAmount0AtSyntheticPriceRoundedUp"]
    )
    amount1 = int(
        previous["priceAndLiquidity"]["expectedAmount1AtSyntheticPriceRoundedUp"]
    )
    remaining_pltr = max_pltr - amount0
    remaining_weth = max_weth - amount1
    old_pltr_expiration = int(
        progress["postState"]["permit2Allowances"]["PLTR"]["expiration"]
    )
    schedule = [
        _allowance_state(
            max_pltr,
            max_weth,
            max_pltr,
            0,
            pltr_expiration=old_pltr_expiration,
            weth_expiration=0,
            original_phase=4,
        ),
        _allowance_state(
            max_pltr,
            max_weth,
            max_pltr,
            0,
            pltr_expiration=permit_expiration,
            weth_expiration=0,
            original_phase=4,
        ),
        _allowance_state(
            max_pltr,
            max_weth,
            max_pltr,
            max_weth,
            pltr_expiration=permit_expiration,
            weth_expiration=permit_expiration,
            original_phase=5,
        ),
        _allowance_state(
            max_pltr,
            max_weth,
            max_pltr,
            max_weth,
            pltr_expiration=permit_expiration,
            weth_expiration=permit_expiration,
            original_phase=6,
        ),
        _allowance_state(
            remaining_pltr,
            remaining_weth,
            remaining_pltr,
            remaining_weth,
            pltr_expiration=permit_expiration,
            weth_expiration=permit_expiration,
            original_phase=7,
        ),
        _allowance_state(
            remaining_pltr,
            remaining_weth,
            0,
            remaining_weth,
            pltr_expiration=0,
            weth_expiration=permit_expiration,
            original_phase=8,
        ),
        _allowance_state(
            remaining_pltr,
            remaining_weth,
            0,
            0,
            pltr_expiration=0,
            weth_expiration=0,
            original_phase=9,
        ),
        _allowance_state(
            0,
            remaining_weth,
            0,
            0,
            pltr_expiration=0,
            weth_expiration=0,
            original_phase=10,
        ),
        _allowance_state(
            0, 0, 0, 0, pltr_expiration=0, weth_expiration=0, original_phase=11
        ),
        _allowance_state(
            0, 0, 0, 0, pltr_expiration=0, weth_expiration=0, original_phase=12
        ),
    ]

    initial_state = copy.deepcopy(progress["postState"])
    initial_state["actorPositionManagerNftBalance"] = initial_state.pop(
        "positionManagerActorNftBalance"
    )
    initial_state.pop("factoryMapping")
    initial_state.pop("permit2Allowances")
    initial_state.pop("erc20Allowances")
    initial_state.pop("pendingNonce")

    plan: dict[str, Any] = {
        "schemaVersion": 1,
        "status": "CONTINUATION_EXECUTION_CANDIDATE_REQUIRES_SEPARATE_AUTHORIZATION",
        "mode": "UNSIGNED_PARTIAL_STATE_NONCE_AND_TIME_BOUND_NO_SIGNING_NO_BROADCAST",
        "network": copy.deepcopy(progress["network"]),
        "sourceBindings": {
            "previousExecutionPlan": {
                "path": _relative(previous_plan_path, generator_path),
                "sha256": file_sha256(previous_plan_path),
                "planBodySha256": previous["executionPlanBodySha256"],
            },
            "publicProgress": {
                "path": _relative(progress_path, generator_path),
                "sha256": file_sha256(progress_path),
            },
            "executionPlanningAcceptance": {
                "path": _relative(acceptance_path, generator_path),
                "sha256": file_sha256(acceptance_path),
            },
            "qualificationPreflight": copy.deepcopy(
                previous["sourceBindings"]["freshPreflight"]
            ),
            "generator": {
                "path": _relative(generator_path, generator_path),
                "sha256": file_sha256(generator_path),
            },
        },
        "market": copy.deepcopy(previous["market"]),
        "actor": copy.deepcopy(previous["actor"]),
        "contracts": copy.deepcopy(previous["contracts"]),
        "priceAndLiquidity": copy.deepcopy(previous["priceAndLiquidity"]),
        "maximumExposure": copy.deepcopy(previous["maximumExposure"]),
        "executionClock": {
            "referenceTimestampUnix": reference_timestamp,
            "liquidityDeadlineUnix": liquidity_deadline,
            "permit2ExpirationUnix": permit_expiration,
            "minimumSecondsRemainingAtTransactionZero": 1800,
            "classification": "TIME_BOUND_PARTIAL_STATE_CONTINUATION_NOT_AUTHORIZATION",
        },
        "initialState": initial_state,
        "stateSchedule": schedule,
        "continuation": {
            "publiclyCompletedThroughPriorIndex": 3,
            "repeatedSourceOrdinal": 3,
            "reasonForRepeat": "Refresh the already bounded PLTR Permit2 approval after the prior liquidity deadline expired.",
            "sourceOrdinals": list(SOURCE_ORDINALS),
            "transactionCount": len(transactions),
            "operationalClockPolicy": {
                "priorLiquidityDeadlineSeconds": int(
                    exposure_acceptance["liquidityDeadlineSeconds"]
                ),
                "continuationLiquidityDeadlineSeconds": CONTINUATION_LIQUIDITY_DEADLINE_SECONDS,
                "priorPermit2AllowanceLifetimeSeconds": int(
                    exposure_acceptance["permit2AllowanceLifetimeSeconds"]
                ),
                "continuationPermit2AllowanceLifetimeSeconds": CONTINUATION_PERMIT2_LIFETIME_SECONDS,
                "reason": "Avoid another partially staged sequence while preserving the exact bounded token amounts and one-step stop policy.",
            },
        },
        "predictedMarketContracts": copy.deepcopy(previous["predictedMarketContracts"]),
        "gasPolicy": copy.deepcopy(previous["gasPolicy"]),
        "startNonce": start_nonce,
        "nextNonce": start_nonce + len(transactions),
        "transactionCount": len(transactions),
        "transactions": transactions,
        "authorization": copy.deepcopy(progress["authorization"]),
        "publicExecution": {
            "ready": False,
            "blockingReasons": [
                "the continuation operator has not passed exact-head simulation",
                "this partial-state candidate becomes stale if state, nonce, or deadlines change",
                "no hash-bound continuation signing or broadcast authorization exists",
            ],
        },
        "nextGate": "CONTINUATION_ONE_STEP_OPERATOR_EXACT_HEAD_REPLAY",
    }
    plan["executionPlanBodySha256"] = execution_plan_body_sha256(plan)
    return plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-plan", type=Path, default=DEFAULT_PREVIOUS_PLAN)
    parser.add_argument("--progress", type=Path, default=DEFAULT_PROGRESS)
    parser.add_argument("--acceptance", type=Path, default=DEFAULT_ACCEPTANCE)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_continuation_plan(
        args.previous_plan,
        args.progress,
        args.acceptance,
        args.authorization,
        Path(__file__).resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Wrote unsigned continuation candidate: {args.output}")
    print(f"Continuation body SHA-256: {plan['executionPlanBodySha256']}")
    print(f"Nonce range: {plan['startNonce']} through {plan['nextNonce'] - 1}")
    print("NO RPC, KEY, SIGNING, SERIALIZATION, OR BROADCAST CAPABILITY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
