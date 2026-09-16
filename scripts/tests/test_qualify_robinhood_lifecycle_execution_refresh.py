import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "qualify_robinhood_lifecycle_execution_refresh.py"
SPEC = importlib.util.spec_from_file_location("lifecycle_refresh_qualifier", SCRIPT)
qualifier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(qualifier)


class LifecycleRefreshQualifierTests(unittest.TestCase):
    def test_qualifier_has_no_signing_or_submission_path(self):
        source = SCRIPT.read_text(encoding="utf-8").lower()
        self.assertNotIn("private_key", source)
        self.assertNotIn("keystore", source)
        self.assertNotIn("eth_sendrawtransaction", source)
        self.assertNotIn("sign_digest", source)

    def test_committed_preflight_is_canonical_and_prefix_bound(self):
        value = qualifier.load_json(qualifier.DEFAULT_OUTPUT)
        body = dict(value)
        expected = body.pop("preflightBodySha256")
        self.assertEqual(expected, qualifier.canonical_sha256(body))
        self.assertEqual(value["completedPrefixCount"], 5)
        self.assertEqual(len(value["evidencePrefix"]), 5)
        self.assertEqual(
            [item["transactionIndex"] for item in value["evidencePrefix"]],
            [0, 1, 2, 3, 4],
        )
        self.assertFalse(value["authorization"]["signing"])
        self.assertFalse(value["authorization"]["publicBroadcast"])


if __name__ == "__main__":
    unittest.main()
