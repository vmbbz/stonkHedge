#!/usr/bin/env python3
"""Reconcile exactly one PLTR/WETH genesis step on Anvil or Robinhood testnet.

Simulation rejects public RPC URLs and never opens credentials. The dormant
public lane is testnet-only and requires an exact generated execution plan,
passing aggregate simulation evidence, a separate hash-bound authorization,
an exact per-index confirmation phrase, and a password-protected Foundry
keystore. It signs and sends at most one transaction, fully reconciles the
post-state, writes evidence outside the repository, and stops.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


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
fork_simulator = _load_sibling(
    "stonkhedge_market_fork_simulator", "simulate_robinhood_market_fork.py"
)
direct_operator = _load_sibling(
    "stonkhedge_direct_operator", "operate_robinhood_direct_deployment.py"
)
qualifier = fork_simulator.qualifier

REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-execution-candidate-2026-09-10.json"
)
DEFAULT_RPC_URL = "http://127.0.0.1:8547"
OFFICIAL_RPC_URL = execution_planner.OFFICIAL_RPC_URL
DEFAULT_SIMULATION_REPORT = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-execution-operator-simulation-2026-09-10.json"
)
SIMULATION_RUNNER = (
    Path(__file__)
    .resolve()
    .with_name("simulate_robinhood_market_execution_operator.py")
)
ERC721_TRANSFER_TOPIC = (
    "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)
ZERO_TOPIC = "0" * 64
CHAIN_MANIFEST = REPOSITORY / "manifests" / "chains" / "robinhood-testnet-46630.json"
DEPLOYMENT_MANIFEST = (
    REPOSITORY
    / "manifests"
    / "deployments"
    / "robinhood-testnet-direct-public-progress-2026-09-09.json"
)
ACTOR_MANIFEST = (
    REPOSITORY
    / "manifests"
    / "deployments"
    / "robinhood-testnet-second-actor-2026-09-09.json"
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


def validate_local_rpc_url(rpc_url: str) -> None:
    fork_simulator.validate_local_rpc_url(rpc_url)


def validate_execution_plan(plan: dict[str, Any], plan_path: Path) -> None:
    if plan.get("status") != "EXECUTION_CANDIDATE_REQUIRES_SEPARATE_AUTHORIZATION":
        raise ValueError("execution-plan status is invalid")
    if plan.get("mode") != "UNSIGNED_NONCE_AND_TIME_BOUND_NO_SIGNING_NO_BROADCAST":
        raise ValueError("execution-plan mode is invalid")
    if plan.get("network", {}).get("chainId") != execution_planner.CHAIN_ID:
        raise ValueError("execution-plan chain is invalid")
    if plan.get("network", {}).get("rpc") != execution_planner.OFFICIAL_RPC_URL:
        raise ValueError("execution-plan public RPC binding drifted")
    if not execution_planner._all_false(plan.get("authorization")):
        raise ValueError("execution-plan authorization must remain entirely false")
    if plan.get("publicExecution", {}).get("ready") is not False:
        raise ValueError("execution-plan public execution must remain disabled")
    transactions = plan.get("transactions")
    if not isinstance(transactions, list) or len(transactions) != 12:
        raise ValueError("execution plan must contain twelve transactions")
    if plan.get("transactionCount") != 12:
        raise ValueError("execution-plan transaction count drifted")
    start_nonce = plan.get("startNonce")
    if not isinstance(start_nonce, int) or start_nonce < 0:
        raise ValueError("execution-plan start nonce is invalid")
    if plan.get("nextNonce") != start_nonce + 12:
        raise ValueError("execution-plan next nonce drifted")
    actor = qualifier.normalize_address(plan.get("actor", {}).get("address", ""))
    for ordinal, transaction in enumerate(transactions):
        if transaction.get("ordinal") != ordinal:
            raise ValueError(f"execution transaction {ordinal} ordinal drifted")
        if transaction.get("nonce") != start_nonce + ordinal:
            raise ValueError(f"execution transaction {ordinal} nonce drifted")
        if qualifier.normalize_address(transaction.get("from", "")) != actor:
            raise ValueError(f"execution transaction {ordinal} actor drifted")
        if transaction.get("authorizedForBroadcast") is not False:
            raise ValueError(f"execution transaction {ordinal} became authorized")
    if plan.get(
        "executionPlanBodySha256"
    ) != execution_planner.execution_plan_body_sha256(plan):
        raise ValueError("execution-plan body SHA-256 drifted")

    repository = Path(plan_path).resolve().parents[2]
    bindings = plan.get("sourceBindings", {})
    paths: dict[str, Path] = {}
    for name in (
        "basePlan",
        "freshPreflight",
        "executionPlanningAcceptance",
        "generator",
    ):
        binding = bindings.get(name, {})
        source = repository / binding.get("path", "")
        if not source.is_file() or file_sha256(source) != binding.get("sha256"):
            raise ValueError(f"execution-plan source binding {name} drifted")
        paths[name] = source
    regenerated = execution_planner.build_execution_plan(
        paths["basePlan"],
        paths["freshPreflight"],
        paths["executionPlanningAcceptance"],
        paths["generator"],
    )
    if plan != regenerated:
        raise ValueError("execution plan is not the exact output of its bound inputs")


def _normalized_hash(value: str, name: str) -> str:
    return direct_operator._normalize_hash(value, name)


def validate_simulation_report(
    report: dict[str, Any],
    plan: dict[str, Any],
    *,
    plan_file_hash: str,
    operator_hash: str,
) -> None:
    if report.get("schemaVersion") != 1:
        raise ValueError("operator simulation report schema version is invalid")
    if report.get("status") != "PASS_EXECUTION_CANDIDATE_ONE_STEP_OPERATOR_REHEARSAL":
        raise ValueError("operator simulation report is not passing")
    if (
        report.get("mode")
        != "LOOPBACK_ANVIL_ONLY_NO_CREDENTIALS_NO_SIGNING_NO_PUBLIC_BROADCAST"
    ):
        raise ValueError("operator simulation report mode is invalid")
    if report.get("stepCount") != len(plan["transactions"]):
        raise ValueError("operator simulation report step count drifted")
    if report.get("authorization") != plan.get(
        "authorization"
    ) or not execution_planner._all_false(report.get("authorization")):
        raise ValueError("operator simulation authorization must remain entirely false")
    if report.get("publicExecution", {}).get("ready") is not False:
        raise ValueError(
            "operator simulation report public execution must remain disabled"
        )
    if report.get("publicExecution", {}).get("broadcastAttempted") is not False:
        raise ValueError("operator simulation report claims a public broadcast")
    bindings = report.get("sourceBindings", {})
    expected = {
        "executionPlanBodySha256": plan["executionPlanBodySha256"],
        "executionPlanFileSha256": plan_file_hash,
        "operatorSha256": operator_hash,
        "runnerSha256": file_sha256(SIMULATION_RUNNER),
    }
    for field, digest in expected.items():
        if _normalized_hash(
            bindings.get(field), f"simulation {field}"
        ) != _normalized_hash(digest, field):
            raise ValueError(f"operator simulation report {field} mismatch")

    lineage = report.get("lineage", {})
    reference_block = plan["network"]["referenceBlock"]
    if (
        not isinstance(lineage.get("clientVersion"), str)
        or "anvil" not in lineage["clientVersion"].lower()
    ):
        raise ValueError("operator simulation report lineage is not Anvil")
    if lineage.get("chainId") != execution_planner.CHAIN_ID:
        raise ValueError("operator simulation report lineage chain ID drifted")
    if lineage.get("referenceBlock") != reference_block:
        raise ValueError("operator simulation report lineage reference block drifted")
    if _normalized_hash(
        lineage.get("referenceBlockHash"), "simulation reference block hash"
    ) != _normalized_hash(
        plan["network"]["referenceBlockHash"], "plan reference block hash"
    ):
        raise ValueError("operator simulation report reference block hash mismatch")
    if lineage.get("compatibilityBlock") != reference_block + 1:
        raise ValueError("operator simulation report compatibility block drifted")
    if lineage.get("latestLocalBlock") != reference_block + 1:
        raise ValueError("operator simulation report initial local head drifted")

    steps = report.get("steps")
    if not isinstance(steps, list) or len(steps) != len(plan["transactions"]):
        raise ValueError("operator simulation report steps are incomplete")
    seen_hashes: set[str] = set()
    maximum_gas = int(plan["gasPolicy"]["maximumGasLimitPerTransaction"])
    maximum_gas_price = int(plan["gasPolicy"]["maximumGasPriceWei"])
    for index, (step, transaction) in enumerate(zip(steps, plan["transactions"])):
        if not isinstance(step, dict):
            raise ValueError(f"operator simulation report step {index} is malformed")
        exact_fields = {
            "ordinal": transaction["ordinal"],
            "label": transaction["label"],
            "nonce": transaction["nonce"],
            "valueWei": transaction["valueWei"],
            "calldataKeccak256": transaction["calldataKeccak256"],
            "status": "PASS",
        }
        for field, expected_value in exact_fields.items():
            if step.get(field) != expected_value:
                raise ValueError(
                    f"operator simulation report step {index} {field} mismatch"
                )
        if qualifier.normalize_address(
            step.get("to", "")
        ) != qualifier.normalize_address(transaction["to"]):
            raise ValueError(
                f"operator simulation report step {index} recipient mismatch"
            )
        if "calldata" in step:
            raise ValueError(
                f"operator simulation report step {index} contains raw calldata"
            )
        expected_position_token_id = (
            int(plan["initialState"]["positionManagerNextTokenIdFloor"])
            if index >= 6
            else None
        )
        if step.get("liquidityPositionTokenId") != expected_position_token_id:
            raise ValueError(
                f"operator simulation report step {index} liquidity token ID mismatch"
            )
        transaction_hash = _normalized_hash(
            step.get("transactionHash"), f"simulation step {index} transaction hash"
        )
        if transaction_hash in seen_hashes:
            raise ValueError(
                "operator simulation report transaction hashes are not unique"
            )
        seen_hashes.add(transaction_hash)
        if step.get("blockNumber") != reference_block + 2 + index:
            raise ValueError(
                f"operator simulation report step {index} block number mismatch"
            )
        gas_used = step.get("gasUsed")
        if (
            isinstance(gas_used, bool)
            or not isinstance(gas_used, int)
            or not 0 < gas_used <= maximum_gas
        ):
            raise ValueError(
                f"operator simulation report step {index} gas used is invalid"
            )
        try:
            effective_gas_price = int(step.get("effectiveGasPriceWei"))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"operator simulation report step {index} gas price is invalid"
            ) from exc
        if not 0 <= effective_gas_price <= maximum_gas_price:
            raise ValueError(
                f"operator simulation report step {index} gas price is invalid"
            )

    initial = plan["initialState"]
    expected_initial = {
        "completedSteps": 0,
        "pendingNonce": plan["startNonce"],
        "nativeBalanceWei": initial["nativeBalanceWei"],
        "pltrBalance": initial["pltrBalance"],
        "wethBalance": initial["wethBalance"],
        "erc20Allowances": {"PLTR": "0", "WETH": "0"},
        "permit2Allowances": {"PLTR": "0", "WETH": "0"},
        "sqrtPriceX96": "0",
        "tick": 0,
        "activeLiquidity": "0",
        "positionManagerNextTokenId": initial["positionManagerNextTokenIdFloor"],
        "positionManagerActorNftBalance": initial["actorPositionManagerNftBalance"],
        "liquidityPositionTokenId": None,
        "sfpmPoolId": "0",
    }
    if report.get("initialState") != expected_initial:
        raise ValueError("operator simulation report initial state mismatch")

    exposure = plan["maximumExposure"]
    price = plan["priceAndLiquidity"]
    expected_final = {
        "completedSteps": 12,
        "pendingNonce": plan["nextNonce"],
        "pltrBalance": str(
            int(initial["pltrBalance"])
            - int(price["expectedAmount0AtSyntheticPriceRoundedUp"])
        ),
        "wethBalance": str(
            int(initial["wethBalance"])
            + int(exposure["wrapNativeWei"])
            - int(price["expectedAmount1AtSyntheticPriceRoundedUp"])
        ),
        "erc20Allowances": {"PLTR": "0", "WETH": "0"},
        "permit2Allowances": {"PLTR": "0", "WETH": "0"},
        "sqrtPriceX96": price["sqrtPriceX96"],
        "tick": price["initialTick"],
        "activeLiquidity": price["liquidity"],
        "positionManagerNextTokenId": str(
            int(initial["positionManagerNextTokenIdFloor"]) + 1
        ),
        "positionManagerActorNftBalance": str(
            int(initial["actorPositionManagerNftBalance"]) + 1
        ),
        "liquidityPositionTokenId": int(initial["positionManagerNextTokenIdFloor"]),
    }
    final = report.get("finalState")
    if not isinstance(final, dict):
        raise ValueError("operator simulation report final state is malformed")
    for field, expected_value in expected_final.items():
        if final.get(field) != expected_value:
            raise ValueError(f"operator simulation report final state {field} mismatch")
    try:
        final_native = int(final.get("nativeBalanceWei"))
        sfpm_pool_id = int(final.get("sfpmPoolId"))
    except (TypeError, ValueError) as exc:
        raise ValueError("operator simulation report final state is malformed") from exc
    if (
        not 0
        < final_native
        <= int(initial["nativeBalanceWei"]) - int(exposure["wrapNativeWei"])
    ):
        raise ValueError(
            "operator simulation report final state native balance is invalid"
        )
    if sfpm_pool_id <= 0:
        raise ValueError(
            "operator simulation report final state SFPM pool ID is invalid"
        )
    if report.get("nextGate") != (
        "REVIEW_THEN_REGENERATE_FINAL_CANDIDATE_BEFORE_ANY_BROADCAST_DECISION"
    ):
        raise ValueError("operator simulation report next gate drifted")


def validate_authorization(
    authorization: dict[str, Any],
    plan: dict[str, Any],
    *,
    index: int,
    plan_file_hash: str,
    operator_hash: str,
    simulation_report_hash: str,
) -> None:
    if (
        authorization.get("status")
        != "AUTHORIZED_MARKET_GENESIS_ONE_TRANSACTION_AT_A_TIME"
    ):
        raise ValueError("authorization status is invalid")
    if authorization.get("chainId") != execution_planner.CHAIN_ID:
        raise ValueError("authorization chain ID is invalid")
    if qualifier.normalize_address(
        authorization.get("actor", "")
    ) != qualifier.normalize_address(plan["actor"]["address"]):
        raise ValueError("authorization actor mismatch")
    bindings = {
        "executionPlanBodySha256": plan["executionPlanBodySha256"],
        "executionPlanFileSha256": plan_file_hash,
        "operatorSha256": operator_hash,
        "operatorSimulationReportSha256": simulation_report_hash,
    }
    for field, expected in bindings.items():
        if _normalized_hash(
            authorization.get(field), f"authorization {field}"
        ) != _normalized_hash(expected, field):
            raise ValueError(f"authorization {field} mismatch")
    maximum_index = authorization.get("maximumTransactionIndex")
    if (
        not isinstance(maximum_index, int)
        or maximum_index < 0
        or maximum_index >= len(plan["transactions"])
    ):
        raise ValueError("authorization maximum transaction index is invalid")
    if not isinstance(index, int) or index < 0 or index > maximum_index:
        raise ValueError("transaction index exceeds authorization")
    if index >= len(plan["transactions"]):
        raise ValueError("transaction index is outside the execution plan")
    if (
        authorization.get("executionPolicy")
        != "ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH"
    ):
        raise ValueError("authorization execution policy is invalid")
    if authorization.get("testnetOnly") is not True:
        raise ValueError("authorization must be testnet-only")
    if (
        not isinstance(authorization.get("approvedBy"), str)
        or not authorization["approvedBy"].strip()
    ):
        raise ValueError("authorization approver is absent")
    approved_at = authorization.get("approvedAt")
    if not isinstance(approved_at, str) or not approved_at.endswith("Z"):
        raise ValueError("authorization timestamp must be UTC")
    try:
        approval_time = datetime.fromisoformat(approved_at[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("authorization timestamp is not valid ISO-8601") from exc
    if (
        approval_time.tzinfo is None
        or approval_time.utcoffset() != timezone.utc.utcoffset(approval_time)
    ):
        raise ValueError("authorization timestamp must be UTC")
    approval_unix = int(approval_time.timestamp())
    if not (
        plan["executionClock"]["referenceTimestampUnix"]
        <= approval_unix
        < plan["executionClock"]["liquidityDeadlineUnix"]
    ):
        raise ValueError("authorization timestamp is outside the plan validity window")


def confirmation_phrase(plan_hash: str, index: int, nonce: int) -> str:
    normalized = _normalized_hash(plan_hash, "execution plan hash")
    return (
        f"BROADCAST_ROBINHOOD_{execution_planner.CHAIN_ID}_MARKET_PLAN_"
        f"{normalized[:8]}_INDEX_{index}_NONCE_{nonce}"
    )


def validate_market_aware_qualification(
    qualification: dict[str, Any], plan: dict[str, Any], index: int
) -> None:
    checks = qualification.get("checks", {})
    results = checks.get("results")
    if not isinstance(results, list) or len(results) != 79:
        raise RuntimeError("strict market qualification did not return 79 checks")
    if any(result.get("status") not in {"PASS", "FAIL"} for result in results):
        raise RuntimeError(
            "strict market qualification returned an invalid check status"
        )
    failures = [result for result in results if result.get("status") != "PASS"]
    passed = len(results) - len(failures)
    if checks.get("passed") != passed or checks.get("failed") != len(failures):
        raise RuntimeError("strict market qualification counters are inconsistent")
    if index < 6:
        if failures or not qualification.get("status", "").startswith(
            "READ_ONLY_QUALIFICATION_PASS_"
        ):
            raise RuntimeError(
                "strict market qualification failed before initialization"
            )
        return

    expected_name = "PLTR V4 PoolId is uninitialized"
    if [failure.get("name") for failure in failures] != [expected_name]:
        names = [failure.get("name") for failure in failures]
        raise RuntimeError(
            f"strict market qualification has unexpected failures: {names}"
        )
    failure = failures[0]
    expected_observation = {
        "poolId": plan["market"]["poolId"],
        "sqrtPriceX96": plan["priceAndLiquidity"]["sqrtPriceX96"],
    }
    if failure.get("actual") != expected_observation:
        raise RuntimeError("initialized PLTR pool observation differs from the plan")


def run_market_aware_strict_verifier(
    plan: dict[str, Any], plan_path: Path, index: int
) -> dict[str, Any]:
    preflight_binding = plan["sourceBindings"]["freshPreflight"]
    preflight_path = Path(plan_path).resolve().parents[2] / preflight_binding["path"]
    preflight = load_json(preflight_path)
    bindings = preflight.get("sourceBindings", {})
    sources = {
        "chainManifestSha256": CHAIN_MANIFEST,
        "deploymentManifestSha256": DEPLOYMENT_MANIFEST,
        "actorManifestSha256": ACTOR_MANIFEST,
        "qualifierSha256": Path(qualifier.__file__),
    }
    for field, source in sources.items():
        if _normalized_hash(bindings.get(field), field) != _normalized_hash(
            file_sha256(source), f"current {field}"
        ):
            raise RuntimeError(f"strict verifier source binding {field} drifted")

    chain = load_json(CHAIN_MANIFEST)
    deployment = load_json(DEPLOYMENT_MANIFEST)
    actor = load_json(ACTOR_MANIFEST)
    rpc = qualifier.CastReadOnlyRpc(OFFICIAL_RPC_URL)
    qualification = qualifier.qualify(rpc, chain, deployment, actor)
    validate_market_aware_qualification(qualification, plan, index)
    return {
        "status": "PASS_MARKET_AWARE_STRICT_QUALIFICATION",
        "blockNumber": qualification["snapshot"]["blockNumber"],
        "blockHash": qualification["snapshot"]["blockHash"],
        "checksPassed": qualification["checks"]["passed"],
        "plannedCheckReplacements": 0 if index < 6 else 1,
    }


def ensure_anvil_lineage(plan: dict[str, Any], client: Any) -> dict[str, Any]:
    version = client.call("web3_clientVersion", [])
    if not isinstance(version, str) or "anvil" not in version.lower():
        raise RuntimeError(f"refusing non-Anvil client: {version}")
    chain_id = int(client.call("eth_chainId", []), 16)
    if chain_id != plan["network"]["chainId"]:
        raise RuntimeError("Anvil chain ID does not match the execution plan")

    reference_number = int(plan["network"]["referenceBlock"])
    reference = client.call("eth_getBlockByNumber", [hex(reference_number), False])
    if not isinstance(reference, dict):
        raise RuntimeError("Anvil does not expose the execution-plan reference block")
    if (
        reference.get("hash", "").lower()
        != plan["network"]["referenceBlockHash"].lower()
    ):
        raise RuntimeError("Anvil reference block hash drifted")
    expected_timestamp = plan["executionClock"]["referenceTimestampUnix"]
    if int(reference["timestamp"], 16) != expected_timestamp:
        raise RuntimeError("Anvil reference block timestamp drifted")

    latest = client.call("eth_getBlockByNumber", ["latest", False])
    if not isinstance(latest, dict):
        raise RuntimeError("Anvil latest block response is malformed")
    latest_number = int(latest["number"], 16)
    if latest_number == reference_number:
        client.call("evm_setNextBlockTimestamp", [expected_timestamp + 1])
        client.call("evm_mine", [])
        latest = client.call("eth_getBlockByNumber", ["latest", False])
        latest_number = int(latest["number"], 16)
    if latest_number < reference_number + 1:
        raise RuntimeError("Anvil local compatibility child is absent")
    child = client.call("eth_getBlockByNumber", [hex(reference_number + 1), False])
    if not isinstance(child, dict):
        raise RuntimeError("Anvil local compatibility child is unreadable")
    if (
        child.get("parentHash", "").lower()
        != plan["network"]["referenceBlockHash"].lower()
    ):
        raise RuntimeError("Anvil local compatibility lineage drifted")
    if int(child["timestamp"], 16) != expected_timestamp + 1:
        raise RuntimeError("Anvil local compatibility timestamp drifted")
    if child.get("excessBlobGas") is None:
        raise RuntimeError("Anvil local compatibility header is incomplete")
    return {
        "clientVersion": version,
        "chainId": chain_id,
        "referenceBlock": reference_number,
        "referenceBlockHash": reference["hash"].lower(),
        "compatibilityBlock": reference_number + 1,
        "latestLocalBlock": latest_number,
    }


def expected_allowances(
    plan: dict[str, Any], completed: int
) -> tuple[int, int, int, int]:
    if not 0 <= completed <= 12:
        raise ValueError("completed step count must be between zero and twelve")
    exposure = plan["maximumExposure"]
    price = plan["priceAndLiquidity"]
    max_pltr = int(exposure["maximumPltrTransfer"])
    max_weth = int(exposure["maximumWethTransfer"])
    remaining_pltr = max_pltr - int(price["expectedAmount0AtSyntheticPriceRoundedUp"])
    remaining_weth = max_weth - int(price["expectedAmount1AtSyntheticPriceRoundedUp"])
    pltr_erc20 = (
        (remaining_pltr if completed >= 7 else max_pltr) if 2 <= completed < 10 else 0
    )
    weth_erc20 = (
        (remaining_weth if completed >= 7 else max_weth) if 3 <= completed < 11 else 0
    )
    pltr_permit2 = (
        (remaining_pltr if completed >= 7 else max_pltr) if 4 <= completed < 8 else 0
    )
    weth_permit2 = (
        (remaining_weth if completed >= 7 else max_weth) if 5 <= completed < 9 else 0
    )
    return pltr_erc20, weth_erc20, pltr_permit2, weth_permit2


def validate_liquidity_token_argument(index: int, token_id: int | None) -> None:
    if index >= 7 and token_id is None:
        raise ValueError(
            "--liquidity-token-id from the passing transaction-6 receipt evidence "
            "is required for indices 7 through 11"
        )
    if index < 7 and token_id is not None:
        raise ValueError("--liquidity-token-id is valid only for indices 7 through 11")
    if token_id is not None and token_id < 0:
        raise ValueError("liquidity token ID cannot be negative")


def _assert_equal(name: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise RuntimeError(f"{name} mismatch: expected {expected}, got {actual}")


def _verify_registered_market(client: Any, plan: dict[str, Any]) -> int:
    contracts = plan["contracts"]
    predicted = plan["predictedMarketContracts"]
    pool = qualifier.normalize_address(predicted["panopticPool"])
    _assert_equal("factory mapping", fork_simulator._factory_pool(client, plan), pool)
    for name in ("panopticPool", "collateralTracker0", "collateralTracker1"):
        code = client.call("eth_getCode", [predicted[name], "latest"])
        if not isinstance(code, str) or code == "0x":
            raise RuntimeError(f"registered {name} has empty code")
    owner = qualifier.normalize_address(
        fork_simulator._contract_call(
            client,
            contracts["panopticFactoryV4"],
            "ownerOf(uint256)",
            ["address"],
            ["uint256"],
            [int(pool, 16)],
        )
    )
    _assert_equal(
        "factory NFT owner",
        owner,
        qualifier.normalize_address(plan["actor"]["address"]),
    )
    tracker0 = qualifier.normalize_address(predicted["collateralTracker0"])
    tracker1 = qualifier.normalize_address(predicted["collateralTracker1"])
    for signature, expected in (
        ("collateralToken0()", tracker0),
        ("collateralToken1()", tracker1),
        ("riskEngine()", qualifier.normalize_address(contracts["riskEngine"])),
        ("poolManager()", qualifier.normalize_address(contracts["poolManager"])),
        ("SFPM()", qualifier.normalize_address(contracts["sfpmV4"])),
    ):
        actual = qualifier.normalize_address(
            fork_simulator._contract_call(client, pool, signature, ["address"])
        )
        _assert_equal(f"PanopticPool {signature}", actual, expected)
    for tracker, underlying in (
        (tracker0, contracts["pltr"]),
        (tracker1, contracts["weth"]),
    ):
        for signature, expected in (
            ("panopticPool()", pool),
            ("underlyingToken()", qualifier.normalize_address(underlying)),
            ("riskEngine()", qualifier.normalize_address(contracts["riskEngine"])),
            ("poolManager()", qualifier.normalize_address(contracts["poolManager"])),
        ):
            actual = qualifier.normalize_address(
                fork_simulator._contract_call(client, tracker, signature, ["address"])
            )
            _assert_equal(f"tracker {tracker} {signature}", actual, expected)
    vegoid = int(
        fork_simulator._contract_call(
            client, contracts["riskEngine"], "vegoid()", ["uint8"]
        )
    )
    sfpm_pool_id = int(
        fork_simulator._contract_call(
            client,
            contracts["sfpmV4"],
            "getPoolId(bytes,uint8)",
            ["uint64"],
            ["bytes", "uint8"],
            [bytes.fromhex(plan["market"]["poolId"][2:]), vegoid],
        )
    )
    if sfpm_pool_id == 0:
        raise RuntimeError("registered SFPM pool ID is zero")
    _assert_equal(
        "PanopticPool SFPM pool ID",
        int(fork_simulator._contract_call(client, pool, "poolId()", ["uint64"])),
        sfpm_pool_id,
    )
    return sfpm_pool_id


def verify_state(
    client: Any,
    plan: dict[str, Any],
    completed: int,
    *,
    position_token_id: int | None = None,
) -> dict[str, Any]:
    if not 0 <= completed <= 12:
        raise ValueError("completed step count must be between zero and twelve")
    actor = qualifier.normalize_address(plan["actor"]["address"])
    contracts = plan["contracts"]
    price = plan["priceAndLiquidity"]
    initial = plan["initialState"]
    exposure = plan["maximumExposure"]
    nonce = int(client.call("eth_getTransactionCount", [actor, "pending"]), 16)
    _assert_equal("actor pending nonce", nonce, plan["startNonce"] + completed)

    wrap = int(exposure["wrapNativeWei"])
    amount0 = int(price["expectedAmount0AtSyntheticPriceRoundedUp"])
    amount1 = int(price["expectedAmount1AtSyntheticPriceRoundedUp"])
    expected_pltr = int(initial["pltrBalance"]) - (amount0 if completed >= 7 else 0)
    expected_weth = int(initial["wethBalance"]) + (wrap if completed >= 1 else 0)
    if completed >= 7:
        expected_weth -= amount1
    pltr = fork_simulator._balance(client, contracts["pltr"], actor)
    weth = fork_simulator._balance(client, contracts["weth"], actor)
    _assert_equal("actor PLTR balance", pltr, expected_pltr)
    _assert_equal("actor WETH balance", weth, expected_weth)

    native = int(client.call("eth_getBalance", [actor, "latest"]), 16)
    initial_native = int(initial["nativeBalanceWei"])
    if completed == 0:
        _assert_equal("actor initial native balance", native, initial_native)
    elif not 0 < native <= initial_native - wrap:
        raise RuntimeError("actor native balance is outside the post-wrap gas range")

    expected = expected_allowances(plan, completed)
    actual = (
        fork_simulator._erc20_allowance(
            client, contracts["pltr"], actor, contracts["permit2"]
        ),
        fork_simulator._erc20_allowance(
            client, contracts["weth"], actor, contracts["permit2"]
        ),
        fork_simulator._permit2_allowance(
            client,
            contracts["permit2"],
            actor,
            contracts["pltr"],
            contracts["positionManager"],
        )[0],
        fork_simulator._permit2_allowance(
            client,
            contracts["permit2"],
            actor,
            contracts["weth"],
            contracts["positionManager"],
        )[0],
    )
    _assert_equal("permission ladder", actual, expected)
    if expected[2] != 0:
        expiration = fork_simulator._permit2_allowance(
            client,
            contracts["permit2"],
            actor,
            contracts["pltr"],
            contracts["positionManager"],
        )[1]
        _assert_equal(
            "PLTR Permit2 expiration",
            expiration,
            plan["executionClock"]["permit2ExpirationUnix"],
        )
    if expected[3] != 0:
        expiration = fork_simulator._permit2_allowance(
            client,
            contracts["permit2"],
            actor,
            contracts["weth"],
            contracts["positionManager"],
        )[1]
        _assert_equal(
            "WETH Permit2 expiration",
            expiration,
            plan["executionClock"]["permit2ExpirationUnix"],
        )

    sqrt_price, tick, _, _ = fork_simulator._slot0(client, plan)
    liquidity = fork_simulator._active_liquidity(client, plan)
    if completed < 6:
        _assert_equal("uninitialized sqrtPriceX96", sqrt_price, 0)
        _assert_equal("pre-initialization active liquidity", liquidity, 0)
    else:
        _assert_equal(
            "initialized sqrtPriceX96", sqrt_price, int(price["sqrtPriceX96"])
        )
        _assert_equal("initialized tick", tick, int(price["initialTick"]))
        _assert_equal(
            "active liquidity",
            liquidity,
            int(price["liquidity"]) if completed >= 7 else 0,
        )

    token_id_floor = int(initial["positionManagerNextTokenIdFloor"])
    next_token_id = int(
        fork_simulator._contract_call(
            client, contracts["positionManager"], "nextTokenId()", ["uint256"]
        )
    )
    minimum_next_token_id = token_id_floor + (1 if completed >= 7 else 0)
    if next_token_id < minimum_next_token_id:
        raise RuntimeError(
            "PositionManager nextTokenId moved below the execution-plan floor"
        )
    actor_nft_balance = int(
        fork_simulator._contract_call(
            client,
            contracts["positionManager"],
            "balanceOf(address)",
            ["uint256"],
            ["address"],
            [actor],
        )
    )
    _assert_equal(
        "PositionManager actor NFT balance",
        actor_nft_balance,
        int(initial["actorPositionManagerNftBalance"]) + (1 if completed >= 7 else 0),
    )
    if completed >= 7:
        if position_token_id is None:
            raise RuntimeError(
                "the receipt-derived liquidity token ID is required after mint"
            )
        if next_token_id <= position_token_id:
            raise RuntimeError(
                "receipt-derived liquidity token ID is outside the NFT range"
            )
        owner = qualifier.normalize_address(
            fork_simulator._contract_call(
                client,
                contracts["positionManager"],
                "ownerOf(uint256)",
                ["address"],
                ["uint256"],
                [position_token_id],
            )
        )
        _assert_equal("liquidity NFT owner", owner, actor)
        position_liquidity = int(
            fork_simulator._contract_call(
                client,
                contracts["positionManager"],
                "getPositionLiquidity(uint256)",
                ["uint128"],
                ["uint256"],
                [position_token_id],
            )
        )
        _assert_equal("position liquidity", position_liquidity, int(price["liquidity"]))

    predicted = plan["predictedMarketContracts"]
    sfpm_pool_id = 0
    if completed < 12:
        _assert_equal(
            "factory mapping before registration",
            fork_simulator._factory_pool(client, plan),
            qualifier.normalize_address("0x" + "00" * 20),
        )
        for name in ("panopticPool", "collateralTracker0", "collateralTracker1"):
            _assert_equal(
                f"empty predicted {name}",
                client.call("eth_getCode", [predicted[name], "latest"]),
                "0x",
            )
    else:
        sfpm_pool_id = _verify_registered_market(client, plan)

    return {
        "completedSteps": completed,
        "pendingNonce": nonce,
        "nativeBalanceWei": str(native),
        "pltrBalance": str(pltr),
        "wethBalance": str(weth),
        "erc20Allowances": {"PLTR": str(actual[0]), "WETH": str(actual[1])},
        "permit2Allowances": {"PLTR": str(actual[2]), "WETH": str(actual[3])},
        "sqrtPriceX96": str(sqrt_price),
        "tick": tick,
        "activeLiquidity": str(liquidity),
        "positionManagerNextTokenId": str(next_token_id),
        "positionManagerActorNftBalance": str(actor_nft_balance),
        "liquidityPositionTokenId": position_token_id,
        "sfpmPoolId": str(sfpm_pool_id),
    }


def _assert_time_window(client: Any, plan: dict[str, Any], index: int) -> None:
    latest = client.call("eth_getBlockByNumber", ["latest", False])
    now = int(latest["timestamp"], 16)
    clock = plan["executionClock"]
    if (
        index == 0
        and clock["liquidityDeadlineUnix"] - now
        < clock["minimumSecondsRemainingAtTransactionZero"]
    ):
        raise RuntimeError(
            "execution candidate lacks the required initial deadline lead"
        )
    if index <= 6 and now >= clock["liquidityDeadlineUnix"]:
        raise RuntimeError("execution candidate liquidity deadline has expired")
    if 3 <= index <= 6 and now >= clock["permit2ExpirationUnix"]:
        raise RuntimeError("execution candidate Permit2 expiration has passed")


def step_result(transaction: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "ordinal": transaction["ordinal"],
        "label": transaction["label"],
        "nonce": transaction["nonce"],
        "to": transaction["to"],
        "valueWei": transaction["valueWei"],
        "calldataKeccak256": transaction["calldataKeccak256"],
        "transactionHash": receipt["transactionHash"],
        "blockNumber": int(receipt["blockNumber"], 16),
        "gasUsed": int(receipt["gasUsed"], 16),
        "effectiveGasPriceWei": str(int(receipt.get("effectiveGasPrice", "0x0"), 16)),
        "status": "PASS" if receipt.get("status") == "0x1" else "REVERT",
    }


def unsigned_legacy_transaction(
    *,
    nonce: int,
    gas_price: int,
    gas_limit: int,
    to: str,
    value: int,
    data: bytes,
    chain_id: int,
) -> bytes:
    direct_operator._validate_address(to, "transaction recipient")
    return direct_operator.rlp_encode(
        [
            nonce,
            gas_price,
            gas_limit,
            bytes.fromhex(to[2:]),
            value,
            data,
            chain_id,
            0,
            0,
        ]
    )


def build_signed_legacy_transaction(
    *,
    nonce: int,
    gas_price: int,
    gas_limit: int,
    to: str,
    value: int,
    data: bytes,
    chain_id: int,
    r: int,
    s: int,
    parity: int,
) -> str:
    direct_operator._validate_address(to, "transaction recipient")
    if parity not in (0, 1):
        raise ValueError("signature parity must be zero or one")
    eip155_v = chain_id * 2 + 35 + parity
    raw = direct_operator.rlp_encode(
        [
            nonce,
            gas_price,
            gas_limit,
            bytes.fromhex(to[2:]),
            value,
            data,
            eip155_v,
            r,
            s,
        ]
    )
    return "0x" + raw.hex()


def _transaction_request(
    transaction: dict[str, Any], actor: str, gas_limit: int | None = None
) -> dict[str, str]:
    request = {
        "from": actor,
        "to": transaction["to"],
        "nonce": hex(transaction["nonce"]),
        "value": hex(int(transaction["valueWei"])),
        "data": transaction["calldata"],
    }
    if gas_limit is not None:
        request["gas"] = hex(gas_limit)
    return request


def public_preflight(
    client: Any,
    plan: dict[str, Any],
    index: int,
    *,
    position_token_id: int | None = None,
) -> dict[str, Any]:
    if not 0 <= index < len(plan["transactions"]):
        raise ValueError("transaction index is outside the execution plan")
    chain_id = int(client.call("eth_chainId", []), 16)
    if chain_id != execution_planner.CHAIN_ID:
        raise RuntimeError(
            f"chain ID mismatch: expected {execution_planner.CHAIN_ID}, got {chain_id}"
        )
    latest = client.call("eth_getBlockByNumber", ["latest", False])
    if not isinstance(latest, dict):
        raise RuntimeError("latest block response is malformed")
    try:
        block_number = int(latest["number"], 16)
        block_timestamp = int(latest["timestamp"], 16)
        block_hash = "0x" + _normalized_hash(latest["hash"], "latest block hash")
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("latest block identity is incomplete") from exc

    _assert_time_window(client, plan, index)
    state = verify_state(client, plan, index, position_token_id=position_token_id)
    transaction = plan["transactions"][index]
    gas_policy = plan["gasPolicy"]
    maximum_gas = int(gas_policy["maximumGasLimitPerTransaction"])
    gas_price = int(client.call("eth_gasPrice", []), 16)
    maximum_gas_price = int(gas_policy["maximumGasPriceWei"])
    if not 0 < gas_price <= maximum_gas_price:
        raise RuntimeError(
            f"gas price {gas_price} exceeds allowed range 1..{maximum_gas_price}"
        )
    estimate = int(
        client.call(
            "eth_estimateGas",
            [
                _transaction_request(
                    transaction, plan["actor"]["address"], maximum_gas
                ),
                "latest",
            ],
        ),
        16,
    )
    multiplier_limit = (
        estimate * int(gas_policy["estimateMultiplierBps"]) + 9_999
    ) // 10_000
    additive_limit = estimate + int(gas_policy["estimateAdditiveBuffer"])
    gas_limit = max(multiplier_limit, additive_limit)
    if estimate <= 0 or gas_limit > maximum_gas or gas_limit >= (1 << 24):
        raise RuntimeError(
            f"buffered gas limit {gas_limit} is invalid for estimate {estimate}"
        )
    actor = plan["actor"]["address"]
    balance = int(client.call("eth_getBalance", [actor, "latest"]), 16)
    value = int(transaction["valueWei"])
    maximum_cost = value + gas_price * gas_limit
    if balance < maximum_cost:
        raise RuntimeError(
            f"actor balance {balance} is below value-plus-gas bound {maximum_cost}"
        )
    return {
        "chainId": chain_id,
        "blockNumber": block_number,
        "blockHash": block_hash,
        "blockTimestamp": block_timestamp,
        "transactionIndex": index,
        "label": transaction["label"],
        "actor": actor,
        "nonce": transaction["nonce"],
        "to": transaction["to"],
        "valueWei": transaction["valueWei"],
        "calldataKeccak256": transaction["calldataKeccak256"],
        "balanceWei": str(balance),
        "gasPriceWei": gas_price,
        "gasEstimate": estimate,
        "gasLimit": gas_limit,
        "maximumCostWei": str(maximum_cost),
        "state": state,
    }


def _post_sign_recheck(
    client: Any,
    plan: dict[str, Any],
    index: int,
    *,
    signed_gas_price: int,
    signed_gas_limit: int,
    position_token_id: int | None = None,
) -> dict[str, Any]:
    if int(client.call("eth_chainId", []), 16) != execution_planner.CHAIN_ID:
        raise RuntimeError(
            "chain ID changed after signing; raw transaction was not published"
        )
    _assert_time_window(client, plan, index)
    state = verify_state(client, plan, index, position_token_id=position_token_id)
    transaction = plan["transactions"][index]
    gas_price = int(client.call("eth_gasPrice", []), 16)
    if gas_price > signed_gas_price:
        raise RuntimeError(
            "gas price increased after signing; raw transaction was not published"
        )
    estimate = int(
        client.call(
            "eth_estimateGas",
            [
                _transaction_request(
                    transaction, plan["actor"]["address"], signed_gas_limit
                ),
                "latest",
            ],
        ),
        16,
    )
    if estimate <= 0 or estimate > signed_gas_limit:
        raise RuntimeError(
            "gas estimate changed after signing; raw transaction was not published"
        )
    balance = int(
        client.call("eth_getBalance", [plan["actor"]["address"], "latest"]), 16
    )
    maximum_cost = int(transaction["valueWei"]) + signed_gas_price * signed_gas_limit
    if balance < maximum_cost:
        raise RuntimeError(
            "actor balance changed after signing; raw transaction was not published"
        )
    return {
        "pendingNonce": state["pendingNonce"],
        "gasPriceWei": gas_price,
        "gasEstimate": estimate,
        "balanceWei": str(balance),
    }


def reviewed_intent(
    plan: dict[str, Any], index: int, position_token_id: int | None = None
) -> dict[str, Any]:
    transaction = plan["transactions"][index]
    return {
        "chainId": execution_planner.CHAIN_ID,
        "actor": plan["actor"]["address"],
        "transactionIndex": index,
        "nonce": transaction["nonce"],
        "label": transaction["label"],
        "to": transaction["to"],
        "valueWei": transaction["valueWei"],
        "calldataKeccak256": transaction["calldataKeccak256"],
        "decodedIntent": transaction["decodedIntent"],
        "maximumExposure": plan["maximumExposure"],
        "receiptDerivedLiquidityTokenId": position_token_id,
        "policy": "ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH",
    }


def verify_mined_transaction(
    client: Any,
    plan: dict[str, Any],
    index: int,
    transaction_hash: str,
    expected_raw_hash: str,
    receipt: dict[str, Any],
    gas_limit: int,
) -> dict[str, Any]:
    if _normalized_hash(transaction_hash, "RPC transaction hash") != _normalized_hash(
        expected_raw_hash, "signed raw transaction hash"
    ):
        raise RuntimeError("RPC transaction hash differs from signed raw transaction")
    mined = client.call("eth_getTransactionByHash", [transaction_hash])
    if not isinstance(mined, dict):
        raise RuntimeError("mined transaction is unavailable after receipt")
    expected = plan["transactions"][index]
    comparisons = {
        "sender": (
            qualifier.normalize_address(mined.get("from", "")),
            qualifier.normalize_address(plan["actor"]["address"]),
        ),
        "recipient": (
            qualifier.normalize_address(mined.get("to", "")),
            qualifier.normalize_address(expected["to"]),
        ),
        "nonce": (int(mined.get("nonce", "0x0"), 16), expected["nonce"]),
        "value": (int(mined.get("value", "0x0"), 16), int(expected["valueWei"])),
        "input": (str(mined.get("input", "")).lower(), expected["calldata"].lower()),
        "transaction block": (mined.get("blockHash"), receipt.get("blockHash")),
        "receipt transaction hash": (
            str(receipt.get("transactionHash", "")).lower(),
            transaction_hash.lower(),
        ),
    }
    for name, (actual, wanted) in comparisons.items():
        if actual != wanted:
            raise RuntimeError(
                f"mined transaction {name} mismatch: expected {wanted}, got {actual}"
            )
    gas_used = int(receipt.get("gasUsed", "0x0"), 16)
    if not 0 < gas_used <= gas_limit:
        raise RuntimeError("receipt gas used is outside the signed gas limit")
    return {
        "transactionHash": transaction_hash,
        "blockNumber": int(receipt["blockNumber"], 16),
        "blockHash": receipt["blockHash"],
        "transactionIndex": int(receipt.get("transactionIndex", "0x0"), 16),
        "from": mined["from"],
        "to": mined["to"],
        "nonce": int(mined["nonce"], 16),
        "valueWei": str(int(mined["value"], 16)),
        "calldataKeccak256": expected["calldataKeccak256"],
        "gasUsed": gas_used,
        "effectiveGasPriceWei": str(int(receipt.get("effectiveGasPrice", "0x0"), 16)),
    }


def verify_liquidity_nft_mint_event(
    receipt: dict[str, Any], plan: dict[str, Any]
) -> dict[str, Any]:
    position_manager = qualifier.normalize_address(plan["contracts"]["positionManager"])
    actor_topic = "0" * 24 + qualifier.normalize_address(plan["actor"]["address"])[2:]
    matches: list[dict[str, Any]] = []
    logs = receipt.get("logs")
    if not isinstance(logs, list):
        raise RuntimeError("liquidity receipt logs are malformed")
    for log in logs:
        if not isinstance(log, dict):
            continue
        try:
            log_address = qualifier.normalize_address(log.get("address", ""))
        except ValueError:
            continue
        topics = log.get("topics")
        if log_address != position_manager or not isinstance(topics, list):
            continue
        if len(topics) != 4:
            continue
        normalized_topics = [
            _normalized_hash(topic, f"liquidity mint topic {index}")
            for index, topic in enumerate(topics)
        ]
        if normalized_topics[:3] != [
            ERC721_TRANSFER_TOPIC,
            ZERO_TOPIC,
            actor_topic,
        ]:
            continue
        matches.append(
            {
                "positionManager": position_manager,
                "from": qualifier.normalize_address("0x" + "00" * 20),
                "to": qualifier.normalize_address(plan["actor"]["address"]),
                "tokenId": int(normalized_topics[3], 16),
                "logIndex": int(log.get("logIndex", "0x0"), 16),
            }
        )
    if len(matches) != 1:
        raise RuntimeError(
            "liquidity receipt must contain exactly one PositionManager NFT mint "
            "to the actor"
        )
    return matches[0]


def verify_pool_deployed_event(
    receipt: dict[str, Any], plan: dict[str, Any]
) -> dict[str, str]:
    event = fork_simulator.decode_pool_deployed_event(receipt.get("logs", []))
    expected = {
        "panopticPool": qualifier.normalize_address(
            plan["predictedMarketContracts"]["panopticPool"]
        ),
        "poolId": plan["market"]["poolId"].lower(),
        "collateralTracker0": qualifier.normalize_address(
            plan["predictedMarketContracts"]["collateralTracker0"]
        ),
        "collateralTracker1": qualifier.normalize_address(
            plan["predictedMarketContracts"]["collateralTracker1"]
        ),
        "riskEngine": qualifier.normalize_address(plan["contracts"]["riskEngine"]),
    }
    if event != expected:
        raise RuntimeError(
            f"PoolDeployed event mismatch: expected {expected}, got {event}"
        )
    return event


def execute_one_step(
    plan: dict[str, Any],
    plan_path: Path,
    simulation_report: dict[str, Any],
    simulation_report_path: Path,
    authorization: dict[str, Any],
    *,
    index: int,
    keystore: Path,
    confirmation: str,
    output_dir: Path,
    position_token_id: int | None = None,
) -> dict[str, Any]:
    validate_execution_plan(plan, plan_path)
    validate_liquidity_token_argument(index, position_token_id)
    plan_hash = file_sha256(plan_path)
    operator_hash = file_sha256(Path(__file__))
    simulation_hash = file_sha256(simulation_report_path)
    validate_simulation_report(
        simulation_report,
        plan,
        plan_file_hash=plan_hash,
        operator_hash=operator_hash,
    )
    validate_authorization(
        authorization,
        plan,
        index=index,
        plan_file_hash=plan_hash,
        operator_hash=operator_hash,
        simulation_report_hash=simulation_hash,
    )
    transaction = plan["transactions"][index]
    expected_confirmation = confirmation_phrase(plan_hash, index, transaction["nonce"])
    if confirmation != expected_confirmation:
        raise ValueError(
            f"confirmation mismatch; expected exactly {expected_confirmation}"
        )

    repository_root = REPOSITORY.resolve()
    try:
        output_dir.resolve().relative_to(repository_root)
    except ValueError:
        pass
    else:
        raise ValueError(
            "execution output directory must be outside the Git repository"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    intent = reviewed_intent(plan, index, position_token_id)
    print("Reviewed one-transaction intent (no password has been requested):")
    print(json.dumps(intent, indent=2))

    client = direct_operator.JsonRpcClient(OFFICIAL_RPC_URL)
    initial_preflight = public_preflight(
        client, plan, index, position_token_id=position_token_id
    )
    strict_qualification = run_market_aware_strict_verifier(plan, plan_path, index)
    signing_preflight = public_preflight(
        client, plan, index, position_token_id=position_token_id
    )

    data = direct_operator._hex_bytes(transaction["calldata"], "transaction calldata")
    unsigned = unsigned_legacy_transaction(
        nonce=transaction["nonce"],
        gas_price=signing_preflight["gasPriceWei"],
        gas_limit=signing_preflight["gasLimit"],
        to=transaction["to"],
        value=int(transaction["valueWei"]),
        data=data,
        chain_id=execution_planner.CHAIN_ID,
    )
    digest = direct_operator.cast_keccak(unsigned)
    evidence_path = output_dir / (
        f"market-nonce-{transaction['nonce']:02d}-"
        f"preflight-block-{signing_preflight['blockNumber']}.json"
    )
    if evidence_path.exists():
        raise FileExistsError(
            f"refusing to overwrite existing execution evidence: {evidence_path}"
        )
    evidence = {
        "schemaVersion": 1,
        "status": "READY_TO_PROMPT_FOR_ENCRYPTED_KEYSTORE",
        "chainId": execution_planner.CHAIN_ID,
        "executionPlanBodySha256": plan["executionPlanBodySha256"],
        "executionPlanFileSha256": plan_hash,
        "operatorSha256": operator_hash,
        "operatorSimulationReportSha256": simulation_hash,
        "intent": intent,
        "initialPreflight": initial_preflight,
        "strictQualification": strict_qualification,
        "signingPreflight": signing_preflight,
        "broadcastAttempted": False,
    }
    direct_operator._write_json(evidence_path, evidence)
    r, s, parity = direct_operator.sign_digest_with_foundry(
        digest, keystore, plan["actor"]["address"]
    )
    raw_transaction = build_signed_legacy_transaction(
        nonce=transaction["nonce"],
        gas_price=signing_preflight["gasPriceWei"],
        gas_limit=signing_preflight["gasLimit"],
        to=transaction["to"],
        value=int(transaction["valueWei"]),
        data=data,
        chain_id=execution_planner.CHAIN_ID,
        r=r,
        s=s,
        parity=parity,
    )
    expected_transaction_hash = direct_operator.cast_keccak(
        bytes.fromhex(raw_transaction[2:])
    )
    post_sign = _post_sign_recheck(
        client,
        plan,
        index,
        signed_gas_price=signing_preflight["gasPriceWei"],
        signed_gas_limit=signing_preflight["gasLimit"],
        position_token_id=position_token_id,
    )
    evidence.update(
        {
            "status": "SIGNED_AND_RECHECKED_NOT_YET_BROADCAST",
            "postSignRecheck": post_sign,
        }
    )
    direct_operator._write_json(evidence_path, evidence)

    try:
        transaction_hash = client.call("eth_sendRawTransaction", [raw_transaction])
    except Exception as exc:
        evidence.update(
            {
                "status": "SUBMISSION_INDETERMINATE_STOP",
                "broadcastAttempted": True,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        direct_operator._write_json(evidence_path, evidence)
        raise RuntimeError(
            "submission returned an indeterminate error; do not retry until the pending "
            "nonce, explorer, and complete market state are checked"
        ) from exc
    normalized_transaction_hash = "0x" + _normalized_hash(
        transaction_hash, "transaction hash"
    )
    if _normalized_hash(
        normalized_transaction_hash, "RPC transaction hash"
    ) != _normalized_hash(expected_transaction_hash, "signed transaction hash"):
        evidence.update(
            {
                "status": "SUBMISSION_HASH_MISMATCH_STOP",
                "broadcastAttempted": True,
                "rpcTransactionHash": normalized_transaction_hash,
                "expectedTransactionHash": expected_transaction_hash,
            }
        )
        direct_operator._write_json(evidence_path, evidence)
        raise RuntimeError("RPC transaction hash differs from the signed transaction")
    evidence.update(
        {
            "status": "SUBMITTED_RECEIPT_PENDING",
            "broadcastAttempted": True,
            "transactionHash": normalized_transaction_hash,
        }
    )
    direct_operator._write_json(evidence_path, evidence)
    print(f"Submitted {normalized_transaction_hash}; waiting for its receipt.")

    receipt = direct_operator._poll_receipt(client, normalized_transaction_hash)
    if receipt.get("status") != "0x1":
        evidence.update({"status": "FAILED_STOP", "receipt": receipt})
        direct_operator._write_json(evidence_path, evidence)
        raise RuntimeError("market transaction receipt failed; stop immediately")
    try:
        mined = verify_mined_transaction(
            client,
            plan,
            index,
            normalized_transaction_hash,
            expected_transaction_hash,
            receipt,
            signing_preflight["gasLimit"],
        )
        liquidity_position_mint = (
            verify_liquidity_nft_mint_event(receipt, plan) if index == 6 else None
        )
        reconciled_position_token_id = (
            liquidity_position_mint["tokenId"]
            if liquidity_position_mint is not None
            else position_token_id
        )
        pool_deployed = (
            verify_pool_deployed_event(receipt, plan) if index == 11 else None
        )
        after = verify_state(
            client,
            plan,
            index + 1,
            position_token_id=reconciled_position_token_id,
        )
    except Exception as exc:
        evidence.update(
            {
                "status": "RECEIPT_OR_POST_STATE_MISMATCH_STOP",
                "receipt": receipt,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        direct_operator._write_json(evidence_path, evidence)
        raise
    evidence.update(
        {
            "status": "PASS_STOP_BEFORE_NEXT",
            "receipt": receipt,
            "minedTransaction": mined,
            "liquidityPositionMint": liquidity_position_mint,
            "poolDeployed": pool_deployed,
            "postState": after,
            "nextGate": "STOP_AND_REVIEW_BEFORE_SELECTING_NEXT_INDEX",
        }
    )
    direct_operator._write_json(evidence_path, evidence)
    return evidence


def simulate_one_step(
    plan: dict[str, Any],
    plan_path: Path,
    client: Any,
    index: int,
    *,
    sleep: Callable[[float], None],
) -> dict[str, Any]:
    validate_execution_plan(plan, plan_path)
    if not 0 <= index < len(plan["transactions"]):
        raise ValueError("transaction index is outside the execution plan")
    lineage = ensure_anvil_lineage(plan, client)
    position_token_id = (
        int(plan["initialState"]["positionManagerNextTokenIdFloor"])
        if index >= 7
        else None
    )
    before = verify_state(client, plan, index, position_token_id=position_token_id)
    _assert_time_window(client, plan, index)
    actor = qualifier.normalize_address(plan["actor"]["address"])
    client.call("anvil_impersonateAccount", [actor])
    try:
        receipt = fork_simulator._send(
            client,
            plan["transactions"][index],
            actor,
            hex(plan["gasPolicy"]["maximumGasLimitPerTransaction"]),
            attempts=300,
            interval_seconds=0.1,
            sleep=sleep,
        )
    finally:
        client.call("anvil_stopImpersonatingAccount", [actor])
    if receipt.get("status") != "0x1":
        raise RuntimeError(f"simulated execution transaction {index} reverted")
    liquidity_position_mint = (
        verify_liquidity_nft_mint_event(receipt, plan) if index == 6 else None
    )
    reconciled_position_token_id = (
        liquidity_position_mint["tokenId"]
        if liquidity_position_mint is not None
        else position_token_id
    )
    after = verify_state(
        client,
        plan,
        index + 1,
        position_token_id=reconciled_position_token_id,
    )
    transaction_result = step_result(plan["transactions"][index], receipt)
    transaction_result["liquidityPositionTokenId"] = reconciled_position_token_id
    return {
        "schemaVersion": 1,
        "status": "PASS_ONE_STEP_LOOPBACK_SIMULATION_STOP",
        "mode": "LOOPBACK_ANVIL_ONLY_NO_CREDENTIALS_NO_SIGNING_NO_PUBLIC_BROADCAST",
        "sourceBindings": {
            "executionPlanBodySha256": plan["executionPlanBodySha256"],
            "executionPlanFileSha256": file_sha256(plan_path),
            "operatorSha256": file_sha256(Path(__file__)),
        },
        "lineage": lineage,
        "transaction": transaction_result,
        "before": before,
        "after": after,
        "authorization": plan["authorization"],
        "publicExecution": {"ready": False, "broadcastAttempted": False},
        "nextGate": "STOP_AND_REVIEW_BEFORE_SELECTING_NEXT_INDEX",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--simulate", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL)
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--simulation-report", type=Path, default=DEFAULT_SIMULATION_REPORT
    )
    parser.add_argument("--authorization-manifest", type=Path)
    parser.add_argument("--keystore", type=Path)
    parser.add_argument("--confirmation")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--liquidity-token-id",
        type=int,
        help=(
            "receipt-derived PositionManager NFT token ID; required for public "
            "indices 7 through 11"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = load_json(args.plan)
    if args.simulate:
        validate_local_rpc_url(args.rpc_url)
        client = fork_simulator.JsonRpcClient(args.rpc_url)
        report = simulate_one_step(
            plan,
            args.plan,
            client,
            args.index,
            sleep=fork_simulator.time.sleep,
        )
        if args.report is not None:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(
                json.dumps(report, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"Wrote one-step loopback report: {args.report}")
        print(
            f"PASS index {args.index}; local transaction reconciled; "
            "stop before the next index."
        )
        print("SIMULATION ONLY; NO CREDENTIALS, SIGNING, OR PUBLIC BROADCAST")
        return 0

    if args.rpc_url != OFFICIAL_RPC_URL:
        raise ValueError(
            f"--execute requires the exact official RPC {OFFICIAL_RPC_URL}"
        )
    if args.authorization_manifest is None:
        raise ValueError("--authorization-manifest is required with --execute")
    if args.keystore is None:
        raise ValueError("--keystore is required with --execute")
    if args.confirmation is None:
        raise ValueError("--confirmation is required with --execute")
    if args.output_dir is None:
        raise ValueError("--output-dir is required with --execute")
    simulation_report = load_json(args.simulation_report)
    authorization = load_json(args.authorization_manifest)
    evidence = execute_one_step(
        plan,
        args.plan,
        simulation_report,
        args.simulation_report,
        authorization,
        index=args.index,
        keystore=args.keystore,
        confirmation=args.confirmation,
        output_dir=args.output_dir,
        position_token_id=args.liquidity_token_id,
    )
    print(json.dumps(evidence, indent=2))
    print("One transaction completed. Stop here and review before the next index.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
