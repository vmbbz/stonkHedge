import copy
import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "operate_robinhood_lifecycle.py"
SPEC = importlib.util.spec_from_file_location("lifecycle_operator", SCRIPT)
operator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(operator)


class LifecycleOperatorTests(unittest.TestCase):
    def setUp(self):
        self.plan = operator.load_json(operator.DEFAULT_PLAN)

    def test_committed_candidate_passes_strict_regeneration(self):
        operator.validate_execution_plan(self.plan, operator.DEFAULT_PLAN)

    def test_confirmation_binds_plan_index_sender_and_nonce(self):
        transaction = self.plan["transactions"][16]
        phrase = operator.confirmation_phrase(
            operator.file_sha256(operator.DEFAULT_PLAN),
            16,
            transaction["sender"],
            transaction["nonce"],
        )
        self.assertIn("INDEX_16", phrase)
        self.assertIn("SENDER_eef5750f", phrase)
        self.assertTrue(phrase.endswith("NONCE_5"))

    def test_plan_sender_nonce_and_authority_mutations_are_rejected(self):
        for mutate, message in (
            (
                lambda value: value["authorization"].__setitem__("signing", True),
                "authorization",
            ),
            (
                lambda value: value["transactions"][16].__setitem__("nonce", 6),
                "body hash",
            ),
            (
                lambda value: value["transactions"][16].__setitem__(
                    "to", value["market"]["stockRegistry"]
                ),
                "body hash",
            ),
        ):
            changed = copy.deepcopy(self.plan)
            mutate(changed)
            with self.assertRaisesRegex(ValueError, message):
                operator.validate_execution_plan(changed, operator.DEFAULT_PLAN)

    def test_allowance_and_leg_schedule_reconciles_key_boundaries(self):
        writer = self.plan["roles"]["writer"]["address"]
        buyer = self.plan["roles"]["buyer"]["address"]
        self.assertEqual(operator._expected_allowances(self.plan, 0)[writer]["pltrToPermit2"], 0)
        self.assertEqual(operator._expected_allowances(self.plan, 5)[writer]["pltrPermit2ToRouter"], 2_000_000_000_000_000)
        self.assertEqual(operator._expected_allowances(self.plan, 7)[writer]["wethPermit2ToRouter"], 1_000_000_000_000)
        self.assertEqual(operator._expected_allowances(self.plan, 19)[writer]["pltrPermit2ToRouter"], 0)
        self.assertEqual(operator._expected_allowances(self.plan, 25)[buyer]["pltrToTracker0"], 0)
        self.assertEqual(operator._expected_open_legs(17), {"writer": 1, "buyer": 1})
        self.assertEqual(operator._expected_open_legs(20), {"writer": 1, "buyer": 0})
        self.assertEqual(operator._expected_open_legs(21), {"writer": 0, "buyer": 0})

    def test_authorization_requires_exact_scope_and_exclusions(self):
        plan_hash = operator.file_sha256(operator.DEFAULT_PLAN)
        operator_hash = operator.file_sha256(SCRIPT)
        simulation_hash = "11" * 32
        authorization = {
            "status": operator.AUTHORIZATION_STATUS,
            "network": {"chainId": 46630},
            "roles": {
                "writer": self.plan["roles"]["writer"]["address"],
                "buyer": self.plan["roles"]["buyer"]["address"],
            },
            "evidenceBindings": {
                "executionPlanBodySha256": self.plan["executionPlanBodySha256"],
                "executionPlanFileSha256": plan_hash,
                "operatorSha256": operator_hash,
                "simulationReportSha256": simulation_hash,
            },
            "maximumTransactionIndex": 24,
            "policy": "ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH",
            "permittedScope": {
                "wrapBuyerWeth": True,
                "exactApprovals": True,
                "fourBoundedSwaps": True,
                "boundedCollateralDeposits": True,
                "matchedOptionOpenAndClose": True,
                "allowanceCleanup": True,
            },
            "excludedScope": {
                "withdrawals": True,
                "otherMarkets": True,
                "issuerAdministration": True,
                "factoryAdministration": True,
                "deployments": True,
                "mainnet": True,
            },
        }
        operator.validate_authorization(
            authorization,
            self.plan,
            index=0,
            plan_file_hash=plan_hash,
            operator_hash=operator_hash,
            simulation_report_hash=simulation_hash,
        )
        authorization["excludedScope"]["withdrawals"] = False
        with self.assertRaisesRegex(ValueError, "exclusions"):
            operator.validate_authorization(
                authorization,
                self.plan,
                index=0,
                plan_file_hash=plan_hash,
                operator_hash=operator_hash,
                simulation_report_hash=simulation_hash,
            )


if __name__ == "__main__":
    unittest.main()
