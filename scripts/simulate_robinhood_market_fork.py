#!/usr/bin/env python3
"""Rehearse the PLTR/WETH market plan only on an exact loopback Anvil fork.

The simulator rejects non-loopback URLs and non-Anvil clients before mutation.
It uses Anvil account impersonation, never reads a key, never signs a
transaction, never changes the positive-path balances or storage, and emits a
sanitized report without calldata.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import ipaddress
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

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


fork_planner = _load_sibling(
    "stonkhedge_market_fork_planner", "prepare_robinhood_market_fork_plan.py"
)
verifier = fork_planner.verifier
qualifier = verifier.qualifier

REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-fork-plan-2026-09-09.json"
)
DEFAULT_REPORT = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-fork-rehearsal-2026-09-09.json"
)
DEFAULT_RPC_URL = "http://127.0.0.1:8547"
DEFAULT_TRANSACTION_GAS = "0xff0000"
EIP7825_TRANSACTION_GAS_LIMIT = 1 << 24
POOL_KEY_ABI = "(address,address,uint24,int24,address)"
POOL_DEPLOYED_TOPIC = "0x" + keccak(
    text="PoolDeployed(address,bytes32,address,address,address)"
).hex()


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


def _is_loopback_hostname(hostname: str | None) -> bool:
    if not hostname:
        return False
    if hostname.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def validate_local_rpc_url(rpc_url: str) -> None:
    parsed = urlparse(rpc_url)
    if parsed.scheme != "http" or not _is_loopback_hostname(parsed.hostname):
        raise ValueError("simulation RPC must be an http loopback URL")
    if parsed.username or parsed.password:
        raise ValueError("simulation RPC must not contain credentials")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("simulation RPC must not contain a path, query, or fragment")
    if parsed.port is None:
        raise ValueError("simulation RPC must include an explicit loopback port")


class JsonRpcClient:
    def __init__(self, rpc_url: str, timeout: float = 30.0):
        validate_local_rpc_url(rpc_url)
        self.rpc_url = rpc_url
        self.timeout = timeout
        self.request_id = 0

    def call(self, method: str, params: list[Any]):
        self.request_id += 1
        request = urllib.request.Request(
            self.rpc_url,
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": self.request_id,
                    "method": method,
                    "params": params,
                },
                separators=(",", ":"),
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"{method} RPC request failed: {exc}") from exc
        if payload.get("error") is not None:
            raise RuntimeError(f"{method} RPC error: {payload['error']}")
        if "result" not in payload:
            raise RuntimeError(f"{method} RPC response is missing result")
        return payload["result"]


def validate_transaction_gas(transaction_gas: str) -> None:
    try:
        value = int(transaction_gas, 16)
    except (TypeError, ValueError) as exc:
        raise ValueError("transaction gas must be a hex quantity") from exc
    if value <= 0 or value >= EIP7825_TRANSACTION_GAS_LIMIT:
        raise ValueError("transaction gas must be positive and below 2^24")


def validate_fork_plan(plan: dict[str, Any], plan_path: Path) -> None:
    if plan.get("status") != "FORK_REHEARSAL_ONLY_NO_PUBLIC_BROADCAST":
        raise ValueError("plan status is not fork-rehearsal only")
    if plan.get("mode") != "LOOPBACK_ANVIL_ONLY_NO_KEYS_NO_SIGNING_NO_PUBLIC_BROADCAST":
        raise ValueError("plan mode is not loopback-only")
    if plan.get("network", {}).get("chainId") != fork_planner.CHAIN_ID:
        raise ValueError("plan chain ID drifted")
    if plan.get("network", {}).get("rpcPolicy") != "HTTP_LOOPBACK_ANVIL_ONLY":
        raise ValueError("plan RPC policy drifted")
    if plan.get("publicExecution", {}).get("ready") is not False:
        raise ValueError("plan must keep public execution disabled")
    if not fork_planner._all_false(plan.get("authorization")):
        raise ValueError("plan authorization must remain entirely false")
    transactions = plan.get("transactions")
    if not isinstance(transactions, list) or len(transactions) != 12:
        raise ValueError("fork plan must contain twelve transactions")
    if plan.get("transactionCount") != len(transactions):
        raise ValueError("fork plan transaction count drifted")
    actor = plan.get("actor", {}).get("address", "").lower()
    for ordinal, transaction in enumerate(transactions):
        if transaction.get("ordinal") != ordinal:
            raise ValueError(f"transaction {ordinal} ordering drifted")
        if transaction.get("from", "").lower() != actor:
            raise ValueError(f"transaction {ordinal} actor drifted")
        if transaction.get("nonce") is not None:
            raise ValueError(f"transaction {ordinal} unexpectedly binds a nonce")
        if transaction.get("authorizedForBroadcast") is not False:
            raise ValueError(f"transaction {ordinal} must remain unauthorized")
    if plan.get("forkPlanBodySha256") != fork_planner.fork_plan_body_sha256(plan):
        raise ValueError("fork-plan body SHA-256 drifted")

    predicted = plan.get("predictedMarketContracts", {})
    expected_proxy = fork_planner.predict_create3_proxy(
        plan["contracts"]["panopticFactoryV4"], predicted.get("derivedSalt32", "")
    )
    if predicted.get("create3Proxy", "").lower() != expected_proxy:
        raise ValueError("fork-plan CREATE3 proxy prediction drifted")

    repository = Path(plan_path).resolve().parents[2]
    bindings = plan.get("sourceBindings", {})
    paths: dict[str, Path] = {}
    for name in ("basePlan", "initialPreflight", "generator"):
        binding = bindings.get(name)
        if not isinstance(binding, dict):
            raise ValueError(f"fork-plan source binding {name} is absent")
        source = repository / binding["path"]
        if not source.is_file() or file_sha256(source) != binding.get("sha256"):
            raise ValueError(f"fork-plan source binding {name} drifted")
        paths[name] = source
    regenerated = fork_planner.build_fork_plan(
        paths["basePlan"], paths["initialPreflight"], paths["generator"]
    )
    if plan != regenerated:
        raise ValueError("fork plan is not the exact output of its bound inputs")


def assert_exact_fork(plan: dict[str, Any], client: Any) -> dict[str, Any]:
    client_version = client.call("web3_clientVersion", [])
    if not isinstance(client_version, str) or "anvil" not in client_version.lower():
        raise RuntimeError(f"refusing non-Anvil client: {client_version}")
    chain_id = int(client.call("eth_chainId", []), 16)
    if chain_id != plan["network"]["chainId"]:
        raise RuntimeError(
            f"chain ID mismatch: expected {plan['network']['chainId']}, got {chain_id}"
        )
    block = client.call("eth_getBlockByNumber", ["latest", False])
    if not isinstance(block, dict):
        raise RuntimeError("latest block response is malformed")
    actual_number = int(block["number"], 16)
    actual_hash = block["hash"].lower()
    actual_timestamp = int(block["timestamp"], 16)
    expected_timestamp = plan["forkClock"]["referenceTimestampUnix"]
    if actual_number != plan["network"]["forkBlock"]:
        raise RuntimeError(
            f"fork block mismatch: expected {plan['network']['forkBlock']}, got {actual_number}"
        )
    if actual_hash != plan["network"]["forkBlockHash"].lower():
        raise RuntimeError("fork block hash mismatch")
    if actual_timestamp != expected_timestamp:
        raise RuntimeError(
            f"fork timestamp mismatch: expected {expected_timestamp}, got {actual_timestamp}"
        )
    return {
        "clientVersion": client_version,
        "chainId": chain_id,
        "forkBlock": actual_number,
        "forkBlockHash": actual_hash,
        "forkTimestampUnix": actual_timestamp,
    }


def mine_local_compatibility_block(
    plan: dict[str, Any], client: Any
) -> dict[str, Any]:
    """Mine one deterministic local child with complete post-Cancun fields."""

    timestamp = plan["forkClock"]["localCompatibilityTimestampUnix"]
    if timestamp != plan["forkClock"]["referenceTimestampUnix"] + 1:
        raise RuntimeError("local compatibility timestamp policy drifted")
    client.call("evm_setNextBlockTimestamp", [timestamp])
    client.call("evm_mine", [])
    block = client.call("eth_getBlockByNumber", ["latest", False])
    if not isinstance(block, dict):
        raise RuntimeError("local compatibility block response is malformed")
    number = int(block["number"], 16)
    actual_timestamp = int(block["timestamp"], 16)
    if number != plan["network"]["forkBlock"] + 1:
        raise RuntimeError("local compatibility block number drifted")
    if block["parentHash"].lower() != plan["network"]["forkBlockHash"].lower():
        raise RuntimeError("local compatibility block parent drifted")
    if actual_timestamp != timestamp:
        raise RuntimeError("local compatibility block timestamp drifted")
    if block.get("excessBlobGas") is None:
        raise RuntimeError("local compatibility block lacks excessBlobGas")
    return {
        "blockNumber": number,
        "blockHash": block["hash"].lower(),
        "parentHash": block["parentHash"].lower(),
        "timestampUnix": actual_timestamp,
        "purpose": "LOCAL_ONLY_POST_CANCUN_HEADER_FOR_ETH_CALL_COMPATIBILITY",
    }


def _contract_call(
    client: Any,
    to: str,
    signature: str,
    return_types: list[str],
    argument_types: list[str] | None = None,
    arguments: list[Any] | None = None,
):
    return qualifier.contract_call(
        client,
        "latest",
        to,
        signature,
        return_types=return_types,
        argument_types=argument_types or [],
        arguments=arguments or [],
    )


def _pool_key_tuple(plan: dict[str, Any]) -> tuple[str, str, int, int, str]:
    return fork_planner.planner.pool_key_tuple(plan["market"]["poolKey"])


def _balance(client: Any, token: str, account: str) -> int:
    return int(
        _contract_call(
            client,
            token,
            "balanceOf(address)",
            ["uint256"],
            ["address"],
            [account],
        )
    )


def _erc20_allowance(client: Any, token: str, owner: str, spender: str) -> int:
    return int(
        _contract_call(
            client,
            token,
            "allowance(address,address)",
            ["uint256"],
            ["address", "address"],
            [owner, spender],
        )
    )


def _permit2_allowance(
    client: Any, permit2: str, owner: str, token: str, spender: str
) -> tuple[int, int, int]:
    amount, expiration, nonce = _contract_call(
        client,
        permit2,
        "allowance(address,address,address)",
        ["uint160", "uint48", "uint48"],
        ["address", "address", "address"],
        [owner, token, spender],
    )
    return int(amount), int(expiration), int(nonce)


def _slot0(client: Any, plan: dict[str, Any]) -> tuple[int, int, int, int]:
    values = _contract_call(
        client,
        plan["contracts"]["stateView"],
        "getSlot0(bytes32)",
        ["uint160", "int24", "uint24", "uint24"],
        ["bytes32"],
        [bytes.fromhex(plan["market"]["poolId"][2:])],
    )
    return tuple(int(value) for value in values)


def _active_liquidity(client: Any, plan: dict[str, Any]) -> int:
    return int(
        _contract_call(
            client,
            plan["contracts"]["stateView"],
            "getLiquidity(bytes32)",
            ["uint128"],
            ["bytes32"],
            [bytes.fromhex(plan["market"]["poolId"][2:])],
        )
    )


def _factory_pool(client: Any, plan: dict[str, Any]) -> str:
    return qualifier.normalize_address(
        _contract_call(
            client,
            plan["contracts"]["panopticFactoryV4"],
            "getPanopticPool((address,address,uint24,int24,address),address)",
            ["address"],
            [POOL_KEY_ABI, "address"],
            [_pool_key_tuple(plan), plan["contracts"]["riskEngine"]],
        )
    )


def _poll_receipt(
    client: Any,
    transaction_hash: str,
    *,
    attempts: int,
    interval_seconds: float,
    sleep: Callable[[float], None],
) -> dict[str, Any]:
    for _ in range(attempts):
        receipt = client.call("eth_getTransactionReceipt", [transaction_hash])
        if receipt is not None:
            return receipt
        sleep(interval_seconds)
    raise TimeoutError(f"receipt timeout for {transaction_hash}")


def _send(
    client: Any,
    transaction: dict[str, Any],
    actor: str,
    transaction_gas: str,
    *,
    attempts: int,
    interval_seconds: float,
    sleep: Callable[[float], None],
) -> dict[str, Any]:
    latest = client.call("eth_getBlockByNumber", ["latest", False])
    if not isinstance(latest, dict) or latest.get("baseFeePerGas") is None:
        raise RuntimeError("local latest block lacks baseFeePerGas")
    base_fee_per_gas = int(latest["baseFeePerGas"], 16)
    max_fee_per_gas = max(1, base_fee_per_gas * 2)
    transaction_hash = client.call(
        "eth_sendTransaction",
        [
            {
                "from": actor,
                "to": transaction["to"],
                "value": hex(int(transaction["valueWei"])),
                "data": transaction["calldata"],
                "gas": transaction_gas,
                "maxFeePerGas": hex(max_fee_per_gas),
                "maxPriorityFeePerGas": "0x0",
            }
        ],
    )
    return _poll_receipt(
        client,
        transaction_hash,
        attempts=attempts,
        interval_seconds=interval_seconds,
        sleep=sleep,
    )


def transaction_result(
    transaction: dict[str, Any], receipt: dict[str, Any]
) -> dict[str, Any]:
    return {
        "ordinal": transaction["ordinal"],
        "label": transaction["label"],
        "to": transaction["to"],
        "valueWei": transaction["valueWei"],
        "calldataKeccak256": transaction["calldataKeccak256"],
        "transactionHash": receipt["transactionHash"],
        "blockNumber": int(receipt["blockNumber"], 16),
        "gasUsed": int(receipt["gasUsed"], 16),
        "effectiveGasPriceWei": str(int(receipt.get("effectiveGasPrice", "0x0"), 16)),
        "status": "PASS" if receipt.get("status") == "0x1" else "REVERT",
    }


def _require_success(
    client: Any,
    plan: dict[str, Any],
    ordinal: int,
    transaction_gas: str,
    *,
    attempts: int,
    interval_seconds: float,
    sleep: Callable[[float], None],
) -> tuple[dict[str, Any], dict[str, Any]]:
    transaction = plan["transactions"][ordinal]
    receipt = _send(
        client,
        transaction,
        plan["actor"]["address"],
        transaction_gas,
        attempts=attempts,
        interval_seconds=interval_seconds,
        sleep=sleep,
    )
    if receipt.get("status") != "0x1":
        raise RuntimeError(
            f"positive transaction reverted: ordinal={ordinal} label={transaction['label']}"
        )
    return receipt, transaction_result(transaction, receipt)


def _expect_revert_in_snapshot(
    client: Any,
    plan: dict[str, Any],
    ordinal: int,
    name: str,
    transaction_gas: str,
    *,
    before_send: Callable[[], None] | None = None,
    attempts: int,
    interval_seconds: float,
    sleep: Callable[[float], None],
) -> dict[str, Any]:
    snapshot = client.call("evm_snapshot", [])
    result: dict[str, Any]
    try:
        if before_send is not None:
            before_send()
        receipt = _send(
            client,
            plan["transactions"][ordinal],
            plan["actor"]["address"],
            transaction_gas,
            attempts=attempts,
            interval_seconds=interval_seconds,
            sleep=sleep,
        )
        if receipt.get("status") != "0x0":
            raise RuntimeError(f"negative case unexpectedly succeeded: {name}")
        result = {
            "name": name,
            "status": "PASS_REVERTED",
            "transactionHash": receipt["transactionHash"],
            "gasUsed": int(receipt["gasUsed"], 16),
        }
    finally:
        if client.call("evm_revert", [snapshot]) is not True:
            raise RuntimeError(f"could not restore snapshot after negative case: {name}")
    return result


def decode_pool_deployed_event(logs: list[dict[str, Any]]) -> dict[str, str]:
    matches = [
        log
        for log in logs
        if log.get("topics")
        and str(log["topics"][0]).lower() == POOL_DEPLOYED_TOPIC.lower()
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one PoolDeployed event, found {len(matches)}")
    event = matches[0]
    topics = event["topics"]
    if len(topics) != 3:
        raise ValueError("PoolDeployed event has unexpected indexed topics")
    pool = qualifier.normalize_address("0x" + topics[1][-40:])
    pool_id = "0x" + topics[2][-64:].lower()
    try:
        tracker0, tracker1, risk_engine = abi_decode(
            ["address", "address", "address"], bytes.fromhex(event["data"][2:])
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("PoolDeployed event data is malformed") from exc
    return {
        "panopticPool": pool,
        "poolId": pool_id,
        "collateralTracker0": qualifier.normalize_address(tracker0),
        "collateralTracker1": qualifier.normalize_address(tracker1),
        "riskEngine": qualifier.normalize_address(risk_engine),
    }


def _run_initial_preflight(
    client: Any,
    plan: dict[str, Any],
    plan_path: Path,
    compatibility_block_number: int,
) -> dict[str, Any]:
    repository = Path(plan_path).resolve().parents[2]
    base_plan_path = repository / plan["sourceBindings"]["basePlan"]["path"]
    base_plan = load_json(base_plan_path)
    qualification = qualifier.qualify(
        client,
        load_json(verifier.DEFAULT_CHAIN),
        load_json(verifier.DEFAULT_DEPLOYMENT),
        load_json(verifier.DEFAULT_ACTOR),
        block=compatibility_block_number,
    )
    preflight = verifier.verify_initial_prestate(client, base_plan, qualification)
    if preflight["status"] != "PASS_INITIAL_MARKET_PREFLIGHT":
        raise RuntimeError(
            f"local strict initial preflight failed: {preflight['checks']['failed']} checks"
        )
    return {
        "status": preflight["status"],
        "checksPassed": preflight["checks"]["passed"],
        "checksFailed": preflight["checks"]["failed"],
        "qualificationPassed": qualification["checks"]["passed"],
        "qualificationFailed": qualification["checks"]["failed"],
        "actorConfirmedNonce": preflight["observations"]["actorConfirmedNonce"],
        "actorPendingNonce": preflight["observations"]["actorPendingNonce"],
        "positionManagerNextTokenId": preflight["observations"][
            "positionManagerNextTokenId"
        ],
    }


def _assert_equal(name: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise RuntimeError(f"{name} mismatch: expected {expected}, got {actual}")


def simulate(
    plan: dict[str, Any],
    plan_path: Path,
    client: Any,
    *,
    transaction_gas: str = DEFAULT_TRANSACTION_GAS,
    receipt_attempts: int = 300,
    receipt_interval_seconds: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    validate_fork_plan(plan, plan_path)
    validate_transaction_gas(transaction_gas)
    if receipt_attempts <= 0 or receipt_interval_seconds < 0:
        raise ValueError("receipt polling limits must be non-negative")
    fork_identity = assert_exact_fork(plan, client)
    compatibility_block = mine_local_compatibility_block(plan, client)
    local_preflight = _run_initial_preflight(
        client, plan, plan_path, compatibility_block["blockNumber"]
    )

    actor = qualifier.normalize_address(plan["actor"]["address"])
    contracts = plan["contracts"]
    exposure = plan["maximumExposureProposal"]
    price = plan["priceAndLiquidity"]
    predicted = plan["predictedMarketContracts"]
    initial_nonce = int(client.call("eth_getTransactionCount", [actor, "pending"]), 16)
    initial_native = int(client.call("eth_getBalance", [actor, "latest"]), 16)
    initial_pltr = _balance(client, contracts["pltr"], actor)
    initial_weth = _balance(client, contracts["weth"], actor)
    next_token_id = int(
        _contract_call(
            client,
            contracts["positionManager"],
            "nextTokenId()",
            ["uint256"],
        )
    )
    _assert_equal(
        "preflight nextTokenId",
        str(next_token_id),
        local_preflight["positionManagerNextTokenId"],
    )

    transactions: list[dict[str, Any]] = []
    negative_cases: list[dict[str, Any]] = []
    client.call("anvil_impersonateAccount", [actor])
    try:
        receipt, result = _require_success(
            client,
            plan,
            0,
            transaction_gas,
            attempts=receipt_attempts,
            interval_seconds=receipt_interval_seconds,
            sleep=sleep,
        )
        transactions.append(result)
        wrap_amount = int(exposure["wrapNativeWei"])
        _assert_equal(
            "wrapped WETH balance",
            _balance(client, contracts["weth"], actor),
            initial_weth + wrap_amount,
        )

        for ordinal, symbol, token, maximum in (
            (1, "PLTR", contracts["pltr"], int(exposure["maximumPltrTransfer"])),
            (2, "WETH", contracts["weth"], int(exposure["maximumWethTransfer"])),
        ):
            _, result = _require_success(
                client,
                plan,
                ordinal,
                transaction_gas,
                attempts=receipt_attempts,
                interval_seconds=receipt_interval_seconds,
                sleep=sleep,
            )
            transactions.append(result)
            _assert_equal(
                f"{symbol} ERC20 allowance",
                _erc20_allowance(client, token, actor, contracts["permit2"]),
                maximum,
            )

        for ordinal, symbol, token, maximum in (
            (3, "PLTR", contracts["pltr"], int(exposure["maximumPltrTransfer"])),
            (4, "WETH", contracts["weth"], int(exposure["maximumWethTransfer"])),
        ):
            _, result = _require_success(
                client,
                plan,
                ordinal,
                transaction_gas,
                attempts=receipt_attempts,
                interval_seconds=receipt_interval_seconds,
                sleep=sleep,
            )
            transactions.append(result)
            amount, expiration, _ = _permit2_allowance(
                client,
                contracts["permit2"],
                actor,
                token,
                contracts["positionManager"],
            )
            _assert_equal(f"{symbol} Permit2 allowance", amount, maximum)
            _assert_equal(
                f"{symbol} Permit2 expiration",
                expiration,
                plan["forkClock"]["permit2ExpirationUnix"],
            )

        _, result = _require_success(
            client,
            plan,
            5,
            transaction_gas,
            attempts=receipt_attempts,
            interval_seconds=receipt_interval_seconds,
            sleep=sleep,
        )
        transactions.append(result)
        sqrt_price, tick, _, _ = _slot0(client, plan)
        _assert_equal("initialized sqrtPriceX96", sqrt_price, int(price["sqrtPriceX96"]))
        _assert_equal("initialized tick", tick, int(price["initialTick"]))
        _assert_equal("pre-mint active liquidity", _active_liquidity(client, plan), 0)

        negative_cases.append(
            _expect_revert_in_snapshot(
                client,
                plan,
                5,
                "duplicate PoolManager initialization",
                transaction_gas,
                attempts=receipt_attempts,
                interval_seconds=receipt_interval_seconds,
                sleep=sleep,
            )
        )
        negative_cases.append(
            _expect_revert_in_snapshot(
                client,
                plan,
                6,
                "expired PositionManager liquidity deadline",
                transaction_gas,
                before_send=lambda: client.call(
                    "evm_setNextBlockTimestamp",
                    [plan["forkClock"]["liquidityDeadlineUnix"] + 1],
                ),
                attempts=receipt_attempts,
                interval_seconds=receipt_interval_seconds,
                sleep=sleep,
            )
        )

        _, result = _require_success(
            client,
            plan,
            6,
            transaction_gas,
            attempts=receipt_attempts,
            interval_seconds=receipt_interval_seconds,
            sleep=sleep,
        )
        transactions.append(result)
        expected_liquidity = int(price["liquidity"])
        _assert_equal(
            "PositionManager nextTokenId",
            int(
                _contract_call(
                    client,
                    contracts["positionManager"],
                    "nextTokenId()",
                    ["uint256"],
                )
            ),
            next_token_id + 1,
        )
        position_owner = qualifier.normalize_address(
            _contract_call(
                client,
                contracts["positionManager"],
                "ownerOf(uint256)",
                ["address"],
                ["uint256"],
                [next_token_id],
            )
        )
        _assert_equal("liquidity NFT owner", position_owner, actor)
        _assert_equal(
            "PositionManager position liquidity",
            int(
                _contract_call(
                    client,
                    contracts["positionManager"],
                    "getPositionLiquidity(uint256)",
                    ["uint128"],
                    ["uint256"],
                    [next_token_id],
                )
            ),
            expected_liquidity,
        )
        _assert_equal(
            "pool active liquidity", _active_liquidity(client, plan), expected_liquidity
        )
        expected_pltr_delta = int(price["expectedAmount0AtSyntheticPriceRoundedUp"])
        expected_weth_delta = int(price["expectedAmount1AtSyntheticPriceRoundedUp"])
        current_pltr = _balance(client, contracts["pltr"], actor)
        current_weth = _balance(client, contracts["weth"], actor)
        _assert_equal("PLTR liquidity delta", initial_pltr - current_pltr, expected_pltr_delta)
        _assert_equal(
            "WETH liquidity delta",
            initial_weth + wrap_amount - current_weth,
            expected_weth_delta,
        )

        for ordinal, symbol, token in (
            (7, "PLTR", contracts["pltr"]),
            (8, "WETH", contracts["weth"]),
        ):
            _, result = _require_success(
                client,
                plan,
                ordinal,
                transaction_gas,
                attempts=receipt_attempts,
                interval_seconds=receipt_interval_seconds,
                sleep=sleep,
            )
            transactions.append(result)
            amount, _, _ = _permit2_allowance(
                client,
                contracts["permit2"],
                actor,
                token,
                contracts["positionManager"],
            )
            _assert_equal(f"revoked {symbol} Permit2 allowance", amount, 0)

        for ordinal, symbol, token in (
            (9, "PLTR", contracts["pltr"]),
            (10, "WETH", contracts["weth"]),
        ):
            _, result = _require_success(
                client,
                plan,
                ordinal,
                transaction_gas,
                attempts=receipt_attempts,
                interval_seconds=receipt_interval_seconds,
                sleep=sleep,
            )
            transactions.append(result)
            _assert_equal(
                f"revoked {symbol} ERC20 allowance",
                _erc20_allowance(client, token, actor, contracts["permit2"]),
                0,
            )

        for name in ("panopticPool", "collateralTracker0", "collateralTracker1"):
            code = client.call("eth_getCode", [predicted[name], "latest"])
            _assert_equal(f"empty predicted {name}", code, "0x")

        def occupy_create3_proxy() -> None:
            create3_proxy = predicted["create3Proxy"]
            client.call("anvil_setNonce", [create3_proxy, "0x1"])
            client.call("anvil_setCode", [create3_proxy, "0x6000"])
            _assert_equal(
                "injected CREATE3 proxy nonce",
                int(client.call("eth_getTransactionCount", [create3_proxy, "latest"]), 16),
                1,
            )
            _assert_equal(
                "injected CREATE3 proxy code",
                client.call("eth_getCode", [create3_proxy, "latest"]),
                "0x6000",
            )

        negative_cases.append(
            _expect_revert_in_snapshot(
                client,
                plan,
                11,
                "occupied CREATE3 proxy address",
                transaction_gas,
                before_send=occupy_create3_proxy,
                attempts=receipt_attempts,
                interval_seconds=receipt_interval_seconds,
                sleep=sleep,
            )
        )

        market_receipt, result = _require_success(
            client,
            plan,
            11,
            transaction_gas,
            attempts=receipt_attempts,
            interval_seconds=receipt_interval_seconds,
            sleep=sleep,
        )
        transactions.append(result)
        expected_pool = qualifier.normalize_address(predicted["panopticPool"])
        expected_tracker0 = qualifier.normalize_address(predicted["collateralTracker0"])
        expected_tracker1 = qualifier.normalize_address(predicted["collateralTracker1"])
        _assert_equal("factory mapping", _factory_pool(client, plan), expected_pool)
        for name in ("panopticPool", "collateralTracker0", "collateralTracker1"):
            code = client.call("eth_getCode", [predicted[name], "latest"])
            if not isinstance(code, str) or code == "0x":
                raise RuntimeError(f"deployed {name} has empty code")

        event = decode_pool_deployed_event(market_receipt.get("logs", []))
        _assert_equal("PoolDeployed PanopticPool", event["panopticPool"], expected_pool)
        _assert_equal("PoolDeployed PoolId", event["poolId"], plan["market"]["poolId"])
        _assert_equal(
            "PoolDeployed tracker0", event["collateralTracker0"], expected_tracker0
        )
        _assert_equal(
            "PoolDeployed tracker1", event["collateralTracker1"], expected_tracker1
        )
        _assert_equal(
            "PoolDeployed RiskEngine",
            event["riskEngine"],
            qualifier.normalize_address(contracts["riskEngine"]),
        )

        factory_nft_owner = qualifier.normalize_address(
            _contract_call(
                client,
                contracts["panopticFactoryV4"],
                "ownerOf(uint256)",
                ["address"],
                ["uint256"],
                [int(expected_pool, 16)],
            )
        )
        _assert_equal("factory NFT owner", factory_nft_owner, actor)
        for signature, expected in (
            ("collateralToken0()", expected_tracker0),
            ("collateralToken1()", expected_tracker1),
            ("riskEngine()", qualifier.normalize_address(contracts["riskEngine"])),
            ("poolManager()", qualifier.normalize_address(contracts["poolManager"])),
            ("SFPM()", qualifier.normalize_address(contracts["sfpmV4"])),
        ):
            actual = qualifier.normalize_address(
                _contract_call(client, expected_pool, signature, ["address"])
            )
            _assert_equal(f"PanopticPool {signature}", actual, expected)

        for tracker, underlying in (
            (expected_tracker0, contracts["pltr"]),
            (expected_tracker1, contracts["weth"]),
        ):
            for signature, expected in (
                ("panopticPool()", expected_pool),
                ("underlyingToken()", qualifier.normalize_address(underlying)),
                ("riskEngine()", qualifier.normalize_address(contracts["riskEngine"])),
                ("poolManager()", qualifier.normalize_address(contracts["poolManager"])),
            ):
                actual = qualifier.normalize_address(
                    _contract_call(client, tracker, signature, ["address"])
                )
                _assert_equal(f"tracker {tracker} {signature}", actual, expected)

        vegoid = int(
            _contract_call(
                client, contracts["riskEngine"], "vegoid()", ["uint8"]
            )
        )
        sfpm_pool_id = int(
            _contract_call(
                client,
                contracts["sfpmV4"],
                "getPoolId(bytes,uint8)",
                ["uint64"],
                ["bytes", "uint8"],
                [bytes.fromhex(plan["market"]["poolId"][2:]), vegoid],
            )
        )
        if sfpm_pool_id == 0:
            raise RuntimeError("SFPM pool ID was not initialized")
        _assert_equal(
            "PanopticPool SFPM pool ID",
            int(_contract_call(client, expected_pool, "poolId()", ["uint64"])),
            sfpm_pool_id,
        )

        negative_cases.append(
            _expect_revert_in_snapshot(
                client,
                plan,
                11,
                "duplicate Panoptic market registration",
                transaction_gas,
                attempts=receipt_attempts,
                interval_seconds=receipt_interval_seconds,
                sleep=sleep,
            )
        )

        final_nonce = int(
            client.call("eth_getTransactionCount", [actor, "pending"]), 16
        )
        _assert_equal("actor local transaction count", final_nonce, initial_nonce + 12)
        final_native = int(client.call("eth_getBalance", [actor, "latest"]), 16)
        final_pltr = _balance(client, contracts["pltr"], actor)
        final_weth = _balance(client, contracts["weth"], actor)
    finally:
        client.call("anvil_stopImpersonatingAccount", [actor])

    return {
        "schemaVersion": 1,
        "status": "PASS_LOCAL_FORK_MARKET_GENESIS_REHEARSAL",
        "mode": "LOOPBACK_ANVIL_ONLY_NO_KEYS_NO_SIGNING_NO_PUBLIC_BROADCAST",
        "forkIdentity": fork_identity,
        "localCompatibilityBlock": compatibility_block,
        "sourceBindings": {
            "forkPlanBodySha256": plan["forkPlanBodySha256"],
            "forkPlanFileSha256": file_sha256(plan_path),
            "simulatorSha256": file_sha256(Path(__file__)),
        },
        "localFeePolicy": "EIP1559_MAX_FEE_EQUALS_TWICE_LATEST_LOCAL_BASE_FEE_WITH_ZERO_PRIORITY_FEE",
        "initialPreflight": local_preflight,
        "positiveTransactions": transactions,
        "negativeCases": negative_cases,
        "observations": {
            "actorInitialNonce": initial_nonce,
            "actorFinalNonce": final_nonce,
            "actorInitialNativeWei": str(initial_native),
            "actorFinalNativeWei": str(final_native),
            "actorInitialPltr": str(initial_pltr),
            "actorFinalPltr": str(final_pltr),
            "actorInitialWeth": str(initial_weth),
            "actorFinalWeth": str(final_weth),
            "positionManagerTokenId": str(next_token_id),
            "positionLiquidity": str(expected_liquidity),
            "panopticPool": expected_pool,
            "collateralTracker0": expected_tracker0,
            "collateralTracker1": expected_tracker1,
            "sfpmPoolId": str(sfpm_pool_id),
        },
        "publicExecution": {
            "ready": False,
            "blockingReasons": [
                "the exact exposure proposal is not accepted for public execution",
                "fork-only deadlines and null nonces are not an execution plan",
                "no market-specific public operator has been reviewed",
                "no signing or public broadcast authorization exists",
            ],
        },
        "authorization": dict(plan["authorization"]),
        "nextGate": "OWNER_EXPOSURE_DECISION_BEFORE_ANY_EXECUTION_CANDIDATE",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL)
    parser.add_argument("--transaction-gas", default=DEFAULT_TRANSACTION_GAS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        validate_local_rpc_url(args.rpc_url)
        plan = load_json(args.plan)
        report = simulate(
            plan,
            args.plan,
            JsonRpcClient(args.rpc_url),
            transaction_gas=args.transaction_gas,
        )
    except Exception as exc:
        report = {
            "schemaVersion": 1,
            "status": "BLOCKED_LOCAL_FORK_REHEARSAL",
            "mode": "LOOPBACK_ANVIL_ONLY_NO_KEYS_NO_SIGNING_NO_PUBLIC_BROADCAST",
            "error": f"{type(exc).__name__}: {exc}",
            "publicExecution": {"ready": False},
            "authorization": {"signing": False, "publicBroadcast": False},
        }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        f"{args.report}: {report['status']}; "
        "LOOPBACK ONLY, NO KEYS, NO SIGNING, NO PUBLIC BROADCAST"
    )
    return 0 if report["status"] == "PASS_LOCAL_FORK_MARKET_GENESIS_REHEARSAL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
