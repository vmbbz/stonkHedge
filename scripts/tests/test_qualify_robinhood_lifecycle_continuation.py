import importlib.util
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "qualify_robinhood_lifecycle_continuation.py"
)
SPEC = importlib.util.spec_from_file_location(
    "lifecycle_continuation_qualifier", SCRIPT
)
qualifier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(qualifier)


class LifecycleContinuationQualifierTests(unittest.TestCase):
    def test_qualifier_has_no_secret_or_submission_path(self):
        source = SCRIPT.read_text(encoding="utf-8").lower()
        self.assertNotIn("private_key", source)
        self.assertNotIn("keystore", source)
        self.assertNotIn("eth_sendrawtransaction", source)
        self.assertNotIn("sign_digest", source)

    def test_committed_preflight_is_canonical_and_receipt_bound(self):
        value = qualifier.load_json(qualifier.DEFAULT_OUTPUT)
        body = dict(value)
        expected = body.pop("preflightBodySha256")
        self.assertEqual(expected, qualifier.canonical_sha256(body))
        self.assertEqual(value["priorExecutionStartIndex"], 5)
        self.assertEqual(value["completedPrefixCount"], 8)
        self.assertEqual(
            [item["transactionIndex"] for item in value["evidencePrefix"]],
            list(range(8)),
        )
        self.assertEqual(value["checks"]["evidenceFileCount"], 3)
        self.assertEqual(value["checks"]["publicReceiptCount"], 8)
        self.assertFalse(value["authorization"]["signing"])
        self.assertFalse(value["authorization"]["publicBroadcast"])


if __name__ == "__main__":
    unittest.main()
