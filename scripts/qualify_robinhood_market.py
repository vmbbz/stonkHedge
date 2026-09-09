#!/usr/bin/env python3
"""Qualify Robinhood testnet Stock Token/WETH market candidates read-only.

This tool deliberately has no private-key, keystore, signing, transaction
construction, or broadcast path. It pins all state reads to one block, derives
the exact no-hook Uniswap V4 PoolKeys and PoolIds, and reports whether a first
market is technically eligible for owner review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from eth_abi import decode as abi_decode
from eth_abi import encode as abi_encode
from eth_utils import keccak


CHAIN_ID = 46630
DEFAULT_FEE = 3_000
DEFAULT_TICK_SPACING = 60
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
READ_ONLY_RPC_METHODS = frozenset(
    {
        "eth_chainId",
        "eth_blockNumber",
        "eth_getBlockByNumber",
        "eth_getCode",
        "eth_call",
        "eth_getBalance",
        "eth_getTransactionCount",
    }
)


class QualificationError(RuntimeError):
    """Raised when qualification cannot produce trustworthy evidence."""


def require_read_only_method(method: str) -> None:
    if method not in READ_ONLY_RPC_METHODS:
        raise ValueError(f"RPC method is not read-only or allowlisted: {method}")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_address(value: str, name: str = "address") -> str:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 42:
        raise ValueError(f"{name} must be a 20-byte hex address")
    try:
        bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ValueError(f"{name} must be a 20-byte hex address") from exc
    return value.lower()


def function_selector(signature: str) -> bytes:
    return keccak(text=signature)[:4]


def encode_call(
    signature: str, argument_types: Iterable[str] = (), arguments=()
) -> str:
    return (
        "0x"
        + (
            function_selector(signature)
            + abi_encode(list(argument_types), list(arguments))
        ).hex()
    )


def pool_key_for(
    stock: str,
    weth: str,
    *,
    fee: int = DEFAULT_FEE,
    tick_spacing: int = DEFAULT_TICK_SPACING,
    hooks: str = ZERO_ADDRESS,
) -> dict[str, Any]:
    stock_normalized = normalize_address(stock, "stock")
    weth_normalized = normalize_address(weth, "WETH")
    hooks_normalized = normalize_address(hooks, "hooks")
    if stock_normalized == weth_normalized:
        raise ValueError("stock and WETH must be different currencies")
    if not 0 <= fee < 2**24:
        raise ValueError("fee must fit uint24")
    if not -(2**23) <= tick_spacing < 2**23 or tick_spacing == 0:
        raise ValueError("tick spacing must be a non-zero int24")
    currency0, currency1 = sorted((stock_normalized, weth_normalized))
    return {
        "currency0": currency0,
        "currency1": currency1,
        "fee": fee,
        "tickSpacing": tick_spacing,
        "hooks": hooks_normalized,
        "stockIsCurrency0": stock_normalized == currency0,
    }


def encode_pool_key(pool_key: dict[str, Any]) -> bytes:
    return abi_encode(
        ["address", "address", "uint24", "int24", "address"],
        [
            pool_key["currency0"],
            pool_key["currency1"],
            pool_key["fee"],
            pool_key["tickSpacing"],
            pool_key["hooks"],
        ],
    )


def pool_id_for(pool_key: dict[str, Any]) -> str:
    return "0x" + keccak(encode_pool_key(pool_key)).hex()


def code_identity(code: str) -> dict[str, Any]:
    if not isinstance(code, str) or not code.startswith("0x") or len(code) % 2 != 0:
        raise QualificationError("eth_getCode returned invalid hex bytes")
    try:
        raw = bytes.fromhex(code[2:])
    except ValueError as exc:
        raise QualificationError("eth_getCode returned invalid hex bytes") from exc
    return {"runtimeBytes": len(raw), "runtimeCodeHash": "0x" + keccak(raw).hex()}


def assess_candidate(candidate: dict[str, Any]) -> list[str]:
    """Return deterministic blockers for one already-observed candidate."""

    blockers: list[str] = []
    if not candidate.get("runtimeIdentityMatches"):
        blockers.append("STOCK_RUNTIME_IDENTITY_DRIFT")
    if candidate.get("paused") is not False:
        blockers.append("STOCK_GLOBAL_PAUSED_OR_UNREADABLE")
    if candidate.get("tokenPaused") is not False:
        blockers.append("STOCK_TOKEN_PAUSED_OR_UNREADABLE")
    if not candidate.get("multiplierStateMatches"):
        blockers.append("STOCK_MULTIPLIER_STATE_DRIFT")
    if not candidate.get("registryWiringMatches"):
        blockers.append("STOCK_REGISTRY_WIRING_DRIFT")
    if int(candidate.get("deployerBalance", "0")) <= 0:
        blockers.append("DEPLOYER_HAS_NO_STOCK_BALANCE")
    if int(candidate.get("actorBalance", "0")) <= 0:
        blockers.append("SECOND_ACTOR_HAS_NO_STOCK_BALANCE")
    if candidate.get("deployerBlocked") is not False:
        blockers.append("DEPLOYER_BLOCKED_OR_UNREADABLE")
    if candidate.get("actorBlocked") is not False:
        blockers.append("SECOND_ACTOR_BLOCKED_OR_UNREADABLE")
    if candidate.get("poolInitialized") is not False:
        blockers.append("V4_POOL_ALREADY_INITIALIZED_OR_UNREADABLE")
    if (
        normalize_address(
            candidate.get("existingPanopticPool", ZERO_ADDRESS),
            "existing Panoptic pool",
        )
        != ZERO_ADDRESS
    ):
        blockers.append("PANOPTIC_MARKET_ALREADY_REGISTERED")
    return blockers


def recommend_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Prefer an eligible stock-as-currency0 pair, retaining manifest order."""

    eligible = [candidate for candidate in candidates if candidate.get("eligible")]
    if not eligible:
        return None
    ranked = sorted(
        enumerate(eligible),
        key=lambda item: (not bool(item[1]["poolKey"]["stockIsCurrency0"]), item[0]),
    )
    selected = ranked[0][1]
    return {
        "symbol": selected["symbol"],
        "stockToken": selected["stockToken"],
        "poolId": selected["poolId"],
        "accepted": False,
        "status": "RECOMMENDED_OWNER_ACCEPTANCE_REQUIRED",
        "basis": (
            "Eligible Stock Token sorts as currency0 and WETH as currency1, preserving "
            "the stock/WETH base-quote orientation and reducing adapter and UI inversion risk."
            if selected["poolKey"]["stockIsCurrency0"]
            else "First eligible candidate in the reviewed chain-manifest order."
        ),
        "excludedBasis": "Ticker popularity, market capitalization, and investment merit were not used.",
    }


