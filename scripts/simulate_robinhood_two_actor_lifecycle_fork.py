#!/usr/bin/env python3
"""Replay the unsigned two-actor lifecycle proposal on loopback Anvil only.

The simulator accepts only an exact Robinhood testnet fork served from an HTTP
loopback URL and refuses any non-Anvil client. It impersonates the two public
addresses locally, never reads a key, never signs, and has no public RPC
submission path. The output is sanitized: calldata is represented only by its
committed hash.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import ipaddress
import json
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from eth_abi import decode as abi_decode
from eth_abi import encode as abi_encode


REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-lifecycle-proposal-2026-09-11.json"
)
DEFAULT_REPORT = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-lifecycle-fork-rehearsal-2026-09-11.json"
)
DEFAULT_RPC_URL = "http://127.0.0.1:8548"
DEFAULT_TRANSACTION_GAS = "0xf00000"
MAX_TRANSACTION_GAS = 1 << 24


def _load_sibling(name: str, filename: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required sibling module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


genesis_simulator = _load_sibling(
    "stonkhedge_genesis_fork_simulator", "simulate_robinhood_market_fork.py"
)
qualifier = genesis_simulator.qualifier


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON manifest must contain an object: {path}")
    return value


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _all_false(value: Any) -> bool:
    return isinstance(value, dict) and bool(value) and all(
        item is False for item in value.values()
    )


def validate_local_rpc_url(rpc_url: str) -> None:
    parsed = urlparse(rpc_url)
    if parsed.scheme != "http" or not parsed.hostname:
        raise ValueError("simulation RPC must be an HTTP loopback URL")
    if parsed.hostname.lower() != "localhost":
        try:
            if not ipaddress.ip_address(parsed.hostname).is_loopback:
                raise ValueError("simulation RPC must be an HTTP loopback URL")
        except ValueError as exc:
            raise ValueError("simulation RPC must be an HTTP loopback URL") from exc
    if parsed.port is None or parsed.username or parsed.password:
        raise ValueError("simulation RPC must use an explicit port and no credentials")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("simulation RPC must not contain path, query, or fragment")


def validate_plan(plan: dict[str, Any], plan_path: Path) -> None:
    if (
        plan.get("status")
        != "OFFLINE_LIFECYCLE_PROPOSAL_OWNER_ACCEPTANCE_REQUIRED_NO_EXECUTION_AUTHORITY"
    ):
        raise ValueError("plan status is not the unsigned lifecycle proposal")
    if (
        plan.get("mode")
        != "PUBLISHED_SDK_TOKEN_IDS_RUNTIME_BOUND_ROBINHOOD_SWAP_ENCODING_NO_RPC_NO_KEYS_NO_SIGNING_NO_BROADCAST"
    ):
        raise ValueError("plan mode is not the offline runtime-bound encoding mode")
    if plan.get("network", {}).get("chainId") != 46630:
        raise ValueError("plan chain ID drifted")
    if not _all_false(plan.get("authorization")):
        raise ValueError("plan authorization must remain entirely false")
    if plan.get("publicExecution", {}).get("ready") is not False:
        raise ValueError("public execution must remain disabled")
    transactions = plan.get("transactions")
    if not isinstance(transactions, list) or len(transactions) != 25:
        raise ValueError("lifecycle proposal must contain 25 bounded transactions")
    if plan.get("transactionCount") != len(transactions):
        raise ValueError("transaction count drifted")
    required_reverts = plan.get("requiredForkReverts")
    if not isinstance(required_reverts, list) or len(required_reverts) != 4:
        raise ValueError("lifecycle proposal must bind four required fork reverts")
    actors = {
        qualifier.normalize_address(plan["roles"]["writer"]["address"]),
        qualifier.normalize_address(plan["roles"]["buyer"]["address"]),
    }
    if len(actors) != 2:
        raise ValueError("writer and buyer must be distinct")
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
    for ordinal, transaction in enumerate(transactions):
        if transaction.get("ordinal") != ordinal:
            raise ValueError(f"transaction {ordinal} ordering drifted")
        if transaction.get("nonce") is not None:
            raise ValueError(f"transaction {ordinal} unexpectedly binds a nonce")
        if qualifier.normalize_address(transaction.get("sender", "")) not in actors:
            raise ValueError(f"transaction {ordinal} sender is outside the two roles")
        if qualifier.normalize_address(transaction.get("to", "")) not in allowed_targets:
            raise ValueError(f"transaction {ordinal} target is outside the user-call allowlist")
        calldata = transaction.get("calldata", "")
        if not isinstance(calldata, str) or not calldata.startswith("0x"):
            raise ValueError(f"transaction {ordinal} calldata is malformed")
        if "0x" + qualifier.keccak(bytes.fromhex(calldata[2:])).hex() != transaction.get(
            "calldataKeccak256"
        ):
            raise ValueError(f"transaction {ordinal} calldata hash drifted")
    plan_body = dict(plan)
    expected_body_hash = plan_body.pop("planBodySha256", None)
    if expected_body_hash != canonical_sha256(plan_body):
        raise ValueError("plan body hash drifted")

    for name, hash_name in (
        ("genesisManifest", "genesisManifestSha256"),
        ("chainManifest", "chainManifestSha256"),
        ("lifecycleInputs", "lifecycleInputsSha256"),
        ("planner", "plannerSha256"),
        ("robinhoodSwapAdapter", "robinhoodSwapAdapterSha256"),
        ("packageLock", "packageLockSha256"),
    ):
        source = REPOSITORY / plan["sourceBindings"][name]
        if not source.is_file() or file_sha256(source) != plan["sourceBindings"][hash_name]:
            raise ValueError(f"source binding {name} drifted")
    if plan_path.resolve() != DEFAULT_PLAN.resolve() and not plan_path.is_file():
        raise ValueError("plan path does not exist")


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


def _assets(client: Any, tracker: str, account: str) -> int:
    return int(
        _contract_call(
            client,
            tracker,
            "assetsOf(address)",
            ["uint256"],
            ["address"],
            [account],
        )
    )


def _max_withdraw(client: Any, tracker: str, account: str) -> int:
    return int(
        _contract_call(
            client,
            tracker,
            "maxWithdraw(address)",
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


def _number_of_legs(client: Any, pool: str, account: str) -> int:
    return int(
        _contract_call(
            client,
            pool,
            "numberOfLegs(address)",
            ["uint256"],
            ["address"],
            [account],
        )
    )


def _slot0(client: Any, plan: dict[str, Any]) -> tuple[int, int, int, int]:
    values = _contract_call(
        client,
        plan["market"]["stateView"],
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
            plan["market"]["stateView"],
            "getLiquidity(bytes32)",
            ["uint128"],
            ["bytes32"],
            [bytes.fromhex(plan["market"]["poolId"][2:])],
        )
    )


def _premium(
    client: Any, pool: str, account: str, token_id: int
) -> dict[str, Any] | None:
    if _number_of_legs(client, pool, account) == 0:
        return None
    short, long, balances, requirements, net = _contract_call(
        client,
        pool,
        "getFullPositionsData(address,bool,uint256[])",
        ["uint256", "uint256", "uint256[]", "uint256[]", "int256[]"],
        ["address", "bool", "uint256[]"],
        [account, True, [token_id]],
    )
    return {
        "shortPremiumPacked": str(int(short)),
        "longPremiumPacked": str(int(long)),
        "positionBalances": [str(int(value)) for value in balances],
        "collateralRequirementsPacked": [str(int(value)) for value in requirements],
        "netPremiaPacked": [str(int(value)) for value in net],
    }


def observe(client: Any, plan: dict[str, Any]) -> dict[str, Any]:
    market = plan["market"]
    writer = qualifier.normalize_address(plan["roles"]["writer"]["address"])
    buyer = qualifier.normalize_address(plan["roles"]["buyer"]["address"])
    short_id = int(plan["tokenIds"]["shortCall"])
    long_id = int(plan["tokenIds"]["longCall"])

    def actor_state(account: str, token_id: int) -> dict[str, Any]:
        return {
            "nonce": int(client.call("eth_getTransactionCount", [account, "latest"]), 16),
            "nativeBalanceWei": str(int(client.call("eth_getBalance", [account, "latest"]), 16)),
            "pltrBalance": str(_balance(client, market["pltr"], account)),
            "wethBalance": str(_balance(client, market["weth"], account)),
            "tracker0Shares": str(_balance(client, market["collateralTracker0"], account)),
            "tracker0Assets": str(_assets(client, market["collateralTracker0"], account)),
            "tracker0MaxWithdraw": str(
                _max_withdraw(client, market["collateralTracker0"], account)
            ),
            "tracker1Shares": str(_balance(client, market["collateralTracker1"], account)),
            "tracker1Assets": str(_assets(client, market["collateralTracker1"], account)),
            "tracker1MaxWithdraw": str(
                _max_withdraw(client, market["collateralTracker1"], account)
            ),
            "openLegs": _number_of_legs(client, market["panopticPool"], account),
            "pltrToPermit2": str(
                _erc20_allowance(client, market["pltr"], account, market["permit2"])
            ),
            "wethToPermit2": str(
                _erc20_allowance(client, market["weth"], account, market["permit2"])
            ),
            "pltrToTracker0": str(
                _erc20_allowance(
                    client, market["pltr"], account, market["collateralTracker0"]
                )
            ),
            "wethToTracker1": str(
                _erc20_allowance(
                    client, market["weth"], account, market["collateralTracker1"]
                )
            ),
            "pltrPermit2ToRouter": list(
                _permit2_allowance(
                    client,
                    market["permit2"],
                    account,
                    market["pltr"],
                    market["universalRouter"],
                )
            ),
            "wethPermit2ToRouter": list(
                _permit2_allowance(
                    client,
                    market["permit2"],
                    account,
                    market["weth"],
                    market["universalRouter"],
                )
            ),
            "premium": _premium(client, market["panopticPool"], account, token_id),
        }

    sqrt_price, tick, protocol_fee, lp_fee = _slot0(client, plan)
    return {
        "blockNumber": int(client.call("eth_blockNumber", []), 16),
        "pool": {
            "sqrtPriceX96": str(sqrt_price),
            "tick": tick,
            "protocolFee": protocol_fee,
            "lpFee": lp_fee,
            "activeLiquidity": str(_active_liquidity(client, plan)),
        },
        "writer": actor_state(writer, short_id),
        "buyer": actor_state(buyer, long_id),
    }


def _runtime_identity(client: Any, address: str) -> dict[str, Any]:
    code = client.call("eth_getCode", [address, "latest"])
    if not isinstance(code, str) or not code.startswith("0x"):
        raise RuntimeError(f"runtime code response is malformed for {address}")
    return qualifier.code_identity(code)


def _computed_pool_id(plan: dict[str, Any]) -> str:
    key = plan["market"]["poolKey"]
    encoded = abi_encode(
        ["address", "address", "uint24", "int24", "address"],
        [
            key["currency0"],
            key["currency1"],
            int(key["fee"]),
            int(key["tickSpacing"]),
            key["hooks"],
        ],
    )
    return "0x" + qualifier.keccak(encoded).hex()


def observe_external_state(client: Any, plan: dict[str, Any]) -> dict[str, Any]:
    """Read the identities and controls that can invalidate a safe replay."""

    market = plan["market"]
    genesis = load_json(REPOSITORY / plan["sourceBindings"]["genesisManifest"])
    chain = load_json(REPOSITORY / plan["sourceBindings"]["chainManifest"])
    registered = genesis["registeredMarket"]
    registry = market["stockRegistry"]
    pltr = market["pltr"]
    writer = qualifier.normalize_address(plan["roles"]["writer"]["address"])
    buyer = qualifier.normalize_address(plan["roles"]["buyer"]["address"])

    runtime_addresses = {
        "stockRegistry": registry,
        "pltr": pltr,
        "weth": market["weth"],
        "permit2": market["permit2"],
        "universalRouter": market["universalRouter"],
        "stateView": market["stateView"],
        "panopticPool": market["panopticPool"],
        "collateralTracker0": market["collateralTracker0"],
        "collateralTracker1": market["collateralTracker1"],
    }
    runtimes = {
        name: {"address": qualifier.normalize_address(address), **_runtime_identity(client, address)}
        for name, address in runtime_addresses.items()
    }

    def call_address(to: str, signature: str) -> str:
        return qualifier.normalize_address(
            _contract_call(client, to, signature, ["address"])
        )

    return {
        "chainId": int(client.call("eth_chainId", []), 16),
        "computedPoolId": _computed_pool_id(plan),
        "runtimes": runtimes,
        "expectedRuntimes": {
            "stockRegistry": {
                "runtimeBytes": chain["sharedStockInfrastructure"]["registryRuntimeBytes"],
                "runtimeCodeHash": chain["sharedStockInfrastructure"]["registryRuntimeCodeHash"],
            },
            "pltr": {
                "runtimeBytes": chain["sharedStockInfrastructure"]["proxyRuntimeBytes"],
                "runtimeCodeHash": chain["sharedStockInfrastructure"]["proxyRuntimeCodeHash"],
            },
            "weth": {
                "runtimeBytes": chain["quoteAssets"]["weth"]["runtimeBytes"],
                "runtimeCodeHash": chain["quoteAssets"]["weth"]["runtimeCodeHash"],
            },
            "permit2": {
                "runtimeBytes": chain["infrastructure"]["permit2"]["runtimeBytes"],
                "runtimeCodeHash": chain["infrastructure"]["permit2"]["runtimeCodeHash"],
            },
            "universalRouter": {
                "runtimeBytes": chain["infrastructure"]["universalRouter"]["runtimeBytes"],
                "runtimeCodeHash": chain["infrastructure"]["universalRouter"]["runtimeCodeHash"],
            },
            "stateView": {
                "runtimeBytes": chain["infrastructure"]["stateView"]["runtimeBytes"],
                "runtimeCodeHash": chain["infrastructure"]["stateView"]["runtimeCodeHash"],
            },
            "panopticPool": {
                "runtimeBytes": registered["panopticPool"]["runtimeBytes"],
                "runtimeCodeHash": registered["panopticPool"]["runtimeKeccak256"],
            },
            "collateralTracker0": {
                "runtimeBytes": registered["collateralTracker0"]["runtimeBytes"],
                "runtimeCodeHash": registered["collateralTracker0"]["runtimeKeccak256"],
            },
            "collateralTracker1": {
                "runtimeBytes": registered["collateralTracker1"]["runtimeBytes"],
                "runtimeCodeHash": registered["collateralTracker1"]["runtimeKeccak256"],
            },
        },
        "stockControls": {
            "registryPaused": bool(_contract_call(client, registry, "paused()", ["bool"])),
            "tokenPaused": bool(_contract_call(client, pltr, "tokenPaused()", ["bool"])),
            "uiMultiplier": str(_contract_call(client, pltr, "uiMultiplier()", ["uint256"])),
            "newUIMultiplier": str(
                _contract_call(client, pltr, "newUIMultiplier()", ["uint256"])
            ),
            "effectiveAt": str(_contract_call(client, pltr, "effectiveAt()", ["uint256"])),
            "writerBlocked": bool(
                _contract_call(
                    client,
                    registry,
                    "isBlocked(address)",
                    ["bool"],
                    ["address"],
                    [writer],
                )
            ),
            "buyerBlocked": bool(
                _contract_call(
                    client,
                    registry,
                    "isBlocked(address)",
                    ["bool"],
                    ["address"],
                    [buyer],
                )
            ),
        },
        "wiring": {
            "pltrRegistry": call_address(pltr, "ACCESS_CONTROLLED_REGISTRY()"),
            "panopticPoolCollateral0": call_address(
                market["panopticPool"], "collateralToken0()"
            ),
            "panopticPoolCollateral1": call_address(
                market["panopticPool"], "collateralToken1()"
            ),
            "panopticPoolManager": call_address(market["panopticPool"], "poolManager()"),
            "panopticPoolRiskEngine": call_address(market["panopticPool"], "riskEngine()"),
            "panopticPoolSfpm": call_address(market["panopticPool"], "SFPM()"),
            "panopticPoolNumericId": str(
                _contract_call(client, market["panopticPool"], "poolId()", ["uint64"])
            ),
            "tracker0Pool": call_address(market["collateralTracker0"], "panopticPool()"),
            "tracker0Underlying": call_address(
                market["collateralTracker0"], "underlyingToken()"
            ),
            "tracker1Pool": call_address(market["collateralTracker1"], "panopticPool()"),
            "tracker1Underlying": call_address(
                market["collateralTracker1"], "underlyingToken()"
            ),
        },
        "expectedWiring": {
            "pltrRegistry": qualifier.normalize_address(registry),
            "panopticPoolCollateral0": qualifier.normalize_address(
                market["collateralTracker0"]
            ),
            "panopticPoolCollateral1": qualifier.normalize_address(
                market["collateralTracker1"]
            ),
            "panopticPoolManager": qualifier.normalize_address(
                registered["panopticPool"]["poolManager"]
            ),
            "panopticPoolRiskEngine": qualifier.normalize_address(
                registered["panopticPool"]["riskEngine"]
            ),
            "panopticPoolSfpm": qualifier.normalize_address(
                registered["panopticPool"]["sfpmV4"]
            ),
            "panopticPoolNumericId": str(market["sfpmPoolId"]),
            "tracker0Pool": qualifier.normalize_address(market["panopticPool"]),
            "tracker0Underlying": qualifier.normalize_address(market["pltr"]),
            "tracker1Pool": qualifier.normalize_address(market["panopticPool"]),
            "tracker1Underlying": qualifier.normalize_address(market["weth"]),
        },
        "requiredStockState": {
            "registryPaused": False,
            "tokenPaused": False,
            "uiMultiplier": str(chain["requiredStockState"]["uiMultiplier"]),
            "newUIMultiplier": str(chain["requiredStockState"]["newUiMultiplier"]),
            "effectiveAt": str(chain["requiredStockState"]["effectiveAt"]),
            "writerBlocked": False,
            "buyerBlocked": False,
        },
    }


def _assert_external_state(plan: dict[str, Any], state: dict[str, Any]) -> None:
    if state["chainId"] != plan["network"]["chainId"]:
        raise RuntimeError("external chain ID drifted")
    if state["computedPoolId"].lower() != plan["market"]["poolId"].lower():
        raise RuntimeError("external PoolId drifted")
    for name, expected in state["expectedRuntimes"].items():
        actual = state["runtimes"][name]
        if (
            actual["runtimeBytes"] != expected["runtimeBytes"]
            or actual["runtimeCodeHash"].lower() != expected["runtimeCodeHash"].lower()
        ):
            raise RuntimeError(f"external {name} runtime identity drifted")
    for name, expected in state["expectedWiring"].items():
        if str(state["wiring"][name]).lower() != str(expected).lower():
            raise RuntimeError(f"external {name} immutable wiring drifted")
    for name, expected in state["requiredStockState"].items():
        if str(state["stockControls"][name]).lower() != str(expected).lower():
            raise RuntimeError(f"external Stock Token control {name} drifted")


def assert_exact_fork(plan: dict[str, Any], client: Any) -> dict[str, Any]:
    version = client.call("web3_clientVersion", [])
    if not isinstance(version, str) or "anvil" not in version.lower():
        raise RuntimeError(f"refusing non-Anvil client: {version}")
    chain_id = int(client.call("eth_chainId", []), 16)
    if chain_id != 46630:
        raise RuntimeError(f"fork chain ID mismatch: {chain_id}")
    block = client.call("eth_getBlockByNumber", ["latest", False])
    if not isinstance(block, dict):
        raise RuntimeError("fork latest block response is malformed")
    if int(block["number"], 16) != plan["network"]["referenceBlock"]:
        raise RuntimeError("fork block number drifted")
    if block["hash"].lower() != plan["network"]["referenceBlockHash"].lower():
        raise RuntimeError("fork block hash drifted")
    if int(block["timestamp"], 16) != plan["network"]["referenceTimestampUnix"]:
        raise RuntimeError("fork block timestamp drifted")
    return {
        "clientVersion": version,
        "chainId": chain_id,
        "forkBlock": int(block["number"], 16),
        "forkBlockHash": block["hash"].lower(),
        "forkTimestampUnix": int(block["timestamp"], 16),
    }


def mine_compatibility_block(plan: dict[str, Any], client: Any) -> dict[str, Any]:
    timestamp = plan["network"]["referenceTimestampUnix"] + 1
    client.call("evm_setNextBlockTimestamp", [timestamp])
    client.call("evm_mine", [])
    block = client.call("eth_getBlockByNumber", ["latest", False])
    if block["parentHash"].lower() != plan["network"]["referenceBlockHash"].lower():
        raise RuntimeError("local compatibility block parent drifted")
    return {
        "blockNumber": int(block["number"], 16),
        "blockHash": block["hash"].lower(),
        "timestampUnix": int(block["timestamp"], 16),
    }


def _poll_receipt(
    client: Any,
    transaction_hash: str,
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


def send_local(
    client: Any,
    transaction: dict[str, Any],
    gas: str,
    *,
    attempts: int = 300,
    interval_seconds: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    gas_value = int(gas, 16)
    if gas_value <= 0 or gas_value >= MAX_TRANSACTION_GAS:
        raise ValueError("transaction gas must be positive and below 2^24")
    latest = client.call("eth_getBlockByNumber", ["latest", False])
    base_fee = int(latest["baseFeePerGas"], 16)
    request = {
        "from": transaction["sender"],
        "to": transaction["to"],
        "value": hex(int(transaction["valueWei"])),
        "data": transaction["calldata"],
        "gas": gas,
        "maxFeePerGas": hex(max(1, base_fee * 2)),
        "maxPriorityFeePerGas": "0x0",
    }
    transaction_hash = client.call("eth_sendTransaction", [request])
    receipt = _poll_receipt(
        client, transaction_hash, attempts, interval_seconds, sleep
    )
    if receipt.get("status") != "0x1":
        raise RuntimeError(
            f"loopback transaction {transaction['ordinal']} reverted: {transaction_hash}"
        )
    return receipt


def expect_local_revert(
    client: Any,
    transaction: dict[str, Any],
    name: str,
    gas: str,
    *,
    before_send: Callable[[], None] | None = None,
    attempts: int = 300,
    interval_seconds: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    snapshot = client.call("evm_snapshot", [])
    try:
        if before_send is not None:
            before_send()
        gas_value = int(gas, 16)
        if gas_value <= 0 or gas_value >= MAX_TRANSACTION_GAS:
            raise ValueError("transaction gas must be positive and below 2^24")
        latest = client.call("eth_getBlockByNumber", ["latest", False])
        request = {
            "from": transaction["sender"],
            "to": transaction["to"],
            "value": hex(int(transaction["valueWei"])),
            "data": transaction["calldata"],
            "gas": gas,
            "maxFeePerGas": hex(max(1, int(latest["baseFeePerGas"], 16) * 2)),
            "maxPriorityFeePerGas": "0x0",
        }
        transaction_hash = client.call("eth_sendTransaction", [request])
        receipt = _poll_receipt(
            client, transaction_hash, attempts, interval_seconds, sleep
        )
        if receipt.get("status") != "0x0":
            raise RuntimeError(f"negative case unexpectedly succeeded: {name}")
        return {
            "name": name,
            "status": "PASS_REVERTED",
            "transactionHash": transaction_hash.lower(),
            "blockNumber": int(receipt["blockNumber"], 16),
            "gasUsed": int(receipt["gasUsed"], 16),
        }
    finally:
        if client.call("evm_revert", [snapshot]) is not True:
            raise RuntimeError(f"could not restore snapshot after negative case: {name}")


def with_zero_effective_liquidity_limit(transaction: dict[str, Any]) -> dict[str, Any]:
    calldata = bytes.fromhex(transaction["calldata"][2:])
    argument_types = [
        "uint256[]",
        "uint256[]",
        "uint128[]",
        "int24[3][]",
        "bool",
        "uint256",
    ]
    values = list(abi_decode(argument_types, calldata[4:]))
    limits = [list(limit) for limit in values[3]]
    if len(limits) != 1:
        raise RuntimeError("buyer long negative vector expected one spread tuple")
    limits[0][2] = 0
    values[3] = limits
    mutated = dict(transaction)
    mutated["calldata"] = "0x" + (calldata[:4] + abi_encode(argument_types, values)).hex()
    return mutated


def receipt_summary(
    transaction: dict[str, Any], receipt: dict[str, Any]
) -> dict[str, Any]:
    return {
        "ordinal": transaction["ordinal"],
        "phase": transaction["phase"],
        "sender": qualifier.normalize_address(transaction["sender"]),
        "label": transaction["label"],
        "to": qualifier.normalize_address(transaction["to"]),
        "valueWei": transaction["valueWei"],
        "calldataKeccak256": transaction["calldataKeccak256"],
        "transactionHash": receipt["transactionHash"].lower(),
        "blockNumber": int(receipt["blockNumber"], 16),
        "blockHash": receipt["blockHash"].lower(),
        "gasUsed": int(receipt["gasUsed"], 16),
        "status": "PASS",
    }


def _assert_initial_state(plan: dict[str, Any], state: dict[str, Any]) -> None:
    for role in ("writer", "buyer"):
        expected = plan["roles"][role]
        actual = state[role]
        for name, expected_name in (
            ("nonce", "confirmedNonce"),
            ("nativeBalanceWei", "nativeBalanceWei"),
            ("pltrBalance", "pltrBalance"),
            ("wethBalance", "wethBalance"),
            ("tracker0Shares", "collateralTracker0Shares"),
            ("tracker1Shares", "collateralTracker1Shares"),
            ("openLegs", "openLegs"),
        ):
            if str(actual[name]) != str(expected[expected_name]):
                raise RuntimeError(f"initial {role} {name} drifted")
        for name in (
            "pltrToPermit2",
            "wethToPermit2",
            "pltrToTracker0",
            "wethToTracker1",
        ):
            if actual[name] != "0":
                raise RuntimeError(f"initial {role} {name} allowance is elevated")
        if actual["pltrPermit2ToRouter"][0] != 0:
            raise RuntimeError(f"initial {role} PLTR Permit2 allowance is elevated")
        if actual["wethPermit2ToRouter"][0] != 0:
            raise RuntimeError(f"initial {role} WETH Permit2 allowance is elevated")
    if state["pool"]["tick"] != plan["market"]["referenceTick"]:
        raise RuntimeError("initial pool tick drifted")
    if state["pool"]["activeLiquidity"] != plan["market"]["referenceActiveLiquidity"]:
        raise RuntimeError("initial active liquidity drifted")


def _expect_preflight_rejection(name: str, check: Callable[[], None]) -> dict[str, Any]:
    try:
        check()
    except RuntimeError as exc:
        return {
            "name": name,
            "status": "PASS_REJECTED_BY_FAIL_CLOSED_PREFLIGHT",
            "reason": str(exc),
        }
    raise RuntimeError(f"adverse preflight mutation unexpectedly passed: {name}")


def rehearse_adverse_preflight_rejections(
    plan: dict[str, Any],
    external: dict[str, Any],
    initial: dict[str, Any],
) -> list[dict[str, Any]]:
    """Prove the verifier rejects representative external-state drift.

    These mutations affect only in-memory copies of read-only observations. They
    do not call an administrator, alter the fork, or broaden transaction scope.
    """

    cases: list[dict[str, Any]] = []

    def external_case(name: str, mutate: Callable[[dict[str, Any]], None]) -> None:
        changed = copy.deepcopy(external)
        mutate(changed)
        cases.append(
            _expect_preflight_rejection(
                name, lambda: _assert_external_state(plan, changed)
            )
        )

    def initial_case(name: str, mutate: Callable[[dict[str, Any]], None]) -> None:
        changed = copy.deepcopy(initial)
        mutate(changed)
        cases.append(
            _expect_preflight_rejection(name, lambda: _assert_initial_state(plan, changed))
        )

    external_case(
        "wrong PoolId",
        lambda state: state.__setitem__("computedPoolId", "0x" + "00" * 32),
    )
    external_case(
        "runtime bytecode drift",
        lambda state: state["runtimes"]["panopticPool"].__setitem__(
            "runtimeCodeHash", "0x" + "11" * 32
        ),
    )
    external_case(
        "immutable wiring drift",
        lambda state: state["wiring"].__setitem__(
            "tracker0Underlying", state["expectedWiring"]["tracker1Underlying"]
        ),
    )
    external_case(
        "Stock registry paused",
        lambda state: state["stockControls"].__setitem__("registryPaused", True),
    )
    external_case(
        "writer blocked by Stock registry",
        lambda state: state["stockControls"].__setitem__("writerBlocked", True),
    )
    external_case(
        "Stock Token UI multiplier drift",
        lambda state: state["stockControls"].__setitem__(
            "uiMultiplier", str(int(state["requiredStockState"]["uiMultiplier"]) + 1)
        ),
    )
    initial_case(
        "writer balance below frozen PLTR snapshot",
        lambda state: state["writer"].__setitem__(
            "pltrBalance", str(int(plan["roles"]["writer"]["pltrBalance"]) - 1)
        ),
    )
    initial_case(
        "elevated buyer tracker allowance",
        lambda state: state["buyer"].__setitem__("pltrToTracker0", "1"),
    )
    return cases


def assert_swap_postconditions(
    plan: dict[str, Any],
    transaction: dict[str, Any],
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    intent = transaction["decodedIntent"]
    if intent.get("route") != "UNISWAP_V4_EXACT_INPUT_SINGLE":
        raise ValueError("transaction is not a bounded Robinhood V4 swap")
    sender = qualifier.normalize_address(transaction["sender"])
    role = next(
        name
        for name in ("writer", "buyer")
        if qualifier.normalize_address(plan["roles"][name]["address"]) == sender
    )
    amount_in = int(intent["amountIn"])
    minimum_out = int(intent["amountOutMinimum"])
    if intent["zeroForOne"]:
        spent = int(before[role]["pltrBalance"]) - int(after[role]["pltrBalance"])
        received = int(after[role]["wethBalance"]) - int(before[role]["wethBalance"])
    else:
        spent = int(before[role]["wethBalance"]) - int(after[role]["wethBalance"])
        received = int(after[role]["pltrBalance"]) - int(before[role]["pltrBalance"])
    if spent != amount_in:
        raise RuntimeError(
            f"swap index {transaction['ordinal']} input spend mismatch"
        )
    if received < minimum_out:
        raise RuntimeError(
            f"swap index {transaction['ordinal']} output below committed minimum"
        )
    return {
        "ordinal": transaction["ordinal"],
        "status": "PASS_EXACT_INPUT_AND_MINIMUM_OUTPUT",
        "amountIn": str(amount_in),
        "actualInputSpent": str(spent),
        "amountOutMinimum": str(minimum_out),
        "actualOutputReceived": str(received),
    }


def simulate(
    plan: dict[str, Any],
    plan_path: Path,
    client: Any,
    *,
    transaction_gas: str = DEFAULT_TRANSACTION_GAS,
) -> dict[str, Any]:
    validate_plan(plan, plan_path)
    fork = assert_exact_fork(plan, client)
    compatibility = mine_compatibility_block(plan, client)
    external = observe_external_state(client, plan)
    _assert_external_state(plan, external)
    before = observe(client, plan)
    _assert_initial_state(plan, before)
    adverse_preflight = rehearse_adverse_preflight_rejections(
        plan, external, before
    )

    writer = qualifier.normalize_address(plan["roles"]["writer"]["address"])
    buyer = qualifier.normalize_address(plan["roles"]["buyer"]["address"])
    for actor in (writer, buyer):
        client.call("anvil_impersonateAccount", [actor])

    receipts: list[dict[str, Any]] = []
    negative_cases: list[dict[str, Any]] = []
    swap_postconditions: list[dict[str, Any]] = []
    milestones: dict[str, Any] = {"initial": before}
    try:
        negative_cases.append(
            expect_local_revert(
                client,
                plan["transactions"][15],
                plan["requiredForkReverts"][0],
                transaction_gas,
            )
        )
        for transaction in plan["transactions"]:
            swap_before = (
                observe(client, plan)
                if transaction["decodedIntent"].get("route")
                == "UNISWAP_V4_EXACT_INPUT_SINGLE"
                else None
            )
            receipt = send_local(client, transaction, transaction_gas)
            receipts.append(receipt_summary(transaction, receipt))
            if swap_before is not None:
                swap_after = observe(client, plan)
                swap_postconditions.append(
                    assert_swap_postconditions(
                        plan, transaction, swap_before, swap_after
                    )
                )
            ordinal = transaction["ordinal"]
            if ordinal == 4:
                negative_cases.append(
                    expect_local_revert(
                        client,
                        plan["transactions"][5],
                        plan["requiredForkReverts"][1],
                        transaction_gas,
                        before_send=lambda: client.call(
                            "evm_setNextBlockTimestamp",
                            [plan["exposureCaps"]["rehearsalOnlyExpiry"]["unix"] + 1],
                        ),
                    )
                )
            if ordinal == 15:
                negative_cases.append(
                    expect_local_revert(
                        client,
                        with_zero_effective_liquidity_limit(
                            plan["transactions"][16]
                        ),
                        plan["requiredForkReverts"][2],
                        transaction_gas,
                    )
                )
            if ordinal == 18:
                negative_cases.append(
                    expect_local_revert(
                        client,
                        plan["transactions"][20],
                        plan["requiredForkReverts"][3],
                        transaction_gas,
                    )
                )
            if ordinal in (6, 14, 16, 18, 20, 24):
                milestones[f"afterIndex{ordinal}"] = observe(client, plan)
    finally:
        for actor in (writer, buyer):
            client.call("anvil_stopImpersonatingAccount", [actor])

    final = milestones["afterIndex24"]
    if final["writer"]["openLegs"] != 0 or final["buyer"]["openLegs"] != 0:
        raise RuntimeError("terminal open-leg cleanup failed")
    for name in (
        "pltrToPermit2",
        "wethToPermit2",
        "pltrToTracker0",
        "wethToTracker1",
    ):
        if final["writer"][name] != "0" or final["buyer"][name] != "0":
            raise RuntimeError(f"terminal ERC20 allowance cleanup failed for {name}")
    if final["writer"]["pltrPermit2ToRouter"][0] != 0:
        raise RuntimeError("terminal PLTR Permit2 allowance is not zero")
    if final["writer"]["wethPermit2ToRouter"][0] != 0:
        raise RuntimeError("terminal WETH Permit2 allowance is not zero")

    premium_before = milestones["afterIndex16"]
    premium_after = milestones["afterIndex18"]
    premium_changed = (
        premium_before["writer"]["premium"] != premium_after["writer"]["premium"]
        or premium_before["buyer"]["premium"] != premium_after["buyer"]["premium"]
    )

    return {
        "schemaVersion": 1,
        "status": "PASS_LOOPBACK_TWO_ACTOR_LIFECYCLE_THROUGH_CLOSE_WITHDRAWAL_DEFERRED",
        "mode": "EXACT_ROBINHOOD_FORK_LOOPBACK_ANVIL_IMPERSONATION_NO_KEYS_NO_SIGNING_NO_PUBLIC_BROADCAST",
        "classification": plan["classification"],
        "sourceBindings": {
            "lifecyclePlanBodySha256": plan["planBodySha256"],
            "lifecyclePlanFileSha256": file_sha256(plan_path),
            "simulatorSha256": file_sha256(Path(__file__)),
        },
        "fork": fork,
        "localCompatibilityBlock": compatibility,
        "externalState": external,
        "adversePreflightRejections": adverse_preflight,
        "transactions": receipts,
        "swapPostconditions": swap_postconditions,
        "milestones": milestones,
        "premiumObservationChanged": premium_changed,
        "negativeCases": {
            "completed": negative_cases,
            "remaining": plan["negativeRehearsalCases"],
        },
        "withdrawal": {
            "executed": False,
            "reason": plan["postCloseContinuation"]["reason"],
            "next": plan["postCloseContinuation"]["requiredSteps"],
        },
        "authorization": plan["authorization"],
        "publicExecution": {"ready": False, "broadcastAttempted": False},
        "nextGate": "REVIEW_REHEARSAL_AND_REBIND_POST_CLOSE_WITHDRAWALS_BEFORE_ANY_PUBLIC_AUTHORIZATION",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--transaction-gas", default=DEFAULT_TRANSACTION_GAS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_local_rpc_url(args.rpc_url)
    plan = load_json(args.plan)
    client = genesis_simulator.JsonRpcClient(args.rpc_url)
    report = simulate(
        plan,
        args.plan,
        client,
        transaction_gas=args.transaction_gas,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "report": str(args.report),
                "transactions": len(report["transactions"]),
                "premiumObservationChanged": report["premiumObservationChanged"],
                "signing": False,
                "publicBroadcast": False,
                "nextGate": report["nextGate"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
