import ast
import copy
import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "simulate_robinhood_market_execution_operator.py"
)
REPOSITORY = Path(__file__).resolve().parents[2]
PLAN_PATH = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-execution-candidate-2026-09-10.json"
)

SPEC = importlib.util.spec_from_file_location("market_operator_runner", SCRIPT)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


class MarketOperatorRunnerTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        self.reports = []
        for index, transaction in enumerate(self.plan["transactions"]):
            self.reports.append(
                {
                    "status": "PASS_ONE_STEP_LOOPBACK_SIMULATION_STOP",
                    "lineage": {"referenceBlock": self.plan["network"]["referenceBlock"]},
                    "transaction": {"ordinal": index, "calldataKeccak256": transaction["calldataKeccak256"]},
                    "before": {"completedSteps": index},
                    "after": {"completedSteps": index + 1},
                    "publicExecution": {"broadcastAttempted": False},
                }
            )

    def test_summary_requires_all_ordered_one_step_stops(self):
        summary = runner.build_summary(self.plan, PLAN_PATH, self.reports)
        self.assertEqual(summary["stepCount"], 12)
        self.assertFalse(summary["publicExecution"]["ready"])
        self.assertNotIn('"calldata":', json.dumps(summary))

        changed = copy.deepcopy(self.reports)
        changed[4]["after"]["completedSteps"] = 9
        with self.assertRaisesRegex(ValueError, "post-state"):
            runner.build_summary(self.plan, PLAN_PATH, changed)

    def test_runner_has_no_key_signing_or_public_broadcast_capability(self):
        source = SCRIPT.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertNotIn("subprocess", imported_roots)
        self.assertNotIn("eth_sendRawTransaction", source)
        self.assertNotIn("keystore", source.lower())
        self.assertNotIn("private key", source.lower())


if __name__ == "__main__":
    unittest.main()
