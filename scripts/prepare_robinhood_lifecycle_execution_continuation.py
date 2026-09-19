#!/usr/bin/env python3
"""Build a receipt-bound continuation after a partially executed lifecycle.

The transformer preserves every canonical transaction, derives the exact
remaining swap inputs, inserts bounded Permit2 renewals for only those inputs,
refreshes future router deadlines, and reassigns nonces from public state. It
has no RPC, wallet, signing, serialization, or broadcast capability.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from eth_abi import decode as abi_decode
from eth_abi import encode as abi_encode
from eth_hash.auto import keccak


REPOSITORY = Path(__file__).resolve().parents[1]
MARKETS = REPOSITORY / "manifests" / "markets"
DEFAULT_PRIOR_PLAN = (
    MARKETS
    / "robinhood-testnet-pltr-weth-lifecycle-refresh-candidate-2026-09-16.json"
)
DEFAULT_PREFLIGHT = (
    MARKETS
    / "robinhood-testnet-pltr-weth-lifecycle-continuation-preflight-2026-09-19.json"
)
DEFAULT_OUTPUT = (
    MARKETS
    / "robinhood-testnet-pltr-weth-lifecycle-continuation-candidate-2026-09-19.json"
)
CHAIN_ID = 46630
OFFICIAL_RPC_URL = "https://rpc.testnet.chain.robinhood.com"
SWAP_DEADLINE_SECONDS = 7 * 24 * 60 * 60
PERMIT2_EXPIRATION_SECONDS = 8 * 24 * 60 * 60
MINIMUM_SECONDS_AT_EXECUTION_START = 6 * 24 * 60 * 60
MINIMUM_SECONDS_AT_SWAP = 30 * 60


def _load_sibling(name: str, filename: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required sibling module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base_planner = _load_sibling(
    "stonkhedge_lifecycle_continuation_base_planner",
    "prepare_robinhood_lifecycle_execution_plan.py",
)
qualifier = base_planner.qualifier


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


def repository_relative(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(REPOSITORY).as_posix()
    except ValueError as exc:
        raise ValueError(f"bound source must be inside the repository: {path}") from exc


def _replace_calldata(transaction: dict[str, Any], raw: bytes) -> None:
    transaction["calldata"] = "0x" + raw.hex()
    transaction["calldataKeccak256"] = "0x" + keccak(raw).hex()


def _set_permit(
    transaction: dict[str, Any], *, amount: int, expiration: int
) -> None:
    selector = keccak(b"approve(address,address,uint160,uint48)")[:4]
    raw = bytes.fromhex(transaction["calldata"][2:])
    if raw[:4] != selector:
        raise ValueError("Permit2 renewal template selector drifted")
    token, spender, _, _ = abi_decode(
        ["address", "address", "uint160", "uint48"], raw[4:]
    )
    _replace_calldata(
        transaction,
        selector
        + abi_encode(
            ["address", "address", "uint160", "uint48"],
            [token, spender, amount, expiration],
        ),
    )
    transaction["decodedIntent"]["amount"] = str(amount)
    transaction["decodedIntent"]["expiration"] = str(expiration)
    transaction["decodedIntent"][
        "clockClassification"
    ] = "EXTENDED_MANUAL_TESTNET_CONTINUATION_TIME_BOUND"


def _remaining_swap_totals(
    transactions: list[dict[str, Any]], allowed_tokens: set[str]
) -> dict[str, int]:
    totals = {token: 0 for token in allowed_tokens}
    for transaction in transactions:
        intent = transaction.get("decodedIntent", {})
        if intent.get("route") != "UNISWAP_V4_EXACT_INPUT_SINGLE":
            continue
        token = qualifier.normalize_address(intent.get("tokenIn", ""))
        if token not in totals:
            raise ValueError("future swap input token is outside the market")
        amount = int(intent.get("amountIn", "0"))
        if amount <= 0:
            raise ValueError("future swap input must be positive")
        totals[token] += amount
    if not all(amount > 0 for amount in totals.values()):
        raise ValueError("continuation must retain bounded swaps for both market tokens")
    return totals


def _find_permit_template(
    prior: dict[str, Any], *, token: str
) -> dict[str, Any]:
    permit2 = qualifier.normalize_address(prior["market"]["permit2"])
    router = qualifier.normalize_address(prior["market"]["universalRouter"])
    for transaction in reversed(prior["transactions"]):
        intent = transaction.get("decodedIntent", {})
        if (
            intent.get("function") == "approve(address,address,uint160,uint48)"
            and int(intent.get("amount", "0")) > 0
            and qualifier.normalize_address(intent.get("token", "")) == token
            and qualifier.normalize_address(intent.get("spender", "")) == router
            and qualifier.normalize_address(transaction.get("to", "")) == permit2
        ):
            return copy.deepcopy(transaction)
    raise ValueError(f"no positive Permit2 template exists for {token}")


def _renewal(
    prior: dict[str, Any], *, token: str, symbol: str, amount: int
) -> dict[str, Any]:
    transaction = _find_permit_template(prior, token=token)
    transaction["phase"] = "WRITER_REMAINING_SWAP_PERMISSION_REFRESH"
    transaction[
        "label"
    ] = f"writer renews remaining exact {symbol} Permit2 allowance to UniversalRouter"
    transaction["authorizedForBroadcast"] = False
    _set_permit(transaction, amount=amount, expiration=0)
    return transaction


def _refresh_future_calldata(
    transactions: list[dict[str, Any]],
    *,
    execution_start: int,
    permit_expiration: int,
    swap_deadline: int,
) -> tuple[list[int], list[int], list[int]]:
    permit_selector = keccak(b"approve(address,address,uint160,uint48)")[:4]
    swap_selector = keccak(b"execute(bytes,bytes[],uint256)")[:4]
    positive_permits: list[int] = []
    zero_permits: list[int] = []
    swaps: list[int] = []
    for transaction in transactions[execution_start:]:
        raw = bytes.fromhex(transaction["calldata"][2:])
        intent = transaction["decodedIntent"]
        ordinal = int(transaction["ordinal"])
        if raw[:4] == permit_selector:
            token, spender, amount, _ = abi_decode(
                ["address", "address", "uint160", "uint48"], raw[4:]
            )
            amount = int(amount)
            expiration = permit_expiration if amount > 0 else 0
            _replace_calldata(
                transaction,
                permit_selector
                + abi_encode(
                    ["address", "address", "uint160", "uint48"],
                    [token, spender, amount, expiration],
                ),
            )
            intent["expiration"] = str(expiration)
            intent[
                "clockClassification"
            ] = "EXTENDED_MANUAL_TESTNET_CONTINUATION_TIME_BOUND"
            (positive_permits if amount > 0 else zero_permits).append(ordinal)
        elif raw[:4] == swap_selector:
            commands, inputs, _ = abi_decode(["bytes", "bytes[]", "uint256"], raw[4:])
            _replace_calldata(
                transaction,
                swap_selector
                + abi_encode(
                    ["bytes", "bytes[]", "uint256"],
                    [commands, inputs, swap_deadline],
                ),
            )
            intent["deadline"] = str(swap_deadline)
            intent[
                "clockClassification"
            ] = "EXTENDED_MANUAL_TESTNET_CONTINUATION_TIME_BOUND"
            swaps.append(ordinal)
    return positive_permits, zero_permits, swaps


def validate_preflight(
    preflight: dict[str, Any],
    preflight_path: Path,
    prior: dict[str, Any],
    prior_path: Path,
) -> None:
    if (
        preflight.get("status")
        != "PASS_PUBLIC_LIFECYCLE_CONTINUATION_PREFLIGHT_NO_AUTHORITY"
    ):
        raise ValueError("lifecycle continuation preflight did not pass")
    if preflight.get("network", {}).get("chainId") != CHAIN_ID:
        raise ValueError("continuation preflight chain ID drifted")
    completed = int(preflight.get("completedPrefixCount", -1))
    if not int(prior.get("executionStartIndex", 0)) < completed <= len(
        prior.get("transactions", [])
    ):
        raise ValueError("continuation completed prefix drifted")
    if preflight.get("priorPlan") != {
        "executionPlanBodySha256": prior["executionPlanBodySha256"],
        "executionPlanFileSha256": file_sha256(prior_path),
    }:
        raise ValueError("continuation prior-plan binding drifted")
    if [item.get("transactionIndex") for item in preflight.get("evidencePrefix", [])] != list(
        range(completed)
    ):
        raise ValueError("continuation evidence prefix drifted")
    if preflight.get("authorization") != {
        "signing": False,
        "publicBroadcast": False,
    }:
        raise ValueError("continuation preflight authorization drifted")
    if preflight.get("publicExecution") != {
        "ready": False,
        "broadcastAttempted": False,
    }:
        raise ValueError("continuation public-execution boundary drifted")
    qualifier_binding = preflight.get("qualifier", {})
    qualifier_path = REPOSITORY / qualifier_binding.get("path", "")
    if (
        not qualifier_path.is_file()
        or qualifier_binding.get("sha256") != file_sha256(qualifier_path)
    ):
        raise ValueError("continuation qualifier binding drifted")
    body = dict(preflight)
    expected = body.pop("preflightBodySha256", None)
    if expected != canonical_sha256(body):
        raise ValueError("continuation preflight body hash drifted")
    if not Path(preflight_path).is_file():
        raise ValueError("continuation preflight file is unavailable")


def build_continuation_plan(
    prior_plan_path: Path, preflight_path: Path, generator_path: Path
) -> dict[str, Any]:
    prior_plan_path = Path(prior_plan_path)
    preflight_path = Path(preflight_path)
    generator_path = Path(generator_path)
    prior = load_json(prior_plan_path)
    preflight = load_json(preflight_path)
    prior_body = dict(prior)
    prior_hash = prior_body.pop("executionPlanBodySha256", None)
    if prior_hash != canonical_sha256(prior_body):
        raise ValueError("prior lifecycle candidate body hash drifted")
    validate_preflight(preflight, preflight_path, prior, prior_plan_path)

    writer = qualifier.normalize_address(prior["roles"]["writer"]["address"])
    buyer = qualifier.normalize_address(prior["roles"]["buyer"]["address"])
    pltr = qualifier.normalize_address(prior["market"]["pltr"])
    weth = qualifier.normalize_address(prior["market"]["weth"])
    completed = int(preflight["completedPrefixCount"])
    continuation_starts = {
        writer: int(preflight["nonceVector"][writer]),
        buyer: int(preflight["nonceVector"][buyer]),
    }
    prefix = copy.deepcopy(prior["transactions"][:completed])
    remaining = copy.deepcopy(prior["transactions"][completed:])
    totals = _remaining_swap_totals(remaining, {pltr, weth})

    observed_writer = preflight["observed"]["writer"]
    allowance_fields = {
        pltr: ("pltrToPermit2", "pltrPermit2ToRouter"),
        weth: ("wethToPermit2", "wethPermit2ToRouter"),
    }
    for token, amount in totals.items():
        erc20_field, permit_field = allowance_fields[token]
        if (
            int(observed_writer[erc20_field]) != amount
            or int(observed_writer[permit_field][0]) != amount
        ):
            raise ValueError(f"remaining exact allowance drifted for {token}")

    renewals = [
        _renewal(prior, token=pltr, symbol="PLTR", amount=totals[pltr]),
        _renewal(prior, token=weth, symbol="WETH", amount=totals[weth]),
    ]
    transactions = prefix + renewals + remaining
    for ordinal, transaction in enumerate(transactions):
        transaction["ordinal"] = ordinal

    reference_timestamp = int(preflight["network"]["referenceTimestampUnix"])
    swap_deadline = reference_timestamp + SWAP_DEADLINE_SECONDS
    permit_expiration = reference_timestamp + PERMIT2_EXPIRATION_SECONDS
    positive_permits, zero_permits, swap_indexes = _refresh_future_calldata(
        transactions,
        execution_start=completed,
        permit_expiration=permit_expiration,
        swap_deadline=swap_deadline,
    )
    if positive_permits != [completed, completed + 1]:
        raise ValueError("continuation renewal ordering drifted")
    if len(zero_permits) != 2 or len(swap_indexes) != 3:
        raise ValueError("continuation cleanup or swap count drifted")

    vector = dict(continuation_starts)
    for transaction in transactions[completed:]:
        sender = qualifier.normalize_address(transaction["sender"])
        transaction["requiredNonceStateBefore"] = dict(vector)
        transaction["nonce"] = vector[sender]
        vector[sender] += 1
        transaction["requiredNonceStateAfter"] = dict(vector)
        transaction["authorizedForBroadcast"] = False

    source_bindings = copy.deepcopy(prior["sourceBindings"])
    source_bindings.update(
        {
            "priorExecutionCandidate": {
                "path": repository_relative(prior_plan_path),
                "sha256": file_sha256(prior_plan_path),
                "executionPlanBodySha256": prior["executionPlanBodySha256"],
            },
            "continuationPreflight": {
                "path": repository_relative(preflight_path),
                "sha256": file_sha256(preflight_path),
                "preflightBodySha256": preflight["preflightBodySha256"],
            },
            "generator": {
                "path": repository_relative(generator_path),
                "sha256": file_sha256(generator_path),
            },
        }
    )

    body = copy.deepcopy(prior)
    body.pop("executionPlanBodySha256", None)
    body.update(
        {
            "mode": "UNSIGNED_RECEIPT_BOUND_EXTENDED_TESTNET_CONTINUATION_NO_SIGNING_NO_BROADCAST",
            "network": {
                "name": prior["network"]["name"],
                "chainId": CHAIN_ID,
                "rpc": OFFICIAL_RPC_URL,
                "referenceBlock": preflight["network"]["referenceBlock"],
                "referenceBlockHash": preflight["network"]["referenceBlockHash"],
                "referenceTimestampUnix": reference_timestamp,
                "referenceTimestampUtc": preflight["network"]["referenceTimestampUtc"],
            },
            "sourceBindings": source_bindings,
            "continuationInitialState": {
                "completedPrefixCount": completed,
                "observed": copy.deepcopy(preflight["observed"]),
                "evidencePrefix": copy.deepcopy(preflight["evidencePrefix"]),
            },
            "executionStartIndex": completed,
            "executionClock": {
                "referenceTimestampUnix": reference_timestamp,
                "swapDeadlineUnix": swap_deadline,
                "permit2ExpirationUnix": permit_expiration,
                "minimumSecondsRemainingAtTransactionZero": MINIMUM_SECONDS_AT_EXECUTION_START,
                "minimumSecondsRemainingAtDeadlineTransaction": MINIMUM_SECONDS_AT_SWAP,
                "deadlineBearingTransactionIndexes": positive_permits
                + zero_permits
                + swap_indexes,
                "swapDeadlineTransactionIndexes": swap_indexes,
                "permit2WindowLastTransactionIndex": max(swap_indexes),
                "classification": "SEVEN_DAY_SWAP_EIGHT_DAY_PERMIT2_TESTNET_ONLY_EXPLICIT_ACCEPTANCE_REQUIRED",
            },
            "continuationStartNonces": continuation_starts,
            "remainingSwapInputTotals": {
                pltr: str(totals[pltr]),
                weth: str(totals[weth]),
            },
            "nextNonces": vector,
            "transactionCount": len(transactions),
            "transactionCountsBySender": {
                writer: sum(
                    1
                    for transaction in transactions
                    if qualifier.normalize_address(transaction["sender"]) == writer
                ),
                buyer: sum(
                    1
                    for transaction in transactions
                    if qualifier.normalize_address(transaction["sender"]) == buyer
                ),
            },
            "transactions": transactions,
            "authorization": {key: False for key in prior["authorization"]},
            "publicExecution": {
                "ready": False,
                "broadcastAttempted": False,
                "blockingReasons": [
                    "the receipt-bound continuation has not passed exact-head simulation",
                    "the seven-day swap and eight-day Permit2 windows require explicit owner acceptance",
                    "no continuation hash-bound authorization manifest exists",
                ],
            },
            "nextGate": "EXACT_HEAD_CONTINUATION_SIMULATION_THEN_NEW_HASH_BOUND_AUTHORIZATION",
        }
    )
    body["executionPlanBodySha256"] = canonical_sha256(body)
    return body


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-plan", type=Path, default=DEFAULT_PRIOR_PLAN)
    parser.add_argument("--preflight", type=Path, default=DEFAULT_PREFLIGHT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_continuation_plan(
        args.prior_plan, args.preflight, Path(__file__).resolve()
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
                "executionPlanBodySha256": plan["executionPlanBodySha256"],
                "executionStartIndex": plan["executionStartIndex"],
                "remainingTransactionCount": len(plan["transactions"])
                - plan["executionStartIndex"],
                "continuationStartNonces": plan["continuationStartNonces"],
                "nextNonces": plan["nextNonces"],
                "remainingSwapInputTotals": plan["remainingSwapInputTotals"],
                "swapDeadlineUnix": plan["executionClock"]["swapDeadlineUnix"],
                "permit2ExpirationUnix": plan["executionClock"][
                    "permit2ExpirationUnix"
                ],
                "signing": False,
                "publicBroadcast": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
