import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "simulate_robinhood_lifecycle_execution_operator.py"
SPEC = importlib.util.spec_from_file_location("lifecycle_operator_simulator", SCRIPT)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


class LifecycleOperatorSimulatorTests(unittest.TestCase):
    def test_runner_is_loopback_only_and_has_no_signing_or_raw_submission(self):
        source = SCRIPT.read_text(encoding="utf-8").lower()
        self.assertEqual(runner.DEFAULT_RPC_URL, "http://127.0.0.1:8549")
        self.assertIn("validate_local_rpc_url", source)
        self.assertNotIn("keystore", source)
        self.assertNotIn("private_key", source)
        self.assertNotIn("eth_sendrawtransaction", source)
        self.assertNotIn("sign_digest", source)


if __name__ == "__main__":
    unittest.main()
