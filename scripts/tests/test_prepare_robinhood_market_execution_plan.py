import ast
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1] / "prepare_robinhood_market_execution_plan.py"
)
REPOSITORY = Path(__file__).resolve().parents[2]
BASE_PLAN = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-offline-plan-2026-09-09.json"
)
PREFLIGHT = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-execution-preflight-2026-09-10.json"
)
ACCEPTANCE = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-execution-planning-acceptance-2026-09-10.json"
)

SPEC = importlib.util.spec_from_file_location("market_execution_planner", SCRIPT)
execution_planner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(execution_planner)


class MarketExecutionPlanTests(unittest.TestCase):
    def build(self):
        return execution_planner.build_execution_plan(
            BASE_PLAN, PREFLIGHT, ACCEPTANCE, SCRIPT
        )

    def test_binds_fresh_nonce_clock_and_keeps_public_authority_closed(self):
        plan = self.build()
        preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
        timestamp = execution_planner.fork_planner._unix_timestamp(
            preflight["network"]["blockTimestamp"]
        )
        nonce = preflight["observations"]["actorPendingNonce"]
        self.assertEqual(
            plan["status"], "EXECUTION_CANDIDATE_REQUIRES_SEPARATE_AUTHORIZATION"
        )
        self.assertEqual(
            plan["network"]["referenceBlock"], preflight["network"]["blockNumber"]
        )
        self.assertEqual(plan["startNonce"], nonce)
        self.assertEqual(plan["nextNonce"], nonce + 12)
        self.assertEqual(
            plan["executionClock"]["liquidityDeadlineUnix"], timestamp + 3600
        )
        self.assertEqual(
            plan["executionClock"]["permit2ExpirationUnix"], timestamp + 7200
        )
        self.assertEqual(
            plan["initialState"]["positionManagerNextTokenIdFloor"],
            preflight["observations"]["positionManagerNextTokenId"],
        )
        self.assertEqual(plan["initialState"]["actorPositionManagerNftBalance"], "0")
        self.assertFalse(plan["publicExecution"]["ready"])
        self.assertTrue(all(value is False for value in plan["authorization"].values()))
        for ordinal, transaction in enumerate(plan["transactions"]):
            self.assertEqual(transaction["nonce"], nonce + ordinal)
            self.assertFalse(transaction["authorizedForBroadcast"])

    def test_preserves_exact_accepted_exposure_and_changes_only_deadlines(self):
        base = json.loads(BASE_PLAN.read_text(encoding="utf-8"))
        plan = self.build()
        self.assertEqual(
            plan["maximumExposure"]["status"],
            "OWNER_ACCEPTED_FOR_EXECUTION_PLANNING_ONLY",
        )
        self.assertEqual(plan["priceAndLiquidity"]["tickLower"], -81120)
        self.assertEqual(plan["priceAndLiquidity"]["tickUpper"], -57060)
        self.assertEqual(plan["priceAndLiquidity"]["liquidity"], "138450781996976174")
        self.assertEqual(plan["predictedMarketContracts"]["factorySalt"], "0")
        changed = [
            index
            for index, transaction in enumerate(plan["transactions"])
            if transaction["calldata"] != base["transactions"][index]["calldata"]
        ]
        self.assertEqual(changed, [3, 4, 6])

    def test_is_deterministic_and_body_hash_is_exact(self):
        first = self.build()
        self.assertEqual(first, self.build())
        self.assertEqual(
            first["executionPlanBodySha256"],
            execution_planner.execution_plan_body_sha256(first),
        )

    def test_rejects_changed_acceptance_or_preflight(self):
        acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
        preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            changed = copy.deepcopy(acceptance)
            changed["acceptedExecutionPlanningExposure"]["maximumPltrTransfer"] = "1"
            path.write_text(json.dumps(changed), encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(ValueError, "acceptance"):
                execution_planner.build_execution_plan(
                    BASE_PLAN, PREFLIGHT, path, SCRIPT
                )

            changed = copy.deepcopy(preflight)
            changed["authorization"]["signing"] = True
            path.write_text(json.dumps(changed), encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(ValueError, "authorization"):
                execution_planner.build_execution_plan(
                    BASE_PLAN, path, ACCEPTANCE, SCRIPT
                )

    def test_generator_has_no_rpc_key_signing_or_broadcast_capability(self):
        source = SCRIPT.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertTrue(
            imported_roots.isdisjoint(
                {"requests", "socket", "subprocess", "urllib", "web3"}
            )
        )
        self.assertNotIn("eth_sendRawTransaction", source)
        self.assertNotIn("eth_sendTransaction", source)
        self.assertNotIn("private key", source.lower())


if __name__ == "__main__":
    unittest.main()
