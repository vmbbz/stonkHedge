#!/usr/bin/env python3
"""Run every remaining one-step lifecycle operator check on an exact fork.

The caller must provide an Anvil instance forked at the candidate's exact
reference block. This runner impersonates only the two committed public EOAs,
loads no keys, signs nothing, and contains no public submission path.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path
from typing import Any


REPOSITORY = Path(__file__).resolve().parents[1]
MARKETS = REPOSITORY / "manifests" / "markets"
DEFAULT_PLAN = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-execution-candidate-2026-09-15.json"
DEFAULT_REPORT = MARKETS / "robinhood-testnet-pltr-weth-lifecycle-execution-operator-simulation-2026-09-15.json"
DEFAULT_RPC_URL = "http://127.0.0.1:8549"


def _load_sibling(name: str, filename: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required sibling module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


operator = _load_sibling(
    "stonkhedge_lifecycle_operator", "operate_robinhood_lifecycle.py"
)
simulator = operator.simulator


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON manifest must contain an object: {path}")
    return value


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def simulate_all(plan: dict[str, Any], plan_path: Path, client: Any) -> dict[str, Any]:
    operator.validate_execution_plan(plan, plan_path)
    fork = simulator.assert_exact_fork(plan, client)
    compatibility = simulator.mine_compatibility_block(plan, client)
    external = simulator.observe_external_state(client, plan)
    simulator._assert_external_state(plan, external)
    execution_start = int(plan.get("executionStartIndex", 0))
    initial = operator.verify_state(client, plan, execution_start)
    if execution_start == 0:
        adverse = simulator.rehearse_adverse_preflight_rejections(
            load_json(
                REPOSITORY
                / plan["sourceBindings"]["baseLifecyclePlan"]["path"]
            ),
            external,
            initial["observed"],
        )
    else:
        adverse = {
            "status": "INHERITED_FROM_HASH_BOUND_PRIOR_SIMULATION",
            "priorSimulationReportSha256": plan["sourceBindings"][
                "priorSimulationReport"
            ]["sha256"],
        }
    transactions: list[dict[str, Any]] = []
    milestones: dict[str, Any] = {"initial": initial["observed"]}
    for index in range(execution_start, len(plan["transactions"])):
        transactions.append(operator.simulate_one_step(
            plan,
            plan_path,
            client,
            index,
            sleep=time.sleep,
        ))
        phase = plan["transactions"][index]["phase"]
        next_phase = (
            plan["transactions"][index + 1]["phase"]
            if index + 1 < len(plan["transactions"])
            else None
        )
        if phase != next_phase:
            milestones[f"afterPhase:{phase}"] = simulator.observe(client, plan)
    final = operator.verify_state(client, plan, len(plan["transactions"]))
    if final["observed"]["writer"]["openLegs"] != 0 or final["observed"]["buyer"]["openLegs"] != 0:
        raise RuntimeError("terminal option-leg cleanup failed")
    premium_before = milestones["afterPhase:MATCHED_OPTION_OPEN"]
    premium_after = milestones["afterPhase:PREMIUM_OBSERVATION"]
    premium_changed = (
        premium_before["writer"]["premium"] != premium_after["writer"]["premium"]
        or premium_before["buyer"]["premium"] != premium_after["buyer"]["premium"]
    )
    if not premium_changed:
        raise RuntimeError("controlled swaps did not change the premium observation")
    return {
        "schemaVersion": 1,
        "status": "PASS_EXACT_HEAD_DUAL_SENDER_LIFECYCLE_OPERATOR",
        "mode": "EXACT_FORK_LOOPBACK_ANVIL_IMPERSONATION_NO_KEYS_NO_SIGNING_NO_PUBLIC_BROADCAST",
        "classification": plan["classification"],
        "sourceBindings": {
            "executionPlanBodySha256": plan["executionPlanBodySha256"],
            "executionPlanFileSha256": file_sha256(plan_path),
            "operatorSha256": file_sha256(Path(operator.__file__)),
            "simulationRunnerSha256": file_sha256(Path(__file__)),
        },
        "fork": fork,
        "localCompatibilityBlock": compatibility,
        "externalState": external,
        "adversePreflightRejections": adverse,
        "transactionCount": len(transactions),
        "transactions": transactions,
        "milestones": milestones,
        "premiumObservationChanged": premium_changed,
        "terminalState": final["observed"],
        "authorization": plan["authorization"],
        "publicExecution": {"ready": False, "broadcastAttempted": False},
        "nextGate": "INDEPENDENT_REVIEW_THEN_EXPLICIT_HASH_BOUND_PUBLIC_AUTHORIZATION",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    simulator.validate_local_rpc_url(args.rpc_url)
    client = simulator.genesis_simulator.JsonRpcClient(args.rpc_url)
    report = simulate_all(load_json(args.plan), args.plan, client)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "output": str(args.report),
                "transactionCount": report["transactionCount"],
                "writerFinalNonce": report["terminalState"]["writer"]["nonce"],
                "buyerFinalNonce": report["terminalState"]["buyer"]["nonce"],
                "signing": False,
                "publicBroadcast": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
