import ast
import copy
import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "prepare_robinhood_lifecycle_execution_plan.py"
SPEC = importlib.util.spec_from_file_location("lifecycle_execution_planner", SCRIPT)
planner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(planner)


class LifecycleExecutionPlannerTests(unittest.TestCase):
    def build(self):
        return planner.build_execution_plan(
            planner.DEFAULT_BASE_PLAN,
            planner.DEFAULT_REHEARSAL,
            planner.DEFAULT_PREFLIGHT,
            SCRIPT,
        )

    def test_candidate_is_deterministic_hash_bound_and_unauthorized(self):
        plan = self.build()
        committed = planner.load_json(planner.DEFAULT_OUTPUT)
        self.assertEqual(plan, committed)
        body = dict(plan)
        expected = body.pop("executionPlanBodySha256")
        self.assertEqual(expected, planner.canonical_sha256(body))
        self.assertTrue(all(value is False for value in plan["authorization"].values()))
        self.assertFalse(plan["publicExecution"]["ready"])
        self.assertTrue(all(tx["authorizedForBroadcast"] is False for tx in plan["transactions"]))

    def test_two_nonce_streams_bind_the_global_order(self):
        plan = self.build()
        writer = plan["roles"]["writer"]["address"]
        buyer = plan["roles"]["buyer"]["address"]
        self.assertEqual(plan["startNonces"], {writer: 13, buyer: 0})
        self.assertEqual(plan["nextNonces"], {writer: 31, buyer: 7})
        counts = {writer: 0, buyer: 0}
        for transaction in plan["transactions"]:
            before = {
                writer: plan["startNonces"][writer] + counts[writer],
                buyer: plan["startNonces"][buyer] + counts[buyer],
            }
            self.assertEqual(transaction["requiredNonceStateBefore"], before)
            self.assertEqual(transaction["nonce"], before[transaction["sender"]])
            counts[transaction["sender"]] += 1

    def test_only_time_bound_calldata_changes(self):
        base = planner.load_json(planner.DEFAULT_BASE_PLAN)
        plan = self.build()
        changed = [
            index
            for index, transaction in enumerate(plan["transactions"])
            if transaction["calldata"] != base["transactions"][index]["calldata"]
        ]
        # Zero-amount Permit2 cleanup calls already encode expiration zero, so
        # only the six live grant/swap calls change bytes.
        self.assertEqual(changed, [3, 4, 5, 6, 17, 18])
        self.assertEqual(
            plan["executionClock"]["deadlineBearingTransactionIndexes"],
            [3, 4, 5, 6, 17, 18, 21, 22],
        )
        self.assertEqual(
            plan["executionClock"]["swapDeadlineUnix"]
            - plan["executionClock"]["referenceTimestampUnix"],
            planner.SWAP_DEADLINE_SECONDS,
        )
        self.assertEqual(
            plan["executionClock"]["permit2ExpirationUnix"]
            - plan["executionClock"]["referenceTimestampUnix"],
            planner.PERMIT2_EXPIRATION_SECONDS,
        )

    def test_preflight_or_transaction_drift_fails_closed(self):
        plan = self.build()
        changed = copy.deepcopy(plan)
        changed["transactions"][16]["sender"] = changed["roles"]["writer"]["address"]
        body = dict(changed)
        body.pop("executionPlanBodySha256")
        changed["executionPlanBodySha256"] = planner.canonical_sha256(body)
        self.assertNotEqual(changed, plan)

    def test_generator_has_no_rpc_key_signing_or_broadcast_capability(self):
        source = SCRIPT.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertTrue(imported.isdisjoint({"requests", "socket", "subprocess", "urllib", "web3"}))
        self.assertNotIn("eth_send", source)


if __name__ == "__main__":
    unittest.main()
