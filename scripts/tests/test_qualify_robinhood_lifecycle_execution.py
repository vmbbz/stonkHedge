import copy
import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "qualify_robinhood_lifecycle_execution.py"
SPEC = importlib.util.spec_from_file_location("lifecycle_execution_qualifier", SCRIPT)
qualifier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(qualifier)


class LifecycleExecutionQualifierTests(unittest.TestCase):
    def test_committed_preflight_is_hash_bound_and_grants_no_authority(self):
        preflight = qualifier.load_json(qualifier.DEFAULT_OUTPUT)
        body = dict(preflight)
        expected = body.pop("preflightBodySha256")
        self.assertEqual(expected, qualifier.canonical_sha256(body))
        self.assertEqual(
            preflight["status"],
            "PASS_PUBLIC_LIFECYCLE_EXECUTION_PREFLIGHT_NO_AUTHORITY",
        )
        self.assertTrue(all(value is False for value in preflight["authorization"].values()))
        self.assertFalse(preflight["publicExecution"]["ready"])
        self.assertFalse(preflight["publicExecution"]["broadcastAttempted"])
        for role in ("writer", "buyer"):
            self.assertEqual(
                preflight["pendingNonces"][role],
                preflight["actors"][role]["confirmedNonce"],
            )

    def test_actor_drift_is_rejected(self):
        plan = qualifier.load_json(qualifier.DEFAULT_PLAN)
        captured = copy.deepcopy(plan["roles"]["writer"])
        captured["initialAllowances"] = copy.deepcopy(
            plan["roles"]["writer"]["initialAllowances"]
        )
        qualifier._assert_actor_unchanged("writer", captured, plan["roles"]["writer"])
        captured["pltrBalance"] = str(int(captured["pltrBalance"]) - 1)
        with self.assertRaisesRegex(RuntimeError, "pltrBalance changed"):
            qualifier._assert_actor_unchanged(
                "writer", captured, plan["roles"]["writer"]
            )

    def test_source_is_read_only_and_has_no_wallet_or_submission_path(self):
        source = SCRIPT.read_text(encoding="utf-8").lower()
        self.assertIn("castreadonlyrpc", source)
        self.assertNotIn("keystore", source)
        self.assertNotIn("eth_send", source)
        self.assertNotIn("private_key", source)
        self.assertNotIn("sign_digest", source)


if __name__ == "__main__":
    unittest.main()
