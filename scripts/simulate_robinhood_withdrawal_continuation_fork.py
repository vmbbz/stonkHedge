#!/usr/bin/env python3
"""Replay the four state-derived withdrawals on the existing loopback fork.

This simulator must attach to the same Anvil process immediately after the
bound lifecycle rehearsal. It impersonates only the two public user accounts,
uses no keys or signatures, and refuses non-loopback or non-Anvil RPCs.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from eth_abi import decode as abi_decode


REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_WITHDRAWAL_PLAN = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-withdrawal-continuation-proposal-2026-09-14.json"
)
DEFAULT_LIFECYCLE_PLAN = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-lifecycle-proposal-2026-09-14.json"
)
DEFAULT_LIFECYCLE_REPORT = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-lifecycle-fork-rehearsal-2026-09-14.json"
)
DEFAULT_REPORT = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-withdrawal-fork-rehearsal-2026-09-14.json"
)
DEFAULT_RPC_URL = "http://127.0.0.1:8551"


def _load_sibling(name: str, filename: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required sibling module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lifecycle_simulator = _load_sibling(
    "stonkhedge_lifecycle_simulator", "simulate_robinhood_two_actor_lifecycle_fork.py"
)
withdrawal_preparer = _load_sibling(
    "stonkhedge_withdrawal_preparer", "prepare_robinhood_withdrawal_continuation.py"
)
qualifier = lifecycle_simulator.qualifier


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


def validate_plan(
    withdrawal_plan: dict[str, Any],
    lifecycle_plan: dict[str, Any],
    lifecycle_plan_path: Path,
    lifecycle_report: dict[str, Any],
    lifecycle_report_path: Path,
) -> None:
    if (
        withdrawal_plan.get("status")
        != "OFFLINE_STATE_DERIVED_WITHDRAWAL_PROPOSAL_REPLAY_REQUIRED_NO_EXECUTION_AUTHORITY"
    ):
        raise ValueError("withdrawal plan status drifted")
    if (
        withdrawal_plan.get("mode")
        != "POST_CLOSE_REPORT_BOUND_NO_RPC_NO_KEYS_NO_SIGNING_NO_BROADCAST"
    ):
        raise ValueError("withdrawal plan mode drifted")
    if not _all_false(withdrawal_plan.get("authorization")):
        raise ValueError("withdrawal authorization must remain entirely false")
    if withdrawal_plan.get("publicExecution", {}).get("ready") is not False:
        raise ValueError("withdrawal public execution must remain disabled")
    transactions = withdrawal_plan.get("transactions")
    if not isinstance(transactions, list) or len(transactions) != 4:
        raise ValueError("withdrawal plan must contain exactly four calls")
    if withdrawal_plan.get("transactionCount") != 4:
        raise ValueError("withdrawal transaction count drifted")
    body = dict(withdrawal_plan)
    expected_hash = body.pop("planBodySha256", None)
    if expected_hash != canonical_sha256(body):
        raise ValueError("withdrawal plan body hash drifted")

    bindings = withdrawal_plan["sourceBindings"]
    if bindings["lifecyclePlanBodySha256"] != lifecycle_plan["planBodySha256"]:
        raise ValueError("withdrawal lifecycle body binding drifted")
    if bindings["lifecyclePlanFileSha256"] != file_sha256(lifecycle_plan_path):
        raise ValueError("withdrawal lifecycle file binding drifted")
    if bindings["lifecycleRehearsalFileSha256"] != file_sha256(
        lifecycle_report_path
    ):
        raise ValueError("withdrawal rehearsal file binding drifted")
    if bindings["preparerSha256"] != file_sha256(
        Path(withdrawal_preparer.__file__).resolve()
    ):
        raise ValueError("withdrawal preparer binding drifted")
    if lifecycle_report.get("publicExecution", {}).get("broadcastAttempted") is not False:
        raise ValueError("source lifecycle report is not a local-only rehearsal")

    writer = qualifier.normalize_address(lifecycle_plan["roles"]["writer"]["address"])
    buyer = qualifier.normalize_address(lifecycle_plan["roles"]["buyer"]["address"])
    expected_sequence = [
        (buyer, qualifier.normalize_address(lifecycle_plan["market"]["collateralTracker0"])),
        (buyer, qualifier.normalize_address(lifecycle_plan["market"]["collateralTracker1"])),
        (writer, qualifier.normalize_address(lifecycle_plan["market"]["collateralTracker0"])),
        (writer, qualifier.normalize_address(lifecycle_plan["market"]["collateralTracker1"])),
    ]
    for ordinal, (transaction, expected) in enumerate(
        zip(transactions, expected_sequence, strict=True)
    ):
        if transaction.get("ordinal") != ordinal or transaction.get("nonce") is not None:
            raise ValueError(f"withdrawal transaction {ordinal} ordering or nonce drifted")
        actual = (
            qualifier.normalize_address(transaction["sender"]),
            qualifier.normalize_address(transaction["to"]),
        )
        if actual != expected:
            raise ValueError(f"withdrawal transaction {ordinal} role/target drifted")
        calldata = transaction.get("calldata", "")
        if not isinstance(calldata, str) or not calldata.startswith("0x"):
            raise ValueError(f"withdrawal transaction {ordinal} calldata is malformed")
        if "0x" + qualifier.keccak(bytes.fromhex(calldata[2:])).hex() != transaction.get(
            "calldataKeccak256"
        ):
            raise ValueError(f"withdrawal transaction {ordinal} calldata hash drifted")


def assert_attached_terminal_state(
    client: Any,
    withdrawal_plan: dict[str, Any],
    lifecycle_plan: dict[str, Any],
    lifecycle_report: dict[str, Any],
) -> dict[str, Any]:
    version = client.call("web3_clientVersion", [])
    if not isinstance(version, str) or "anvil" not in version.lower():
        raise RuntimeError(f"refusing non-Anvil client: {version}")
    if int(client.call("eth_chainId", []), 16) != 46630:
        raise RuntimeError("withdrawal fork chain ID drifted")
    latest = client.call("eth_getBlockByNumber", ["latest", False])
    expected_block = int(withdrawal_plan["sourcePostCloseBlock"])
    expected_hash = lifecycle_report["transactions"][-1]["blockHash"].lower()
    if int(latest["number"], 16) != expected_block:
        raise RuntimeError("withdrawal fork is not at the bound post-close block")
    if latest["hash"].lower() != expected_hash:
        raise RuntimeError("withdrawal post-close block hash drifted")
    observed = lifecycle_simulator.observe(client, lifecycle_plan)
    if observed != lifecycle_report["milestones"]["afterIndex24"]:
        raise RuntimeError("withdrawal initial state differs from the bound terminal state")
    return {
        "clientVersion": version,
        "chainId": 46630,
        "postCloseBlock": expected_block,
        "postCloseBlockHash": expected_hash,
        "terminalStateMatched": True,
    }


def assert_withdrawal_postconditions(
    lifecycle_plan: dict[str, Any],
    transaction: dict[str, Any],
    before: dict[str, Any],
    after: dict[str, Any],
    pre_accrual_preview_shares: int,
    event_assets: int,
    event_shares: int,
    receipt_burned_shares: int,
) -> dict[str, Any]:
    sender = qualifier.normalize_address(transaction["sender"])
    role = next(
        name
        for name in ("writer", "buyer")
        if qualifier.normalize_address(lifecycle_plan["roles"][name]["address"])
        == sender
    )
    tracker0 = qualifier.normalize_address(
        lifecycle_plan["market"]["collateralTracker0"]
    )
    tracker_index = (
        0 if qualifier.normalize_address(transaction["to"]) == tracker0 else 1
    )
    symbol = "pltr" if tracker_index == 0 else "weth"
    balance_name = f"{symbol}Balance"
    shares_name = f"tracker{tracker_index}Shares"
    assets = int(transaction["decodedIntent"]["assets"])
    received = int(after[role][balance_name]) - int(before[role][balance_name])
    shares_burned = int(before[role][shares_name]) - int(after[role][shares_name])
    if event_assets != assets:
        raise RuntimeError(f"withdrawal {transaction['ordinal']} event assets drifted")
    if received != assets:
        raise RuntimeError(f"withdrawal {transaction['ordinal']} asset receipt drifted")
    if shares_burned != receipt_burned_shares:
        raise RuntimeError(f"withdrawal {transaction['ordinal']} share burn drifted")
    if event_shares > receipt_burned_shares:
        raise RuntimeError(
            f"withdrawal {transaction['ordinal']} event shares exceed receipt burns"
        )
    return {
        "ordinal": transaction["ordinal"],
        "role": role,
        "asset": symbol.upper(),
        "assets": str(assets),
        "eventAssets": str(event_assets),
        "underlyingReceived": str(received),
        "preAccrualPreviewWithdrawShares": str(pre_accrual_preview_shares),
        "eventShares": str(event_shares),
        "interestAccrualSharesBurned": str(receipt_burned_shares - event_shares),
        "receiptTransferToZeroShares": str(receipt_burned_shares),
        "sharesBurned": str(shares_burned),
        "status": "PASS_EXACT_ASSETS_AND_RECEIPT_RECONCILED_SHARE_BURNS",
    }


def withdrawal_event(receipt: dict[str, Any], tracker: str) -> tuple[int, int]:
    topic0 = "0x" + qualifier.keccak(
        b"Withdraw(address,address,address,uint256,uint256)"
    ).hex()
    matching = [
        log
        for log in receipt.get("logs", [])
        if qualifier.normalize_address(log.get("address", ""))
        == qualifier.normalize_address(tracker)
        and len(log.get("topics", [])) > 0
        and log["topics"][0].lower() == topic0.lower()
    ]
    if len(matching) != 1:
        raise RuntimeError("withdrawal receipt must contain exactly one tracker Withdraw event")
    data = matching[0].get("data", "")
    if not isinstance(data, str) or not data.startswith("0x"):
        raise RuntimeError("withdrawal event data is malformed")
    assets, shares = abi_decode(["uint256", "uint256"], bytes.fromhex(data[2:]))
    return int(assets), int(shares)


def receipt_burned_shares(
    receipt: dict[str, Any], tracker: str, owner: str
) -> int:
    topic0 = "0x" + qualifier.keccak(b"Transfer(address,address,uint256)").hex()
    owner_topic = "0x" + qualifier.normalize_address(owner)[2:].rjust(64, "0")
    zero_topic = "0x" + "00" * 32
    burned = 0
    for log in receipt.get("logs", []):
        topics = log.get("topics", [])
        if (
            qualifier.normalize_address(log.get("address", ""))
            != qualifier.normalize_address(tracker)
            or len(topics) != 3
            or topics[0].lower() != topic0.lower()
            or topics[1].lower() != owner_topic.lower()
            or topics[2].lower() != zero_topic
        ):
            continue
        data = log.get("data", "")
        if not isinstance(data, str) or not data.startswith("0x"):
            raise RuntimeError("tracker burn event data is malformed")
        (amount,) = abi_decode(["uint256"], bytes.fromhex(data[2:]))
        burned += int(amount)
    if burned <= 0:
        raise RuntimeError("withdrawal receipt contains no tracker share burn")
    return burned


def simulate(
    withdrawal_plan: dict[str, Any],
    lifecycle_plan: dict[str, Any],
    lifecycle_plan_path: Path,
    lifecycle_report: dict[str, Any],
    lifecycle_report_path: Path,
    client: Any,
) -> dict[str, Any]:
    validate_plan(
        withdrawal_plan,
        lifecycle_plan,
        lifecycle_plan_path,
        lifecycle_report,
        lifecycle_report_path,
    )
    attached = assert_attached_terminal_state(
        client, withdrawal_plan, lifecycle_plan, lifecycle_report
    )
    snapshot = client.call("evm_snapshot", [])
    writer = qualifier.normalize_address(lifecycle_plan["roles"]["writer"]["address"])
    buyer = qualifier.normalize_address(lifecycle_plan["roles"]["buyer"]["address"])
    receipts: list[dict[str, Any]] = []
    postconditions: list[dict[str, Any]] = []
    for actor in (writer, buyer):
        client.call("anvil_impersonateAccount", [actor])
    try:
        for transaction in withdrawal_plan["transactions"]:
            before = lifecycle_simulator.observe(client, lifecycle_plan)
            sender = qualifier.normalize_address(transaction["sender"])
            role = next(
                name
                for name in ("writer", "buyer")
                if qualifier.normalize_address(lifecycle_plan["roles"][name]["address"])
                == sender
            )
            tracker0 = qualifier.normalize_address(
                lifecycle_plan["market"]["collateralTracker0"]
            )
            tracker_index = (
                0 if qualifier.normalize_address(transaction["to"]) == tracker0 else 1
            )
            assets = int(transaction["decodedIntent"]["assets"])
            live_maximum = int(before[role][f"tracker{tracker_index}MaxWithdraw"])
            if live_maximum < assets:
                raise RuntimeError(
                    f"withdrawal {transaction['ordinal']} exceeds fresh maxWithdraw"
                )
            preview_shares = int(
                lifecycle_simulator._contract_call(
                    client,
                    transaction["to"],
                    "previewWithdraw(uint256)",
                    ["uint256"],
                    ["uint256"],
                    [assets],
                )
            )
            receipt = lifecycle_simulator.send_local(
                client, transaction, lifecycle_simulator.DEFAULT_TRANSACTION_GAS
            )
            receipts.append(lifecycle_simulator.receipt_summary(transaction, receipt))
            event_assets, event_shares = withdrawal_event(receipt, transaction["to"])
            burned_shares = receipt_burned_shares(
                receipt, transaction["to"], transaction["sender"]
            )
            after = lifecycle_simulator.observe(client, lifecycle_plan)
            postconditions.append(
                assert_withdrawal_postconditions(
                    lifecycle_plan,
                    transaction,
                    before,
                    after,
                    preview_shares,
                    event_assets,
                    event_shares,
                    burned_shares,
                )
            )
    except Exception:
        if client.call("evm_revert", [snapshot]) is not True:
            raise RuntimeError("could not restore post-close snapshot after withdrawal failure")
        raise
    finally:
        for actor in (writer, buyer):
            client.call("anvil_stopImpersonatingAccount", [actor])

    final = lifecycle_simulator.observe(client, lifecycle_plan)
    residual_limit = int(withdrawal_plan["maximumResidualRawUnitsPerAsset"])
    residuals: dict[str, dict[str, str]] = {}
    for role in ("writer", "buyer"):
        if final[role]["openLegs"] != 0:
            raise RuntimeError(f"{role} regained an unexpected option leg")
        residuals[role] = {}
        for tracker_index, symbol in ((0, "PLTR"), (1, "WETH")):
            residual = int(final[role][f"tracker{tracker_index}Assets"])
            if residual > residual_limit:
                raise RuntimeError(f"{role} {symbol} residual exceeds the bound")
            residuals[role][symbol] = str(residual)

    return {
        "schemaVersion": 1,
        "status": "PASS_LOOPBACK_STATE_DERIVED_WITHDRAWAL_SEQUENCE",
        "mode": "BOUND_POST_CLOSE_ANVIL_IMPERSONATION_NO_KEYS_NO_SIGNING_NO_PUBLIC_BROADCAST",
        "classification": withdrawal_plan["classification"],
        "sourceBindings": {
            "withdrawalPlanBodySha256": withdrawal_plan["planBodySha256"],
            "withdrawalPlanFileSha256": file_sha256(DEFAULT_WITHDRAWAL_PLAN),
            "lifecyclePlanBodySha256": lifecycle_plan["planBodySha256"],
            "lifecyclePlanFileSha256": file_sha256(lifecycle_plan_path),
            "lifecycleRehearsalFileSha256": file_sha256(lifecycle_report_path),
            "simulatorSha256": file_sha256(Path(__file__)),
        },
        "attachedPostCloseState": attached,
        "transactions": receipts,
        "postconditions": postconditions,
        "finalState": final,
        "residualAssets": residuals,
        "authorization": withdrawal_plan["authorization"],
        "publicExecution": {"ready": False, "broadcastAttempted": False},
        "nextGate": "OWNER_REVIEW_ONLY_NO_PUBLIC_EXECUTION_OPERATOR_OR_AUTHORIZATION_EXISTS",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--withdrawal-plan", type=Path, default=DEFAULT_WITHDRAWAL_PLAN)
    parser.add_argument("--lifecycle-plan", type=Path, default=DEFAULT_LIFECYCLE_PLAN)
    parser.add_argument("--lifecycle-report", type=Path, default=DEFAULT_LIFECYCLE_REPORT)
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lifecycle_simulator.validate_local_rpc_url(args.rpc_url)
    withdrawal_plan = load_json(args.withdrawal_plan)
    lifecycle_plan = load_json(args.lifecycle_plan)
    lifecycle_report = load_json(args.lifecycle_report)
    client = lifecycle_simulator.genesis_simulator.JsonRpcClient(args.rpc_url)
    report = simulate(
        withdrawal_plan,
        lifecycle_plan,
        args.lifecycle_plan,
        lifecycle_report,
        args.lifecycle_report,
        client,
    )
    report["sourceBindings"]["withdrawalPlanFileSha256"] = file_sha256(
        args.withdrawal_plan
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