class ReadOnlyRpc:
    def __init__(self, url: str, *, timeout_seconds: float = 20.0, attempts: int = 6):
        self.url = url
        self.timeout_seconds = timeout_seconds
        self.attempts = attempts
        self._request_id = 0

    def call(self, method: str, params: list[Any]) -> Any:
        require_read_only_method(method)
        self._request_id += 1
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": method,
                "params": params,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "stonkHedge-market-qualifier/1",
            },
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self.attempts):
            try:
                with urllib.request.urlopen(
                    request, timeout=self.timeout_seconds
                ) as response:
                    decoded = json.loads(response.read().decode("utf-8"))
                if decoded.get("error") is not None:
                    raise QualificationError(
                        f"RPC {method} failed: {decoded['error'].get('message', decoded['error'])}"
                    )
                if "result" not in decoded:
                    raise QualificationError(f"RPC {method} omitted result")
                return decoded["result"]
            except (
                urllib.error.HTTPError,
                urllib.error.URLError,
                TimeoutError,
                QualificationError,
            ) as exc:
                last_error = exc
                if attempt + 1 == self.attempts:
                    break
                time.sleep(min(2**attempt, 8))
        raise QualificationError(
            f"RPC {method} remained unavailable after {self.attempts} attempts: {last_error}"
        )


