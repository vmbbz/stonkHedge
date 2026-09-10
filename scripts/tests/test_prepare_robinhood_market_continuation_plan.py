import ast
import copy
import importlib.util
import json
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPT = REPOSITORY / "scripts" / "prepare_robinhood_market_continuation_plan.py"
PLAN_PATH = (
    REPOSITORY
    / "manifests"
    / "markets"
    / "robinhood-testnet-pltr-weth-continuation-candidate-2026-09-10.json"
)
OPERATOR_SCRIPT = REPOSITORY / "scripts" / "operate_robinhood_market_genesis.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


planner = load_module("continuation_planner_test", SCRIPT)
operator = load_module("continuation_operator_test", OPERATOR_SCRIPT)


class ContinuationPlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    def test_committed_plan_is_exact_offline_generator_output(self):
        regenerated = planner.build_continuation_plan(
            planner.DEFAULT_PREVIOUS_PLAN,
            planner.DEFAULT_PROGRESS,
            planner.DEFAULT_ACCEPTANCE,
            planner.DEFAULT_AUTHORIZATION,
            SCRIPT,
        )
        self.assertEqual(self.plan, regenerated)
        operator.validate_execution_plan(self.plan, PLAN_PATH)

    def test_sequence_repeats_only_pltr_permit_then_finishes_original_intents(self):
        self.assertEqual(
            [transaction["sourceOrdinal"] for transaction in self.plan["transactions"]],
            [3, 4, 5, 6, 7, 8, 9, 10, 11],
        )
        self.assertEqual(
            [transaction["nonce"] for transaction in self.plan["transactions"]],
            list(range(4, 13)),
        )
        self.assertEqual(self.plan["startNonce"], 4)
        self.assertEqual(self.plan["nextNonce"], 13)
        self.assertTrue(
            all(
                transaction["authorizedForBroadcast"] is False
                for transaction in self.plan["transactions"]
            )
        )

    def test_state_schedule_models_refresh_mint_and_complete_cleanup(self):
        schedule = self.plan["stateSchedule"]
        self.assertEqual(len(schedule), 10)
        self.assertEqual(schedule[0]["originalCompletedSteps"], 4)
        self.assertNotEqual(
            schedule[0]["permit2"]["PLTR"]["expiration"],
            schedule[1]["permit2"]["PLTR"]["expiration"],
        )
        self.assertEqual(schedule[2]["permit2"]["WETH"]["amount"], "2000000000000000")
        self.assertEqual(schedule[4]["originalCompletedSteps"], 7)
        self.assertEqual(schedule[-1]["originalCompletedSteps"], 12)
        self.assertEqual(schedule[-1]["erc20"], {"PLTR": "0", "WETH": "0"})
        self.assertEqual(
            schedule[-1]["permit2"]["PLTR"]["amount"],
            "0",
        )
        self.assertEqual(
            [operator.expected_allowances(self.plan, i) for i in (0, 4, 9)],
            [
                (2000000000000000000, 2000000000000000, 2000000000000000000, 0),
                (22157655355120211, 20000000000000, 22157655355120211, 20000000000000),
                (0, 0, 0, 0),
            ],
        )
        self.assertEqual(
            self.plan["executionClock"]["liquidityDeadlineUnix"]
            - self.plan["executionClock"]["referenceTimestampUnix"],
            14_400,
        )
        self.assertEqual(
            self.plan["executionClock"]["permit2ExpirationUnix"]
            - self.plan["executionClock"]["referenceTimestampUnix"],
            21_600,
        )

    def test_committed_nine_step_report_is_fully_revalidated(self):
        report_path = (
            REPOSITORY
            / "manifests"
            / "markets"
            / "robinhood-testnet-pltr-weth-continuation-operator-simulation-2026-09-10.json"
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        operator.validate_simulation_report(
            report,
            self.plan,
            plan_file_hash=operator.file_sha256(PLAN_PATH),
            operator_hash=operator.file_sha256(OPERATOR_SCRIPT),
        )
        self.assertEqual(report["stepCount"], 9)

    def test_liquidity_nft_argument_follows_source_phase(self):
        operator.validate_liquidity_token_argument(3, None, self.plan)
        operator.validate_liquidity_token_argument(4, 3896, self.plan)
        with self.assertRaisesRegex(ValueError, "required"):
            operator.validate_liquidity_token_argument(4, None, self.plan)
        with self.assertRaisesRegex(ValueError, "only"):
            operator.validate_liquidity_token_argument(3, 3896, self.plan)

    def test_authorization_must_explicitly_bind_longer_clock_policy(self):
        clock = self.plan["executionClock"]
        authorization = {
            "status": "AUTHORIZED_MARKET_GENESIS_ONE_TRANSACTION_AT_A_TIME",
            "chainId": 46630,
            "actor": self.plan["actor"]["address"],
            "executionPlanBodySha256": self.plan["executionPlanBodySha256"],
            "executionPlanFileSha256": "11" * 32,
            "operatorSha256": "22" * 32,
            "operatorSimulationReportSha256": "33" * 32,
            "maximumTransactionIndex": 8,
            "executionPolicy": "ONE_TRANSACTION_WAIT_VERIFY_STOP_ON_MISMATCH",
            "testnetOnly": True,
            "approvedBy": "owner",
            "approvedAt": self.plan["network"]["referenceBlockTimestamp"],
            "continuationClockPolicyAcceptance": {
                "accepted": True,
                "liquidityDeadlineSeconds": 14_400,
                "permit2AllowanceLifetimeSeconds": 21_600,
                "liquidityDeadlineUnix": clock["liquidityDeadlineUnix"],
                "permit2ExpirationUnix": clock["permit2ExpirationUnix"],
            },
        }
        kwargs = {
            "index": 8,
            "plan_file_hash": "11" * 32,
            "operator_hash": "22" * 32,
            "simulation_report_hash": "33" * 32,
        }
        operator.validate_authorization(authorization, self.plan, **kwargs)
        for field, replacement in (
            ("accepted", False),
            ("liquidityDeadlineSeconds", 3_600),
            ("permit2AllowanceLifetimeSeconds", 7_200),
            ("liquidityDeadlineUnix", clock["liquidityDeadlineUnix"] + 1),
            ("permit2ExpirationUnix", clock["permit2ExpirationUnix"] + 1),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(authorization)
                changed["continuationClockPolicyAcceptance"][field] = replacement
                with self.assertRaisesRegex(ValueError, "clock policy"):
                    operator.validate_authorization(changed, self.plan, **kwargs)

    def test_plan_tampering_is_rejected(self):
        changed = copy.deepcopy(self.plan)
        changed["transactions"][0]["nonce"] = 5
        changed["executionPlanBodySha256"] = planner.execution_plan_body_sha256(changed)
        with self.assertRaisesRegex(ValueError, "nonce"):
            operator.validate_execution_plan(changed, PLAN_PATH)

    def test_generator_has_no_rpc_key_signing_or_broadcast_calls(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertFalse(
            calls.intersection(
                {"urlopen", "request", "sign", "send", "send_raw_transaction"}
            )
        )
        source = SCRIPT.read_text(encoding="utf-8").lower()
        self.assertNotIn("private_key", source)
        self.assertNotIn("eth_sendrawtransaction", source)


if __name__ == "__main__":
    unittest.main()
