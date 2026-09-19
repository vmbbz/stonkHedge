import copy
import importlib.util
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "prepare_robinhood_lifecycle_execution_continuation.py"
)
SPEC = importlib.util.spec_from_file_location(
    "lifecycle_continuation_planner", SCRIPT
)
planner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(planner)


class LifecycleContinuationPlannerTests(unittest.TestCase):
    def setUp(self):
        self.plan = planner.load_json(planner.DEFAULT_OUTPUT)

    def test_committed_candidate_matches_deterministic_regeneration(self):
        rebuilt = planner.build_continuation_plan(
            planner.DEFAULT_PRIOR_PLAN,
            planner.DEFAULT_PREFLIGHT,
            SCRIPT,
        )
        self.assertEqual(rebuilt, self.plan)

    def test_prefix_exact_remaining_renewals_and_clock_policy(self):
        prior = planner.load_json(planner.DEFAULT_PRIOR_PLAN)
        self.assertEqual(self.plan["executionStartIndex"], 8)
        self.assertEqual(self.plan["transactions"][:8], prior["transactions"][:8])
        self.assertEqual(len(self.plan["transactions"]), 29)
        self.assertEqual(
            self.plan["transactions"][8]["decodedIntent"]["amount"],
            "1000000000000000",
        )
        self.assertEqual(
            self.plan["transactions"][9]["decodedIntent"]["amount"],
            "2000000000000",
        )
        self.assertEqual(
            self.plan["executionClock"]["swapDeadlineTransactionIndexes"],
            [10, 21, 22],
        )
        self.assertEqual(
            self.plan["executionClock"]["permit2WindowLastTransactionIndex"],
            22,
        )
        self.assertEqual(
            self.plan["executionClock"]["swapDeadlineUnix"]
            - self.plan["executionClock"]["referenceTimestampUnix"],
            7 * 24 * 60 * 60,
        )
        self.assertEqual(
            self.plan["executionClock"]["permit2ExpirationUnix"]
            - self.plan["executionClock"]["referenceTimestampUnix"],
            8 * 24 * 60 * 60,
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