class CastReadOnlyRpc:
    """Use Foundry's TLS transport while retaining the same method allowlist."""

    def __init__(self, url: str, *, timeout_seconds: float = 45.0, attempts: int = 6):
        self.url = url
        self.timeout_seconds = timeout_seconds
        self.attempts = attempts

    def call(self, method: str, params: list[Any]) -> Any:
        require_read_only_method(method)
        command = [
            "cast",
            "rpc",
            method,
            json.dumps(params, separators=(",", ":")),
            "--raw",
            "--rpc-url",
            self.url,
            "--rpc-timeout",
            str(int(self.timeout_seconds)),
        ]
        last_error: Exception | None = None
        for attempt in range(self.attempts):
            try:
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=self.timeout_seconds + 5,
                )
                return json.loads(completed.stdout.strip())
            except (
                FileNotFoundError,
                json.JSONDecodeError,
                subprocess.CalledProcessError,
                subprocess.TimeoutExpired,
            ) as exc:
                last_error = exc
                if isinstance(exc, FileNotFoundError) or attempt + 1 == self.attempts:
                    break
                time.sleep(min(2**attempt, 8))
        detail = last_error
        if isinstance(last_error, subprocess.CalledProcessError):
            detail = (last_error.stderr or last_error.stdout or str(last_error)).strip()
        raise QualificationError(
            f"cast RPC {method} remained unavailable after {self.attempts} attempts: {detail}"
        )


def contract_call(
    rpc: ReadOnlyRpc,
    block_tag: str,
    to: str,
    signature: str,
    *,
    return_types: Iterable[str],
    argument_types: Iterable[str] = (),
    arguments=(),
):
    result = rpc.call(
        "eth_call",
        [
            {
                "to": normalize_address(to),
                "data": encode_call(signature, argument_types, arguments),
            },
            block_tag,
        ],
    )
    if not isinstance(result, str) or not result.startswith("0x"):
        raise QualificationError(f"{signature} returned malformed data")
    try:
        decoded = abi_decode(list(return_types), bytes.fromhex(result[2:]))
    except (ValueError, TypeError) as exc:
        raise QualificationError(f"{signature} returned undecodable data") from exc
    return decoded[0] if len(decoded) == 1 else decoded


def add_check(
    checks: list[dict[str, Any]],
    name: str,
    passed: bool,
    *,
    actual: Any,
    expected: Any,
) -> bool:
    checks.append(
        {
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "actual": actual,
            "expected": expected,
        }
    )
    return passed


def observe_code(
    rpc: ReadOnlyRpc,
    block_tag: str,
    address: str,
    expected_bytes: int,
    expected_hash: str,
    checks: list[dict[str, Any]],
    label: str,
) -> dict[str, Any]:
    observed = code_identity(
        rpc.call("eth_getCode", [normalize_address(address), block_tag])
    )
    observed["address"] = address
    observed["matches"] = add_check(
        checks,
        f"{label} runtime identity",
        observed["runtimeBytes"] == expected_bytes
        and observed["runtimeCodeHash"].lower() == expected_hash.lower(),
        actual={"bytes": observed["runtimeBytes"], "hash": observed["runtimeCodeHash"]},
        expected={"bytes": expected_bytes, "hash": expected_hash},
    )
    return observed


