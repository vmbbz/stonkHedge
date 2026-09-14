#!/usr/bin/env python3
"""Prepare a nonce-free withdrawal continuation from fresh post-close evidence.

This tool is deliberately offline. It accepts a lifecycle proposal and its
discarded-fork rehearsal report, verifies clean close state and state-derived
``maxWithdraw`` bounds, and emits four inspectable withdrawal calls. It has no
RPC, key, signing, transaction-submission, or broadcast capability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from eth_abi import encode as abi_encode
from eth_hash.auto import keccak


REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_LIFECYCLE_PLAN = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-lifecycle-proposal-2026-09-11.json"
)
DEFAULT_REHEARSAL = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-lifecycle-fork-rehearsal-2026-09-11.json"
)
DEFAULT_OUTPUT = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-withdrawal-continuation-proposal.json"
)
DEPLOYER = "0xca60c8ef6934f8a97c6a503c4e3a46e87f5b08bd"
MAX_RESIDUAL_RAW_UNITS = 2_000_000_000_000
WITHDRAWAL_EXECUTION_BUFFER_RAW_UNITS = 1_000_000_000_000


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


def normalize_address(value: str) -> str:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        raise ValueError(f"invalid address: {value}")
    int(value[2:], 16)
    return value.lower()


def _all_false(value: Any) -> bool:
    return isinstance(value, dict) and bool(value) and all(
        item is False for item in value.values()
    )


def assert_unprivileged_buyer(lifecycle_plan: dict[str, Any]) -> None:
    roles = lifecycle_plan["roles"]
    writer = normalize_address(roles["writer"]["address"])
    buyer = normalize_address(roles["buyer"]["address"])
    if writer == buyer:
        raise ValueError("writer and buyer must be distinct accounts")
    if buyer == DEPLOYER:
        raise ValueError(
            "execution preparation requires a third unprivileged buyer; "
            "the shared deployer/guardian/treasurer is not accepted"
        )
    if "UNPRIVILEGED" not in str(roles["buyer"].get("role", "")).upper():
        raise ValueError("buyer role must be explicitly classified as unprivileged")
    if roles.get("privilegedBuyerRisk", {}).get("accepted") is not False:
        raise ValueError("privileged-buyer risk field must remain false after replacement")


def _validate_sources(
    lifecycle_plan: dict[str, Any],
    lifecycle_path: Path,
    rehearsal: dict[str, Any],
    rehearsal_path: Path,
) -> dict[str, Any]:
    if (
        lifecycle_plan.get("status")
        != "OFFLINE_LIFECYCLE_PROPOSAL_OWNER_ACCEPTANCE_REQUIRED_NO_EXECUTION_AUTHORITY"
    ):
        raise ValueError("source lifecycle plan status is not accepted")
    if not _all_false(lifecycle_plan.get("authorization")):
        raise ValueError("source lifecycle authorization must remain entirely false")
    if not str(rehearsal.get("status", "")).startswith(
        "PASS_LOOPBACK_TWO_ACTOR_LIFECYCLE_THROUGH_CLOSE"
    ):
        raise ValueError("rehearsal did not pass through both closes")
    if rehearsal.get("publicExecution", {}).get("broadcastAttempted") is not False:
        raise ValueError("rehearsal must prove no public broadcast was attempted")
    bindings = rehearsal.get("sourceBindings", {})
    if bindings.get("lifecyclePlanBodySha256") != lifecycle_plan.get(
        "planBodySha256"
    ):
        raise ValueError("rehearsal lifecycle plan body hash drifted")
    if bindings.get("lifecyclePlanFileSha256") != file_sha256(lifecycle_path):
        raise ValueError("rehearsal lifecycle plan file hash drifted")
    if file_sha256(rehearsal_path) == "":  # pragma: no cover - defensive only
        raise ValueError("rehearsal file hash is empty")
    return bindings


def _assert_clean_terminal_actor(role: str, state: dict[str, Any]) -> None:
    if int(state["openLegs"]) != 0:
        raise ValueError(f"{role} still has open option legs")
    for name in (
        "pltrToPermit2",
        "wethToPermit2",
        "pltrToTracker0",
        "wethToTracker1",
    ):
        if int(state[name]) != 0:
            raise ValueError(f"{role} terminal allowance {name} is not zero")
    if int(state["pltrPermit2ToRouter"][0]) != 0:
        raise ValueError(f"{role} terminal PLTR Permit2 allowance is not zero")
    if int(state["wethPermit2ToRouter"][0]) != 0:
        raise ValueError(f"{role} terminal WETH Permit2 allowance is not zero")


def _withdraw_calldata(assets: int, receiver: str, owner: str) -> str:
    selector = keccak(b"withdraw(uint256,address,address)")[:4]
    return "0x" + (
        selector + abi_encode(["uint256", "address", "address"], [assets, receiver, owner])
    ).hex()


def build_withdrawal_plan(
    lifecycle_plan: dict[str, Any],
    lifecycle_path: Path,
    rehearsal: dict[str, Any],
    rehearsal_path: Path,
    *,
    script_path: Path | None = None,
) -> dict[str, Any]:
    _validate_sources(lifecycle_plan, lifecycle_path, rehearsal, rehearsal_path)
    assert_unprivileged_buyer(lifecycle_plan)
    terminal = rehearsal.get("milestones", {}).get("afterIndex24")
    if not isinstance(terminal, dict):
        raise ValueError("rehearsal omits the canonical post-close state")

    transactions: list[dict[str, Any]] = []
    residuals: dict[str, dict[str, str]] = {}
    sequence = (
        ("buyer", 0, "PLTR"),
        ("buyer", 1, "WETH"),
        ("writer", 0, "PLTR"),
        ("writer", 1, "WETH"),
    )
    for ordinal, (role, tracker_index, symbol) in enumerate(sequence):
        actor_state = terminal[role]
        _assert_clean_terminal_actor(role, actor_state)
        required_fields = (
            f"tracker{tracker_index}Assets",
            f"tracker{tracker_index}Shares",
            f"tracker{tracker_index}MaxWithdraw",
        )
        missing = [name for name in required_fields if name not in actor_state]
        if missing:
            raise ValueError(
                f"{role} {symbol} state omits fresh derivation field(s): "
                + ", ".join(missing)
            )
        assets = int(actor_state[required_fields[0]])
        shares = int(actor_state[required_fields[1]])
        max_withdraw = int(actor_state[required_fields[2]])
        if shares <= 0 or assets <= 0 or max_withdraw <= 0:
            raise ValueError(f"{role} {symbol} withdrawal state is not positive")
        if max_withdraw > assets:
            raise ValueError(f"{role} {symbol} maxWithdraw exceeds assetsOf")
        if max_withdraw <= WITHDRAWAL_EXECUTION_BUFFER_RAW_UNITS:
            raise ValueError(
                f"{role} {symbol} maxWithdraw cannot absorb the execution buffer"
            )
        withdrawal_assets = max_withdraw - WITHDRAWAL_EXECUTION_BUFFER_RAW_UNITS
        residual = assets - withdrawal_assets
        if residual > MAX_RESIDUAL_RAW_UNITS:
            raise ValueError(
                f"{role} {symbol} residual exceeds {MAX_RESIDUAL_RAW_UNITS} raw units"
            )
        sender = normalize_address(lifecycle_plan["roles"][role]["address"])
        tracker = normalize_address(
            lifecycle_plan["market"][f"collateralTracker{tracker_index}"]
        )
        calldata = _withdraw_calldata(withdrawal_assets, sender, sender)
        transactions.append(
            {
                "ordinal": ordinal,
                "phase": "STATE_DERIVED_COLLATERAL_WITHDRAWAL",
                "sender": sender,
                "nonce": None,
                "label": f"{role} withdraws bounded recoverable {symbol} collateral",
                "to": tracker,
                "valueWei": "0",
                "calldata": calldata,
                "calldataKeccak256": "0x" + keccak(bytes.fromhex(calldata[2:])).hex(),
                "decodedIntent": {
                    "function": "withdraw(uint256,address,address)",
                    "assets": str(withdrawal_assets),
                    "receiver": sender,
                    "owner": sender,
                    "sourceMaxWithdraw": str(max_withdraw),
                    "sourceAssetsOf": str(assets),
                    "sourceShares": str(shares),
                    "executionBufferRawUnits": str(
                        WITHDRAWAL_EXECUTION_BUFFER_RAW_UNITS
                    ),
                },
                "mandatoryPreconditions": [
                    "the public post-close block and all source hashes still match",
                    "owner has zero open option legs and all temporary allowances remain zero",
                    "a fresh read of maxWithdraw is at least the committed assets amount",
                ],
                "mandatoryPostconditions": [
                    "receipt succeeds for this exact owner, receiver, tracker, and assets amount",
                    "underlying balance increases by exactly the withdrawn assets",
                    "tracker shares decrease only by previewWithdraw of the committed assets",
                ],
            }
        )
        residuals.setdefault(role, {})[symbol] = str(residual)

    script = script_path or Path(__file__).resolve()
    body = {
        "schemaVersion": 1,
        "status": "OFFLINE_STATE_DERIVED_WITHDRAWAL_PROPOSAL_REPLAY_REQUIRED_NO_EXECUTION_AUTHORITY",
        "mode": "POST_CLOSE_REPORT_BOUND_NO_RPC_NO_KEYS_NO_SIGNING_NO_BROADCAST",
        "classification": lifecycle_plan["classification"],
        "network": lifecycle_plan["network"],
        "sourceBindings": {
            "lifecyclePlanBodySha256": lifecycle_plan["planBodySha256"],
            "lifecyclePlanFileSha256": file_sha256(lifecycle_path),
            "lifecycleRehearsalFileSha256": file_sha256(rehearsal_path),
            "preparerSha256": file_sha256(script),
        },
        "rolePolicy": {
            "writerAndBuyerDistinct": True,
            "buyerMustBeThirdUnprivilegedAccount": True,
            "sharedDeployerGuardianTreasurerForbiddenAsBuyer": True,
        },
        "sourcePostCloseBlock": terminal["blockNumber"],
        "maximumResidualRawUnitsPerAsset": str(MAX_RESIDUAL_RAW_UNITS),
        "withdrawalExecutionBufferRawUnits": str(
            WITHDRAWAL_EXECUTION_BUFFER_RAW_UNITS
        ),
        "withdrawalExecutionBufferReason": (
            "withdraw() accrues interest before re-reading maxWithdraw; the bounded "
            "buffer prevents a view-to-execution one-unit drift from exceeding the limit"
        ),
        "derivedResiduals": residuals,
        "transactionCount": len(transactions),
        "transactions": transactions,
        "authorization": {key: False for key in lifecycle_plan["authorization"]},
        "publicExecution": {
            "ready": False,
            "blockingReasons": [
                "all nonces are deliberately null",
                "the four-call sequence needs an exact fork replay because earlier withdrawals can change later maxWithdraw values",
                "a fresh public post-close snapshot is required after any public lifecycle",
                "no signing path, operator, authorization manifest, or broadcast authority exists",
            ],
        },
        "executionPolicy": "ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH",
        "nextGate": "EXACT_SEQUENCE_FORK_REPLAY_THEN_SEPARATE_HASH_BOUND_WITHDRAWAL_AUTHORIZATION",
    }
    return {**body, "planBodySha256": canonical_sha256(body)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lifecycle-plan", type=Path, default=DEFAULT_LIFECYCLE_PLAN)
    parser.add_argument("--rehearsal", type=Path, default=DEFAULT_REHEARSAL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_withdrawal_plan(
        load_json(args.lifecycle_plan),
        args.lifecycle_plan,
        load_json(args.rehearsal),
        args.rehearsal,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                "status": plan["status"],
                "output": str(args.output),
                "planBodySha256": plan["planBodySha256"],
                "transactionCount": plan["transactionCount"],
                "signing": False,
                "publicBroadcast": False,
                "nextGate": plan["nextGate"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
