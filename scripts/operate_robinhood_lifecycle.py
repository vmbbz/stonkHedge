#!/usr/bin/env python3
"""Verify, simulate, or execute one plan-bound PLTR/WETH lifecycle step.

Public execution is deliberately difficult: one exact global index, both
senders' confirmed and pending nonces, short-lived clocks, immutable runtime
and wiring checks, a separately hash-bound simulation report and authorization,
an exact confirmation phrase, one encrypted Foundry keystore, one raw
transaction, one receipt, and then an unconditional stop before the next step.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import time
from pathlib import Path
from typing import Any, Callable


REPOSITORY = Path(__file__).resolve().parents[1]
MARKETS = REPOSITORY / "manifests" / "markets"
DEFAULT_PLAN = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-execution-candidate-2026-09-15.json"
DEFAULT_SIMULATION_REPORT = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-execution-operator-simulation-2026-09-15.json"
OFFICIAL_RPC_URL = "https://rpc.testnet.chain.robinhood.com"
CHAIN_ID = 46630
AUTHORIZATION_STATUS = "AUTHORIZED_PLTR_WETH_LIFECYCLE_ONE_TRANSACTION_AT_A_TIME"


def _load_sibling(name: str, filename: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required sibling module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


planner = _load_sibling(
    "stonkhedge_lifecycle_execution_planner",
    "prepare_robinhood_lifecycle_execution_plan.py",
)
refresh_planner = _load_sibling(
    "stonkhedge_lifecycle_execution_refresh_planner",
    "prepare_robinhood_lifecycle_execution_refresh.py",
)
simulator = _load_sibling(
    "stonkhedge_lifecycle_simulator", "simulate_robinhood_two_actor_lifecycle_fork.py"
)
direct_operator = _load_sibling(
    "stonkhedge_direct_operator", "operate_robinhood_direct_deployment.py"
)
genesis_operator = _load_sibling(
    "stonkhedge_market_operator", "operate_robinhood_market_genesis.py"
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


def _all_false(value: Any) -> bool:
    return isinstance(value, dict) and bool(value) and all(
        item is False for item in value.values()
    )


def _normalize_hash(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a hex hash")
    raw = value[2:] if value.startswith("0x") else value
    if len(raw) != 64:
        raise ValueError(f"{name} must contain 32 bytes")
    bytes.fromhex(raw)
    return raw.lower()


def validate_execution_plan(plan: dict[str, Any], plan_path: Path) -> None:
    if plan.get("status") != "LIFECYCLE_EXECUTION_CANDIDATE_REQUIRES_SEPARATE_AUTHORIZATION":
        raise ValueError("plan is not a lifecycle execution candidate")
    if plan.get("network", {}).get("chainId") != CHAIN_ID:
        raise ValueError("execution plan chain ID drifted")
    if not _all_false(plan.get("authorization")):
        raise ValueError("candidate authorization must remain entirely false")
    if plan.get("publicExecution", {}).get("ready") is not False:
        raise ValueError("candidate public execution must remain disabled")
    body = dict(plan)
    expected_body_hash = body.pop("executionPlanBodySha256", None)
    if expected_body_hash != canonical_sha256(body):
        raise ValueError("execution plan body hash drifted")

    bindings = plan.get("sourceBindings", {})
    refresh = "refreshPreflight" in bindings
    required_bindings = (
        ("priorExecutionCandidate", "refreshPreflight", "generator")
        if refresh
        else (
            "baseLifecyclePlan",
            "successfulLifecycleRehearsal",
            "freshExecutionPreflight",
            "generator",
        )
    )
    for name in required_bindings:
        binding = bindings.get(name, {})
        source = REPOSITORY / binding.get("path", "")
        if not source.is_file() or binding.get("sha256") != file_sha256(source):
            raise ValueError(f"execution plan source binding {name} drifted")
    if refresh:
        regenerated = refresh_planner.build_refresh_plan(
            REPOSITORY / bindings["priorExecutionCandidate"]["path"],
            REPOSITORY / bindings["refreshPreflight"]["path"],
            REPOSITORY / bindings["generator"]["path"],
        )
    else:
        regenerated = planner.build_execution_plan(
            REPOSITORY / bindings["baseLifecyclePlan"]["path"],
            REPOSITORY / bindings["successfulLifecycleRehearsal"]["path"],
            REPOSITORY / bindings["freshExecutionPreflight"]["path"],
            REPOSITORY / bindings["generator"]["path"],
        )
    if regenerated != plan:
        raise ValueError("execution plan no longer matches deterministic regeneration")

    writer = qualifier.normalize_address(plan["roles"]["writer"]["address"])
    buyer = qualifier.normalize_address(plan["roles"]["buyer"]["address"])
    actors = {writer, buyer}
    allowed_targets = {
        qualifier.normalize_address(plan["market"][name])
        for name in (
            "pltr",
            "weth",
            "permit2",
            "universalRouter",
            "collateralTracker0",
            "collateralTracker1",
            "panopticPool",
        )
    }
    transactions = plan.get("transactions")
    execution_start = int(plan.get("executionStartIndex", 0))
    expected_shape = (0, 25) if not refresh else (5, 27)
    if (
        not isinstance(transactions, list)
        or (execution_start, len(transactions)) != expected_shape
    ):
        raise ValueError("lifecycle execution candidate transaction shape drifted")
    if plan.get("transactionCount") != len(transactions):
        raise ValueError("transaction count drifted")
    for index, transaction in enumerate(transactions):
        if transaction.get("ordinal") != index:
            raise ValueError(f"transaction {index} ordering drifted")
        sender = qualifier.normalize_address(transaction.get("sender", ""))
        if sender not in actors:
            raise ValueError(f"transaction {index} sender is outside the role allowlist")
        if qualifier.normalize_address(transaction.get("to", "")) not in allowed_targets:
            raise ValueError(f"transaction {index} target is outside the user-call allowlist")
        if transaction.get("authorizedForBroadcast") is not False:
            raise ValueError(f"transaction {index} unexpectedly grants broadcast authority")
        calldata = transaction.get("calldata", "")
        if not isinstance(calldata, str) or not calldata.startswith("0x"):
            raise ValueError(f"transaction {index} calldata is malformed")
        if "0x" + qualifier.keccak(bytes.fromhex(calldata[2:])).hex() != transaction.get(
            "calldataKeccak256"
        ):
            raise ValueError(f"transaction {index} calldata hash drifted")
        before = transaction.get("requiredNonceStateBefore", {})
        after = transaction.get("requiredNonceStateAfter", {})
        if set(before) != actors or set(after) != actors:
            raise ValueError(f"transaction {index} dual nonce vector drifted")
        if transaction.get("nonce") != before[sender]:
            raise ValueError(f"transaction {index} sender nonce drifted")
        for actor in actors:
            expected = before[actor] + (1 if actor == sender else 0)
            if after[actor] != expected:
                raise ValueError(f"transaction {index} post-nonce vector drifted")
        if index + 1 < len(transactions):
            if after != transactions[index + 1].get("requiredNonceStateBefore"):
                raise ValueError(f"transaction {index} nonce chain drifted")
    if not Path(plan_path).is_file():
        raise ValueError("execution plan path is unavailable")


def validate_simulation_report(
    report: dict[str, Any],
    plan: dict[str, Any],
    *,
    plan_file_hash: str,
    operator_hash: str,
) -> None:
    if report.get("status") != "PASS_EXACT_HEAD_DUAL_SENDER_LIFECYCLE_OPERATOR":
        raise ValueError("operator simulation report did not pass")
    if report.get("sourceBindings") != {
        "executionPlanBodySha256": plan["executionPlanBodySha256"],
        "executionPlanFileSha256": plan_file_hash,
        "operatorSha256": operator_hash,
        "simulationRunnerSha256": file_sha256(
            Path(__file__).resolve().with_name(
                "simulate_robinhood_lifecycle_execution_operator.py"
            )
        ),
    }:
        raise ValueError("operator simulation source binding drifted")
    execution_start = int(plan.get("executionStartIndex", 0))
    expected_count = len(plan["transactions"]) - execution_start
    if (
        report.get("transactionCount") != expected_count
        or len(report.get("transactions", [])) != expected_count
    ):
        raise ValueError("operator simulation is incomplete")
    if [step.get("transactionIndex") for step in report["transactions"]] != list(
        range(execution_start, len(plan["transactions"]))
    ):
        raise ValueError("operator simulation transaction range drifted")
    if report.get("premiumObservationChanged") is not True:
        raise ValueError("operator simulation did not prove premium movement")
    if report.get("publicExecution") != {
        "ready": False,
        "broadcastAttempted": False,
    }:
        raise ValueError("operator simulation public-execution boundary drifted")
    if not all(step.get("status") == "PASS_STOP_BEFORE_NEXT" for step in report["transactions"]):
        raise ValueError("operator simulation contains a failed step")


def validate_authorization(
    authorization: dict[str, Any],
    plan: dict[str, Any],
    *,
    index: int,
    plan_file_hash: str,
    operator_hash: str,
    simulation_report_hash: str,
) -> None:
    if authorization.get("status") != AUTHORIZATION_STATUS:
        raise ValueError("lifecycle authorization status is invalid")
    if authorization.get("network", {}).get("chainId") != CHAIN_ID:
        raise ValueError("lifecycle authorization chain drifted")
    expected_roles = {
        role: qualifier.normalize_address(plan["roles"][role]["address"])
        for role in ("writer", "buyer")
    }
    actual_roles = {
        role: qualifier.normalize_address(authorization.get("roles", {}).get(role, ""))
        for role in ("writer", "buyer")
    }
    if actual_roles != expected_roles:
        raise ValueError("lifecycle authorization role addresses drifted")
    if authorization.get("evidenceBindings") != {
        "executionPlanBodySha256": plan["executionPlanBodySha256"],
        "executionPlanFileSha256": plan_file_hash,
        "operatorSha256": operator_hash,
        "simulationReportSha256": simulation_report_hash,
    }:
        raise ValueError("lifecycle authorization evidence binding drifted")
    minimum_index = int(plan.get("executionStartIndex", 0))
    maximum_index = len(plan["transactions"]) - 1
    if (
        authorization.get("minimumTransactionIndex", minimum_index) != minimum_index
        or authorization.get("maximumTransactionIndex") != maximum_index
        or not minimum_index <= index <= maximum_index
    ):
        raise ValueError("lifecycle authorization index range drifted")
    if authorization.get("policy") != "ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH":
        raise ValueError("lifecycle authorization operator policy drifted")
    permitted = authorization.get("permittedScope", {})
    if permitted != {
        "wrapBuyerWeth": True,
        "exactApprovals": True,
        "fourBoundedSwaps": True,
        "boundedCollateralDeposits": True,
        "matchedOptionOpenAndClose": True,
        "allowanceCleanup": True,
    }:
        raise ValueError("lifecycle authorization permitted scope drifted")
    excluded = authorization.get("excludedScope", {})
    if excluded != {
        "withdrawals": True,
        "otherMarkets": True,
        "issuerAdministration": True,
        "factoryAdministration": True,
        "deployments": True,
        "mainnet": True,
    }:
        raise ValueError("lifecycle authorization exclusions drifted")


def confirmation_phrase(plan_hash: str, index: int, sender: str, nonce: int) -> str:
    normalized = _normalize_hash(plan_hash, "plan hash")
    actor = qualifier.normalize_address(sender)[-8:]
    return (
        f"BROADCAST_ROBINHOOD_{CHAIN_ID}_LIFECYCLE_PLAN_{normalized[:8]}_"
        f"INDEX_{index}_SENDER_{actor}_NONCE_{nonce}"
    )


def _expected_allowances(plan: dict[str, Any], completed: int) -> dict[str, dict[str, Any]]:
    writer = qualifier.normalize_address(plan["roles"]["writer"]["address"])
    buyer = qualifier.normalize_address(plan["roles"]["buyer"]["address"])
    state = {
        actor: {
            "pltrToPermit2": 0,
            "wethToPermit2": 0,
            "pltrToTracker0": 0,
            "wethToTracker1": 0,
            "pltrPermit2ToRouter": 0,
            "wethPermit2ToRouter": 0,
        }
        for actor in (writer, buyer)
    }
    market = plan["market"]
    for transaction in plan["transactions"][:completed]:
        sender = qualifier.normalize_address(transaction["sender"])
        target = qualifier.normalize_address(transaction["to"])
        intent = transaction["decodedIntent"]
        function = intent["function"]
        if function == "approve(address,uint256)":
            spender = qualifier.normalize_address(intent["spender"])
            amount = int(intent["amount"])
            if target == qualifier.normalize_address(market["pltr"]):
                name = "pltrToPermit2" if spender == qualifier.normalize_address(market["permit2"]) else "pltrToTracker0"
            elif target == qualifier.normalize_address(market["weth"]):
                name = "wethToPermit2" if spender == qualifier.normalize_address(market["permit2"]) else "wethToTracker1"
            else:  # pragma: no cover - target validation catches this first
                raise ValueError("unsupported approval target")
            state[sender][name] = amount
        elif function == "approve(address,address,uint160,uint48)":
            token = qualifier.normalize_address(intent["token"])
            name = "pltrPermit2ToRouter" if token == qualifier.normalize_address(market["pltr"]) else "wethPermit2ToRouter"
            state[sender][name] = int(intent["amount"])
        elif function == "execute(bytes,bytes[],uint256)":
            amount = int(intent["amountIn"])
            if intent["zeroForOne"]:
                state[sender]["pltrToPermit2"] -= amount
                state[sender]["pltrPermit2ToRouter"] -= amount
            else:
                state[sender]["wethToPermit2"] -= amount
                state[sender]["wethPermit2ToRouter"] -= amount
        elif function == "deposit(uint256,address)":
            if target == qualifier.normalize_address(market["collateralTracker0"]):
                state[sender]["pltrToTracker0"] = 0
            else:
                state[sender]["wethToTracker1"] = 0
    return state


def _expected_open_legs(plan: dict[str, Any], completed: int) -> dict[str, int]:
    result = {"writer": 0, "buyer": 0}
    writer = qualifier.normalize_address(plan["roles"]["writer"]["address"])
    for transaction in plan["transactions"][:completed]:
        phase = transaction["phase"]
        sender = qualifier.normalize_address(transaction["sender"])
        role = "writer" if sender == writer else "buyer"
        if phase == "MATCHED_OPTION_OPEN":
            result[role] += 1
        elif phase == "ORDERED_CLOSE":
            result[role] -= 1
        if result[role] not in (0, 1):
            raise ValueError(f"{role} option-leg schedule drifted")
    return result


def _required_collateral_share_checks(
    plan: dict[str, Any], completed: int
) -> set[tuple[str, str]]:
    writer = qualifier.normalize_address(plan["roles"]["writer"]["address"])
    tracker0 = qualifier.normalize_address(plan["market"]["collateralTracker0"])
    result: set[tuple[str, str]] = set()
    for transaction in plan["transactions"][:completed]:
        if transaction["decodedIntent"]["function"] != "deposit(uint256,address)":
            continue
        role = (
            "writer"
            if qualifier.normalize_address(transaction["sender"]) == writer
            else "buyer"
        )
        shares = (
            "tracker0Shares"
            if qualifier.normalize_address(transaction["to"]) == tracker0
            else "tracker1Shares"
        )
        result.add((role, shares))
    return result


def _assert_nonce_vector(client: Any, transaction: dict[str, Any], field: str) -> None:
    expected = transaction[field]
    for actor, nonce in expected.items():
        for tag in ("latest", "pending"):
            actual = int(client.call("eth_getTransactionCount", [actor, tag]), 16)
            if actual != int(nonce):
                raise RuntimeError(
                    f"{actor} {tag} nonce mismatch: expected {nonce}, got {actual}"
                )


def verify_state(client: Any, plan: dict[str, Any], completed: int) -> dict[str, Any]:
    if not 0 <= completed <= len(plan["transactions"]):
        raise ValueError("completed transaction count is outside the plan")
    if completed < len(plan["transactions"]):
        vector = plan["transactions"][completed]["requiredNonceStateBefore"]
    else:
        vector = plan["nextNonces"]
    for actor, expected in vector.items():
        confirmed = int(client.call("eth_getTransactionCount", [actor, "latest"]), 16)
        pending = int(client.call("eth_getTransactionCount", [actor, "pending"]), 16)
        if confirmed != int(expected) or pending != int(expected):
            raise RuntimeError(f"dual-sender nonce vector drifted for {actor}")

    external = simulator.observe_external_state(client, plan)
    simulator._assert_external_state(plan, external)
    observed = simulator.observe(client, plan)
    if completed == 0:
        base_path = REPOSITORY / plan["sourceBindings"]["baseLifecyclePlan"]["path"]
        simulator._assert_initial_state(load_json(base_path), observed)
    expected_allowances = _expected_allowances(plan, completed)
    for role in ("writer", "buyer"):
        actor = qualifier.normalize_address(plan["roles"][role]["address"])
        actual = observed[role]
        for name, expected in expected_allowances[actor].items():
            actual_value = actual[name][0] if name.endswith("Permit2ToRouter") else actual[name]
            if int(actual_value) != expected:
                raise RuntimeError(f"{role} {name} allowance drifted")
        if int(actual["openLegs"]) != _expected_open_legs(plan, completed)[role]:
            raise RuntimeError(f"{role} open-leg count drifted")
    for role, shares in _required_collateral_share_checks(plan, completed):
        if int(observed[role][shares]) <= 0:
            raise RuntimeError(f"{role} {shares} collateral shares are absent")
    return {"observed": observed, "external": external, "nonceVector": vector}


def _assert_time_window(client: Any, plan: dict[str, Any], index: int) -> int:
    block = client.call("eth_getBlockByNumber", ["latest", False])
    now = int(block["timestamp"], 16)
    clock = plan["executionClock"]
    swap_deadline = int(clock["swapDeadlineUnix"])
    permit_expiration = int(clock["permit2ExpirationUnix"])
    execution_start = int(plan.get("executionStartIndex", 0))
    if index == execution_start and swap_deadline - now < int(
        clock["minimumSecondsRemainingAtTransactionZero"]
    ):
        raise RuntimeError("lifecycle execution window is too short at transaction zero")
    swap_indexes = clock.get(
        "swapDeadlineTransactionIndexes", [3, 4, 5, 6, 17, 18]
    )
    if index in swap_indexes:
        if swap_deadline - now < int(clock["minimumSecondsRemainingAtDeadlineTransaction"]):
            raise RuntimeError("swap deadline safety margin is exhausted")
    permit_last = int(clock.get("permit2WindowLastTransactionIndex", 22))
    if execution_start <= index <= permit_last and now >= permit_expiration:
        raise RuntimeError("Permit2 lifecycle window expired")
    return now


def _transaction_request(transaction: dict[str, Any], gas_limit: int | None = None) -> dict[str, str]:
    request = {
        "from": transaction["sender"],
        "to": transaction["to"],
        "nonce": hex(int(transaction["nonce"])),
        "value": hex(int(transaction["valueWei"])),
        "data": transaction["calldata"],
    }
    if gas_limit is not None:
        request["gas"] = hex(gas_limit)
    return request


def public_preflight(client: Any, plan: dict[str, Any], index: int) -> dict[str, Any]:
    if not 0 <= index < len(plan["transactions"]):
        raise ValueError("transaction index is outside the execution plan")
    if int(client.call("eth_chainId", []), 16) != CHAIN_ID:
        raise RuntimeError("public RPC chain ID mismatch")
    _assert_time_window(client, plan, index)
    transaction = plan["transactions"][index]
    state = verify_state(client, plan, index)
    gas_policy = plan["gasPolicy"]
    gas_price = int(client.call("eth_gasPrice", []), 16)
    if not 0 < gas_price <= int(gas_policy["maximumGasPriceWei"]):
        raise RuntimeError("gas price is outside the plan cap")
    maximum_gas = int(gas_policy["maximumGasLimitPerTransaction"])
    estimate = int(
        client.call("eth_estimateGas", [_transaction_request(transaction, maximum_gas), "latest"]),
        16,
    )
    multiplier = (estimate * int(gas_policy["estimateMultiplierBps"]) + 9999) // 10000
    gas_limit = max(multiplier, estimate + int(gas_policy["estimateAdditiveBuffer"]))
    if estimate <= 0 or gas_limit > maximum_gas or gas_limit >= 1 << 24:
        raise RuntimeError("buffered gas limit is invalid")
    balance = int(client.call("eth_getBalance", [transaction["sender"], "latest"]), 16)
    maximum_cost = int(transaction["valueWei"]) + gas_price * gas_limit
    if balance < maximum_cost:
        raise RuntimeError("sender native balance is below value-plus-gas bound")
    latest = client.call("eth_getBlockByNumber", ["latest", False])
    return {
        "chainId": CHAIN_ID,
        "blockNumber": int(latest["number"], 16),
        "blockHash": latest["hash"].lower(),
        "blockTimestamp": int(latest["timestamp"], 16),
        "transactionIndex": index,
        "sender": transaction["sender"],
        "nonce": transaction["nonce"],
        "gasPriceWei": gas_price,
        "gasEstimate": estimate,
        "gasLimit": gas_limit,
        "maximumCostWei": str(maximum_cost),
        "state": state,
    }


def _verify_postconditions(
    plan: dict[str, Any],
    index: int,
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    transaction = plan["transactions"][index]
    intent = transaction["decodedIntent"]
    function = intent["function"]
    sender = qualifier.normalize_address(transaction["sender"])
    role = "writer" if sender == qualifier.normalize_address(plan["roles"]["writer"]["address"]) else "buyer"
    result: dict[str, Any] = {"function": function, "status": "PASS"}
    if function == "deposit()":
        delta = int(after[role]["wethBalance"]) - int(before[role]["wethBalance"])
        if delta != int(transaction["valueWei"]):
            raise RuntimeError("WETH wrap delta mismatch")
        result["wethReceived"] = str(delta)
    elif function == "execute(bytes,bytes[],uint256)":
        result["swap"] = simulator.assert_swap_postconditions(
            plan, transaction, before, after
        )
    elif function == "deposit(uint256,address)":
        assets = int(intent["assets"])
        tracker0 = qualifier.normalize_address(transaction["to"]) == qualifier.normalize_address(plan["market"]["collateralTracker0"])
        token_key = "pltrBalance" if tracker0 else "wethBalance"
        shares_key = "tracker0Shares" if tracker0 else "tracker1Shares"
        spent = int(before[role][token_key]) - int(after[role][token_key])
        if spent != assets or int(after[role][shares_key]) <= int(before[role][shares_key]):
            raise RuntimeError("collateral deposit accounting mismatch")
        result["assetsDeposited"] = str(spent)
    return result


def _receipt_summary(
    client: Any,
    transaction: dict[str, Any],
    receipt: dict[str, Any],
    gas_limit: int,
) -> dict[str, Any]:
    mined = client.call("eth_getTransactionByHash", [receipt["transactionHash"]])
    if not isinstance(mined, dict):
        raise RuntimeError("mined transaction is unavailable")
    comparisons = {
        "sender": (qualifier.normalize_address(mined.get("from", "")), qualifier.normalize_address(transaction["sender"])),
        "recipient": (qualifier.normalize_address(mined.get("to", "")), qualifier.normalize_address(transaction["to"])),
        "nonce": (int(mined.get("nonce", "0x0"), 16), int(transaction["nonce"])),
        "value": (int(mined.get("value", "0x0"), 16), int(transaction["valueWei"])),
        "input": (str(mined.get("input", "")).lower(), transaction["calldata"].lower()),
    }
    for name, (actual, expected) in comparisons.items():
        if actual != expected:
            raise RuntimeError(f"mined transaction {name} mismatch")
    if receipt.get("status") != "0x1":
        raise RuntimeError("lifecycle transaction receipt failed")
    gas_used = int(receipt.get("gasUsed", "0x0"), 16)
    if not 0 < gas_used <= gas_limit:
        raise RuntimeError("receipt gas used is outside the committed gas limit")
    return {
        "transactionHash": receipt["transactionHash"].lower(),
        "blockNumber": int(receipt["blockNumber"], 16),
        "blockHash": receipt["blockHash"].lower(),
        "from": qualifier.normalize_address(mined["from"]),
        "to": qualifier.normalize_address(mined["to"]),
        "nonce": int(mined["nonce"], 16),
        "valueWei": str(int(mined["value"], 16)),
        "calldataKeccak256": transaction["calldataKeccak256"],
        "gasUsed": gas_used,
    }


def reviewed_intent(plan: dict[str, Any], index: int) -> dict[str, Any]:
    transaction = plan["transactions"][index]
    return {
        "chainId": CHAIN_ID,
        "transactionIndex": index,
        "sender": transaction["sender"],
        "nonce": transaction["nonce"],
        "label": transaction["label"],
        "to": transaction["to"],
        "valueWei": transaction["valueWei"],
        "calldataKeccak256": transaction["calldataKeccak256"],
        "decodedIntent": transaction["decodedIntent"],
        "requiredNonceStateBefore": transaction["requiredNonceStateBefore"],
        "exposureCaps": plan["exposureCaps"],
        "policy": "ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH",
    }


def _send_local(
    client: Any,
    transaction: dict[str, Any],
    gas_limit: int,
    *,
    sleep: Callable[[float], None],
) -> dict[str, Any]:
    latest = client.call("eth_getBlockByNumber", ["latest", False])
    base_fee = int(latest["baseFeePerGas"], 16)
    request = _transaction_request(transaction, gas_limit)
    request.update({"maxFeePerGas": hex(max(1, base_fee * 2)), "maxPriorityFeePerGas": "0x0"})
    transaction_hash = client.call("eth_sendTransaction", [request])
    return simulator._poll_receipt(client, transaction_hash, 300, 0.1, sleep)


def simulate_one_step(
    plan: dict[str, Any],
    plan_path: Path,
    client: Any,
    index: int,
    *,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    validate_execution_plan(plan, plan_path)
    if not 0 <= index < len(plan["transactions"]):
        raise ValueError("transaction index is outside the execution plan")
    snapshot = client.call("evm_snapshot", [])
    try:
        _assert_time_window(client, plan, index)
        before_state = verify_state(client, plan, index)
        transaction = plan["transactions"][index]
        sender = transaction["sender"]
        client.call("anvil_impersonateAccount", [sender])
        try:
            receipt = _send_local(
                client,
                transaction,
                int(plan["gasPolicy"]["maximumGasLimitPerTransaction"]),
                sleep=sleep,
            )
        finally:
            client.call("anvil_stopImpersonatingAccount", [sender])
        mined = _receipt_summary(
            client,
            transaction,
            receipt,
            int(plan["gasPolicy"]["maximumGasLimitPerTransaction"]),
        )
        after_state = verify_state(client, plan, index + 1)
        postconditions = _verify_postconditions(
            plan,
            index,
            before_state["observed"],
            after_state["observed"],
        )
        return {
            "status": "PASS_STOP_BEFORE_NEXT",
            "transactionIndex": index,
            "sender": sender,
            "nonce": transaction["nonce"],
            "label": transaction["label"],
            "to": transaction["to"],
            "valueWei": transaction["valueWei"],
            "calldataKeccak256": transaction["calldataKeccak256"],
            "minedTransaction": mined,
            "postconditions": postconditions,
            "postNonceVector": after_state["nonceVector"],
            "nextGate": "STOP_AND_REVIEW_BEFORE_SELECTING_NEXT_INDEX",
        }
    except Exception:
        if client.call("evm_revert", [snapshot]) is not True:
            raise RuntimeError("operator failure occurred and Anvil snapshot could not be restored")
        raise


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
) -> dict[str, Any]:
    validate_execution_plan(plan, plan_path)
    plan_file_hash = file_sha256(plan_path)
    operator_hash = file_sha256(Path(__file__))
    simulation_hash = file_sha256(simulation_report_path)
    validate_simulation_report(
        simulation_report,
        plan,
        plan_file_hash=plan_file_hash,
        operator_hash=operator_hash,
    )
    validate_authorization(
        authorization,
        plan,
        index=index,
        plan_file_hash=plan_file_hash,
        operator_hash=operator_hash,
        simulation_report_hash=simulation_hash,
    )
    transaction = plan["transactions"][index]
    expected_confirmation = confirmation_phrase(
        plan_file_hash, index, transaction["sender"], transaction["nonce"]
    )
    if confirmation != expected_confirmation:
        raise ValueError(f"confirmation mismatch; expected exactly {expected_confirmation}")
    try:
        Path(output_dir).resolve().relative_to(REPOSITORY.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("execution evidence directory must be outside the repository")
    output_dir.mkdir(parents=True, exist_ok=True)
    intent = reviewed_intent(plan, index)
    print("Reviewed one-transaction intent (no password has been requested):")
    print(json.dumps(intent, indent=2))

    client = direct_operator.JsonRpcClient(OFFICIAL_RPC_URL)
    initial = public_preflight(client, plan, index)
    signing = public_preflight(client, plan, index)
    data = bytes.fromhex(transaction["calldata"][2:])
    unsigned = genesis_operator.unsigned_legacy_transaction(
        nonce=transaction["nonce"],
        gas_price=signing["gasPriceWei"],
        gas_limit=signing["gasLimit"],
        to=transaction["to"],
        value=int(transaction["valueWei"]),
        data=data,
        chain_id=CHAIN_ID,
    )
    digest = direct_operator.cast_keccak(unsigned)
    evidence_path = output_dir / f"lifecycle-index-{index:02d}-nonce-{transaction['nonce']}.json"
    if evidence_path.exists():
        raise FileExistsError(f"refusing to overwrite execution evidence: {evidence_path}")
    evidence = {
        "schemaVersion": 1,
        "status": "READY_TO_PROMPT_FOR_ENCRYPTED_KEYSTORE",
        "executionPlanBodySha256": plan["executionPlanBodySha256"],
        "executionPlanFileSha256": plan_file_hash,
        "operatorSha256": operator_hash,
        "operatorSimulationReportSha256": simulation_hash,
        "intent": intent,
        "initialPreflight": initial,
        "signingPreflight": signing,
        "broadcastAttempted": False,
    }
    direct_operator._write_json(evidence_path, evidence)
    r, s, parity = direct_operator.sign_digest_with_foundry(
        digest, keystore, transaction["sender"]
    )
    raw = genesis_operator.build_signed_legacy_transaction(
        nonce=transaction["nonce"],
        gas_price=signing["gasPriceWei"],
        gas_limit=signing["gasLimit"],
        to=transaction["to"],
        value=int(transaction["valueWei"]),
        data=data,
        chain_id=CHAIN_ID,
        r=r,
        s=s,
        parity=parity,
    )
    expected_hash = direct_operator.cast_keccak(bytes.fromhex(raw[2:])).lower()
    post_sign = public_preflight(client, plan, index)
    if post_sign["gasPriceWei"] > signing["gasPriceWei"] or post_sign["gasEstimate"] > signing["gasLimit"]:
        raise RuntimeError("post-sign gas state changed; raw transaction was not published")
    evidence.update({"status": "SIGNED_AND_RECHECKED_NOT_YET_BROADCAST", "postSignRecheck": post_sign})
    direct_operator._write_json(evidence_path, evidence)
    try:
        transaction_hash = client.call("eth_sendRawTransaction", [raw])
    except Exception as exc:
        evidence.update({"status": "SUBMISSION_INDETERMINATE_STOP", "broadcastAttempted": True, "error": f"{type(exc).__name__}: {exc}"})
        direct_operator._write_json(evidence_path, evidence)
        raise RuntimeError("submission indeterminate; do not retry before nonce and explorer reconciliation") from exc
    transaction_hash = transaction_hash.lower()
    if transaction_hash != expected_hash:
        evidence.update({"status": "SUBMISSION_HASH_MISMATCH_STOP", "broadcastAttempted": True, "transactionHash": transaction_hash, "expectedTransactionHash": expected_hash})
        direct_operator._write_json(evidence_path, evidence)
        raise RuntimeError("RPC transaction hash differs from signed raw transaction")
    evidence.update({"status": "SUBMITTED_RECEIPT_PENDING", "broadcastAttempted": True, "transactionHash": transaction_hash})
    direct_operator._write_json(evidence_path, evidence)
    receipt = direct_operator._poll_receipt(client, transaction_hash)
    try:
        mined = _receipt_summary(client, transaction, receipt, signing["gasLimit"])
        after = verify_state(client, plan, index + 1)
        postconditions = _verify_postconditions(
            plan,
            index,
            signing["state"]["observed"],
            after["observed"],
        )
    except Exception as exc:
        evidence.update({"status": "RECEIPT_OR_POST_STATE_MISMATCH_STOP", "receipt": receipt, "error": f"{type(exc).__name__}: {exc}"})
        direct_operator._write_json(evidence_path, evidence)
        raise
    evidence.update(
        {
            "status": "PASS_STOP_BEFORE_NEXT",
            "receipt": receipt,
            "minedTransaction": mined,
            "postconditions": postconditions,
            "postNonceVector": after["nonceVector"],
            "nextGate": "STOP_AND_REVIEW_BEFORE_SELECTING_NEXT_INDEX",
        }
    )
    direct_operator._write_json(evidence_path, evidence)
    return evidence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--review", action="store_true")
    mode.add_argument("--simulate", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--rpc-url", default="http://127.0.0.1:8549")
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument("--simulation-report", type=Path, default=DEFAULT_SIMULATION_REPORT)
    parser.add_argument("--authorization-manifest", type=Path)
    parser.add_argument("--keystore", type=Path)
    parser.add_argument("--confirmation")
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = load_json(args.plan)
    validate_execution_plan(plan, args.plan)
    if args.review:
        print(json.dumps(reviewed_intent(plan, args.index), indent=2))
        return 0
    if args.simulate:
        simulator.validate_local_rpc_url(args.rpc_url)
        client = simulator.genesis_simulator.JsonRpcClient(args.rpc_url)
        print(json.dumps(simulate_one_step(plan, args.plan, client, args.index), indent=2))
        return 0
    if args.authorization_manifest is None or args.keystore is None or args.confirmation is None or args.output_dir is None:
        raise ValueError("--execute requires authorization manifest, keystore, confirmation, and output directory")
    if args.rpc_url != OFFICIAL_RPC_URL:
        raise ValueError("public execution requires the exact official Robinhood testnet RPC URL")
    result = execute_one_step(
        plan,
        args.plan,
        load_json(args.simulation_report),
        args.simulation_report,
        load_json(args.authorization_manifest),
        index=args.index,
        keystore=args.keystore,
        confirmation=args.confirmation,
        output_dir=args.output_dir,
    )
    print(json.dumps({"status": result["status"], "transactionIndex": args.index, "transactionHash": result["minedTransaction"]["transactionHash"], "nextGate": result["nextGate"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
