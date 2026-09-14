#!/usr/bin/env python3
"""Capture one pinned, read-only PLTR/WETH lifecycle input snapshot.

The resulting JSON is planning evidence only. This process allowlists read-only
JSON-RPC methods, pins every state read to one immutable block, never loads a
wallet, and has no signing or transaction-submission capability.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_CHAIN = REPOSITORY / "manifests" / "chains" / "robinhood-testnet-46630.json"
DEFAULT_GENESIS = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-public-genesis-2026-09-11.json"
)
DEFAULT_POLICY = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-lifecycle-inputs-2026-09-11.json"
)
DEFAULT_OUTPUT = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-lifecycle-inputs-2026-09-14.json"
)
DEFAULT_RPC_URL = "https://rpc.testnet.chain.robinhood.com"
REHEARSAL_EXPIRY_SECONDS = 24 * 60 * 60


def _load_sibling(name: str, filename: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required sibling module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


qualifier = _load_sibling("stonkhedge_market_qualifier", "qualify_robinhood_market.py")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON manifest must contain an object: {path}")
    return value


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _call(
    rpc: Any,
    block_tag: str,
    to: str,
    signature: str,
    return_types: list[str],
    argument_types: list[str] | None = None,
    arguments: list[Any] | None = None,
):
    return qualifier.contract_call(
        rpc,
        block_tag,
        to,
        signature,
        return_types=return_types,
        argument_types=argument_types or [],
        arguments=arguments or [],
    )


def _balance(rpc: Any, block_tag: str, token: str, account: str) -> int:
    return int(
        _call(
            rpc,
            block_tag,
            token,
            "balanceOf(address)",
            ["uint256"],
            ["address"],
            [account],
        )
    )


def _erc20_allowance(
    rpc: Any, block_tag: str, token: str, owner: str, spender: str
) -> int:
    return int(
        _call(
            rpc,
            block_tag,
            token,
            "allowance(address,address)",
            ["uint256"],
            ["address", "address"],
            [owner, spender],
        )
    )


def _permit2_allowance(
    rpc: Any,
    block_tag: str,
    permit2: str,
    owner: str,
    token: str,
    spender: str,
) -> list[int]:
    values = _call(
        rpc,
        block_tag,
        permit2,
        "allowance(address,address,address)",
        ["uint160", "uint48", "uint48"],
        ["address", "address", "address"],
        [owner, token, spender],
    )
    return [int(value) for value in values]


def _actor(
    rpc: Any,
    block_tag: str,
    *,
    address: str,
    role: str,
    pltr: str,
    weth: str,
    permit2: str,
    router: str,
    tracker0: str,
    tracker1: str,
    panoptic_pool: str,
    registry: str,
) -> dict[str, Any]:
    account = qualifier.normalize_address(address)
    code = qualifier.code_identity(rpc.call("eth_getCode", [account, block_tag]))
    if code["runtimeBytes"] != 0:
        raise RuntimeError(f"actor is not an EOA: {account}")
    initial_allowances = {
        "pltrToPermit2": str(
            _erc20_allowance(rpc, block_tag, pltr, account, permit2)
        ),
        "wethToPermit2": str(
            _erc20_allowance(rpc, block_tag, weth, account, permit2)
        ),
        "pltrToTracker0": str(
            _erc20_allowance(rpc, block_tag, pltr, account, tracker0)
        ),
        "wethToTracker1": str(
            _erc20_allowance(rpc, block_tag, weth, account, tracker1)
        ),
        "pltrPermit2ToRouter": _permit2_allowance(
            rpc, block_tag, permit2, account, pltr, router
        ),
        "wethPermit2ToRouter": _permit2_allowance(
            rpc, block_tag, permit2, account, weth, router
        ),
    }
    if any(
        int(initial_allowances[name]) != 0
        for name in (
            "pltrToPermit2",
            "wethToPermit2",
            "pltrToTracker0",
            "wethToTracker1",
        )
    ):
        raise RuntimeError(f"actor has elevated ERC20 allowance: {account}")
    if (
        initial_allowances["pltrPermit2ToRouter"][0] != 0
        or initial_allowances["wethPermit2ToRouter"][0] != 0
    ):
        raise RuntimeError(f"actor has elevated Permit2 allowance: {account}")

    blocked = bool(
        _call(
            rpc,
            block_tag,
            registry,
            "isBlocked(address)",
            ["bool"],
            ["address"],
            [account],
        )
    )
    if blocked:
        raise RuntimeError(f"actor is blocked by the Stock registry: {account}")
    open_legs = int(
        _call(
            rpc,
            block_tag,
            panoptic_pool,
            "numberOfLegs(address)",
            ["uint256"],
            ["address"],
            [account],
        )
    )
    tracker0_shares = _balance(rpc, block_tag, tracker0, account)
    tracker1_shares = _balance(rpc, block_tag, tracker1, account)
    if open_legs != 0 or tracker0_shares != 0 or tracker1_shares != 0:
        raise RuntimeError(f"actor does not have a clean lifecycle start: {account}")

    return {
        "address": account,
        "role": role,
        "confirmedNonce": int(
            rpc.call("eth_getTransactionCount", [account, block_tag]), 16
        ),
        "nativeBalanceWei": str(
            int(rpc.call("eth_getBalance", [account, block_tag]), 16)
        ),
        "pltrBalance": str(_balance(rpc, block_tag, pltr, account)),
        "wethBalance": str(_balance(rpc, block_tag, weth, account)),
        "collateralTracker0Shares": str(tracker0_shares),
        "collateralTracker1Shares": str(tracker1_shares),
        "openLegs": open_legs,
        "blockedByStockRegistry": blocked,
        "initialAllowances": initial_allowances,
    }


def capture(
    rpc: Any,
    *,
    chain: dict[str, Any],
    genesis: dict[str, Any],
    policy: dict[str, Any],
    buyer_address: str,
    block_number: int | None = None,
    source_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    chain_id = int(rpc.call("eth_chainId", []), 16)
    if chain_id != 46630:
        raise RuntimeError(f"unexpected chain ID: {chain_id}")
    if block_number is None:
        block_number = int(rpc.call("eth_blockNumber", []), 16)
    block_tag = hex(block_number)
    header = rpc.call("eth_getBlockByNumber", [block_tag, False])
    if not isinstance(header, dict) or int(header["number"], 16) != block_number:
        raise RuntimeError("pinned block header is malformed")
    if not header.get("hash"):
        raise RuntimeError("pinned block has no hash")

    market = genesis["market"]
    registered = genesis["registeredMarket"]
    pltr = qualifier.normalize_address(market["asset"]["address"])
    weth = qualifier.normalize_address(market["quoteAsset"]["address"])
    tracker0 = qualifier.normalize_address(registered["collateralTracker0"]["address"])
    tracker1 = qualifier.normalize_address(registered["collateralTracker1"]["address"])
    panoptic_pool = qualifier.normalize_address(registered["panopticPool"]["address"])
    permit2 = qualifier.normalize_address(chain["infrastructure"]["permit2"]["address"])
    router = qualifier.normalize_address(
        chain["infrastructure"]["universalRouter"]["address"]
    )
    registry = qualifier.normalize_address(
        chain["sharedStockInfrastructure"]["registryAndBeacon"]
    )
    state_view = qualifier.normalize_address(
        chain["infrastructure"]["stateView"]["address"]
    )
    writer_address = qualifier.normalize_address(policy["actors"]["writer"]["address"])
    buyer_address = qualifier.normalize_address(buyer_address)
    deployer = qualifier.normalize_address(chain["deployer"]["address"])
    if buyer_address in {writer_address, deployer}:
        raise RuntimeError("buyer must be a third account distinct from writer and deployer")

    slot0 = _call(
        rpc,
        block_tag,
        state_view,
        "getSlot0(bytes32)",
        ["uint160", "int24", "uint24", "uint24"],
        ["bytes32"],
        [bytes.fromhex(market["poolId"][2:])],
    )
    liquidity = int(
        _call(
            rpc,
            block_tag,
            state_view,
            "getLiquidity(bytes32)",
            ["uint128"],
            ["bytes32"],
            [bytes.fromhex(market["poolId"][2:])],
        )
    )
    registry_paused = bool(
        _call(rpc, block_tag, registry, "paused()", ["bool"])
    )
    token_paused = bool(_call(rpc, block_tag, pltr, "tokenPaused()", ["bool"]))
    ui_multiplier = int(_call(rpc, block_tag, pltr, "uiMultiplier()", ["uint256"]))
    pending_multiplier = int(
        _call(rpc, block_tag, pltr, "newUIMultiplier()", ["uint256"])
    )
    effective_at = int(_call(rpc, block_tag, pltr, "effectiveAt()", ["uint256"]))
    required = chain["requiredStockState"]
    if (
        registry_paused
        or token_paused
        or str(ui_multiplier) != str(required["uiMultiplier"])
        or str(pending_multiplier) != str(required["newUiMultiplier"])
        or str(effective_at) != str(required["effectiveAt"])
    ):
        raise RuntimeError("Stock Token controls are not eligible for lifecycle planning")

    actors = {
        "writer": _actor(
            rpc,
            block_tag,
            address=writer_address,
            role="UNPRIVILEGED_SECOND_ACTOR_LP_OWNER_AND_BOUNDED_SHORT_WRITER",
            pltr=pltr,
            weth=weth,
            permit2=permit2,
            router=router,
            tracker0=tracker0,
            tracker1=tracker1,
            panoptic_pool=panoptic_pool,
            registry=registry,
        ),
        "buyer": _actor(
            rpc,
            block_tag,
            address=buyer_address,
            role="UNPRIVILEGED_THIRD_ACTOR_BOUNDED_TEST_BUYER",
            pltr=pltr,
            weth=weth,
            permit2=permit2,
            router=router,
            tracker0=tracker0,
            tracker1=tracker1,
            panoptic_pool=panoptic_pool,
            registry=registry,
        ),
    }
    exposure = deepcopy(policy["proposedExposure"])
    timestamp_unix = int(header["timestamp"], 16)
    expiry = timestamp_unix + REHEARSAL_EXPIRY_SECONDS
    exposure["rehearsalOnlyExpiry"] = {
        "unix": expiry,
        "utc": datetime.fromtimestamp(expiry, timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "rule": "A public candidate must replace this with a fresh, short-lived deadline and Permit2 expiry after exact-head replay.",
    }

    if int(actors["writer"]["pltrBalance"]) < int(
        exposure["writerCollateral"]["pltrAssets"]
    ) + int(exposure["writerSwapBudget"]["pltrTotalInput"]):
        raise RuntimeError("writer PLTR funding is below the frozen cap")
    if int(actors["writer"]["wethBalance"]) < int(
        exposure["writerCollateral"]["wethAssets"]
    ) + int(exposure["writerSwapBudget"]["wethTotalInput"]):
        raise RuntimeError("writer WETH funding is below the frozen cap")
    if int(actors["buyer"]["pltrBalance"]) < int(
        exposure["buyerCollateral"]["pltrAssets"]
    ):
        raise RuntimeError("buyer PLTR funding is below the frozen cap")
    buyer_after_wrap = int(actors["buyer"]["nativeBalanceWei"]) - int(
        exposure["buyerWrapNativeWei"]
    )
    if buyer_after_wrap < int(exposure["nativeReserveFloorsBeforeGas"]["buyerAfterWrap"]):
        raise RuntimeError("buyer native funding is below the frozen reserve floor")

    paths = source_paths or {}
    source_bindings = {
        f"{name}Sha256": file_sha256(path) for name, path in paths.items()
    }
    timestamp_utc = (
        datetime.fromtimestamp(timestamp_unix, timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return {
        "schemaVersion": 2,
        "status": "READ_ONLY_PINNED_SNAPSHOT_PASS_THIRD_BUYER_LIFECYCLE_PROPOSAL_NOT_AUTHORIZED",
        "mode": "PINNED_PUBLIC_READS_NO_KEYS_NO_SIGNING_NO_BROADCAST",
        "classification": policy["classification"],
        "warning": policy["warning"],
        "sourceBindings": source_bindings,
        "network": {
            "name": chain["network"]["name"],
            "chainId": chain_id,
            "rpc": chain["network"]["rpcUrl"],
            "referenceBlock": block_number,
            "referenceBlockHash": header["hash"].lower(),
            "referenceTimestampUnix": timestamp_unix,
            "referenceTimestampUtc": timestamp_utc,
        },
        "marketState": {
            "poolId": market["poolId"],
            "sfpmPoolId": registered["sfpmPoolId"],
            "sqrtPriceX96": str(int(slot0[0])),
            "currentTick": int(slot0[1]),
            "twapTick": None,
            "twapObservation": "NOT_CAPTURED_SPOT_TICK_IS_NOT_LABELLED_AS_TWAP",
            "activeLiquidity": str(liquidity),
            "registryPaused": registry_paused,
            "stockTokenPaused": token_paused,
            "stockUiMultiplier": str(ui_multiplier),
            "stockPendingMultiplier": str(pending_multiplier),
            "stockMultiplierEffectiveAt": str(effective_at),
        },
        "actors": actors,
        "proposedExposure": exposure,
        "roleRisk": {
            "accepted": False,
            "finding": "The buyer is a dedicated third unprivileged actor, distinct from the writer and shared deployer/guardian/treasurer.",
            "containment": [
                "only ordinary WETH, ERC20, Permit2, UniversalRouter, CollateralTracker, and PanopticPool user calls are proposed",
                "no registry, guardian, treasurer, ownership, factory-admin, upgrade, or deployment call is permitted",
                "all public execution fields remain false and every nonce remains null",
            ],
        },
        "authorization": {key: False for key in policy["authorization"]},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL)
    parser.add_argument("--buyer", required=True)
    parser.add_argument("--block-number", type=int)
    parser.add_argument("--chain", type=Path, default=DEFAULT_CHAIN)
    parser.add_argument("--genesis", type=Path, default=DEFAULT_GENESIS)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    chain = load_json(args.chain)
    genesis = load_json(args.genesis)
    policy = load_json(args.policy)
    rpc = qualifier.CastReadOnlyRpc(args.rpc_url)
    captured = capture(
        rpc,
        chain=chain,
        genesis=genesis,
        policy=policy,
        buyer_address=args.buyer,
        block_number=args.block_number,
        source_paths={
            "chainManifest": args.chain,
            "genesisManifest": args.genesis,
            "exposurePolicy": args.policy,
            "snapshotter": Path(__file__).resolve(),
        },
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(captured, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                "status": captured["status"],
                "output": str(args.output),
                "referenceBlock": captured["network"]["referenceBlock"],
                "referenceBlockHash": captured["network"]["referenceBlockHash"],
                "writer": captured["actors"]["writer"]["address"],
                "buyer": captured["actors"]["buyer"]["address"],
                "signing": False,
                "publicBroadcast": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
