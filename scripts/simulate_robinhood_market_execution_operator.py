#!/usr/bin/env python3
"""Rehearse all 12 execution-candidate steps through the one-step operator.

The runner is loopback-Anvil only. It calls the operator once per consecutive
index, requiring full state reconciliation each time, and writes a sanitized
aggregate report. It has no credential, signing, or public-broadcast path.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path
from typing import Any


def _load_operator():
    path = Path(__file__).resolve().with_name("operate_robinhood_market_genesis.py")
    spec = importlib.util.spec_from_file_location("stonkhedge_market_operator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load market operator {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


operator = _load_operator()
REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = operator.DEFAULT_PLAN
DEFAULT_REPORT = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-execution-operator-simulation-2026-09-10.json"
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_summary(
    plan: dict[str, Any], plan_path: Path, step_reports: list[dict[str, Any]]
) -> dict[str, Any]:
    if len(step_reports) != len(plan["transactions"]):
        raise ValueError("operator simulation did not produce twelve step reports")
    for index, report in enumerate(step_reports):
        if report.get("status") != "PASS_ONE_STEP_LOOPBACK_SIMULATION_STOP":
            raise ValueError(f"operator step {index} did not pass")
        if report.get("transaction", {}).get("ordinal") != index:
            raise ValueError(f"operator step {index} ordering drifted")
        if report.get("before", {}).get("completedSteps") != index:
            raise ValueError(f"operator step {index} pre-state drifted")
        if report.get("after", {}).get("completedSteps") != index + 1:
            raise ValueError(f"operator step {index} post-state drifted")
        if report.get("publicExecution", {}).get("broadcastAttempted") is not False:
            raise ValueError(f"operator step {index} claims a public broadcast")
    return {
        "schemaVersion": 1,
        "status": "PASS_EXECUTION_CANDIDATE_ONE_STEP_OPERATOR_REHEARSAL",
        "mode": "LOOPBACK_ANVIL_ONLY_NO_CREDENTIALS_NO_SIGNING_NO_PUBLIC_BROADCAST",
        "sourceBindings": {
            "executionPlanBodySha256": plan["executionPlanBodySha256"],
            "executionPlanFileSha256": file_sha256(plan_path),
            "operatorSha256": file_sha256(Path(operator.__file__)),
            "runnerSha256": file_sha256(Path(__file__)),
        },
        "lineage": step_reports[0]["lineage"],
        "stepCount": len(step_reports),
        "steps": [report["transaction"] for report in step_reports],
        "initialState": step_reports[0]["before"],
        "finalState": step_reports[-1]["after"],
        "authorization": plan["authorization"],
        "publicExecution": {
            "ready": False,
            "broadcastAttempted": False,
            "blockingReasons": [
                "this execution candidate is time-bound and will become stale",
                "the operator public lane was not invoked during this rehearsal",
                "no hash-bound signing or public broadcast authorization exists",
            ],
        },
        "nextGate": "REVIEW_THEN_REGENERATE_FINAL_CANDIDATE_BEFORE_ANY_BROADCAST_DECISION",
    }


def simulate_all(plan: dict[str, Any], plan_path: Path, client: Any) -> dict[str, Any]:
    operator.validate_execution_plan(plan, plan_path)
    reports = [
        operator.simulate_one_step(plan, plan_path, client, index, sleep=time.sleep)
        for index in range(len(plan["transactions"]))
    ]
    return build_summary(plan, plan_path, reports)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--rpc-url", default=operator.DEFAULT_RPC_URL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    operator.validate_local_rpc_url(args.rpc_url)
    plan = operator.load_json(args.plan)
    client = operator.fork_simulator.JsonRpcClient(args.rpc_url)
    report = simulate_all(plan, args.plan, client)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        f"{args.report}: {report['status']}; 12 isolated operator steps reconciled"
    )
    print("LOOPBACK ONLY; NO CREDENTIALS, SIGNING, OR PUBLIC BROADCAST")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
