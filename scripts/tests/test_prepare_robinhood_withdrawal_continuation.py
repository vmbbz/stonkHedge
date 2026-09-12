import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "prepare_robinhood_withdrawal_continuation.py"
)
SPEC = importlib.util.spec_from_file_location("withdrawal_preparer", SCRIPT)
preparer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(preparer)


class WithdrawalContinuationPreparerTests(unittest.TestCase):
    def setUp(self):
        self.lifecycle = preparer.load_json(preparer.DEFAULT_LIFECYCLE_PLAN)
        self.rehearsal = preparer.load_json(preparer.DEFAULT_REHEARSAL)

    def _fresh_unprivileged_fixture(self, directory: Path):
        lifecycle = copy.deepcopy(self.lifecycle)
        lifecycle["roles"]["buyer"]["address"] = "0x1111111111111111111111111111111111111111"
        lifecycle["roles"]["buyer"]["role"] = (
            "UNPRIVILEGED_THIRD_ACTOR_BOUNDED_TEST_BUYER"
        )
        body = dict(lifecycle)
        body.pop("planBodySha256")
        lifecycle["planBodySha256"] = preparer.canonical_sha256(body)
        lifecycle_path = directory / "lifecycle.json"
        lifecycle_path.write_text(json.dumps(lifecycle, indent=2) + "\n", encoding="utf-8")

        rehearsal = copy.deepcopy(self.rehearsal)
        rehearsal["sourceBindings"]["lifecyclePlanBodySha256"] = lifecycle[
            "planBodySha256"
        ]
        rehearsal["sourceBindings"]["lifecyclePlanFileSha256"] = preparer.file_sha256(
            lifecycle_path
        )
        terminal = rehearsal["milestones"]["afterIndex24"]
        for role in ("writer", "buyer"):
            for tracker_index in (0, 1):
                assets = int(terminal[role][f"tracker{tracker_index}Assets"])
                terminal[role][f"tracker{tracker_index}MaxWithdraw"] = str(assets - 1)
        rehearsal_path = directory / "rehearsal.json"
        rehearsal_path.write_text(json.dumps(rehearsal, indent=2) + "\n", encoding="utf-8")
        return lifecycle, lifecycle_path, rehearsal, rehearsal_path

    def test_current_privileged_deployer_buyer_is_not_execution_eligible(self):
        with self.assertRaisesRegex(ValueError, "third unprivileged buyer"):
            preparer.build_withdrawal_plan(
                self.lifecycle,
                preparer.DEFAULT_LIFECYCLE_PLAN,
                self.rehearsal,
                preparer.DEFAULT_REHEARSAL,
            )

    def test_builds_four_nonce_free_state_derived_withdrawals(self):
        with tempfile.TemporaryDirectory() as name:
            lifecycle, lifecycle_path, rehearsal, rehearsal_path = (
                self._fresh_unprivileged_fixture(Path(name))
            )
            plan = preparer.build_withdrawal_plan(
                lifecycle,
                lifecycle_path,
                rehearsal,
                rehearsal_path,
                script_path=SCRIPT,
            )

        self.assertEqual(plan["transactionCount"], 4)
        self.assertEqual(
            [transaction["ordinal"] for transaction in plan["transactions"]],
            [0, 1, 2, 3],
        )
        self.assertEqual(
            [transaction["sender"] for transaction in plan["transactions"]],
            [
                "0x1111111111111111111111111111111111111111",
                "0x1111111111111111111111111111111111111111",
                lifecycle["roles"]["writer"]["address"].lower(),
                lifecycle["roles"]["writer"]["address"].lower(),
            ],
        )
        self.assertTrue(
            all(transaction["nonce"] is None for transaction in plan["transactions"])
        )
        self.assertTrue(all(value is False for value in plan["authorization"].values()))
        self.assertFalse(plan["publicExecution"]["ready"])
        self.assertEqual(
            plan["planBodySha256"],
            preparer.canonical_sha256(
                {
                    key: value
                    for key, value in plan.items()
                    if key != "planBodySha256"
                }
            ),
        )
        for transaction in plan["transactions"]:
            self.assertRegex(transaction["calldata"], r"^0x[0-9a-f]+$")
            self.assertRegex(transaction["calldataKeccak256"], r"^0x[0-9a-f]{64}$")
            self.assertEqual(
                transaction["decodedIntent"]["assets"],
                transaction["decodedIntent"]["sourceMaxWithdraw"],
            )

    def test_rejects_missing_state_derivation_and_large_residual(self):
        with tempfile.TemporaryDirectory() as name:
            lifecycle, lifecycle_path, rehearsal, rehearsal_path = (
                self._fresh_unprivileged_fixture(Path(name))
            )
            del rehearsal["milestones"]["afterIndex24"]["writer"][
                "tracker0MaxWithdraw"
            ]
            with self.assertRaisesRegex(ValueError, "omits fresh derivation"):
                preparer.build_withdrawal_plan(
                    lifecycle,
                    lifecycle_path,
                    rehearsal,
                    rehearsal_path,
                    script_path=SCRIPT,
                )

            lifecycle, lifecycle_path, rehearsal, rehearsal_path = (
                self._fresh_unprivileged_fixture(Path(name))
            )
            assets = int(
                rehearsal["milestones"]["afterIndex24"]["writer"][
                    "tracker0Assets"
                ]
            )
            rehearsal["milestones"]["afterIndex24"]["writer"][
                "tracker0MaxWithdraw"
            ] = str(assets - preparer.MAX_RESIDUAL_RAW_UNITS - 1)
            with self.assertRaisesRegex(ValueError, "residual exceeds"):
                preparer.build_withdrawal_plan(
                    lifecycle,
                    lifecycle_path,
                    rehearsal,
                    rehearsal_path,
                    script_path=SCRIPT,
                )

    def test_source_has_no_rpc_wallet_signing_or_submission_primitive(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("urllib", source)
        self.assertNotIn("requests", source)
        self.assertNotIn("private_key", source.lower())
        self.assertNotIn("keystore", source.lower())
        self.assertNotIn("eth_send", source)
        self.assertNotIn("cast wallet", source.lower())


if __name__ == "__main__":
    unittest.main()
