#!/usr/bin/env python3
"""Build a deterministic, unsigned Robinhood testnet market rehearsal plan.

This tool is intentionally offline. It has no RPC client, private-key or
keystore input, signing path, transaction serialization, or broadcast path.
It validates reviewed public manifests, performs exact Uniswap V4 price and
liquidity math, and emits ABI calldata for inspection and local fork rehearsal.

The committed clock is historical by design. Its deadlines are rehearsal-only
and a public execution candidate must be regenerated after fresh state,
exposure, simulation, nonce, and authorization gates all pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

from eth_abi import decode as abi_decode
from eth_abi import encode as abi_encode
from eth_utils import keccak


CHAIN_ID = 46630
Q96 = 1 << 96
MIN_TICK = -887_272
MAX_TICK = 887_272
MIN_SQRT_PRICE = 4_295_128_739
MAX_SQRT_PRICE = 1_461_446_703_485_210_103_287_273_052_203_988_822_378_723_970_342
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
POOL_KEY_ABI = "(address,address,uint24,int24,address)"
CREATE3_PROXY_BYTECODE_HASH = bytes.fromhex(
    "21c35dbe1b344a2488cf3321d6ce542f8e9f305544ff09e4993a62319a497c1f"
)

DEFAULT_ACCEPTANCE = Path(
    "manifests/markets/robinhood-testnet-pltr-weth-offline-acceptance-2026-09-09.json"
)
DEFAULT_SELECTION = Path(
    "manifests/markets/robinhood-testnet-market-selection-2026-09-09.json"
)
DEFAULT_CHAIN = Path("manifests/chains/robinhood-testnet-46630.json")
DEFAULT_DEPLOYMENT = Path(
    "manifests/deployments/robinhood-testnet-direct-public-progress-2026-09-09.json"
)
DEFAULT_OUTPUT = Path(
    "manifests/markets/robinhood-testnet-pltr-weth-offline-plan-2026-09-09.json"
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def repository_relative_path(path: Path, generator_path: Path) -> str:
    repository = generator_path.resolve().parent.parent
    resolved = path.resolve()
    try:
        return resolved.relative_to(repository).as_posix()
    except ValueError:
        return resolved.as_posix()


def normalize_address(value: str, name: str = "address") -> str:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 42:
        raise ValueError(f"{name} must be a 20-byte hex address")
    try:
        bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ValueError(f"{name} must be a 20-byte hex address") from exc
    return value.lower()


def normalize_hash(value: str, name: str = "hash") -> str:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 66:
        raise ValueError(f"{name} must be a 32-byte hex hash")
    try:
        bytes.fromhex(value[2:])
    except ValueError as exc:
        raise ValueError(f"{name} must be a 32-byte hex hash") from exc
    return value.lower()


def pool_key_tuple(pool_key: dict[str, Any]) -> tuple[str, str, int, int, str]:
    return (
        normalize_address(pool_key["currency0"], "currency0"),
        normalize_address(pool_key["currency1"], "currency1"),
        int(pool_key["fee"]),
        int(pool_key["tickSpacing"]),
        normalize_address(pool_key["hooks"], "hooks"),
    )


def pool_id_for(pool_key: dict[str, Any]) -> str:
    return "0x" + keccak(abi_encode([POOL_KEY_ABI], [pool_key_tuple(pool_key)])).hex()


def get_sqrt_price_at_tick(tick: int) -> int:
    """Exact Python port of Uniswap V4 TickMath.getSqrtPriceAtTick."""

    if not isinstance(tick, int) or tick < MIN_TICK or tick > MAX_TICK:
        raise ValueError("tick is outside the Uniswap V4 TickMath range")
    abs_tick = abs(tick)
    ratio = 0xFFF_CB933_BD6F_AD37_AA2D_162D_1A59_4001 if abs_tick & 0x1 else 1 << 128
    constants = (
        (0x2, 0xFFF97272373D413259A46990580E213A),
        (0x4, 0xFFF2E50F5F656932EF12357CF3C7FDCC),
        (0x8, 0xFFE5CACA7E10E4E61C3624EAA0941CD0),
        (0x10, 0xFFCB9843D60F6159C9DB58835C926644),
        (0x20, 0xFF973B41FA98C081472E6896DFB254C0),
        (0x40, 0xFF2EA16466C96A3843EC78B326B52861),
        (0x80, 0xFE5DEE046A99A2A811C461F1969C3053),
        (0x100, 0xFCBE86C7900A88AEDCFFC83B479AA3A4),
        (0x200, 0xF987A7253AC413176F2B074CF7815E54),
        (0x400, 0xF3392B0822B70005940C7A398E4B70F3),
        (0x800, 0xE7159475A2C29B7443B29C7FA6E889D9),
        (0x1000, 0xD097F3BDFD2022B8845AD8F792AA5825),
        (0x2000, 0xA9F746462D870FDF8A65DC1F90E061E5),
        (0x4000, 0x70D869A156D2A1B890BB3DF62BAF32F7),
        (0x8000, 0x31BE135F97D08FD981231505542FCFA6),
        (0x10000, 0x9AA508B5B7A84E1C677DE54F3E99BC9),
        (0x20000, 0x5D6AF8DEDB81196699C329225EE604),
        (0x40000, 0x2216E584F5FA1EA926041BEDFE98),
        (0x80000, 0x48A170391F7DC42444E8FA2),
    )
    for bit, multiplier in constants:
        if abs_tick & bit:
            ratio = (ratio * multiplier) >> 128
    if tick > 0:
        ratio = ((1 << 256) - 1) // ratio
    return (ratio >> 32) + (1 if ratio & ((1 << 32) - 1) else 0)


def get_tick_at_sqrt_price(sqrt_price_x96: int) -> int:
    """Return the greatest tick whose canonical sqrt price is not greater."""

    if sqrt_price_x96 < MIN_SQRT_PRICE or sqrt_price_x96 >= MAX_SQRT_PRICE:
        raise ValueError("sqrt price is outside the Uniswap V4 TickMath range")
    low = MIN_TICK
    high = MAX_TICK
    while low < high:
        middle = (low + high + 1) // 2
        if get_sqrt_price_at_tick(middle) <= sqrt_price_x96:
            low = middle
        else:
            high = middle - 1
    return low


def sqrt_price_x96_for_ratio(numerator: int, denominator: int) -> int:
    """Floor sqrt(numerator / denominator) * 2**96 without floating point."""

    if not isinstance(numerator, int) or not isinstance(denominator, int):
        raise ValueError("price ratio must use integer numerator and denominator")
    if numerator <= 0 or denominator <= 0:
        raise ValueError("price ratio must be positive")
    return math.isqrt((numerator << 192) // denominator)


def floor_to_spacing(tick: int, spacing: int) -> int:
    if spacing <= 0:
        raise ValueError("tick spacing must be positive")
    return (tick // spacing) * spacing


def ceil_to_spacing(tick: int, spacing: int) -> int:
    if spacing <= 0:
        raise ValueError("tick spacing must be positive")
    return -((-tick) // spacing) * spacing


def ceil_div(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("division denominator must be positive")
    return (numerator + denominator - 1) // denominator


def liquidity_for_amount0(sqrt_a: int, sqrt_b: int, amount0: int) -> int:
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a
    intermediate = (sqrt_a * sqrt_b) // Q96
    return (amount0 * intermediate) // (sqrt_b - sqrt_a)


def liquidity_for_amount1(sqrt_a: int, sqrt_b: int, amount1: int) -> int:
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a
    return (amount1 * Q96) // (sqrt_b - sqrt_a)


def liquidity_for_amounts(
    sqrt_price: int, sqrt_a: int, sqrt_b: int, amount0: int, amount1: int
) -> int:
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a
    if sqrt_price <= sqrt_a:
        return liquidity_for_amount0(sqrt_a, sqrt_b, amount0)
    if sqrt_price < sqrt_b:
        return min(
            liquidity_for_amount0(sqrt_price, sqrt_b, amount0),
            liquidity_for_amount1(sqrt_a, sqrt_price, amount1),
        )
    return liquidity_for_amount1(sqrt_a, sqrt_b, amount1)


def amount0_for_liquidity_rounding_up(sqrt_a: int, sqrt_b: int, liquidity: int) -> int:
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a
    intermediate = ceil_div((liquidity << 96) * (sqrt_b - sqrt_a), sqrt_b)
    return ceil_div(intermediate, sqrt_a)


def amount1_for_liquidity_rounding_up(sqrt_a: int, sqrt_b: int, liquidity: int) -> int:
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a
    return ceil_div(liquidity * (sqrt_b - sqrt_a), Q96)


def amounts_for_liquidity_rounding_up(
    sqrt_price: int, sqrt_a: int, sqrt_b: int, liquidity: int
) -> tuple[int, int]:
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a
    if sqrt_price <= sqrt_a:
        return amount0_for_liquidity_rounding_up(sqrt_a, sqrt_b, liquidity), 0
    if sqrt_price < sqrt_b:
        return (
            amount0_for_liquidity_rounding_up(sqrt_price, sqrt_b, liquidity),
            amount1_for_liquidity_rounding_up(sqrt_a, sqrt_price, liquidity),
        )
    return 0, amount1_for_liquidity_rounding_up(sqrt_a, sqrt_b, liquidity)


def fit_liquidity_within_budgets(
    sqrt_price: int,
    sqrt_a: int,
    sqrt_b: int,
    amount0_budget: int,
    amount1_budget: int,
) -> int:
    """Maximize liquidity while canonical round-up deltas stay within budgets."""

    high = liquidity_for_amounts(
        sqrt_price, sqrt_a, sqrt_b, amount0_budget, amount1_budget
    )
    low = 0
    while low < high:
        middle = (low + high + 1) // 2
        amount0, amount1 = amounts_for_liquidity_rounding_up(
            sqrt_price, sqrt_a, sqrt_b, middle
        )
        if amount0 <= amount0_budget and amount1 <= amount1_budget:
            low = middle
        else:
            high = middle - 1
    return low


def function_selector(signature: str) -> bytes:
    return keccak(text=signature)[:4]


def encode_call(
    signature: str, argument_types: Iterable[str] = (), arguments: Iterable[Any] = ()
) -> str:
    return (
        "0x"
        + (
            function_selector(signature)
            + abi_encode(list(argument_types), list(arguments))
        ).hex()
    )


def _address_bytes(address: str) -> bytes:
    return bytes.fromhex(normalize_address(address)[2:])


def factory_salt32(actor: str, pool_id: str, risk_engine: str, salt: int) -> bytes:
    if not 0 <= salt < 2**96:
        raise ValueError("factory salt must fit uint96")
    actor_bytes = _address_bytes(actor)
    pool_id_bytes = bytes.fromhex(normalize_hash(pool_id, "PoolId")[2:])
    risk_bytes = _address_bytes(risk_engine)
    return (
        actor_bytes[:10]
        + pool_id_bytes[12:17]
        + risk_bytes[:5]
        + salt.to_bytes(12, "big")
    )


def predict_create3(factory: str, salt32: bytes) -> str:
    if len(salt32) != 32:
        raise ValueError("CREATE3 salt must be 32 bytes")
    proxy_hash = keccak(
        b"\xff" + _address_bytes(factory) + salt32 + CREATE3_PROXY_BYTECODE_HASH
    )
    proxy = proxy_hash[-20:]
    deployed_hash = keccak(b"\xd6\x94" + proxy + b"\x01")
    return "0x" + deployed_hash[-20:].hex()


def clone2_creation_code(implementation: str, immutable_data: bytes) -> bytes:
    """Port the pinned ClonesWithImmutableArgs.getCreationBytecode layout."""

    if len(immutable_data) > 65_535:
        raise ValueError("clone immutable data exceeds uint16 length")
    extra_length = len(immutable_data) + 2
    creation_size = 0x41 + extra_length
    run_size = creation_size - 10
    prefix = (
        b"\x61"
        + run_size.to_bytes(2, "big")
        + bytes.fromhex("3d81600a3d39f33d3d3d3d363d3d3761")
        + extra_length.to_bytes(2, "big")
        + bytes.fromhex("603736393661")
        + extra_length.to_bytes(2, "big")
        + bytes.fromhex("013d73")
        + _address_bytes(implementation)
        + bytes.fromhex("5af43d3d93803e603557fd5bf3")
    )
    if len(prefix) != 0x41:
        raise AssertionError("clone2 creation prefix length drifted")
    return prefix + immutable_data + len(immutable_data).to_bytes(2, "big")


def predict_clone2(
    factory: str, implementation: str, immutable_data: bytes
) -> tuple[str, str]:
    creation_code_hash = keccak(clone2_creation_code(implementation, immutable_data))
    digest = keccak(b"\xff" + _address_bytes(factory) + bytes(32) + creation_code_hash)
    return "0x" + digest[-20:].hex(), "0x" + creation_code_hash.hex()


def tracker_immutable_data(
    panoptic_pool: str,
    is_token0: bool,
    collateral_token: str,
    pool_key: dict[str, Any],
    risk_engine: str,
    pool_manager: str,
) -> bytes:
    key = pool_key_tuple(pool_key)
    return b"".join(
        (
            _address_bytes(panoptic_pool),
            b"\x01" if is_token0 else b"\x00",
            _address_bytes(collateral_token),
            _address_bytes(key[0]),
            _address_bytes(key[1]),
            _address_bytes(risk_engine),
            _address_bytes(pool_manager),
            key[2].to_bytes(3, "big"),
        )
    )


def transaction(
    ordinal: int,
    label: str,
    actor: str,
    target: str,
    value_wei: int,
    calldata: str,
    decoded_intent: dict[str, Any],
    required_pre_state: list[str],
    expected_post_state: list[str],
) -> dict[str, Any]:
    raw = bytes.fromhex(calldata[2:])
    return {
        "ordinal": ordinal,
        "label": label,
        "from": actor,
        "to": target,
        "nonce": None,
        "noncePolicy": "FRESH_PENDING_NONCE_REQUIRED_IN_LATER_EXECUTION_PLAN",
        "valueWei": str(value_wei),
        "calldataBytes": len(raw),
        "calldataKeccak256": "0x" + keccak(raw).hex(),
        "calldata": calldata,
        "decodedIntent": decoded_intent,
        "requiredPreState": required_pre_state,
        "expectedPostState": expected_post_state,
        "authorizedForBroadcast": False,
    }


def _load(path: Path) -> dict[str, Any]:
    decoded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return decoded


def _require_all_false(values: dict[str, Any], name: str) -> None:
    if (
        not isinstance(values, dict)
        or not values
        or any(value is not False for value in values.values())
    ):
        raise ValueError(f"{name} authorization must remain entirely false")


def _deployed_address(deployment: dict[str, Any], label: str) -> str:
    matches = [
        item.get("createdAddress")
        for item in deployment.get("transactions", [])
        if item.get("label") == label and item.get("receiptStatus") == 1
    ]
    if len(matches) != 1:
        raise ValueError(f"deployment manifest must contain one reconciled {label}")
    return normalize_address(matches[0], label)


def _validate_inputs(
    acceptance_path: Path,
    acceptance: dict[str, Any],
    selection_path: Path,
    selection: dict[str, Any],
    chain: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if acceptance.get("status") != "OWNER_ACCEPTED_FOR_OFFLINE_PLANNING_ONLY":
        raise ValueError("acceptance status does not permit offline planning")
    _require_all_false(acceptance.get("authorization", {}), "acceptance")
    if acceptance["selectionBinding"].get("sha256") != file_sha256(selection_path):
        raise ValueError("selection manifest hash does not match owner acceptance")
    if selection.get("verification", {}).get("failedChecks") != 0:
        raise ValueError("selection qualification has failed checks")
    if selection.get("verification", {}).get("passedChecks") != 79:
        raise ValueError("selection qualification check count drifted")
    _require_all_false(selection.get("authorization", {}), "selection")
    if chain.get("network", {}).get("chainId") != CHAIN_ID:
        raise ValueError("chain manifest does not target Robinhood testnet")

    accepted = acceptance["acceptedDesign"]
    candidates = [
        candidate
        for candidate in selection.get("candidates", [])
        if candidate.get("symbol") == accepted.get("symbol")
    ]
    if len(candidates) != 1 or not candidates[0].get("eligible"):
        raise ValueError("accepted Stock Token is not uniquely eligible")
    candidate = candidates[0]
    if pool_id_for(accepted["poolKey"]) != normalize_hash(
        accepted["poolId"], "accepted PoolId"
    ):
        raise ValueError("accepted PoolId does not match accepted PoolKey")
    if normalize_hash(candidate["poolId"], "candidate PoolId") != normalize_hash(
        accepted["poolId"], "accepted PoolId"
    ):
        raise ValueError("candidate PoolId does not match owner acceptance")
    if pool_key_tuple(candidate["poolKey"]) != pool_key_tuple(accepted["poolKey"]):
        raise ValueError("candidate PoolKey does not match owner acceptance")
    if candidate.get("poolInitialized") is not False:
        raise ValueError("selection snapshot did not observe an uninitialized pool")
    if normalize_address(candidate["existingPanopticPool"]) != ZERO_ADDRESS:
        raise ValueError("selection snapshot already contains a Panoptic market")
    price_policy = accepted["pricePolicy"]
    if (
        price_policy.get("classification")
        != "SYNTHETIC_MECHANISM_TEST_ONLY_NOT_A_MARKET_QUOTE"
    ):
        raise ValueError("price policy must remain explicitly synthetic")
    return accepted, candidate


def build_plan(
    acceptance_path: Path,
    selection_path: Path,
    chain_path: Path,
    deployment_path: Path,
    generator_path: Path,
) -> dict[str, Any]:
    acceptance_path = Path(acceptance_path)
    selection_path = Path(selection_path)
    chain_path = Path(chain_path)
    deployment_path = Path(deployment_path)
    generator_path = Path(generator_path)
    acceptance = _load(acceptance_path)
    selection = _load(selection_path)
    chain = _load(chain_path)
    deployment = _load(deployment_path)
    accepted, candidate = _validate_inputs(
        acceptance_path, acceptance, selection_path, selection, chain
    )

    pool_key = accepted["poolKey"]
    key_tuple = pool_key_tuple(pool_key)
    actor = normalize_address(accepted["roles"]["actor"], "actor")
    if actor != normalize_address(
        selection["accounts"]["secondActor"]["address"], "selection second actor"
    ):
        raise ValueError("accepted actor does not match the qualified second actor")
    if actor == normalize_address(accepted["roles"]["administrativeDeployerExcluded"]):
        raise ValueError(
            "administrative deployer cannot be substituted for the accepted actor"
        )

    contracts = {
        "pltr": normalize_address(accepted["stockToken"], "PLTR"),
        "weth": normalize_address(accepted["weth"], "WETH"),
        "permit2": normalize_address(
            chain["infrastructure"]["permit2"]["address"], "Permit2"
        ),
        "poolManager": normalize_address(
            selection["configuration"]["poolManager"], "PoolManager"
        ),
        "positionManager": normalize_address(
            selection["configuration"]["positionManager"], "PositionManager"
        ),
        "stateView": normalize_address(
            selection["configuration"]["stateView"], "StateView"
        ),
        "riskEngine": _deployed_address(deployment, "RiskEngine"),
        "sfpmV4": _deployed_address(deployment, "SemiFungiblePositionManagerV4"),
        "collateralTrackerReference": _deployed_address(
            deployment, "CollateralTrackerV2"
        ),
        "panopticPoolReference": _deployed_address(deployment, "PanopticPoolV2"),
        "panopticFactoryV4": _deployed_address(deployment, "PanopticFactoryV4"),
    }
    if contracts["riskEngine"] != normalize_address(
        selection["configuration"]["riskEngine"]
    ):
        raise ValueError("RiskEngine address drift between manifests")
    if contracts["panopticFactoryV4"] != normalize_address(
        selection["configuration"]["panopticFactoryV4"]
    ):
        raise ValueError("PanopticFactoryV4 address drift between manifests")
    if contracts["pltr"] != key_tuple[0] or contracts["weth"] != key_tuple[1]:
        raise ValueError("accepted PLTR/WETH currency orientation drifted")

    proposal = acceptance["proposedExposureForOfflineCalculationOnly"]
    if proposal.get("status") != "PROPOSAL_REQUIRES_SEPARATE_OWNER_ACCEPTANCE":
        raise ValueError("exposure must remain a separately reviewable proposal")
    wrap_native = int(proposal["wrapNativeWei"])
    amount0_budget = int(proposal["maximumPltrForInitialLiquidity"])
    amount1_budget = int(proposal["maximumWethForInitialLiquidity"])
    native_reserve = int(proposal["minimumNativeReserveBeforeGasWei"])
    pltr_reserve = int(proposal["minimumPltrReserveAfterLiquidity"])
    weth_reserve = int(proposal["minimumWethReserveAfterLiquidity"])
    observed_actor = selection["accounts"]["secondActor"]
    if wrap_native + native_reserve > int(observed_actor["nativeBalanceWei"]):
        raise ValueError("proposed wrap breaches historical native reserve")
    if amount0_budget + pltr_reserve > int(observed_actor["eachStockTokenBalance"]):
        raise ValueError("proposed PLTR budget breaches historical reserve")
    if amount1_budget + weth_reserve > wrap_native:
        raise ValueError("proposed WETH budget breaches post-wrap reserve")
    if proposal.get("allowanceCleanupRequired") is not True:
        raise ValueError("allowance cleanup cannot be disabled")

    price_policy = accepted["pricePolicy"]
    numerator = int(price_policy["currency1RawUnitsPerCurrency0RawUnitNumerator"])
    denominator = int(price_policy["currency1RawUnitsPerCurrency0RawUnitDenominator"])
    sqrt_price = sqrt_price_x96_for_ratio(numerator, denominator)
    initial_tick = get_tick_at_sqrt_price(sqrt_price)
    range_width = int(proposal["rangeWidthTicksEachSideBeforeOutwardSpacingRounding"])
    spacing = key_tuple[3]
    tick_lower = floor_to_spacing(initial_tick - range_width, spacing)
    tick_upper = ceil_to_spacing(initial_tick + range_width, spacing)
    sqrt_lower = get_sqrt_price_at_tick(tick_lower)
    sqrt_upper = get_sqrt_price_at_tick(tick_upper)
    maximum_liquidity = fit_liquidity_within_budgets(
        sqrt_price, sqrt_lower, sqrt_upper, amount0_budget, amount1_budget
    )
    utilization_bps = int(proposal["liquidityBudgetUtilizationBps"])
    if not 0 < utilization_bps < 10_000:
        raise ValueError("liquidity budget utilization must leave positive headroom")
    liquidity = (maximum_liquidity * utilization_bps) // 10_000
    required0, required1 = amounts_for_liquidity_rounding_up(
        sqrt_price, sqrt_lower, sqrt_upper, liquidity
    )
    if liquidity <= 0:
        raise ValueError("proposed budgets produce zero liquidity")

    reference_time = int(acceptance["rehearsalClock"]["referenceTimestampUnix"])
    permit_expiration = reference_time + int(
        proposal["permit2AllowanceLifetimeSeconds"]
    )
    liquidity_deadline = reference_time + int(proposal["liquidityDeadlineSeconds"])
    factory_salt = int(proposal["factorySalt"])
    pool_id = normalize_hash(accepted["poolId"], "PoolId")
    salt32 = factory_salt32(actor, pool_id, contracts["riskEngine"], factory_salt)
    predicted_pool = predict_create3(contracts["panopticFactoryV4"], salt32)
    tracker0_data = tracker_immutable_data(
        predicted_pool,
        True,
        key_tuple[0],
        pool_key,
        contracts["riskEngine"],
        contracts["poolManager"],
    )
    tracker1_data = tracker_immutable_data(
        predicted_pool,
        False,
        key_tuple[1],
        pool_key,
        contracts["riskEngine"],
        contracts["poolManager"],
    )
    predicted_tracker0, tracker0_initcode_hash = predict_clone2(
        contracts["panopticFactoryV4"],
        contracts["collateralTrackerReference"],
        tracker0_data,
    )
    predicted_tracker1, tracker1_initcode_hash = predict_clone2(
        contracts["panopticFactoryV4"],
        contracts["collateralTrackerReference"],
        tracker1_data,
    )

    approval0 = amount0_budget
    approval1 = amount1_budget
    mint_parameter = abi_encode(
        [
            POOL_KEY_ABI,
            "int24",
            "int24",
            "uint256",
            "uint128",
            "uint128",
            "address",
            "bytes",
        ],
        [
            key_tuple,
            tick_lower,
            tick_upper,
            liquidity,
            approval0,
            approval1,
            actor,
            b"",
        ],
    )
    close0 = abi_encode(["address"], [key_tuple[0]])
    close1 = abi_encode(["address"], [key_tuple[1]])
    unlock_data = abi_encode(
        ["bytes", "bytes[]"], [b"\x02\x12\x12", [mint_parameter, close0, close1]]
    )

    txs: list[dict[str, Any]] = []

    def add(
        label: str,
        target: str,
        value: int,
        calldata: str,
        intent: dict[str, Any],
        pre: list[str],
        post: list[str],
    ) -> None:
        txs.append(
            transaction(
                len(txs), label, actor, target, value, calldata, intent, pre, post
            )
        )

    shared_pre = [
        "chainId == 46630 and canonical head is freshly pinned",
        "actor pending nonce equals the later execution plan nonce",
        "all qualified runtime identities and Stock Token controls still pass",
    ]
    add(
        "wrap bounded native ETH into WETH",
        contracts["weth"],
        wrap_native,
        encode_call("deposit()"),
        {"function": "deposit()", "wrapNativeWei": str(wrap_native)},
        shared_pre
        + ["actor native balance covers wrap value plus reviewed gas reserve"],
        [
            f"actor WETH balance increases by {wrap_native}",
            "actor native principal decreases by wrap value",
        ],
    )
    for token_name, token, amount in (
        ("PLTR", contracts["pltr"], approval0),
        ("WETH", contracts["weth"], approval1),
    ):
        add(
            f"approve bounded {token_name} to Permit2",
            token,
            0,
            encode_call(
                "approve(address,uint256)",
                ["address", "uint256"],
                [contracts["permit2"], amount],
            ),
            {
                "function": "approve(address,uint256)",
                "spender": contracts["permit2"],
                "amount": str(amount),
            },
            shared_pre + [f"actor {token_name} ERC20 allowance to Permit2 is zero"],
            [f"actor {token_name} ERC20 allowance to Permit2 equals {amount}"],
        )
    for token_name, token, amount in (
        ("PLTR", contracts["pltr"], approval0),
        ("WETH", contracts["weth"], approval1),
    ):
        add(
            f"approve bounded {token_name} from Permit2 to PositionManager",
            contracts["permit2"],
            0,
            encode_call(
                "approve(address,address,uint160,uint48)",
                ["address", "address", "uint160", "uint48"],
                [token, contracts["positionManager"], amount, permit_expiration],
            ),
            {
                "function": "approve(address,address,uint160,uint48)",
                "token": token,
                "spender": contracts["positionManager"],
                "amount": str(amount),
                "expiration": permit_expiration,
                "clockClassification": "HISTORICAL_REHEARSAL_ONLY",
            },
            shared_pre
            + [f"actor {token_name} Permit2 allowance to PositionManager is zero"],
            [
                f"bounded {token_name} Permit2 allowance and historical rehearsal expiration are set"
            ],
        )
    add(
        "initialize exact PLTR/WETH pool directly through PoolManager",
        contracts["poolManager"],
        0,
        encode_call(
            "initialize((address,address,uint24,int24,address),uint160)",
            [POOL_KEY_ABI, "uint160"],
            [key_tuple, sqrt_price],
        ),
        {
            "function": "initialize(PoolKey,uint160)",
            "poolKey": dict(
                zip(
                    ("currency0", "currency1", "fee", "tickSpacing", "hooks"), key_tuple
                )
            ),
            "poolId": pool_id,
            "sqrtPriceX96": str(sqrt_price),
            "syntheticInitialTick": initial_tick,
        },
        shared_pre
        + [
            "exact PoolId sqrtPriceX96 is zero",
            "exact PoolKey/RiskEngine factory mapping is zero",
        ],
        [
            f"exact PoolId sqrtPriceX96 equals {sqrt_price}",
            f"exact PoolId tick equals {initial_tick}",
        ],
    )
    add(
        "mint bounded two-sided V4 liquidity position",
        contracts["positionManager"],
        0,
        encode_call(
            "modifyLiquidities(bytes,uint256)",
            ["bytes", "uint256"],
            [unlock_data, liquidity_deadline],
        ),
        {
            "function": "modifyLiquidities(bytes,uint256)",
            "actions": "0x021212",
            "actionNames": ["MINT_POSITION", "CLOSE_CURRENCY", "CLOSE_CURRENCY"],
            "tickLower": tick_lower,
            "tickUpper": tick_upper,
            "liquidity": str(liquidity),
            "amount0Max": str(approval0),
            "amount1Max": str(approval1),
            "expectedAmount0AtSyntheticPrice": str(required0),
            "expectedAmount1AtSyntheticPrice": str(required1),
            "owner": actor,
            "deadline": liquidity_deadline,
            "clockClassification": "HISTORICAL_REHEARSAL_ONLY",
        },
        shared_pre
        + [
            f"exact PoolId sqrtPriceX96 still equals {sqrt_price}",
            "exact PoolId active liquidity is zero",
            "PositionManager nextTokenId is freshly recorded for post-state reconciliation",
            "both ERC20 and Permit2 allowances are positive and no greater than plan maxima",
            "historical rehearsal timestamp is not past the encoded deadline",
        ],
        [
            "PositionManager nextTokenId increments by one",
            "the preflight nextTokenId is owned by the second actor",
            f"position liquidity equals {liquidity}",
            "actual PLTR and WETH deltas do not exceed plan maxima",
            "pool active liquidity becomes positive",
        ],
    )
    for token_name, token in (("PLTR", contracts["pltr"]), ("WETH", contracts["weth"])):
        add(
            f"revoke {token_name} Permit2-to-PositionManager allowance",
            contracts["permit2"],
            0,
            encode_call(
                "approve(address,address,uint160,uint48)",
                ["address", "address", "uint160", "uint48"],
                [token, contracts["positionManager"], 0, 0],
            ),
            {
                "function": "approve(address,address,uint160,uint48)",
                "token": token,
                "spender": contracts["positionManager"],
                "amount": "0",
                "expiration": 0,
            },
            shared_pre + ["liquidity mint receipt and post-state are reconciled"],
            [f"actor {token_name} Permit2 allowance to PositionManager equals zero"],
        )
    for token_name, token in (("PLTR", contracts["pltr"]), ("WETH", contracts["weth"])):
        add(
            f"revoke {token_name} ERC20-to-Permit2 allowance",
            token,
            0,
            encode_call(
                "approve(address,uint256)",
                ["address", "uint256"],
                [contracts["permit2"], 0],
            ),
            {
                "function": "approve(address,uint256)",
                "spender": contracts["permit2"],
                "amount": "0",
            },
            shared_pre
            + [f"actor {token_name} Permit2 allowance to PositionManager equals zero"],
            [f"actor {token_name} ERC20 allowance to Permit2 equals zero"],
        )
    add(
        "deploy and register Panoptic market; mint factory NFT to actor",
        contracts["panopticFactoryV4"],
        0,
        encode_call(
            "deployNewPool((address,address,uint24,int24,address),address,uint96)",
            [POOL_KEY_ABI, "address", "uint96"],
            [key_tuple, contracts["riskEngine"], factory_salt],
        ),
        {
            "function": "deployNewPool(PoolKey,address,uint96)",
            "poolKey": dict(
                zip(
                    ("currency0", "currency1", "fee", "tickSpacing", "hooks"), key_tuple
                )
            ),
            "riskEngine": contracts["riskEngine"],
            "salt": str(factory_salt),
            "derivedSalt32": "0x" + salt32.hex(),
            "predictedPanopticPool": predicted_pool,
            "predictedCollateralTracker0": predicted_tracker0,
            "predictedCollateralTracker1": predicted_tracker1,
            "factoryNftRecipient": actor,
            "factoryNftTokenIdPolicy": "uint256(uint160(predictedPanopticPool))",
        },
        shared_pre
        + [
            "exact PoolId remains initialized and has positive liquidity",
            "exact PoolKey/RiskEngine factory mapping is zero",
            "predicted PanopticPool and both predicted tracker addresses have empty code",
            "all token allowances from the actor are zero",
        ],
        [
            "PoolDeployed event fields exactly match all three predicted addresses, PoolId, and RiskEngine",
            "factory mapping equals predicted PanopticPool",
            "SFPM mapping is initialized for the PoolKey and RiskEngine vegoid",
            "PanopticPool and both trackers have non-empty expected proxy runtime",
            "factory NFT tokenId is owned by the second actor",
            "PanopticPool, tracker assets, PoolManager, SFPM poolId, and RiskEngine wiring reconcile",
        ],
    )

    price_squared = sqrt_price * sqrt_price
    plan: dict[str, Any] = {
        "schemaVersion": 1,
        "status": "OFFLINE_REHEARSAL_ONLY_NO_BROADCAST",
        "generatedFromRecordedAcceptanceAt": acceptance["recordedAt"],
        "mode": "OFFLINE_NO_RPC_NO_KEYS_NO_SIGNING_NO_SERIALIZATION_NO_BROADCAST",
        "network": {
            "name": "Robinhood Chain Testnet",
            "chainId": CHAIN_ID,
            "historicalQualificationBlock": selection["network"]["snapshotBlock"],
            "historicalQualificationBlockHash": selection["network"][
                "snapshotBlockHash"
            ],
            "liveStatePolicy": "STALE_BY_DEFINITION_FRESH_PINNED_PREFLIGHT_REQUIRED",
        },
        "sourceBindings": {
            "acceptance": {
                "path": repository_relative_path(acceptance_path, generator_path),
                "sha256": file_sha256(acceptance_path),
            },
            "selection": {
                "path": repository_relative_path(selection_path, generator_path),
                "sha256": file_sha256(selection_path),
            },
            "chain": {
                "path": repository_relative_path(chain_path, generator_path),
                "sha256": file_sha256(chain_path),
            },
            "deployment": {
                "path": repository_relative_path(deployment_path, generator_path),
                "sha256": file_sha256(deployment_path),
            },
            "generator": {
                "path": repository_relative_path(generator_path, generator_path),
                "sha256": file_sha256(generator_path),
            },
            "uniswapV4PeripheryCommit": "3779387e5d296f39df543d23524b050f89a62917",
            "uniswapV4CoreCommit": "59d3ecf53afa9264a16bba0e38f4c5d2231f80bc",
            "permit2Commit": "cc56ad0f3439c502c246fc5cfcc3db92bb8b7219",
            "panopticCoreCommit": "f4abdd7de13ea1414eb1b8f97b53ecbc448b9b8d",
            "clonesWithImmutableArgsCommit": "196f1ecc6485c1bf2d41677fa01d3df4927ff9ce",
        },
        "market": {
            "symbol": accepted["symbol"],
            "stockToken": contracts["pltr"],
            "poolKey": dict(
                zip(
                    ("currency0", "currency1", "fee", "tickSpacing", "hooks"), key_tuple
                )
            ),
            "poolId": pool_id,
            "historicalEligibility": candidate["eligible"],
            "historicalPoolInitialized": candidate["poolInitialized"],
            "historicalPanopticPool": normalize_address(
                candidate["existingPanopticPool"]
            ),
        },
        "actor": {
            "address": actor,
            "roles": [
                "POOL_INITIALIZER",
                "V4_LIQUIDITY_PROVIDER",
                "V4_LIQUIDITY_NFT_RECIPIENT",
                "PANOPTIC_MARKET_DEPLOYER",
                "PANOPTIC_FACTORY_NFT_RECIPIENT",
            ],
            "administrativeDeployerExcluded": normalize_address(
                accepted["roles"]["administrativeDeployerExcluded"]
            ),
            "independentReviewClaim": False,
        },
        "contracts": contracts,
        "priceAndLiquidity": {
            "classification": price_policy["classification"],
            "warning": price_policy["uiRestriction"],
            "currency0": "PLTR",
            "currency1": "test WETH",
            "currency1PerCurrency0Target": {
                "numerator": str(numerator),
                "denominator": str(denominator),
            },
            "currency0PerCurrency1Target": {
                "numerator": str(denominator),
                "denominator": str(numerator),
            },
            "sqrtPriceX96": str(sqrt_price),
            "sqrtPriceRounding": "FLOOR_INTEGER_SQRT_OF_RATIO_TIMES_2_POW_192",
            "realizedRawRatioNumerator": str(price_squared),
            "realizedRawRatioDenominator": str(1 << 192),
            "initialTick": initial_tick,
            "initialTickPolicy": "GREATEST_TICK_WITH_SQRT_PRICE_NOT_ABOVE_SYNTHETIC_SQRT_PRICE",
            "tickLower": tick_lower,
            "tickUpper": tick_upper,
            "rangePolicy": "INITIAL_TICK_PLUS_OR_MINUS_12000_THEN_ROUND_OUTWARD_TO_TICK_SPACING_60",
            "approximatePriceCoverageRelativeToInitial": "about 0.30x through 3.33x",
            "sqrtPriceLowerX96": str(sqrt_lower),
            "sqrtPriceUpperX96": str(sqrt_upper),
            "liquidity": str(liquidity),
            "maximumLiquidityAtBudgets": str(maximum_liquidity),
            "liquidityBudgetUtilizationBps": utilization_bps,
            "amount0Max": str(amount0_budget),
            "amount1Max": str(amount1_budget),
            "expectedAmount0AtSyntheticPriceRoundedUp": str(required0),
            "expectedAmount1AtSyntheticPriceRoundedUp": str(required1),
            "amountMath": "PINNED_V4_TICKMATH_AND_SQRTPRICEMATH_ROUND_UP_EQUIVALENT",
            "preMintPriceDeviationPolicy": "ZERO_EXACT_SQRT_PRICE_AND_TICK_REQUIRED",
        },
        "maximumExposureProposal": {
            "status": proposal["status"],
            "wrapNativeWei": str(wrap_native),
            "maximumPltrTransfer": str(amount0_budget),
            "maximumWethTransfer": str(amount1_budget),
            "minimumNativeReserveBeforeGasWei": str(native_reserve),
            "minimumPltrReserveAfterLiquidity": str(pltr_reserve),
            "minimumWethReserveAfterLiquidity": str(weth_reserve),
            "approvalPolicy": "EXACT_BOUNDED_APPROVALS_THEN_EXPLICIT_ZERO_ALLOWANCE_CLEANUP",
        },
        "rehearsalClock": {
            "referenceTimestampUnix": reference_time,
            "liquidityDeadlineUnix": liquidity_deadline,
            "permit2ExpirationUnix": permit_expiration,
            "classification": "HISTORICAL_REHEARSAL_ONLY_NOT_VALID_FOR_PUBLIC_EXECUTION",
        },
        "predictedMarketContracts": {
            "factorySalt": str(factory_salt),
            "derivedSalt32": "0x" + salt32.hex(),
            "panopticPool": predicted_pool,
            "collateralTracker0": predicted_tracker0,
            "collateralTracker1": predicted_tracker1,
            "collateralTracker0InitcodeHash": tracker0_initcode_hash,
            "collateralTracker1InitcodeHash": tracker1_initcode_hash,
            "derivation": "PANOPTIC_FACTORY_SOURCE_CREATE3_AND_CLONE2_FORMULAS",
        },
        "transactionCount": len(txs),
        "transactions": txs,
        "requiredBeforeForkRehearsal": [
            "independently validate every calldata decode and predicted address",
            "build strict read-only step verifier including nextTokenId and allowances",
            "fork a fresh pinned Robinhood testnet head",
            "set the local rehearsal timestamp before the historical deadline",
            "impersonate only the accepted actor and fund no public account",
        ],
        "requiredBeforeAnyExecutionCandidate": [
            "owner separately accepts exact exposure, ticks, liquidity, and salt",
            "fresh qualifier and strict verifier pass at one pinned canonical head",
            "fresh execution timestamps and actor pending nonce are bound",
            "exact-head positive and negative fork rehearsal passes",
            "a separate execution plan and one-step operator are reviewed",
            "separate hash-bound public broadcast authorization is recorded",
        ],
        "authorization": dict(acceptance["authorization"]),
        "nextGate": "OWNER_EXPOSURE_REVIEW_AND_STRICT_VERIFIER_PLUS_EXACT_HEAD_FORK_REHEARSAL",
    }
    plan["planBodySha256"] = canonical_sha256(
        {
            "status": plan["status"],
            "network": plan["network"],
            "sourceBindings": plan["sourceBindings"],
            "market": plan["market"],
            "actor": plan["actor"],
            "contracts": plan["contracts"],
            "priceAndLiquidity": plan["priceAndLiquidity"],
            "maximumExposureProposal": plan["maximumExposureProposal"],
            "rehearsalClock": plan["rehearsalClock"],
            "predictedMarketContracts": plan["predictedMarketContracts"],
            "transactions": plan["transactions"],
            "authorization": plan["authorization"],
        }
    )
    return plan


def decode_liquidity_calldata(calldata: str) -> dict[str, Any]:
    raw = bytes.fromhex(calldata.removeprefix("0x"))
    selector = function_selector("modifyLiquidities(bytes,uint256)")
    if raw[:4] != selector:
        raise ValueError("calldata is not PositionManager.modifyLiquidities")
    unlock_data, deadline = abi_decode(["bytes", "uint256"], raw[4:])
    actions, params = abi_decode(["bytes", "bytes[]"], unlock_data)
    if actions != b"\x02\x12\x12" or len(params) != 3:
        raise ValueError(
            "liquidity action sequence is not MINT_POSITION plus two CLOSE_CURRENCY actions"
        )
    decoded = abi_decode(
        [
            POOL_KEY_ABI,
            "int24",
            "int24",
            "uint256",
            "uint128",
            "uint128",
            "address",
            "bytes",
        ],
        params[0],
    )
    key = decoded[0]
    return {
        "actions": "0x" + actions.hex(),
        "poolKey": dict(
            zip(("currency0", "currency1", "fee", "tickSpacing", "hooks"), key)
        ),
        "tickLower": decoded[1],
        "tickUpper": decoded[2],
        "liquidity": str(decoded[3]),
        "amount0Max": str(decoded[4]),
        "amount1Max": str(decoded[5]),
        "owner": decoded[6],
        "hookData": "0x" + decoded[7].hex(),
        "deadline": deadline,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acceptance", type=Path, default=DEFAULT_ACCEPTANCE)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--chain", type=Path, default=DEFAULT_CHAIN)
    parser.add_argument("--deployment", type=Path, default=DEFAULT_DEPLOYMENT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_path = Path(__file__).resolve()
    plan = build_plan(
        args.acceptance,
        args.selection,
        args.chain,
        args.deployment,
        script_path,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Wrote offline rehearsal plan: {args.output}")
    print(f"Plan body SHA-256: {plan['planBodySha256']}")
    print(f"Transactions: {plan['transactionCount']} (all unauthorized; nonces unset)")
    print("NO RPC, SIGNING, SERIALIZATION, OR BROADCAST CAPABILITY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
