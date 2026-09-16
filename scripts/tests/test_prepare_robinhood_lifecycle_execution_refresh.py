import copy
import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "prepare_robinhood_lifecycle_execution_refresh.py"
SPEC = importlib.util.spec_from_file_location("lifecycle_refresh_planner", SCRIPT)
planner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(planner)


class LifecycleRefreshPlannerTests(unittest.TestCase):
    def setUp(self):
        self.plan = planner.load_json(planner.DEFAULT_OUTPUT)

    def test_committed_candidate_matches_deterministic_regeneration(self):
        rebuilt = planner.build_refresh_plan(
            planner.DEFAULT_PRIOR_PLAN,
            planner.DEFAULT_PREFLIGHT,
            SCRIPT,
        )
        self.assertEqual(rebuilt, self.plan)

    def test_prefix_is_preserved_and_continuation_is_fresh(self):
        prior = planner.load_json(planner.DEFAULT_PRIOR_PLAN)
        self.assertEqual(self.plan["executionStartIndex"], 5)
        self.assertEqual(self.plan["transactions"][:5], prior["transactions"][:5])
        self.assertEqual(len(self.plan["transactions"]), 27)
        self.assertEqual(
            self.plan["executionClock"]["swapDeadlineTransactionIndexes"],
            [7, 8, 19, 20],
        )
        self.assertEqual(
            self.plan["executionClock"]["deadlineBearingTransactionIndexes"],
            [5, 6, 23, 24, 7, 8, 19, 20],
        )
        self.assertEqual(
            self.plan["transactions"][5]["decodedIntent"]["amount"],
            "2000000000000000",
        )
        self.assertEqual(
            self.plan["transactions"][6]["decodedIntent"]["amount"],
            "2000000000000",
        )

    def test_preflight_body_mutation_is_rejected(self):
        preflight = planner.load_json(planner.DEFAULT_PREFLIGHT)
        changed = copy.deepcopy(preflight)
        changed["nonceVector"][next(iter(changed["nonceVector"]))] += 1
        with self.assertRaisesRegex(ValueError, "body hash"):
            planner.validate_preflight(
                changed,
                planner.DEFAULT_PREFLIGHT,
                planner.load_json(planner.DEFAULT_PRIOR_PLAN),
                planner.DEFAULT_PRIOR_PLAN,
            )


if __name__ == "__main__":
    unittest.main()