def qualify(
    rpc: ReadOnlyRpc,
    chain_manifest: dict[str, Any],
    deployment_manifest: dict[str, Any],
    actor_manifest: dict[str, Any],
    *,
    block: int | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    actual_chain_id = int(rpc.call("eth_chainId", []), 16)
    add_check(
        checks,
        "chain ID",
        actual_chain_id == CHAIN_ID,
        actual=actual_chain_id,
        expected=CHAIN_ID,
    )
    if actual_chain_id != CHAIN_ID:
        raise QualificationError(
            f"wrong chain ID {actual_chain_id}; expected {CHAIN_ID}"
        )

    if block is None:
        block = int(rpc.call("eth_blockNumber", []), 16)
    if block < 0:
        raise ValueError("block must be non-negative")
    block_tag = hex(block)
    header = rpc.call("eth_getBlockByNumber", [block_tag, False])
    if header is None or int(header["number"], 16) != block:
        raise QualificationError(f"RPC did not return requested block {block}")
    block_hash = header.get("hash")
    if not isinstance(block_hash, str) or len(block_hash) != 66:
        raise QualificationError("snapshot block has no canonical hash")

    infrastructure: dict[str, Any] = {}
    for label, expected in chain_manifest["infrastructure"].items():
        infrastructure[label] = observe_code(
            rpc,
            block_tag,
            expected["address"],
            expected["runtimeBytes"],
            expected["runtimeCodeHash"],
            checks,
            label,
        )

    pool_manager_expected = chain_manifest["infrastructure"]["poolManager"]
    pool_manager_owner = contract_call(
        rpc,
        block_tag,
        pool_manager_expected["address"],
        "owner()",
        return_types=["address"],
    )
    add_check(
        checks,
        "PoolManager owner",
        normalize_address(pool_manager_owner)
        == normalize_address(pool_manager_expected["owner"]),
        actual=pool_manager_owner,
        expected=pool_manager_expected["owner"],
    )
    pool_manager_owner_code = code_identity(
        rpc.call("eth_getCode", [normalize_address(pool_manager_owner), block_tag])
    )
    add_check(
        checks,
        "PoolManager owner runtime bytes",
        pool_manager_owner_code["runtimeBytes"]
        == pool_manager_expected["ownerRuntimeBytes"],
        actual=pool_manager_owner_code["runtimeBytes"],
        expected=pool_manager_expected["ownerRuntimeBytes"],
    )
    protocol_fee_controller = contract_call(
        rpc,
        block_tag,
        pool_manager_expected["address"],
        "protocolFeeController()",
        return_types=["address"],
    )
    add_check(
        checks,
        "PoolManager protocol fee controller",
        normalize_address(protocol_fee_controller)
        == normalize_address(pool_manager_expected["protocolFeeController"]),
        actual=protocol_fee_controller,
        expected=pool_manager_expected["protocolFeeController"],
    )
    position_manager_expected = chain_manifest["infrastructure"]["positionManager"]
    position_manager_pool = contract_call(
        rpc,
        block_tag,
        position_manager_expected["address"],
        "poolManager()",
        return_types=["address"],
    )
    add_check(
        checks,
        "PositionManager PoolManager wiring",
        normalize_address(position_manager_pool)
        == normalize_address(position_manager_expected["poolManager"]),
        actual=position_manager_pool,
        expected=position_manager_expected["poolManager"],
    )

    stock_infrastructure = chain_manifest["sharedStockInfrastructure"]
    registry = observe_code(
        rpc,
        block_tag,
        stock_infrastructure["registryAndBeacon"],
        stock_infrastructure["registryRuntimeBytes"],
        stock_infrastructure["registryRuntimeCodeHash"],
        checks,
        "Stock registry/beacon",
    )
    implementation = observe_code(
        rpc,
        block_tag,
        stock_infrastructure["implementation"],
        stock_infrastructure["implementationRuntimeBytes"],
        stock_infrastructure["implementationRuntimeCodeHash"],
        checks,
        "Stock implementation",
    )
    weth_expected = chain_manifest["quoteAssets"]["weth"]
    weth = observe_code(
        rpc,
        block_tag,
        weth_expected["address"],
        weth_expected["runtimeBytes"],
        weth_expected["runtimeCodeHash"],
        checks,
        "WETH",
    )
    weth_symbol = contract_call(
        rpc, block_tag, weth_expected["address"], "symbol()", return_types=["string"]
    )
    weth_decimals = int(
        contract_call(
            rpc,
            block_tag,
            weth_expected["address"],
            "decimals()",
            return_types=["uint8"],
        )
    )
    add_check(
        checks,
        "WETH metadata",
        weth_symbol == weth_expected["symbol"]
        and weth_decimals == weth_expected["decimals"],
        actual={"symbol": weth_symbol, "decimals": weth_decimals},
        expected={
            "symbol": weth_expected["symbol"],
            "decimals": weth_expected["decimals"],
        },
    )

    panoptic: dict[str, Any] = {}
    transactions = deployment_manifest.get("transactions", [])
    if (
        deployment_manifest.get("completedTransactionCount") != 16
        or len(transactions) != 16
    ):
        raise QualificationError(
            "public deployment manifest is not the completed 16-contract record"
        )
    deployed_by_label = {
        transaction["label"]: transaction for transaction in transactions
    }
    required_labels = {
        "RiskEngine",
        "SemiFungiblePositionManagerV4",
        "PanopticFactoryV4",
    }
    if not required_labels.issubset(deployed_by_label):
        raise QualificationError(
            "public deployment manifest omits required named contracts"
        )
    for transaction in transactions:
        label = transaction["label"]
        panoptic[label] = observe_code(
            rpc,
            block_tag,
            transaction["createdAddress"],
            transaction["runtimeBytes"],
            transaction["runtimeCodeHash"],
            checks,
            f"Panoptic {label}",
        )

    registry_address = stock_infrastructure["registryAndBeacon"]
    registry_paused = bool(
        contract_call(
            rpc, block_tag, registry_address, "paused()", return_types=["bool"]
        )
    )
    add_check(
        checks,
        "Stock registry global pause",
        registry_paused is stock_infrastructure["registryPaused"],
        actual=registry_paused,
        expected=stock_infrastructure["registryPaused"],
    )
    current_implementation = contract_call(
        rpc, block_tag, registry_address, "implementation()", return_types=["address"]
    )
    add_check(
        checks,
        "Stock beacon implementation",
        normalize_address(current_implementation)
        == normalize_address(stock_infrastructure["implementation"]),
        actual=current_implementation,
        expected=stock_infrastructure["implementation"],
    )

    deployer_address = chain_manifest["deployer"]["address"]
    actor_address = actor_manifest["actor"]["address"]
    account_addresses = {"deployer": deployer_address, "secondActor": actor_address}
    accounts: dict[str, Any] = {}
    blocked: dict[str, bool] = {}
    for role, address in account_addresses.items():
        runtime = code_identity(
            rpc.call("eth_getCode", [normalize_address(address), block_tag])
        )
        native_balance = int(
            rpc.call("eth_getBalance", [normalize_address(address), block_tag]), 16
        )
        confirmed_nonce = int(
            rpc.call(
                "eth_getTransactionCount", [normalize_address(address), block_tag]
            ),
            16,
        )
        weth_balance = int(
            contract_call(
                rpc,
                block_tag,
                weth_expected["address"],
                "balanceOf(address)",
                return_types=["uint256"],
                argument_types=["address"],
                arguments=[address],
            )
        )
        is_blocked = bool(
            contract_call(
                rpc,
                block_tag,
                registry_address,
                "isBlocked(address)",
                return_types=["bool"],
                argument_types=["address"],
                arguments=[address],
            )
        )
        blocked[role] = is_blocked
        add_check(
            checks,
            f"{role} is an EOA",
            runtime["runtimeBytes"] == 0,
            actual=runtime["runtimeBytes"],
            expected=0,
        )
        add_check(
            checks,
            f"{role} Stock registry block status",
            not is_blocked,
            actual=is_blocked,
            expected=False,
        )
        add_check(
            checks,
            f"{role} has native gas balance",
            native_balance > 0,
            actual=str(native_balance),
            expected=">0",
        )
        accounts[role] = {
            "address": address,
            "runtimeBytes": runtime["runtimeBytes"],
            "nativeBalanceWei": str(native_balance),
            "confirmedNonce": confirmed_nonce,
            "wethBalance": str(weth_balance),
            "blockedByStockRegistry": is_blocked,
            "stockBalances": {},
        }

    state_view_address = chain_manifest["infrastructure"]["stateView"]["address"]
    factory_address = deployed_by_label["PanopticFactoryV4"]["createdAddress"]
    risk_engine_address = deployed_by_label["RiskEngine"]["createdAddress"]
    required_stock_state = chain_manifest["requiredStockState"]
    candidates: list[dict[str, Any]] = []
    for stock in chain_manifest["stockTokens"]:
        symbol = stock["symbol"]
        address = stock["address"]
        runtime = observe_code(
            rpc,
            block_tag,
            address,
            stock_infrastructure["proxyRuntimeBytes"],
            stock_infrastructure["proxyRuntimeCodeHash"],
            checks,
            f"{symbol} proxy",
        )
        actual_registry = contract_call(
            rpc,
            block_tag,
            address,
            "ACCESS_CONTROLLED_REGISTRY()",
            return_types=["address"],
        )
        actual_symbol = contract_call(
            rpc, block_tag, address, "symbol()", return_types=["string"]
        )
        actual_name = contract_call(
            rpc, block_tag, address, "name()", return_types=["string"]
        )
        actual_decimals = int(
            contract_call(rpc, block_tag, address, "decimals()", return_types=["uint8"])
        )
        add_check(
            checks,
            f"{symbol} metadata",
            actual_symbol == symbol
            and actual_name == stock["name"]
            and actual_decimals == required_stock_state["decimals"],
            actual={
                "symbol": actual_symbol,
                "name": actual_name,
                "decimals": actual_decimals,
            },
            expected={
                "symbol": symbol,
                "name": stock["name"],
                "decimals": required_stock_state["decimals"],
            },
        )
        registry_matches = normalize_address(actual_registry) == normalize_address(
            registry_address
        )
        add_check(
            checks,
            f"{symbol} registry wiring",
            registry_matches,
            actual=actual_registry,
            expected=registry_address,
        )
        paused = bool(
            contract_call(rpc, block_tag, address, "paused()", return_types=["bool"])
        )
        token_paused = bool(
            contract_call(
                rpc, block_tag, address, "tokenPaused()", return_types=["bool"]
            )
        )
        ui_multiplier = int(
            contract_call(
                rpc, block_tag, address, "uiMultiplier()", return_types=["uint256"]
            )
        )
        pending_multiplier = int(
            contract_call(
                rpc, block_tag, address, "newUIMultiplier()", return_types=["uint256"]
            )
        )
        effective_at = int(
            contract_call(
                rpc, block_tag, address, "effectiveAt()", return_types=["uint256"]
            )
        )
        expected_multiplier = int(required_stock_state["uiMultiplier"])
        expected_pending_multiplier = int(required_stock_state["newUiMultiplier"])
        expected_effective_at = int(required_stock_state["effectiveAt"])
        multiplier_matches = (
            ui_multiplier == expected_multiplier
            and pending_multiplier == expected_pending_multiplier
            and effective_at == expected_effective_at
        )
        add_check(
            checks,
            f"{symbol} health",
            paused is False and token_paused is False and multiplier_matches,
            actual={
                "paused": paused,
                "tokenPaused": token_paused,
                "uiMultiplier": str(ui_multiplier),
                "newUIMultiplier": str(pending_multiplier),
                "effectiveAt": str(effective_at),
            },
            expected={
                "paused": False,
                "tokenPaused": False,
                "uiMultiplier": str(expected_multiplier),
                "newUIMultiplier": str(expected_pending_multiplier),
                "effectiveAt": str(expected_effective_at),
            },
        )

        stock_balances: dict[str, str] = {}
        for role, account_address in account_addresses.items():
            balance = int(
                contract_call(
                    rpc,
                    block_tag,
                    address,
                    "balanceOf(address)",
                    return_types=["uint256"],
                    argument_types=["address"],
                    arguments=[account_address],
                )
            )
            stock_balances[role] = str(balance)
            accounts[role]["stockBalances"][symbol] = str(balance)
            add_check(
                checks,
                f"{symbol} {role} positive stock balance",
                balance > 0,
                actual=str(balance),
                expected=">0",
            )

        pool_key = pool_key_for(address, weth_expected["address"])
        pool_id = pool_id_for(pool_key)
        slot0 = contract_call(
            rpc,
            block_tag,
            state_view_address,
            "getSlot0(bytes32)",
            return_types=["uint160", "int24", "uint24", "uint24"],
            argument_types=["bytes32"],
            arguments=[bytes.fromhex(pool_id[2:])],
        )
        sqrt_price_x96, tick, protocol_fee, lp_fee = (int(value) for value in slot0)
        pool_initialized = sqrt_price_x96 != 0
        pool_key_tuple = (
            pool_key["currency0"],
            pool_key["currency1"],
            pool_key["fee"],
            pool_key["tickSpacing"],
            pool_key["hooks"],
        )
        existing_panoptic_pool = contract_call(
            rpc,
            block_tag,
            factory_address,
            "getPanopticPool((address,address,uint24,int24,address),address)",
            return_types=["address"],
            argument_types=["(address,address,uint24,int24,address)", "address"],
            arguments=[pool_key_tuple, risk_engine_address],
        )
        add_check(
            checks,
            f"{symbol} V4 PoolId is uninitialized",
            not pool_initialized,
            actual={"poolId": pool_id, "sqrtPriceX96": str(sqrt_price_x96)},
            expected={"poolId": pool_id, "sqrtPriceX96": "0"},
        )
        add_check(
            checks,
            f"{symbol} Panoptic market is unregistered",
            normalize_address(existing_panoptic_pool) == ZERO_ADDRESS,
            actual=existing_panoptic_pool,
            expected=ZERO_ADDRESS,
        )
        candidate: dict[str, Any] = {
            "name": stock["name"],
            "symbol": symbol,
            "stockToken": address,
            "runtimeIdentityMatches": runtime["matches"],
            "registryWiringMatches": registry_matches,
            "paused": paused,
            "tokenPaused": token_paused,
            "uiMultiplier": str(ui_multiplier),
            "newUIMultiplier": str(pending_multiplier),
            "effectiveAt": str(effective_at),
            "multiplierStateMatches": multiplier_matches,
            "deployerBalance": stock_balances["deployer"],
            "actorBalance": stock_balances["secondActor"],
            "deployerBlocked": blocked["deployer"],
            "actorBlocked": blocked["secondActor"],
            "poolKey": pool_key,
            "poolId": pool_id,
            "slot0": {
                "sqrtPriceX96": str(sqrt_price_x96),
                "tick": tick,
                "protocolFee": protocol_fee,
                "lpFee": lp_fee,
            },
            "poolInitialized": pool_initialized,
            "existingPanopticPool": existing_panoptic_pool,
        }
        blockers = assess_candidate(candidate)
        candidate["eligible"] = not blockers
        candidate["blockers"] = blockers
        candidates.append(candidate)

    recommendation = recommend_candidate(candidates)
    failed_checks = [check for check in checks if check["status"] != "PASS"]
    if failed_checks:
        status = "BLOCKED_READ_ONLY_QUALIFICATION_FAILED"
    elif recommendation is None:
        status = "BLOCKED_NO_ELIGIBLE_MARKET_CANDIDATE"
    else:
        status = (
            f"READ_ONLY_QUALIFICATION_PASS_{recommendation['symbol']}_"
            "RECOMMENDED_OWNER_ACCEPTANCE_REQUIRED"
        )

    timestamp = datetime.fromtimestamp(int(header["timestamp"], 16), timezone.utc)
    return {
        "schemaVersion": 1,
        "status": status,
        "qualificationMode": "READ_ONLY_NO_KEYS_NO_SIGNING_NO_BROADCAST",
        "network": {
            "name": chain_manifest["network"]["name"],
            "chainId": actual_chain_id,
            "rpcUrl": chain_manifest["network"]["rpcUrl"],
        },
        "snapshot": {
            "blockNumber": block,
            "blockHash": block_hash,
            "blockTimestamp": timestamp.isoformat().replace("+00:00", "Z"),
        },
        "configuration": {
            "fee": DEFAULT_FEE,
            "tickSpacing": DEFAULT_TICK_SPACING,
            "hooks": ZERO_ADDRESS,
            "riskEngine": risk_engine_address,
            "poolManager": chain_manifest["infrastructure"]["poolManager"]["address"],
            "positionManager": chain_manifest["infrastructure"]["positionManager"][
                "address"
            ],
            "stateView": state_view_address,
            "weth": weth_expected["address"],
            "panopticFactoryV4": factory_address,
        },
        "runtimeQualification": {
            "externalInfrastructure": infrastructure,
            "v4Wiring": {
                "poolManagerOwner": pool_manager_owner,
                "poolManagerOwnerRuntimeBytes": pool_manager_owner_code["runtimeBytes"],
                "protocolFeeController": protocol_fee_controller,
                "positionManagerPoolManager": position_manager_pool,
            },
            "stockRegistry": registry,
            "stockImplementation": implementation,
            "weth": weth,
            "panoptic": panoptic,
        },
        "accounts": accounts,
        "candidates": candidates,
        "recommendation": recommendation,
        "unresolvedOwnerDecisions": {
            "assetSelection": "OWNER_ACCEPTANCE_REQUIRED",
            "initialPrice": "UNDECIDED_DO_NOT_COPY_LOCAL_ONE_TO_ONE",
            "initialLiquidityAndExposure": "UNDECIDED",
            "transactionRolesAndFactoryNftRecipient": "UNDECIDED",
        },
        "authorization": {
            "publicBroadcast": False,
            "wrapping": False,
            "approvals": False,
            "poolInitialization": False,
            "liquidity": False,
            "swaps": False,
            "panopticMarketRegistration": False,
            "collateralOrTrading": False,
        },
        "checks": {
            "passed": len(checks) - len(failed_checks),
            "failed": len(failed_checks),
            "results": checks,
        },
    }


def parse_args() -> argparse.Namespace:
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chain-manifest",
        type=Path,
        default=repository / "manifests" / "chains" / "robinhood-testnet-46630.json",
    )
    parser.add_argument(
        "--deployment-manifest",
        type=Path,
        default=repository
        / "manifests"
        / "deployments"
        / "robinhood-testnet-direct-public-progress-2026-09-09.json",
    )
    parser.add_argument(
        "--actor-manifest",
        type=Path,
        default=repository
        / "manifests"
        / "deployments"
        / "robinhood-testnet-second-actor-2026-09-09.json",
    )
    parser.add_argument(
        "--rpc-url", help="Read-only RPC override; defaults to chain manifest"
    )
    parser.add_argument(
        "--transport",
        choices=("cast", "urllib"),
        default="cast",
        help="Read-only JSON-RPC transport (default: cast)",
    )
    parser.add_argument("--block", type=int, help="Pin qualification to this block")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QualificationError(f"cannot load JSON manifest {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise QualificationError(f"JSON manifest must contain an object: {path}")
    return value


def main() -> int:
    args = parse_args()
    chain_manifest = load_json(args.chain_manifest)
    deployment_manifest = load_json(args.deployment_manifest)
    actor_manifest = load_json(args.actor_manifest)
    if chain_manifest.get("network", {}).get("chainId") != CHAIN_ID:
        raise QualificationError(f"chain manifest must target chain {CHAIN_ID}")
    if deployment_manifest.get("chainId") != CHAIN_ID:
        raise QualificationError(f"deployment manifest must target chain {CHAIN_ID}")
    if actor_manifest.get("network", {}).get("chainId") != CHAIN_ID:
        raise QualificationError(f"actor manifest must target chain {CHAIN_ID}")

    rpc_url = args.rpc_url or chain_manifest["network"]["rpcUrl"]
    rpc = CastReadOnlyRpc(rpc_url) if args.transport == "cast" else ReadOnlyRpc(rpc_url)
    report = qualify(
        rpc,
        chain_manifest,
        deployment_manifest,
        actor_manifest,
        block=args.block,
    )
    report["sourceBindings"] = {
        "qualifierSha256": file_sha256(Path(__file__)),
        "chainManifestSha256": file_sha256(args.chain_manifest),
        "deploymentManifestSha256": file_sha256(args.deployment_manifest),
        "actorManifestSha256": file_sha256(args.actor_manifest),
    }
    print(json.dumps(report, indent=None if args.compact else 2, sort_keys=True))
    return 0 if report["status"].startswith("READ_ONLY_QUALIFICATION_PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
