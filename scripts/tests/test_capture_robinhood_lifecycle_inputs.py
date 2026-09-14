import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "capture_robinhood_lifecycle_inputs.py"
SPEC = importlib.util.spec_from_file_location("lifecycle_snapshotter", SCRIPT)
snapshotter = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(snapshotter)


class HeaderOnlyRpc:
    def call(self, method, params):
        if method == "eth_chainId":
            return hex(46630)
        if method == "eth_blockNumber":
            return hex(123)
        if method == "eth_getBlockByNumber":
            return {"number": hex(123), "hash": "0x" + "12" * 32, "timestamp": hex(456)}
        raise AssertionError(f"unexpected RPC call before role gate: {method} {params}")


class LifecycleSnapshotterTests(unittest.TestCase):
    def setUp(self):
        self.chain = snapshotter.load_json(snapshotter.DEFAULT_CHAIN)
        self.genesis = snapshotter.load_json(snapshotter.DEFAULT_GENESIS)
        self.policy = snapshotter.load_json(snapshotter.DEFAULT_POLICY)

    def test_rejects_shared_deployer_as_buyer_before_contract_reads(self):
        with self.assertRaisesRegex(RuntimeError, "buyer must be a third account"):
            snapshotter.capture(
                HeaderOnlyRpc(),
                chain=self.chain,
                genesis=self.genesis,
                policy=self.policy,
                buyer_address=self.chain["deployer"]["address"],
            )

    def test_generated_snapshot_is_pinned_clean_and_honest_about_twap(self):
        snapshot = snapshotter.load_json(snapshotter.DEFAULT_OUTPUT)
        self.assertEqual(snapshot["schemaVersion"], 2)
        self.assertIn("PINNED_SNAPSHOT_PASS_THIRD_BUYER", snapshot["status"])
        self.assertIsNone(snapshot["marketState"]["twapTick"])
        self.assertEqual(
            snapshot["marketState"]["twapObservation"],
            "NOT_CAPTURED_SPOT_TICK_IS_NOT_LABELLED_AS_TWAP",
        )
        self.assertNotEqual(
            snapshot["actors"]["buyer"]["address"],
            snapshot["actors"]["writer"]["address"],
        )
        self.assertIn("UNPRIVILEGED", snapshot["actors"]["buyer"]["role"])
        self.assertTrue(all(value is False for value in snapshot["authorization"].values()))
        for actor in snapshot["actors"].values():
            self.assertEqual(actor["openLegs"], 0)
            self.assertEqual(actor["collateralTracker0Shares"], "0")
            self.assertEqual(actor["collateralTracker1Shares"], "0")
            self.assertEqual(actor["initialAllowances"]["pltrToPermit2"], "0")
            self.assertEqual(actor["initialAllowances"]["wethToPermit2"], "0")
            self.assertEqual(actor["initialAllowances"]["pltrToTracker0"], "0")
            self.assertEqual(actor["initialAllowances"]["wethToTracker1"], "0")
            self.assertEqual(actor["initialAllowances"]["pltrPermit2ToRouter"][0], 0)
            self.assertEqual(actor["initialAllowances"]["wethPermit2ToRouter"][0], 0)

    def test_source_has_read_only_rpc_and_no_wallet_or_submission_primitive(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("CastReadOnlyRpc", source)
        self.assertNotIn("private_key", source.lower())
        self.assertNotIn("keystore", source.lower())
        self.assertNotIn("eth_send", source)
        self.assertNotIn("cast wallet", source.lower())
        self.assertNotIn("sign_transaction", source.lower())


if __name__ == "__main__":
    unittest.main()
