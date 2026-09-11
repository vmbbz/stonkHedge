import copy
import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "simulate_robinhood_two_actor_lifecycle_fork.py"
)
SPEC = importlib.util.spec_from_file_location("lifecycle_simulator", SCRIPT)
simulator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(simulator)


class LifecycleForkSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(simulator.DEFAULT_PLAN.read_text(encoding="utf-8"))

    def test_committed_plan_passes_strict_offline_validation(self):
        simulator.validate_plan(self.plan, simulator.DEFAULT_PLAN)

    def test_only_http_loopback_rpc_is_allowed(self):
        for allowed in (
            "http://127.0.0.1:8548",
            "http://localhost:8548",
            "http://[::1]:8548",
        ):
            simulator.validate_local_rpc_url(allowed)
        for rejected in (
            "https://rpc.testnet.chain.robinhood.com",
            "http://192.0.2.1:8548",
            "ws://127.0.0.1:8548",
            "http://user:pass@127.0.0.1:8548",
            "http://127.0.0.1",
            "http://127.0.0.1:8548/path",
        ):
            with self.assertRaises(ValueError):
                simulator.validate_local_rpc_url(rejected)

    def test_rejects_authority_nonce_and_target_expansion(self):
        authorized = copy.deepcopy(self.plan)
        authorized["authorization"]["signing"] = True
        with self.assertRaisesRegex(ValueError, "authorization"):
            simulator.validate_plan(authorized, simulator.DEFAULT_PLAN)

        nonce_bound = copy.deepcopy(self.plan)
        nonce_bound["transactions"][0]["nonce"] = 16
        with self.assertRaisesRegex(ValueError, "binds a nonce"):
            simulator.validate_plan(nonce_bound, simulator.DEFAULT_PLAN)

        admin_target = copy.deepcopy(self.plan)
        admin_target["transactions"][0]["to"] = admin_target["market"][
            "stockRegistry"
        ]
        with self.assertRaisesRegex(ValueError, "outside the user-call allowlist"):
            simulator.validate_plan(admin_target, simulator.DEFAULT_PLAN)

    def test_source_has_no_wallet_or_signing_import(self):
        source = SCRIPT.read_text(encoding="utf-8")
        tree = compile(source, str(SCRIPT), "exec", flags=0, dont_inherit=True)
        self.assertIsNotNone(tree)
        self.assertNotIn("eth_sendRawTransaction", source)
        self.assertNotIn("private_key", source.lower())
        self.assertNotIn("keystore", source.lower())
        self.assertNotIn("cast wallet", source.lower())
        self.assertEqual(simulator.DEFAULT_RPC_URL, "http://127.0.0.1:8548")


if __name__ == "__main__":
    unittest.main()
