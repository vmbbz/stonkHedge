#!/usr/bin/env python3
"""Strict read-only initial preflight for the PLTR/WETH offline market plan.

The verifier first runs the repository's complete pinned-block market
qualification, then applies plan-specific checks for the exact actor, PoolKey,
balances, allowance layers, active liquidity, PositionManager state, and
predicted Panoptic addresses. It has no key, signing, serialization, or
broadcast capability. A pass is rehearsal evidence only because the committed
plan deliberately has null nonces and historical deadlines.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from eth_abi import encode as abi_encode
from eth_utils import keccak


def _load_sibling(name: str, filename: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required sibling module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


qualifier = _load_sibling("stonkhedge_market_qualifier", "qualify_robinhood_market.py")
planner = _load_sibling("stonkhedge_market_planner", "prepare_robinhood_market_plan.py")

CHAIN_ID = 46630
ZERO_ADDRESS = qualifier.ZERO_ADDRESS
RPC_METHODS = qualifier.READ_ONLY_RPC_METHODS
REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-offline-plan-2026-09-09.json"
)
DEFAULT_CHAIN = REPOSITORY / "manifests" / "chains" / "robinhood-testnet-46630.json"
DEFAULT_DEPLOYMENT = (
    REPOSITORY
    / "manifests"
    / "deployments"
    / "robinhood-testnet-direct-public-progress-2026-09-09.json"
)
DEFAULT_ACTOR = (
    REPOSITORY
    / "manifests"
    / "deployments"
    / "robinhood-testnet-second-actor-2026-09-09.json"
)

PLAN_BODY_FIELDS = (
    "status",
    "network",
    "sourceBindings",
    "market",
    "actor",
    "contracts",
    "priceAndLiquidity",
    "maximumExposureProposal",
    "rehearsalClock",
    "predictedMarketContracts",
    "transactions",
    "authorization",
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_selector_hex(signature: str) -> str:
    return "0x" + keccak(text=signature)[:4].hex()


def encode_return(types: list[str], values: list[Any]) -> str:
    return "0x" + abi_encode(types, values).hex()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON manifest must contain an object: {path}")
    return value


def _all_false(values: Any) -> bool:
    return (
        isinstance(values, dict)
        and bool(values)
        and all(value is False for value in values.values())
    )


def validate_offline_plan(plan: dict[str, Any], plan_path: Path) -> None:
    """Fail closed if the committed plan or one of its source bindings drifted."""

    if plan.get("status") != "OFFLINE_REHEARSAL_ONLY_NO_BROADCAST":
        raise ValueError("plan status is not offline rehearsal only")
    if (
        plan.get("mode")
        != "OFFLINE_NO_RPC_NO_KEYS_NO_SIGNING_NO_SERIALIZATION_NO_BROADCAST"
    ):
        raise ValueError("plan mode drifted from the offline-only boundary")
    if plan.get("network", {}).get("chainId") != CHAIN_ID:
        raise ValueError(f"plan chain ID must be {CHAIN_ID}")
    if not _all_false(plan.get("authorization")):
        raise ValueError("plan authorization must remain entirely false")

    transactions = plan.get("transactions")
    if not isinstance(transactions, list) or len(transactions) != 12:
        raise ValueError("plan must contain the reviewed twelve transactions")
    if plan.get("transactionCount") != len(transactions):
        raise ValueError("plan transaction count drifted")
    for ordinal, transaction in enumerate(transactions):
        if transaction.get("ordinal") != ordinal:
            raise ValueError(f"transaction {ordinal} ordering drifted")
        if transaction.get("nonce") is not None:
            raise ValueError(f"transaction {ordinal} unexpectedly binds a nonce")
        if transaction.get("authorizedForBroadcast") is not False:
            raise ValueError(f"transaction {ordinal} is unexpectedly authorized")
        calldata = transaction.get("calldata")
        if not isinstance(calldata, str) or not calldata.startswith("0x"):
            raise ValueError(f"transaction {ordinal} calldata is invalid")
        try:
            raw = bytes.fromhex(calldata[2:])
        except ValueError as exc:
            raise ValueError(f"transaction {ordinal} calldata is invalid hex") from exc
        if transaction.get("calldataBytes") != len(raw):
            raise ValueError(f"transaction {ordinal} calldata length drifted")
        expected_hash = "0x" + keccak(raw).hex()
        if transaction.get("calldataKeccak256") != expected_hash:
            raise ValueError(f"transaction {ordinal} calldata hash drifted")

    body = {field: plan[field] for field in PLAN_BODY_FIELDS}
    if plan.get("planBodySha256") != planner.canonical_sha256(body):
        raise ValueError("plan body SHA-256 drifted")

    repository = Path(plan_path).resolve().parents[2]
    source_paths: dict[str, Path] = {}
    for name in ("acceptance", "selection", "chain", "deployment", "generator"):
        binding = plan.get("sourceBindings", {}).get(name)
        if not isinstance(binding, dict):
            raise ValueError(f"plan source binding {name} is absent")
        source_path = repository / binding["path"]
        if not source_path.is_file():
            raise ValueError(f"plan source binding {name} does not exist")
        if file_sha256(source_path) != binding.get("sha256"):
            raise ValueError(f"plan source binding {name} SHA-256 drifted")
        source_paths[name] = source_path

    regenerated = planner.build_plan(
        source_paths["acceptance"],
        source_paths["selection"],
        source_paths["chain"],
        source_paths["deployment"],
        source_paths["generator"],
    )
    if plan != regenerated:
        raise ValueError("plan is not the exact output of its bound generator inputs")


def _add_check(
    checks: list[dict[str, Any]],
    name: str,
    passed: bool,
    *,
    actual: Any,
    expected: Any,
) -> None:
    checks.append(
        {
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "actual": actual,
            "expected": expected,
        }
    )


def _one_candidate(qualification: dict[str, Any], symbol: str) -> dict[str, Any] | None:
    matches = [
        candidate
        for candidate in qualification.get("candidates", [])
        if candidate.get("symbol") == symbol
    ]
    return matches[0] if len(matches) == 1 else None


def verify_initial_prestate(
    rpc: Any, plan: dict[str, Any], qualification: dict[str, Any]
) -> dict[str, Any]:
    """Verify state before transaction zero at the qualification's pinned head."""

    checks: list[dict[str, Any]] = []
    expected_config = {
        "fee": plan["market"]["poolKey"]["fee"],
        "tickSpacing": plan["market"]["poolKey"]["tickSpacing"],
        "hooks": plan["market"]["poolKey"]["hooks"],
        "riskEngine": plan["contracts"]["riskEngine"],
        "poolManager": plan["contracts"]["poolManager"],
        "positionManager": plan["contracts"]["positionManager"],
        "stateView": plan["contracts"]["stateView"],
        "weth": plan["contracts"]["weth"],
        "panopticFactoryV4": plan["contracts"]["panopticFactoryV4"],
    }
    actual_config = qualification.get("configuration", {})
    normalized_actual_config = dict(actual_config)
    normalized_expected_config = dict(expected_config)
    for key in (
        "hooks",
        "riskEngine",
        "poolManager",
        "positionManager",
        "stateView",
        "weth",
        "panopticFactoryV4",
    ):
        if key in normalized_actual_config:
            normalized_actual_config[key] = qualifier.normalize_address(
                normalized_actual_config[key]
            )
        normalized_expected_config[key] = qualifier.normalize_address(
            normalized_expected_config[key]
        )
    qualification_passed = (
        isinstance(qualification.get("status"), str)
        and qualification["status"].startswith("READ_ONLY_QUALIFICATION_PASS_")
        and qualification.get("checks", {}).get("failed") == 0
    )
    _add_check(
        checks,
        "complete market qualification",
        qualification_passed,
        actual={
            "status": qualification.get("status"),
            "passed": qualification.get("checks", {}).get("passed"),
            "failed": qualification.get("checks", {}).get("failed"),
        },
        expected={"statusPrefix": "READ_ONLY_QUALIFICATION_PASS_", "failed": 0},
    )
    _add_check(
        checks,
        "qualification configuration equals plan",
        normalized_actual_config == normalized_expected_config,
        actual=normalized_actual_config,
        expected=normalized_expected_config,
    )

    candidate = _one_candidate(qualification, plan["market"]["symbol"])
    candidate_matches = candidate is not None
    if candidate is not None:
        candidate_matches = (
            candidate.get("poolId", "").lower() == plan["market"]["poolId"].lower()
            and planner.pool_key_tuple(candidate["poolKey"])
            == planner.pool_key_tuple(plan["market"]["poolKey"])
            and qualifier.normalize_address(candidate["stockToken"])
            == qualifier.normalize_address(plan["contracts"]["pltr"])
            and candidate.get("eligible") is True
            and candidate.get("poolInitialized") is False
            and int(candidate.get("slot0", {}).get("sqrtPriceX96", "-1")) == 0
            and qualifier.normalize_address(candidate.get("existingPanopticPool", ""))
            == ZERO_ADDRESS
        )
    _add_check(
        checks,
        "exact accepted PLTR PoolKey is eligible, uninitialized, and unregistered",
        candidate_matches,
        actual=candidate,
        expected={
            "poolId": plan["market"]["poolId"],
            "poolKey": plan["market"]["poolKey"],
            "eligible": True,
            "poolInitialized": False,
            "sqrtPriceX96": "0",
            "existingPanopticPool": ZERO_ADDRESS,
        },
    )

    actor = qualification.get("accounts", {}).get("secondActor", {})
    actor_address = plan["actor"]["address"]
    actor_matches = (
        qualifier.normalize_address(actor.get("address", ""))
        == qualifier.normalize_address(actor_address)
        and actor.get("blockedByStockRegistry") is False
    )
    _add_check(
        checks,
        "qualified second actor equals plan actor and is unblocked",
        actor_matches,
        actual={
            "address": actor.get("address"),
            "blocked": actor.get("blockedByStockRegistry"),
        },
        expected={"address": actor_address, "blocked": False},
    )

    exposure = plan["maximumExposureProposal"]
    native_required = int(exposure["wrapNativeWei"]) + int(
        exposure["minimumNativeReserveBeforeGasWei"]
    )
    pltr_required = int(exposure["maximumPltrTransfer"]) + int(
        exposure["minimumPltrReserveAfterLiquidity"]
    )
    native_balance = int(actor.get("nativeBalanceWei", "0"))
    pltr_balance = int(actor.get("stockBalances", {}).get("PLTR", "0"))
    weth_balance = int(actor.get("wethBalance", "-1"))
    _add_check(
        checks,
        "actor native balance covers wrap plus reserve before gas",
        native_balance >= native_required,
        actual=str(native_balance),
        expected=f">={native_required}",
    )
    _add_check(
        checks,
        "actor PLTR balance covers LP cap plus reserve",
        pltr_balance >= pltr_required,
        actual=str(pltr_balance),
        expected=f">={pltr_required}",
    )
    _add_check(
        checks,
        "actor starts with zero WETH for deterministic wrap accounting",
        weth_balance == 0,
        actual=str(weth_balance),
        expected="0",
    )

    snapshot = qualification.get("snapshot", {})
    block_tag = hex(int(snapshot.get("blockNumber", -1)))
    pending_nonce = int(
        rpc.call(
            "eth_getTransactionCount",
            [qualifier.normalize_address(actor_address), "pending"],
        ),
        16,
    )
    confirmed_nonce = int(actor.get("confirmedNonce", -1))
    _add_check(
        checks,
        "actor has no pending nonce gap",
        pending_nonce == confirmed_nonce,
        actual={"confirmed": confirmed_nonce, "pending": pending_nonce},
        expected="confirmed == pending",
    )

    erc_allowances: dict[str, str] = {}
    permit_allowances: dict[str, dict[str, int | str]] = {}
    for symbol, token in (
        ("PLTR", plan["contracts"]["pltr"]),
        ("WETH", plan["contracts"]["weth"]),
    ):
        erc_allowance = int(
            qualifier.contract_call(
                rpc,
                block_tag,
                token,
                "allowance(address,address)",
                return_types=["uint256"],
                argument_types=["address", "address"],
                arguments=[actor_address, plan["contracts"]["permit2"]],
            )
        )
        permit_amount, expiration, permit_nonce = qualifier.contract_call(
            rpc,
            block_tag,
            plan["contracts"]["permit2"],
            "allowance(address,address,address)",
            return_types=["uint160", "uint48", "uint48"],
            argument_types=["address", "address", "address"],
            arguments=[actor_address, token, plan["contracts"]["positionManager"]],
        )
        erc_allowances[symbol] = str(int(erc_allowance))
        permit_allowances[symbol] = {
            "amount": str(int(permit_amount)),
            "expiration": int(expiration),
            "nonce": int(permit_nonce),
        }
        _add_check(
            checks,
            f"actor {symbol} ERC20 allowance to Permit2 is zero",
            erc_allowance == 0,
            actual=str(erc_allowance),
            expected="0",
        )
        _add_check(
            checks,
            f"actor {symbol} Permit2 allowance to PositionManager is zero",
            int(permit_amount) == 0,
            actual=permit_allowances[symbol],
            expected={
                "amount": "0",
                "expiration": "informational",
                "nonce": "informational",
            },
        )

    next_token_id = int(
        qualifier.contract_call(
            rpc,
            block_tag,
            plan["contracts"]["positionManager"],
            "nextTokenId()",
            return_types=["uint256"],
        )
    )
    _add_check(
        checks,
        "PositionManager nextTokenId is readable and nonzero",
        next_token_id > 0,
        actual=str(next_token_id),
        expected=">0 and must be rebound immediately before mint",
    )

    active_liquidity = int(
        qualifier.contract_call(
            rpc,
            block_tag,
            plan["contracts"]["stateView"],
            "getLiquidity(bytes32)",
            return_types=["uint128"],
            argument_types=["bytes32"],
            arguments=[bytes.fromhex(plan["market"]["poolId"][2:])],
        )
    )
    _add_check(
        checks,
        "exact PoolId active liquidity is zero before initialization",
        active_liquidity == 0,
        actual=str(active_liquidity),
        expected="0",
    )

    predicted_code: dict[str, dict[str, Any]] = {}
    for name in ("panopticPool", "collateralTracker0", "collateralTracker1"):
        address = plan["predictedMarketContracts"][name]
        identity = qualifier.code_identity(
            rpc.call("eth_getCode", [qualifier.normalize_address(address), block_tag])
        )
        predicted_code[name] = {"address": address, **identity}
        _add_check(
            checks,
            f"predicted {name} address has empty code",
            identity["runtimeBytes"] == 0,
            actual=predicted_code[name],
            expected={"address": address, "runtimeBytes": 0},
        )

    failed = [check for check in checks if check["status"] != "PASS"]
    return {
        "schemaVersion": 1,
        "status": (
            "PASS_INITIAL_MARKET_PREFLIGHT"
            if not failed
            else "BLOCKED_INITIAL_MARKET_PREFLIGHT_FAILED"
        ),
        "mode": "READ_ONLY_REHEARSAL_PREFLIGHT_NO_KEYS_NO_SIGNING_NO_BROADCAST",
        "network": {
            "chainId": CHAIN_ID,
            "blockNumber": snapshot.get("blockNumber"),
            "blockHash": snapshot.get("blockHash"),
            "blockTimestamp": snapshot.get("blockTimestamp"),
        },
        "plan": {
            "planBodySha256": plan["planBodySha256"],
            "poolId": plan["market"]["poolId"],
            "actor": actor_address,
        },
        "observations": {
            "actorConfirmedNonce": confirmed_nonce,
            "actorPendingNonce": pending_nonce,
            "positionManagerNextTokenId": str(next_token_id),
            "activeLiquidity": str(active_liquidity),
            "erc20Allowances": erc_allowances,
            "permit2Allowances": permit_allowances,
            "predictedAddressCode": predicted_code,
        },
        "checks": {
            "passed": len(checks) - len(failed),
            "failed": len(failed),
            "results": checks,
        },
        "qualificationChecks": qualification.get("checks"),
        "publicExecution": {
            "ready": False,
            "blockingReasons": [
                "owner has not accepted the exact exposure proposal",
                "plan nonces are null",
                "plan deadlines are historical rehearsal values",
                "exact-head positive and negative fork rehearsal is not yet committed",
                "no execution operator or broadcast authorization exists for this plan",
            ],
        },
        "authorization": dict(plan["authorization"]),
        "nextGate": "LOCAL_EXACT_HEAD_FORK_REHEARSAL_OF_UNACCEPTED_EXPOSURE_PROPOSAL",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--chain-manifest", type=Path, default=DEFAULT_CHAIN)
    parser.add_argument("--deployment-manifest", type=Path, default=DEFAULT_DEPLOYMENT)
    parser.add_argument("--actor-manifest", type=Path, default=DEFAULT_ACTOR)
    parser.add_argument(
        "--rpc-url", help="Read-only RPC override; defaults to chain manifest"
    )
    parser.add_argument("--transport", choices=("cast", "urllib"), default="cast")
    parser.add_argument("--block", type=int, help="Pin verification to this block")
    parser.add_argument("--output", type=Path, help="Optional JSON evidence output")
    parser.add_argument("--compact", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        plan = load_json(args.plan)
        validate_offline_plan(plan, args.plan)
        chain = load_json(args.chain_manifest)
        deployment = load_json(args.deployment_manifest)
        actor = load_json(args.actor_manifest)
        rpc_url = args.rpc_url or chain["network"]["rpcUrl"]
        rpc = (
            qualifier.CastReadOnlyRpc(rpc_url)
            if args.transport == "cast"
            else qualifier.ReadOnlyRpc(rpc_url)
        )
        qualification = qualifier.qualify(
            rpc, chain, deployment, actor, block=args.block
        )
        report = verify_initial_prestate(rpc, plan, qualification)
        report["sourceBindings"] = {
            "verifierSha256": file_sha256(Path(__file__)),
            "planFileSha256": file_sha256(args.plan),
            "qualifierSha256": file_sha256(Path(qualifier.__file__)),
            "chainManifestSha256": file_sha256(args.chain_manifest),
            "deploymentManifestSha256": file_sha256(args.deployment_manifest),
            "actorManifestSha256": file_sha256(args.actor_manifest),
        }
    except Exception as exc:
        report = {
            "schemaVersion": 1,
            "status": "BLOCKED_RPC_OR_INPUT_ERROR",
            "mode": "READ_ONLY_REHEARSAL_PREFLIGHT_NO_KEYS_NO_SIGNING_NO_BROADCAST",
            "error": f"{type(exc).__name__}: {exc}",
            "publicExecution": {"ready": False},
            "authorization": {"publicBroadcast": False, "signing": False},
        }

    encoded = json.dumps(report, indent=None if args.compact else 2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8", newline="\n")
    print(encoded)
    return 0 if report["status"] == "PASS_INITIAL_MARKET_PREFLIGHT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
